# LAN Folder Share (Windows, Python)

A desktop app to share a selected folder over your local network. Any phone or device on the same Wi-Fi/LAN can open the URL in a browser and upload/download files.

## Features

- Windows desktop GUI built with PyQt5
- Flask server runs in a background thread (GUI stays responsive)
- Share any selected folder as root over LAN (`0.0.0.0`)
- Auto-detect and display local IP + URL
- QR code generation for instant phone access
- Start/Stop sharing controls with status indicator
- Live log panel (requests, uploads, deletes, errors)
- Recent folder history:
	- use last selected folder quickly
	- select a new folder anytime
- Mobile-friendly web interface:
	- browse folders/subfolders
	- view file sizes and file/folder types
	- root/up navigation
	- upload progress bar
- Upload support:
	- multiple files in one request
	- full folder upload (preserves structure)
	- chunked streaming write to disk (large file friendly)
- Download support:
	- file download
	- full folder download as ZIP
	- optional download password
- Optional delete password for file/folder deletion
- Security protections:
	- strict root folder path restriction
	- traversal protection
	- sanitized upload names
	- safe duplicate naming (`name_1`, `name_2`, ...)
- PyInstaller-compatible for single EXE build

## EXE Download

- Google Drive (prebuilt executable):
	- https://drive.google.com/drive/folders/1HyqefYZWfqfw0GHKAbCtc6Jzl7p-DUXl?usp=drive_link

## Project Structure

- `app.py` - app entry point
- `lan_share/gui.py` - PyQt5 desktop UI
- `lan_share/server.py` - Flask file server and security logic

## Setup

1. Create and activate a virtual environment (recommended).
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the app:

```powershell
python app.py
```

## Usage

1. Choose a shared folder:
	- **Use Selected Saved Folder** (from recent history), or
	- **Select New Folder**
2. Keep default port `8000` or set a custom port.
3. Optionally set:
	- Delete Password
	- Download Password
4. Click **Start Sharing**.
5. Open the URL from another device on same LAN (or scan QR).
6. In browser:
	- upload files/folders
	- download files
	- download folders as ZIP
	- navigate subfolders
	- delete items (if enabled)

Uploads are saved in the currently browsed folder under the selected root.
For folder upload, directory structure is preserved relative to the selected folder upload root.

## Build Single EXE (PyInstaller)

Install PyInstaller:

```powershell
pip install pyinstaller
```

Build command:

```powershell
pyinstaller --noconfirm --onefile --windowed --name LANFolderShare app.py
```

The executable is generated in the `dist` folder.

## Notes

- Works fully offline on same LAN.
- No mobile app installation needed.
- If Windows Firewall prompts access, allow private network access.
- Large files are handled using streaming/chunked I/O to reduce memory usage.
