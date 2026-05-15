"""
Start the Amplio web UI + API on one process, then open the browser.

Double-click run.bat in this folder, or run:  python run.py
"""
import os
import threading
import time
import webbrowser

import uvicorn

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def _open_browser() -> None:
    time.sleep(1.8)
    webbrowser.open("http://127.0.0.1:8000/")


if __name__ == "__main__":
    threading.Thread(target=_open_browser, daemon=True).start()
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
