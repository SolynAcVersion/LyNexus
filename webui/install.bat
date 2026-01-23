@echo off
REM LyNexus WebUI Installation Script
REM This script handles the installation with proper mirror configuration

echo ============================================
echo LyNexus WebUI - Installation Script
echo ============================================
echo.

REM Check if npm is installed
where npm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: npm is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo [1/4] Using China mirror for faster downloads...
echo Registry: https://registry.npmmirror.com
echo.

REM Set npm configuration for this session
npm config set registry https://registry.npmmirror.com
npm config set electron_mirror https://npmmirror.com/mirrors/electron/
npm config set electron_builder_binaries_mirror https://npmmirror.com/mirrors/electron-builder-binaries/

echo [2/4] Cleaning previous installation...
if exist node_modules rmdir /s /q node_modules
if exist package-lock.json del package-lock.json
if exist dist rmdir /s /q dist
if exist dist-electron rmdir /s /q dist-electron
if exist release rmdir /s /q release
echo Done.
echo.

echo [3/4] Installing dependencies...
echo This may take a few minutes, please wait...
echo.
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: npm install failed!
    echo.
    echo Troubleshooting:
    echo 1. Make sure you have a stable internet connection
    echo 2. Try running: npm cache clean --force
    echo 3. If the issue persists, try: npm install --legacy-peer-deps
    echo.
    pause
    exit /b 1
)
echo.
echo [4/4] Installation completed successfully!
echo.

echo ============================================
echo Next Steps:
echo ============================================
echo.
echo To start development:
echo   npm run dev              (Web only)
echo   npm run electron:dev     (Electron app)
echo.
echo To build for production:
echo   npm run build            (Build web)
echo   npm run electron:build   (Build Electron app)
echo.
echo ============================================

pause
