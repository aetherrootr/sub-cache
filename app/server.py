import logging
from threading import Thread

from app.api.base import app
from app.api.sub_api import sub_api
from app.cronjob.periodic_fetch import periodic_fetch
from app.gunicorn_app import GunicornApp
from app.model.base import Database
from app.model.subscription import SubscriptionSource
from app.utils.sub_utils import CACHE_FILE_DIR, DATABASE_DIR, DATABASE_URL, cache_remote_sub


def verify_cache_directory(database):
    with database.session() as session:
        sources = session.query(SubscriptionSource).all()
        for sub in sources:
            cache_file = CACHE_FILE_DIR / f"{sub.id}.yml"
            if not cache_file.exists():
                if sub.type == "remote" and sub.url:
                    cache_remote_sub(sub.id, sub.url)
                elif sub.type == "local":
                    session.delete(sub)

        session.commit()


def main():
    options = {
        'bind': '0.0.0.0:8080',
        'workers': '1',
        'loglevel': 'info',
    }

    CACHE_FILE_DIR.mkdir(parents=True, exist_ok=True)
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    app.register_blueprint(sub_api)
    database = Database(DATABASE_URL)
    database.init_db()
    verify_cache_directory(database)
    app.extensions['database'] = database
    logging.error(f"static_folder = {app.static_folder}")

    fetch_thread = Thread(target=periodic_fetch, args=(database,))
    fetch_thread.daemon = True
    fetch_thread.start()

    GunicornApp(app, options).run()


if __name__ == '__main__':
    main()
