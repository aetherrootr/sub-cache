import logging
import os
import time
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse

import requests
from flask import Flask, render_template_string, request, send_file

from app.gunicorn_app import GunicornApp

SUB_URL_FILE = Path("/config/sub_url.txt")
FETCH_SUB_INTERVAL = int(os.getenv("FETCH_INTERVAL", 1800))
CACHE_FILE = Path("/work/cached_content.txt")
HEADERS = {
    "User-Agent": "clash.meta/1.18.0",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

app = Flask(__name__)


def read_file(filename, mode="r"):
    with open(filename, mode) as f:
        return f.read()


def write_file(filename, content):
    Path(filename).write_text(content)


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def fetch_content():
    try:
        sub_url = read_file(SUB_URL_FILE)
        if not is_valid_url(sub_url):
            logging.error(f"The subscription link {sub_url} you set is not a valid URL")
            return

        response = requests.get(sub_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        CACHE_FILE.write_bytes(response.content)
        logging.error(f"Fetched content from {sub_url} and saved to {CACHE_FILE}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch content: {e}")


@app.route("/")
def serve_content():
    return send_file(CACHE_FILE, as_attachment=False)


@app.route("/update", methods=["GET", "POST"])
def update_sub_url():
    result = None
    if request.method == "POST":
        data = request.form.get("input_data")
        if is_valid_url(data):
            write_file(SUB_URL_FILE, data)
            fetch_content()
            result = "Update successful"
        else:
            result = "Update failed, the subscription link you set is not a valid URL."

    current_sub_url = read_file(SUB_URL_FILE)
    return render_template_string(
        """
        <!doctype html>
        <title>Update sub url</title>
        <h1>Current sub url is {{ current_sub_url }}<h1>
        <h1>Enter new sub url:</h1>
        <form method="post">
            <input type="text" name="input_data">
            <input type="submit" value="Submit">
        </form>
        {% if result %}
        <h2>{{ result }}</h2>
        {% endif %}
    """,
        result=result,
        current_sub_url=current_sub_url,
    )


def periodic_fetch():
    while True:
        fetch_content()
        time.sleep(FETCH_SUB_INTERVAL)


def main():
    options = {
        "bind": "0.0.0.0:8080",
        "workers": "1",
        "loglevel": "info",
    }

    SUB_URL_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SUB_URL_FILE.touch(exist_ok=True)
    CACHE_FILE.touch(exist_ok=True)

    fetch_thread = Thread(target=periodic_fetch)
    fetch_thread.daemon = True
    fetch_thread.start()

    GunicornApp(app, options).run()


if __name__ == '__main__':
    main()
