import os

from flask import Flask, send_from_directory

STATIC_DIR = os.environ.get("STATIC_DIR", "/app/dist")


app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/<path:path>")
def static_proxy(path):
    full = os.path.join(app.static_folder, path)
    if os.path.exists(full):
        return send_from_directory(app.static_folder, path)
    # SPA fallback
    return send_from_directory(app.static_folder, "index.html")
