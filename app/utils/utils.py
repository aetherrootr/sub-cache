from pathlib import Path
from urllib.parse import urlparse

from flask import current_app


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


def get_database():
    return current_app.extensions["database"]
