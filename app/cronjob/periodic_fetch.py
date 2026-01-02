import os
import time

from app.model.subscription import SubscriptionSource
from app.utils.sub_utils import cache_remote_sub

FETCH_SUB_INTERVAL = int(os.getenv("FETCH_INTERVAL", 1800))


def periodic_fetch(database):
    while True:
        with database.session() as session:
            source = session.query(SubscriptionSource).all()
            for sub in source:
                if sub.type == "remote" and sub.url:
                    cache_remote_sub(sub.id, sub.url)

        time.sleep(FETCH_SUB_INTERVAL)
