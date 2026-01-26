@echo off
REM LyNexus Windows 打包脚本
REM 使用方法：以管理员身份运行此脚本

echo ========================================
echo LyNexus 快速打包脚本
echo ========================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] 请以管理员身份运行此脚本
    echo 右键点击此文件 -^> 以管理员身份运行
    pause
    exit /b 1
)

echo [1/5] 清理旧文件...
taskkill /F /IM electron.exe 2>nul
timeout /t 2 /nobreak >nul
rmdir /S /Q webui\release 2>nul
rmdir /S /Q webui\dist 2>nul

echo [2/5] 打包 Python 后端...
UV_SKIP_WHEEL_FILENAME_CHECK=1 uv run pyinstaller --clean api_server.spec
copy dist\api_server.exe webui\dist-electron\python\

echo [3/5] 构建 React 前端...
cd webui
call npm run build
cd ..

echo [4/5] 打包 Electron 应用...
cd webui
set CSC_IDENTITY_AUTO_DISCOVERY=false
call npx electron-builder --win --config.win.target=zip
cd ..

echo [5/5] 完成！
echo.
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo 安装包位置:
dir /B webui\release\*.zip
echo.
echo 未打包版本位置:
echo webui\release\win-unpacked\
echo.
echo 注意: Python 后端已包含在应用中
echo.
pause
