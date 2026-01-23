"""
Simple start script for LyNexus
Uses uv run to execute Python commands
"""

import subprocess
import time
import webbrowser
from pathlib import Path

def run_cmd(command, description):
    """Run a command and wait for it to complete"""
    print(f"\n{description}...")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"✗ Error: {result.stderr}")
        return False
    print("✓ Success")
    return True

def main():
    project_root = Path(__file__).parent

    print("\n" + "="*50)
    print("🚀 LyNexus - Quick Start")
    print("="*50)
    print(f"📂 Project: {project_root}")
    print("="*50)

    try:
        # Install dependencies
        print("\n[1/3] Installing dependencies...")
        if not run_cmd(
            "uv pip install fastapi uvicorn[standard] sse-starlette pydantic python-multipart httpx requests aiofiles python-dotenv",
            "Installing Python packages (this may take a few minutes)"
        ):
            return

        # Start API server in background
        print("\n[2/3] Starting API server...")
        api_process = subprocess.Popen(
            "uv run uvicorn api_server:app --host 127.0.0.1 --port 8000 --reload",
            cwd=project_root,
            shell=True
        )

        # Wait for API server to start
        print("  Waiting for server to start...")
        time.sleep(5)
        print("✓ API server running at http://127.0.0.1:8000")

        # Start WebUI in background
        print("\n[3/3] Starting WebUI...")
        webui_dir = project_root / "webui"
        if webui_dir.exists():
            web_process = subprocess.Popen(
                "npm run dev",
                cwd=webui_dir,
                shell=True
            )
            print("✓ WebUI running at http://localhost:5173")
        else:
            print("✗ WebUI directory not found")
            print("  Run: cd webui && npm install && npm run dev")
            api_process.terminate()
            return

        print("\n" + "="*50)
        print("✓ All services started!")
        print("="*50)
        print("\n🌐 Opening browser...")
        webbrowser.open("http://localhost:5173")
        print("\n💡 Press Ctrl+C to stop all services")
        print("="*50 + "\n")

        # Wait for user to stop
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n" + "="*50)
            print("🛑 Stopping all services...")
            print("="*50 + "\n")

            api_process.terminate()
            if 'web_process' in locals():
                web_process.terminate()

            api_process.wait()
            if 'web_process' in locals():
                web_process.wait()

            print("✓ All services stopped. Goodbye!\n")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        # Cleanup
        try:
            if 'api_process' in locals():
                api_process.terminate()
        except:
            pass

if __name__ == "__main__":
    main()
