from datetime import datetime
from io import BytesIO

import qrcode
from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .server import SharedFolderServer, detect_local_ip


class LogEmitter(QObject):
    message = pyqtSignal(str)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LAN Folder Share")
        self.setMinimumSize(860, 620)

        self.server = SharedFolderServer()
        self.local_ip = detect_local_ip()
        self.selected_folder = ""

        self.log_emitter = LogEmitter()
        self.log_emitter.message.connect(self.append_log)

        self._build_ui()
        self.refresh_url()
        self.set_status(False)

    def _build_ui(self):
        wrapper = QWidget()
        self.setCentralWidget(wrapper)

        root_layout = QVBoxLayout(wrapper)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        header = QLabel("Share a local folder to any phone on your LAN")
        header.setStyleSheet("font-size: 18px; font-weight: 600;")
        root_layout.addWidget(header)

        folder_group = QGroupBox("Shared Folder")
        folder_layout = QHBoxLayout(folder_group)
        self.path_label = QLabel("No folder selected")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("padding: 6px; border: 1px solid #d9d9d9; border-radius: 6px;")

        select_btn = QPushButton("Select Folder")
        select_btn.clicked.connect(self.select_folder)

        folder_layout.addWidget(self.path_label, stretch=1)
        folder_layout.addWidget(select_btn)
        root_layout.addWidget(folder_group)

        net_group = QGroupBox("Network")
        net_layout = QFormLayout(net_group)
        self.ip_value = QLabel(self.local_ip)

        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(8000)
        self.port_input.valueChanged.connect(self.refresh_url)

        self.url_value = QLabel()
        self.url_value.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.delete_password_input = QLineEdit()
        self.delete_password_input.setPlaceholderText("Optional password required for delete action")
        self.delete_password_input.setEchoMode(QLineEdit.Password)

        net_layout.addRow("Local IP:", self.ip_value)
        net_layout.addRow("Port:", self.port_input)
        net_layout.addRow("URL:", self.url_value)
        net_layout.addRow("Delete Password (optional):", self.delete_password_input)
        root_layout.addWidget(net_group)

        controls_group = QGroupBox("Controls")
        controls_layout = QHBoxLayout(controls_group)
        self.start_btn = QPushButton("Start Sharing")
        self.stop_btn = QPushButton("Stop Sharing")
        self.status_value = QLabel("Stopped")
        self.status_value.setAlignment(Qt.AlignCenter)
        self.status_value.setFixedWidth(120)

        self.start_btn.clicked.connect(self.start_server)
        self.stop_btn.clicked.connect(self.stop_server)

        controls_layout.addWidget(self.start_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addWidget(self.status_value)
        controls_layout.addStretch()
        root_layout.addWidget(controls_group)

        bottom_layout = QGridLayout()

        qr_group = QGroupBox("QR Code")
        qr_layout = QVBoxLayout(qr_group)
        self.qr_label = QLabel("QR code appears when sharing starts")
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setMinimumHeight(220)
        self.qr_label.setStyleSheet("border: 1px dashed #c5c5c5; border-radius: 8px; padding: 8px;")
        qr_layout.addWidget(self.qr_label)

        log_group = QGroupBox("Logs")
        log_layout = QVBoxLayout(log_group)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)

        bottom_layout.addWidget(qr_group, 0, 0)
        bottom_layout.addWidget(log_group, 0, 1)
        bottom_layout.setColumnStretch(0, 1)
        bottom_layout.setColumnStretch(1, 2)

        root_layout.addLayout(bottom_layout)

    def refresh_url(self):
        self.local_ip = detect_local_ip()
        self.ip_value.setText(self.local_ip)
        url = f"http://{self.local_ip}:{self.port_input.value()}"
        self.url_value.setText(url)

    def set_status(self, running: bool):
        if running:
            self.status_value.setText("Running")
            self.status_value.setStyleSheet(
                "background: #e7f8ed; color: #1f6f43; padding: 6px; border-radius: 8px; font-weight: 600;"
            )
        else:
            self.status_value.setText("Stopped")
            self.status_value.setStyleSheet(
                "background: #fdecea; color: #8b1d18; padding: 6px; border-radius: 8px; font-weight: 600;"
            )

        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.port_input.setEnabled(not running)

    def append_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {message}")

    def _log_from_server(self, message: str):
        self.log_emitter.message.emit(message)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select folder to share")
        if folder:
            self.selected_folder = folder
            self.path_label.setText(folder)
            self.append_log(f"Selected folder: {folder}")

    def _show_qr(self, url: str):
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(url)
        qr.make(fit=True)

        image = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        image.save(buffer, format="PNG")

        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue(), "PNG")
        scaled = pixmap.scaled(220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.qr_label.setPixmap(scaled)

    def start_server(self):
        if not self.selected_folder:
            QMessageBox.warning(self, "Folder Required", "Please select a folder before starting sharing.")
            return

        if self.server.is_running:
            self.append_log("Server is already running.")
            return

        self.server.port = self.port_input.value()
        self.refresh_url()

        try:
            self.server.start(
                folder_path=self.selected_folder,
                delete_password=self.delete_password_input.text().strip(),
                log_callback=self._log_from_server,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Failed to Start", f"Could not start server: {exc}")
            self.append_log(f"Start failed: {exc}")
            return

        self._show_qr(self.url_value.text())
        self.set_status(True)
        self.append_log(f"Open from phone: {self.url_value.text()}")

    def stop_server(self):
        if not self.server.is_running:
            self.append_log("Server is not running.")
            return

        self.server.stop()
        self.set_status(False)
        self.qr_label.clear()
        self.qr_label.setText("QR code appears when sharing starts")

    def closeEvent(self, event):
        if self.server.is_running:
            self.server.stop()
        super().closeEvent(event)


def run_app():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
