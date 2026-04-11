import os
import shutil
import socket
import tempfile
import threading
import zipfile
from pathlib import Path

from flask import (
    Flask,
  after_this_request,
    abort,
    flash,
    redirect,
    render_template_string,
    request,
  send_file,
    send_from_directory,
    url_for,
)
from werkzeug.serving import make_server
from werkzeug.utils import secure_filename


BROWSE_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>LAN File Share</title>
  <style>
    :root {
      --bg: #f3f6fb;
      --panel: #ffffff;
      --text: #17202a;
      --muted: #516071;
      --line: #dde5ef;
      --accent: #147efb;
      --accent-2: #0f69d7;
      --danger: #b3261e;
      --radius: 12px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 16px;
      font-family: "Segoe UI", Tahoma, sans-serif;
      background: radial-gradient(circle at top right, #e8f2ff 0%, var(--bg) 55%);
      color: var(--text);
    }
    .container {
      width: min(860px, 100%);
      margin: 0 auto;
      display: grid;
      gap: 14px;
    }
    .card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: 0 8px 24px rgba(23, 32, 42, 0.08);
      padding: 14px;
    }
    h1 {
      margin: 0 0 6px;
      font-size: clamp(1.2rem, 2vw, 1.5rem);
    }
    .meta { color: var(--muted); font-size: 0.92rem; }
    .breadcrumb {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      font-size: 0.95rem;
    }
    .toolbar {
      display: grid;
      gap: 10px;
    }
    form.upload {
      display: grid;
      grid-template-columns: 1fr 1fr auto;
      gap: 8px;
    }
    .upload-field {
      display: grid;
      gap: 4px;
    }
    .upload-label {
      font-size: 0.82rem;
      color: var(--muted);
      font-weight: 600;
    }
    input[type="file"] {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px;
      background: #fff;
    }
    button, .btn {
      border: 0;
      border-radius: 10px;
      padding: 9px 12px;
      color: #fff;
      background: var(--accent);
      cursor: pointer;
      text-decoration: none;
      font-weight: 600;
      font-size: 0.92rem;
      transition: background 160ms ease;
    }
    .toolbar .btn,
    .toolbar button[type="submit"] {
      padding: 6px 10px;
      border-radius: 8px;
      font-size: 0.86rem;
      align-self: end;
    }
    button:hover, .btn:hover { background: var(--accent-2); }
    .progress-wrap {
      height: 8px;
      background: #e8edf3;
      border-radius: 999px;
      overflow: hidden;
      display: none;
    }
    .progress {
      width: 0%;
      height: 100%;
      background: linear-gradient(90deg, #45b6fe, #147efb);
      transition: width 140ms linear;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.95rem;
    }
    th, td {
      text-align: left;
      border-bottom: 1px solid var(--line);
      padding: 10px 6px;
      vertical-align: middle;
    }
    tbody tr:hover {
      background: #f8fbff;
    }
    tr:last-child td { border-bottom: 0; }
    .muted { color: var(--muted); }
    .name {
      max-width: 45vw;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      display: inline-block;
      vertical-align: bottom;
    }
    .delete {
      display: inline-flex;
      gap: 6px;
      align-items: center;
    }
    .download {
      display: inline-flex;
      gap: 6px;
      align-items: center;
      margin-right: 8px;
    }
    .download input {
      width: 130px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 6px 8px;
      font-size: 0.85rem;
    }
    .download button {
      background: #1f7a4f;
    }
    .actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
    }
    .actions input[type="password"] {
      width: 130px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 6px 8px;
      font-size: 0.85rem;
    }
    .delete input {
      width: 130px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 6px 8px;
      font-size: 0.85rem;
    }
    .delete button { background: var(--danger); }
    .flash {
      margin: 0;
      padding-left: 18px;
      color: #8b1b17;
      font-size: 0.92rem;
    }
    @media (max-width: 640px) {
      form.upload { grid-template-columns: 1fr; }
      .name { max-width: 38vw; }
      .delete, .download {
        width: 100%;
        margin-right: 0;
      }
      .actions input[type="password"] {
        flex: 1;
        min-width: 0;
      }
      .actions button {
        flex-shrink: 0;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <section class="card">
      <h1>LAN File Share</h1>
      <div class="meta">Folder root: {{ current_rel or '/' }}</div>
    </section>

    <section class="card toolbar">
      <div class="breadcrumb">
        <a class="btn" href="{{ url_for('browse', subpath='') }}">Root</a>
        {% if parent_rel is not none %}
          <a class="btn" href="{{ url_for('browse', subpath=parent_rel) }}">Up</a>
        {% endif %}
      </div>

      <form id="uploadForm" class="upload" method="post" action="{{ url_for('upload_file') }}" enctype="multipart/form-data">
        <input type="hidden" name="target" value="{{ current_rel }}" />
        <label class="upload-field" for="fileInput">
          <span class="upload-label"> Upload Files Here</span>
          <input type="file" id="fileInput" name="files" multiple />
        </label>
        <label class="upload-field" for="folderInput">
          <span class="upload-label"> Upload Folder Here</span>
          <input type="file" id="folderInput" name="files" webkitdirectory directory multiple />
        </label>
        <button type="submit">Upload</button>
      </form>
      <div id="progressWrap" class="progress-wrap">
        <div id="progressBar" class="progress"></div>
      </div>
      <div class="meta" id="progressText"></div>

      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <ul class="flash">
            {% for message in messages %}
              <li>{{ message }}</li>
            {% endfor %}
          </ul>
        {% endif %}
      {% endwith %}
    </section>

    <section class="card">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Type</th>
            <th>Size</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {% for item in items %}
            <tr>
              <td>
                {% if item.is_dir %}
                  <a href="{{ url_for('browse', subpath=item.rel_path) }}"><span class="name">{{ item.name }}/</span></a>
                {% else %}
                  <span class="name">{{ item.name }}</span>
                {% endif %}
              </td>
              <td class="muted">{{ 'Folder' if item.is_dir else 'File' }}</td>
              <td class="muted">{{ item.size_display }}</td>
              <td>
                <div class="actions">
                  {% if item.is_dir %}
                    <form class="download" method="post" action="{{ url_for('download_folder_post') }}">
                      <input type="hidden" name="target" value="{{ item.rel_path }}" />
                      {% if needs_download_password %}
                        <input type="password" name="password" placeholder="Download password" required />
                      {% else %}
                        <input type="hidden" name="password" value="" />
                      {% endif %}
                      <button type="submit">Download ZIP</button>
                    </form>
                  {% else %}
                    <form class="download" method="post" action="{{ url_for('download_file_post') }}">
                      <input type="hidden" name="target" value="{{ item.rel_path }}" />
                      {% if needs_download_password %}
                        <input type="password" name="password" placeholder="Download password" required />
                      {% else %}
                        <input type="hidden" name="password" value="" />
                      {% endif %}
                      <button type="submit">Download</button>
                    </form>
                  {% endif %}
                  <form class="delete" method="post" action="{{ url_for('delete_item') }}" onsubmit="return confirm('Delete ' + {{ item.name|tojson }} + '?');">
                    <input type="hidden" name="target" value="{{ item.rel_path }}" />
                    <input type="hidden" name="return_to" value="{{ current_rel }}" />
                    {% if needs_delete_password %}
                      <input type="password" name="password" placeholder="Delete password" required />
                    {% else %}
                      <input type="hidden" name="password" value="" />
                    {% endif %}
                    <button type="submit">Delete</button>
                  </form>
                </div>
              </td>
            </tr>
          {% else %}
            <tr>
              <td colspan="4" class="muted">This folder is empty.</td>
            </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
  </div>

  <script>
    const uploadForm = document.getElementById('uploadForm');
    const progressWrap = document.getElementById('progressWrap');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');

    uploadForm.addEventListener('submit', function (event) {
      event.preventDefault();
      const fileInput = document.getElementById('fileInput');
      const folderInput = document.getElementById('folderInput');
      if (!fileInput.files.length && !folderInput.files.length) {
        return;
      }

      const formData = new FormData(uploadForm);
      const xhr = new XMLHttpRequest();
      xhr.open('POST', uploadForm.action, true);

      progressWrap.style.display = 'block';
      progressBar.style.width = '0%';
      progressText.textContent = 'Uploading...';

      xhr.upload.onprogress = function (e) {
        if (e.lengthComputable) {
          const pct = Math.round((e.loaded / e.total) * 100);
          progressBar.style.width = pct + '%';
          progressText.textContent = 'Uploading: ' + pct + '%';
        }
      };

      xhr.onload = function () {
        if (xhr.status >= 200 && xhr.status < 400) {
          progressBar.style.width = '100%';
          progressText.textContent = 'Upload complete';
          window.location.reload();
        } else {
          progressText.textContent = 'Upload failed';
        }
      };

      xhr.onerror = function () {
        progressText.textContent = 'Network error during upload';
      };

      xhr.send(formData);
    });
  </script>
</body>
</html>
"""


def detect_local_ip() -> str:
    """Get the likely LAN IP by opening a UDP socket to a public target."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def format_size(size_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size_bytes)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size_bytes} B"


class FlaskServerThread(threading.Thread):
    def __init__(self, app: Flask, host: str, port: int, log_callback):
        super().__init__(daemon=True)
        self._app = app
        self._host = host
        self._port = port
        self._log_callback = log_callback
        self._http_server = None

    def run(self):
        try:
            self._http_server = make_server(self._host, self._port, self._app, threaded=True)
            self._http_server.serve_forever()
        except Exception as exc:
            self._log_callback(f"Server thread error: {exc}")

    def shutdown(self):
        if self._http_server is not None:
            self._http_server.shutdown()


class SharedFolderServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.root_dir = None
        self.delete_password = ""
        self.download_password = ""
        self._app = None
        self._thread = None
        self._log_callback = lambda _msg: None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _log(self, message: str):
        self._log_callback(message)

    def _resolve_inside_root(self, rel_path: str) -> Path:
        root = Path(self.root_dir).resolve()
        cleaned = (rel_path or "").replace("\\", "/").strip("/")
        target = (root / cleaned).resolve()

        if target == root:
            return target
        if root not in target.parents:
            raise PermissionError("Blocked invalid path traversal")
        return target

    def _stream_to_disk(self, file_storage, destination: Path):
        chunk_size = 1024 * 1024
        with destination.open("wb") as output:
            while True:
                chunk = file_storage.stream.read(chunk_size)
                if not chunk:
                    break
                output.write(chunk)

    def _sanitize_relative_upload_path(self, raw_name: str) -> Path | None:
        normalized = (raw_name or "").replace("\\", "/").strip("/")
        if not normalized:
            return None

        safe_parts = []
        for segment in normalized.split("/"):
            if segment in ("", "."):
                continue
            if segment == "..":
                return None
            safe_segment = secure_filename(segment)
            if not safe_segment:
                continue
            safe_parts.append(safe_segment)

        if not safe_parts:
            return None
        return Path(*safe_parts)

    def _unique_destination_path(self, destination: Path) -> Path:
        if not destination.exists():
            return destination

        stem = destination.stem
        suffix = destination.suffix
        counter = 1
        while destination.exists():
            destination = destination.with_name(f"{stem}_{counter}{suffix}")
            counter += 1
        return destination

    def _is_download_password_valid(self, provided_password: str) -> bool:
        if not self.download_password:
            return True
        return provided_password == self.download_password

    def _ensure_port_available(self):
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            probe.bind((self.host, self.port))
        except OSError as exc:
            raise RuntimeError(f"Port {self.port} is unavailable: {exc}") from exc
        finally:
            probe.close()

    def _build_folder_zip(self, folder_path: Path) -> str:
      temp_file = tempfile.NamedTemporaryFile(prefix="lan_share_", suffix=".zip", delete=False)
      zip_path = temp_file.name
      temp_file.close()

      with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
        for path in folder_path.rglob("*"):
          if path.is_file():
            archive.write(path, arcname=path.relative_to(folder_path))
      return zip_path

    def _build_app(self) -> Flask:
        app = Flask(__name__)
        app.secret_key = "lan-file-share-secret"
        app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024 * 5

        @app.before_request
        def log_request():
            self._log(f"[{request.remote_addr}] {request.method} {request.path}")

        @app.route("/", defaults={"subpath": ""})
        @app.route("/browse/<path:subpath>")
        def browse(subpath: str):
            try:
                current_dir = self._resolve_inside_root(subpath)
            except PermissionError:
                abort(403)

            if not current_dir.exists() or not current_dir.is_dir():
                abort(404)

            root = Path(self.root_dir).resolve()
            items = []
            for entry in sorted(current_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                rel = entry.relative_to(root).as_posix()
                size_display = "-" if entry.is_dir() else format_size(entry.stat().st_size)
                items.append(
                    {
                        "name": entry.name,
                        "is_dir": entry.is_dir(),
                        "rel_path": rel,
                        "size_display": size_display,
                    }
                )

            current_rel = current_dir.relative_to(root).as_posix()
            if current_rel == ".":
                current_rel = ""
            parent_rel = None
            if current_rel:
                parent = Path(current_rel).parent.as_posix()
                parent_rel = "" if parent == "." else parent

            return render_template_string(
                BROWSE_TEMPLATE,
                items=items,
                current_rel=current_rel,
                parent_rel=parent_rel,
              needs_download_password=bool(self.download_password),
              needs_delete_password=bool(self.delete_password),
            )

        @app.post("/upload")
        def upload_file():
            target = request.form.get("target", "")
            try:
                destination_dir = self._resolve_inside_root(target)
            except PermissionError:
                abort(403)

            if not destination_dir.exists() or not destination_dir.is_dir():
                flash("Invalid target folder")
                return redirect(url_for("browse", subpath=""))

            uploads = [
                item
                for item in request.files.getlist("files")
                if item is not None and item.filename is not None and item.filename.strip() != ""
            ]
            if not uploads:
                flash("No files selected")
                return redirect(url_for("browse", subpath=target))

            uploaded_count = 0
            skipped_count = 0
            target_root = destination_dir.resolve()

            for upload in uploads:
                rel_upload_path = self._sanitize_relative_upload_path(upload.filename)
                if rel_upload_path is None:
                    skipped_count += 1
                    self._log(f"Skipped unsafe upload name: {upload.filename}")
                    continue

                destination = (target_root / rel_upload_path).resolve()
                if destination != target_root and target_root not in destination.parents:
                    skipped_count += 1
                    self._log(f"Blocked traversal upload: {upload.filename}")
                    continue

                destination.parent.mkdir(parents=True, exist_ok=True)
                destination = self._unique_destination_path(destination)

                self._stream_to_disk(upload, destination)
                size_text = format_size(destination.stat().st_size)
                relative_saved_path = destination.relative_to(Path(self.root_dir).resolve()).as_posix()
                self._log(f"Uploaded: {relative_saved_path} ({size_text})")
                uploaded_count += 1

            if uploaded_count == 0:
                flash("No valid files were uploaded")
            elif skipped_count > 0:
                flash(f"Uploaded {uploaded_count} file(s), skipped {skipped_count} unsafe/invalid item(s)")
            else:
                flash(f"Uploaded {uploaded_count} file(s)")

            return redirect(url_for("browse", subpath=target))

        @app.route("/download/<path:relpath>")
        def download_file(relpath: str):
            provided = request.args.get("password", "")
            if not self._is_download_password_valid(provided):
                abort(403)

            try:
                file_path = self._resolve_inside_root(relpath)
            except PermissionError:
                abort(403)

            if not file_path.exists() or not file_path.is_file():
                abort(404)

            self._log(f"Download: {file_path.name}")
            return send_from_directory(
                directory=str(file_path.parent),
                path=file_path.name,
                as_attachment=True,
                conditional=True,
            )

        @app.post("/download")
        def download_file_post():
            relpath = request.form.get("target", "")
            provided = request.form.get("password", "")
            if not self._is_download_password_valid(provided):
                flash("Invalid download password")
                return redirect(request.referrer or url_for("browse", subpath=""))

            try:
                file_path = self._resolve_inside_root(relpath)
            except PermissionError:
                abort(403)

            if not file_path.exists() or not file_path.is_file():
                abort(404)

            self._log(f"Download: {file_path.name}")
            return send_from_directory(
                directory=str(file_path.parent),
                path=file_path.name,
                as_attachment=True,
                conditional=True,
            )

        @app.post("/download-folder")
        def download_folder_post():
            relpath = request.form.get("target", "")
            provided = request.form.get("password", "")
            if not self._is_download_password_valid(provided):
                flash("Invalid download password")
                return redirect(request.referrer or url_for("browse", subpath=""))

            try:
                folder_path = self._resolve_inside_root(relpath)
            except PermissionError:
                abort(403)

            if not folder_path.exists() or not folder_path.is_dir():
                abort(404)

            zip_path = self._build_folder_zip(folder_path)

            @after_this_request
            def cleanup_zip(response):
                try:
                    os.remove(zip_path)
                except OSError:
                    pass
                return response

            self._log(f"Folder download: {folder_path.name}")
            return send_file(
                zip_path,
                as_attachment=True,
                download_name=f"{folder_path.name}.zip",
                conditional=True,
            )

        @app.post("/delete")
        def delete_item():
            target = request.form.get("target", "")
            return_to = request.form.get("return_to", "")
            provided = request.form.get("password", "")

            if self.delete_password and provided != self.delete_password:
                flash("Invalid delete password")
                return redirect(url_for("browse", subpath=return_to))

            try:
                item = self._resolve_inside_root(target)
            except PermissionError:
                abort(403)

            if not item.exists():
                flash("Item does not exist")
                return redirect(url_for("browse", subpath=return_to))

            if item.is_dir():
                shutil.rmtree(item)
                self._log(f"Deleted folder: {item.name}")
            else:
                item.unlink(missing_ok=True)
                self._log(f"Deleted file: {item.name}")

            flash(f"Deleted {item.name}")
            return redirect(url_for("browse", subpath=return_to))

        return app

    def start(self, folder_path: str, delete_password: str, download_password: str, log_callback):
        if self.is_running:
            self._log("Server is already running")
            return

        self.root_dir = os.path.abspath(folder_path)
        self.delete_password = delete_password or ""
        self.download_password = download_password or ""
        self._log_callback = log_callback
        self._ensure_port_available()

        self._app = self._build_app()
        self._thread = FlaskServerThread(self._app, self.host, self.port, self._log)
        self._thread.start()
        self._log(f"Sharing started on {self.host}:{self.port}")
        self._log(f"Root folder: {self.root_dir}")

    def stop(self):
        if not self.is_running:
            self._log("Server is not running")
            return

        self._thread.shutdown()
        self._thread.join(timeout=3)
        self._thread = None
        self._app = None
        self._log("Sharing stopped")
