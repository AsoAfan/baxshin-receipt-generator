# Running Receipt App Without Python

There are now **two ways** to run the Receipt App:

## Option 1: Standalone Executable (No Python Required) ⭐

Simply run one of these files from the main folder:

- **`RUN-APP.bat`** - Basic launcher
- **`START-Receipt-App.bat`** - Friendly launcher with instructions

No Python installation needed! The app is bundled with all dependencies.

**Steps:**
1. Double-click `START-Receipt-App.bat` (or `RUN-APP.bat`)
2. A terminal window will open
3. Open your browser to `http://localhost:5000`
4. Keep the terminal window open while using the app
5. Close the terminal to stop the app

---

## Option 2: Original Python Method (Still Available)

If you have Python and want to use the venv:

```bash
.\venv\Scripts\python.exe .\wsgi.py
```

Then open `http://localhost:5000` in your browser.

---

## What's New

- **`dist/ReceiptApp.exe`** - Standalone executable (~13 MB)
- **`RUN-APP.bat`** - Quick launcher
- **`START-Receipt-App.bat`** - User-friendly launcher with messaging
- **`build_exe.spec`** - PyInstaller configuration (for rebuilding if needed)

All dependencies (Flask, Waitress, Jinja2, etc.) are bundled into the .exe.

---

## Sharing with Others

You can share just the `dist` folder with others, and they can run `ReceiptApp.exe` directly without any Python installation! Or give them either batch file as a shortcut.
