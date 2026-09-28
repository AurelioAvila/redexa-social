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
import subprocess
import sys
import logging
import ctypes
import re

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


class WindowTheme:
    """Expose only native caption colors to the local web UI."""

    def __init__(self):
        self._window = None

    def set_window_theme(self, background, foreground):
        if any(not isinstance(color, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', color)
               for color in (background, foreground)):
            return False
        if sys.platform != 'win32' or self._window is None or self._window.native is None:
            return False
        try:
            # WinForms sets Window.native to its Form after the HWND is created.
            hwnd = self._window.native.Handle.ToInt64()
            setter = ctypes.windll.dwmapi.DwmSetWindowAttribute
            setter.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32]
            setter.restype = ctypes.c_long
            colors = [tuple(bytes.fromhex(color[1:])) for color in (background, foreground)]
            caption, text = [r | (g << 8) | (b << 16) for r, g, b in colors]
            r, g, b = colors[0]
            dark = int(299 * r + 587 * g + 114 * b < 128000)
            succeeded = True
            for attribute, value in ((20, dark), (34, 0xFFFFFFFE), (35, caption), (36, text)):
                color = ctypes.c_uint32(value)
                succeeded = setter(hwnd, attribute, ctypes.byref(color), ctypes.sizeof(color)) == 0 and succeeded
            return succeeded
        except (AttributeError, OSError, ValueError):
            # Older Windows versions keep their native, functional title bar.
            return False


def _desktop_port():
    if getattr(sys, 'frozen', False):
        return 8787
    port = int(os.getenv('REDEXA_DEV_PORT', '8787'))
    if not 1024 <= port <= 65535:
        raise ValueError('REDEXA_DEV_PORT must be between 1024 and 65535')
    return port


def _run_server(port=8787):
    uvicorn.run(backend.app, host="127.0.0.1", port=port, log_level="warning")


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
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("AurelioAvila.RedexaSocial")
    except (AttributeError, OSError):
        pass  # Safe to skip outside Windows or when the API is unavailable.


def main():
    _set_taskbar_identity()
    if sys.platform == 'win32' and getattr(sys, 'frozen', False):
        try:
            subprocess.run(
                ['powershell.exe', '-NoProfile', '-NonInteractive', '-File',
                 os.path.join(os.path.dirname(__file__), 'scripts', 'migrate_shortcuts.ps1'),
                 '-AppDirectory', os.path.dirname(sys.executable)],
                timeout=15, check=True, creationflags=subprocess.CREATE_NO_WINDOW,
                capture_output=True,
            )
        except (OSError, subprocess.SubprocessError):
            logging.warning('Could not refresh Windows shortcuts; the app will continue.')
    port = _desktop_port()
    threading.Thread(target=_run_server, args=(port,), daemon=True).start()
    _wait_for_server(port=port)
    theme = WindowTheme()
    window = webview.create_window(
        "Redexa Social",
        f"http://127.0.0.1:{port}",
        width=1020,
        height=680,
        min_size=(760, 520),
        background_color="#f0f3f6",
        js_api=theme,
    )
    theme._window = window
    window.events.shown += lambda: theme.set_window_theme('#21354d', '#eef3fa')
    os.makedirs(WEBVIEW_STORAGE, exist_ok=True)
    # Without icon=, the window and its taskbar entry take python.exe's icon
    # (the process hosting them) rather than the app's - which only shows when
    # starting from source like this: the PyInstaller build already carries
    # its own inside the .exe (see Redexa Social.spec) and is unaffected.
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    webview.start(private_mode=False, storage_path=WEBVIEW_STORAGE, icon=icon_path)


if __name__ == "__main__":
    main()
