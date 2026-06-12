@echo off
echo ================================================
echo    BUILDING RECEIPT APP STANDALONE EXE
echo ================================================
echo.

REM Check for virtual environment
if exist venv\Scripts\activate.bat (
    echo Using virtual environment...
    call venv\Scripts\activate.bat
)

REM Install PyInstaller if not present
pip install pyinstaller pywebview flask

echo.
echo Running PyInstaller...
pyinstaller --clean desktop_app.spec

echo.
echo ================================================
echo    BUILD COMPLETE!
echo ================================================
echo.
echo Your installable app is in the "dist" folder.
echo You only need to share the "ReceiptAppDesktop" 
echo folder (or the .exe if you used --onefile).
echo.
pause
