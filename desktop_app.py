"""
Avvio come vera app desktop: il server FastAPI gira in background e la UI
si apre in una finestra nativa dedicata (WebView2 su Windows) - niente
terminale visibile, niente tab del browser, un'icona/finestra propria in
taskbar. Lanciato da run.bat via pythonw (nessuna console).
"""
import os
import socket
import threading
import time

import uvicorn
import webview

import app as backend
import cache

# pywebview parte in "private mode" se non gli si dice altro: e' l'equivalente
# di una finestra in incognito, quindi localStorage viene azzerato a ogni
# chiusura dell'app e il token di sessione sparisce - l'utente si ritrovava
# scollegato ad ogni riavvio. Con private_mode=False e una cartella di storage
# stabile la sessione dura finche' non si preme "Esci".
WEBVIEW_STORAGE = os.path.join(cache.DATA_DIR, "webview")


def _run_server():
    uvicorn.run(backend.app, host="127.0.0.1", port=8787, log_level="warning")


def _wait_for_server(host="127.0.0.1", port=8787, timeout=10):
    """Attende che uvicorn accetti connessioni prima di aprire la finestra,
    invece di un time.sleep fisso - la finestra si apre appena il server e'
    davvero pronto, senza ritardo inutile ne' rischio di pagina bianca."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.3):
                return
        except OSError:
            time.sleep(0.05)


def main():
    threading.Thread(target=_run_server, daemon=True).start()
    _wait_for_server()
    webview.create_window(
        "Social Dashboard",
        "http://127.0.0.1:8787",
        width=1020,
        height=680,
        min_size=(760, 520),
        background_color="#0f1115",
    )
    os.makedirs(WEBVIEW_STORAGE, exist_ok=True)
    webview.start(private_mode=False, storage_path=WEBVIEW_STORAGE)


if __name__ == "__main__":
    main()
