# LAN Folder Share (Windows, Python)

A desktop app to share a selected folder over your local network. Any phone or device on the same Wi-Fi/LAN can open the URL in a browser and upload/download files.

## Features

- PyQt5 desktop GUI
- Flask server running in a background thread
- Folder browsing and download from mobile browser
- File upload with progress bar
- QR code for instant mobile access
- LAN IP auto-detection
- Path traversal protection
- Sanitized upload filenames
- Optional delete password
- Large file friendly streaming upload/download

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

1. Click **Select Folder** and choose the folder to share.
2. Keep default port `8000` or change it.
3. Optionally set a delete password.
4. Click **Start Sharing**.
5. Scan the QR code with your phone or open the displayed URL in browser.

Uploads are saved in the currently browsed folder under the selected root.

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
