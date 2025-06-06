#!/usr/bin/env python3
"""
Launch Baryon – opens the 3-D viewer either online (https://baryon.live)
or from the packaged folder visualizers/baryon_web/.

Flags
-----
--local  serve the local copy on http://127.0.0.1:7878
--ask    show a confirmation dialog first (used by the UI)

The helper `launch()` wraps all this for the PySide6 UI.
"""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import socket, threading, webbrowser, sys, argparse

THIS = Path(__file__).resolve()
BARYON_DIR = THIS.parent / "baryon_web"

def _free_port(p=7878):
    with socket.socket() as s:
        while True:
            try:
                s.bind(("127.0.0.1", p)); return p
            except OSError: p += 1

def _serve_local() -> str:
    port = _free_port()
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(BARYON_DIR), **kw)
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{port}/index.html"

def _kiosk(url: str):
    # attempt fullscreen / kiosk where possible
    if sys.platform.startswith("win"):
        webbrowser.get().open_new(url)               # cannot force F11
    elif sys.platform == "darwin":
        webbrowser.get("safari").open_new(url)
    else:  # linux: try chrome
        try:
            chrome = webbrowser.get("chrome")
            chrome.open_new(f'--kiosk "{url}"')
        except webbrowser.Error:
            webbrowser.open_new(url)

def launch(force_local=False, ask=False) -> bool:
    """Return True on success."""
    if ask:
        from PySide6.QtWidgets import QMessageBox
        if QMessageBox.question(
            None, "Launch 3-D Viewer",
            "Open the external Baryon window?",
            QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return False
    try:
        url = _serve_local() if force_local else "https://baryon.live"
        _kiosk(url); return True
    except Exception as exc:
        print("Launch error:", exc); return False

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", action="store_true")
    ap.add_argument("--ask",   action="store_true")
    launch(**vars(ap.parse_args()))
