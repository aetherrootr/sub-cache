import os
import time
import logging
import requests
from flask import Flask, send_file

# 从环境变量中获取 URL 和定时周期（默认为60秒）
SUB_URL = os.getenv("SUB_URL", "https://example.com/data")
FETCH_SUB_INTERVAL = int(os.getenv("FETCH_INTERVAL", 600))
CACHE_FILE = "cached_content.txt"

app = Flask(__name__)

def fetch_content():
    try:
        response = requests.get(SUB_URL)
        response.raise_for_status()  # 检查请求是否成功
        with open(CACHE_FILE, "wb") as file:
            file.write(response.content)
        logging.error(f"Fetched content from {SUB_URL} and saved to {CACHE_FILE}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch content: {e}")

@app.route("/")
def serve_content():
    return send_file(CACHE_FILE, as_attachment=False)

def periodic_fetch():
    while True:
        fetch_content()
        time.sleep(FETCH_SUB_INTERVAL)

if __name__ == "__main__":
    from threading import Thread
    fetch_thread = Thread(target=periodic_fetch)
    fetch_thread.daemon = True  # 让线程在程序退出时自动关闭
    fetch_thread.start()
    app.run(host="0.0.0.0", port=8080)
