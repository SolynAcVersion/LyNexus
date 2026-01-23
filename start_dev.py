#!/usr/bin/env python
"""
Start both API server and WebUI development servers
"""

import subprocess
import time
import threading
import webbrowser
from pathlib import Path

def run_command(cmd, cwd=None, shell=False):
    """Run command and return process"""
    if shell:
        print(f"Running: {cmd}")
        return subprocess.Popen(cmd, cwd=cwd, shell=True)
    else:
        print(f"Running: {' '.join(cmd)}")
        return subprocess.Popen(cmd, cwd=cwd)

def main():
    project_root = Path(__file__).parent

    print("\n" + "="*50)
    print("🚀 Starting LyNexus Development Environment")
    print("="*50)
    print(f"📂 Project: {project_root}")
    print("="*50 + "\n")

    processes = []

    try:
        # Install dependencies first
        print("[0/3] Installing Python dependencies...")
        print("Using: uv pip install")

        # Try uv pip install
        install_cmd = "uv pip install fastapi uvicorn[standard] sse-starlette pydantic python-multipart httpx requests aiofiles python-dotenv"
        run_command(install_cmd, cwd=project_root, shell=True)
        # Wait for installation
        time.sleep(5)
        print("✓ Dependencies installed\n")

        # Start API server
        print("[1/3] Starting API server...")
        api_process = run_command(
            "uv run uvicorn api_server:app --host 127.0.0.1 --port 8000 --reload",
            cwd=project_root,
            shell=True
        )
        processes.append(("API Server", api_process))
        print("✓ API server running at http://127.0.0.1:8000\n")

        # Wait a bit for API server to start
        time.sleep(3)

        # Start WebUI
        print("[2/3] Starting WebUI...")
        webui_dir = project_root / "webui"
        if webui_dir.exists():
            web_process = run_command(
                ["npm", "run", "dev"],
                cwd=webui_dir
            )
            processes.append(("WebUI", web_process))
            print("✓ WebUI running at http://localhost:5173\n")
        else:
            print("✗ WebUI directory not found!")
            print("  Please run: cd webui && npm install && npm run dev")

        print("="*50)
        print("✓ All services started!")
        print("="*50)
        print("\n🌐 Open your browser:")
        print("   - WebUI: http://localhost:5173")
        print("   - API Docs: http://localhost:8000/docs")
        print("\n💡 Press Ctrl+C to stop all services")
        print("="*50 + "\n")

        # Open browser automatically
        webbrowser.open("http://localhost:5173")

        # Wait for processes
        for name, process in processes:
            process.wait()

    except KeyboardInterrupt:
        print("\n\n" + "="*50)
        print("🛑 Stopping all services...")
        print("="*50 + "\n")

        for name, process in processes:
            print(f"Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except:
                process.kill()

        print("✓ All services stopped. Goodbye!\n")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        # Cleanup
        for name, process in processes:
            try:
                process.terminate()
            except:
                pass

if __name__ == "__main__":
    main()
