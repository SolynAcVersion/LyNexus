@echo off
REM LyNexus Quick Start
REM Uses uv run for Python commands

echo.
echo ============================================
echo    LyNexus - Quick Start
echo ============================================
echo.

echo [1/2] Installing Python packages...
uv pip install fastapi uvicorn[standard] sse-starlette pydantic python-multipart httpx requests aiofiles python-dotenv
echo.

echo [2/2] Starting LyNexus...
uv run python start.py
