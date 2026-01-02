import contextlib
import logging
import os
from pathlib import Path

import requests
from filelock import FileLock

from app.utils.utils import is_valid_url

CACHE_FILE_DIR = Path("/work/cache_files") if os.getenv('ENV', 'dev') == 'prod' else Path(os.getcwd()) / "work" / "cache_files"
DATABASE_DIR = Path("/work/database") if os.getenv('ENV', 'dev') == 'prod' else Path(os.getcwd()) / "work" / "database"
DATABASE_URL = f"sqlite:///{DATABASE_DIR}/subscription.db"
HEADERS = {
    "User-Agent": "clash.meta/1.18.0",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


def cache_remote_sub(sub_id: int, sub_url: str) -> bool:
    cache_file = CACHE_FILE_DIR / f"{sub_id}.yml"
    cache_file_tmp = CACHE_FILE_DIR / f"{sub_id}.yml.tmp"
    cache_file_lock = CACHE_FILE_DIR / f"{sub_id}.lock"

    try:
        if not is_valid_url(sub_url):
            logging.error(f"The subscription link {sub_url} you set is not a valid URL")
            return False

        response = requests.get(sub_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        if len(response.content) <= 0:
            logging.error(f"Fetched empty content from {sub_url}")
            return False

        with FileLock(cache_file_lock, timeout=5):
            with open(cache_file_tmp, "wb") as f:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        f.write(chunk)
            if cache_file_tmp.stat().st_size == 0:
                logging.error(f"Fetched empty content from {sub_url}")
                with contextlib.suppress(Exception):
                    cache_file_tmp.unlink(missing_ok=True)
                return False

            os.replace(cache_file_tmp, cache_file)
            logging.error(f"Fetched content from {sub_url} and saved to {cache_file}")
    except Exception as e:  # noqa: BLE001
        logging.error(f"An error occurred: {e}")
        return False
    finally:
        with contextlib.suppress(Exception):
            cache_file_tmp.unlink(missing_ok=True)

    return True


def save_local_sub(sub_id: int, content: str) -> bool:
    cache_file = CACHE_FILE_DIR / f"{sub_id}.yml"
    cache_file_tmp = CACHE_FILE_DIR / f"{sub_id}.yml.tmp"
    cache_file_lock = CACHE_FILE_DIR / f"{sub_id}.lock"

    try:
        with FileLock(cache_file_lock, timeout=5):
            cache_file_tmp.write_text(content)

            if cache_file_tmp.stat().st_size == 0:
                logging.error("Local subscription content is empty")
                with contextlib.suppress(Exception):
                    cache_file_tmp.unlink(missing_ok=True)
                return False

            os.replace(cache_file_tmp, cache_file)
            logging.info(f"Saved local subscription content to {cache_file}")
    except Exception as e:  # noqa: BLE001
        logging.error(f"An error occurred while saving local subscription: {e}")
        return False
    finally:
        with contextlib.suppress(Exception):
            cache_file_tmp.unlink(missing_ok=True)

    return True
