"""
Starting as a real desktop app: the FastAPI server runs in the background and
the UI opens in a dedicated native window (WebView2 on Windows) - no visible
terminal, no browser tab, its own icon and window in the taskbar. Launched by
run.bat through pythonw (no console).

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import os
import socket
import threading
import time

import uvicorn
import webview

import app as backend
import cache

# pywebview starts in "private mode" unless told otherwise: the equivalent of
# an incognito window, so localStorage is wiped every time the app closes and
# the session token goes with it - users found themselves signed out on every
# restart. With private_mode=False and a stable storage folder, the session
# lasts until someone presses "Sign out".
WEBVIEW_STORAGE = os.path.join(cache.DATA_DIR, "webview")


def _run_server():
    uvicorn.run(backend.app, host="127.0.0.1", port=8787, log_level="warning")


def _wait_for_server(host="127.0.0.1", port=8787, timeout=10):
    """Waits for uvicorn to accept connections before opening the window,
    rather than a fixed time.sleep - the window opens as soon as the server is
    genuinely ready, with no wasted delay and no risk of a blank page."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.3):
                return
        except OSError:
            time.sleep(0.05)


def _set_taskbar_identity():
    """Without this, Windows groups the process under the default App User
    Model ID (python.exe's) and shows its icon in the taskbar - the window
    icon (webview.start(icon=...)) is enough for the title bar and Alt+Tab,
    but not for the taskbar button, which follows the process's AppID. It has
    to run before any window is created."""
    import ctypes
    try:
        # Keep the established identifier so upgrades preserve taskbar pins and
        # existing Windows app state while the visible product name changes.
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("AurelioAvila.SocialDashboard")
    except (AttributeError, OSError):
        pass  # Safe to skip outside Windows or when the API is unavailable.


def main():
    _set_taskbar_identity()
    threading.Thread(target=_run_server, daemon=True).start()
    _wait_for_server()
    webview.create_window(
        "Redexa Social",
        "http://127.0.0.1:8787",
        width=1020,
        height=680,
        min_size=(760, 520),
        background_color="#f7f9fc",
    )
    os.makedirs(WEBVIEW_STORAGE, exist_ok=True)
    # Without icon=, the window and its taskbar entry take python.exe's icon
    # (the process hosting them) rather than the app's - which only shows when
    # starting from source like this: the PyInstaller build already carries
    # its own inside the .exe (see Social Dashboard.spec) and is unaffected.
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    webview.start(private_mode=False, storage_path=WEBVIEW_STORAGE, icon=icon_path)


if __name__ == "__main__":
    main()
