@echo off
echo ========================================
echo Run Electron from Source
echo ========================================
echo.
echo This bypasses the packaged electron.exe
echo and uses the one from node_modules instead.
echo.

cd /d "%~dp0"

set "ELECTRON_EXE=node_modules\.bin\electron.cmd"

if exist "%ELECTRON_EXE%" (
    echo [OK] Found electron in node_modules
    echo.
    echo Running: %ELECTRON_EXE% .
    echo.
    
    call "%ELECTRON_EXE%" .
    
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Failed to run.
        echo.
        echo Make sure Python backend is running:
        echo   cd ..
        echo   python api_server.py
    )
) else (
    echo [ERROR] Electron not found in node_modules
    echo.
    echo Installing dependencies...
    call npm install
    echo.
    echo Try running this script again.
)
pause
