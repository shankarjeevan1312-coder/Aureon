"""
AUREON Native Desktop Launcher
Launches AUREON as a standalone desktop window application (borderless app mode).
"""

import sys
import time
import os
import subprocess
import threading
import uvicorn
from pathlib import Path
from aureon.config import settings

def start_backend():
    from aureon.server.api import app
    uvicorn.run(app, host="127.0.0.1", port=settings.port, log_level="warning")

def launch_native_window():
    url = f"http://localhost:{settings.port}"
    
    # Try pywebview if installed
    try:
        import webview
        webview.create_window(
            title="AUREON — Autonomous System Intelligence",
            url=url,
            width=1240,
            height=820,
            background_color="#070a0f"
        )
        webview.start()
        return
    except ImportError:
        pass

    # Fallback to Windows Native Edge / Chrome App Mode (borderless, dedicated window)
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe")
    ]
    
    edge_exe = next((p for p in edge_paths if os.path.exists(p)), "msedge.exe")

    temp_profile = os.path.expandvars(r"%TEMP%\aureon_desktop_profile")
    cmd = [
        edge_exe,
        f"--app={url}",
        "--window-size=1240,820",
        "--enable-features=OverlayScrollbar",
        f"--user-data-dir={temp_profile}"
    ]

    try:
        proc = subprocess.Popen(cmd)
        proc.wait()
    except Exception as e:
        print(f"Opening default browser as fallback: {e}")
        import webbrowser
        webbrowser.open(url)

def main():
    print("===================================================")
    print("   AUREON — Autonomous Desktop Intelligence")
    print("===================================================")
    
    # Start FastAPI backend in a daemon thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()

    # Wait 1.5 seconds for server to bind
    time.sleep(1.5)

    # Launch native desktop window
    launch_native_window()

if __name__ == "__main__":
    main()
