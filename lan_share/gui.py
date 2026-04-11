import json
from datetime import datetime
from io import BytesIO
from pathlib import Path

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
    QComboBox,
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
        self.setWindowTitle("Quick LAN Folder Share developped by      { Md. Babla Islam } ")
        self.setMinimumSize(860, 620)

        self.server = SharedFolderServer()
        self.local_ip = detect_local_ip()
        self.selected_folder = ""
        self.config_path = Path.home() / ".lan_folder_share_config.json"
        self.app_config = self._load_config()
        self.recent_folders = self.app_config.get("recent_folders", [])

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

        folder_group = QGroupBox("Shared Folder")
        folder_layout = QVBoxLayout(folder_group)
        self.path_label = QLabel("No folder selected")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("padding: 6px; border: 1px solid #d9d9d9; border-radius: 6px;")

        picker_row = QHBoxLayout()
        self.recent_folder_combo = QComboBox()
        self.recent_folder_combo.setMinimumWidth(520)
        self.recent_folder_combo.addItems(self.recent_folders)
        self.recent_folder_combo.setEnabled(bool(self.recent_folders))

        self.use_last_btn = QPushButton("Use Selected Saved Folder")
        self.use_last_btn.clicked.connect(self.use_selected_history_folder)
        self.use_last_btn.setEnabled(bool(self.recent_folders))

        select_btn = QPushButton("Select New Folder")
        select_btn.clicked.connect(self.select_folder)

        picker_row.addWidget(self.recent_folder_combo, stretch=1)
        picker_row.addWidget(self.use_last_btn)
        picker_row.addWidget(select_btn)

        folder_layout.addWidget(self.path_label)
        folder_layout.addLayout(picker_row)
        root_layout.addWidget(folder_group)

        if self.recent_folders:
            self.selected_folder = self.recent_folders[0]
            self.path_label.setText(self.selected_folder)

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
        self.delete_password_input.setText(self.app_config.get("delete_password", ""))
        self.delete_password_input.setPlaceholderText("Optional password required for delete action")
        self.delete_password_input.setEchoMode(QLineEdit.Password)

        self.download_password_input = QLineEdit()
        self.download_password_input.setText(self.app_config.get("download_password", ""))
        self.download_password_input.setPlaceholderText("Optional password required for file download")
        self.download_password_input.setEchoMode(QLineEdit.Password)

        net_layout.addRow("Local IP:", self.ip_value)
        net_layout.addRow("Port:", self.port_input)
        net_layout.addRow("URL:", self.url_value)
        net_layout.addRow("Delete Password (optional):", self.delete_password_input)
        net_layout.addRow("Download Password (optional):", self.download_password_input)
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

        if self.selected_folder:
            self.append_log(f"Loaded last folder: {self.selected_folder}")

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

    def _load_config(self):
        try:
            if not self.config_path.exists():
                return {}
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
            folders = data.get("recent_folders", [])
            valid_folders = [item for item in folders if isinstance(item, str) and item.strip()]
            data["recent_folders"] = valid_folders[:8]
            return data
        except Exception:
            return {}

    def _save_config(self):
        data = {
            "recent_folders": getattr(self, "recent_folders", [])[:8],
            "delete_password": self.delete_password_input.text() if hasattr(self, "delete_password_input") else "",
            "download_password": self.download_password_input.text() if hasattr(self, "download_password_input") else ""
        }
        self.config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _add_recent_folder(self, folder: str):
        normalized = str(Path(folder))
        self.recent_folders = [item for item in self.recent_folders if Path(item) != Path(normalized)]
        self.recent_folders.insert(0, normalized)
        self.recent_folders = self.recent_folders[:8]
        self._save_config()
        self.recent_folder_combo.clear()
        self.recent_folder_combo.addItems(self.recent_folders)
        self.recent_folder_combo.setEnabled(True)
        self.use_last_btn.setEnabled(True)

    def use_selected_history_folder(self):
        folder = self.recent_folder_combo.currentText().strip()
        if not folder:
            QMessageBox.information(self, "No Saved Folder", "No saved folder is available yet.")
            return

        if not Path(folder).is_dir():
            QMessageBox.warning(self, "Folder Missing", "Saved folder does not exist anymore. Please select a new one.")
            self.append_log(f"Saved folder missing: {folder}")
            return

        self.selected_folder = folder
        self.path_label.setText(folder)
        self._add_recent_folder(folder)
        self.append_log(f"Using saved folder: {folder}")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select folder to share")
        if folder:
            self.selected_folder = folder
            self.path_label.setText(folder)
            self._add_recent_folder(folder)
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
                download_password=self.download_password_input.text().strip(),
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
        self._save_config()
        if self.server.is_running:
            self.server.stop()
        super().closeEvent(event)


def run_app():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
