# Running Receipt App Without Python

There are now **two ways** to run the Receipt App:

## Option 1: Standalone Desktop Window (Native App) ⭐
Simply run:
- **`RUN-DESKTOP.bat`**
This will open the app in its own window, making it feel like a real desktop application.

## Option 2: Standalone Executable (Browser-based)
Simply run one of these files from the main folder:

- **`RUN-APP.bat`** - Basic launcher
- **`START-Receipt-App.bat`** - Friendly launcher with instructions

No Python installation needed! The app is bundled with all dependencies.

**Steps:**
1. Double-click `START-Receipt-App.bat` (or `RUN-APP.bat`)
2. A terminal window will open
3. Open your browser to `http://localhost:81`
4. Keep the terminal window open while using the app
5. Close the terminal to stop the app

---

## Option 2: Original Python Method (Still Available)

If you have Python and want to use the venv:

```bash
.\venv\Scripts\python.exe .\wsgi.py
```

Then open `http://localhost:81` in your browser.

---

## What's New

- **`dist/ReceiptApp.exe`** - Standalone executable (~13 MB)
- **`RUN-APP.bat`** - Quick launcher
- **`START-Receipt-App.bat`** - User-friendly launcher with messaging
- **`build_exe.spec`** - PyInstaller configuration (for rebuilding if needed)

All dependencies (Flask, Waitress, Jinja2, etc.) are bundled into the .exe.

---

## Sharing with Others (No Source Code)

To give the app to a client without giving them the Python source code:

1. Run **`BUILD-EXE.bat`**. This will create a `dist` folder.
2. Inside `dist`, you will find the `ReceiptAppDesktop` folder (or just `ReceiptAppDesktop.exe`).
3. Send that folder/file to your client.
4. They can run it directly. All assets and the database will be handled automatically.

**Note:** The app will create `receipts.db` and `app_config.json` in the same folder as the `.exe` the first time it runs.
