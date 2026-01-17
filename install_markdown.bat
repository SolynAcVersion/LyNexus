@echo off
echo Installing Markdown and LaTeX dependencies...
.venv\Scripts\python -m pip install markdown pymdown-extensions markdown-katex
echo Installation complete!
pause
