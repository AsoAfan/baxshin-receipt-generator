@echo off
REM Receipt App - One-Click Launcher
REM Starts app, shows network IP, and opens browser

cls
echo.
echo ================================================
echo         RECEIPT APP - ONE-CLICK START
echo ================================================
echo.

REM Get local IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4 Address"') do (
    set "ip=%%a"
)
set "ip=%ip: =%"

REM Navigate to dist and start app in background
echo Starting Receipt App...
cd /d "%~dp0dist"
start "" ReceiptApp.exe
cd ..

REM Wait for app to start
timeout /t 2 /nobreak >nul

echo.
echo ================================================
echo      APP IS RUNNING - READY TO USE
echo ================================================
echo.
echo Open in your browser:
echo.
echo   LOCAL:   http://localhost:81
echo   NETWORK: http://%ip%:81
echo.
echo Share the NETWORK URL with others on your WiFi
echo.
echo This window will close in 5 seconds...
echo ================================================
echo.

REM Try to open browser
start http://localhost:81

REM Keep window visible briefly then close
timeout /t 5 /nobreak >nul
exit /b 0
