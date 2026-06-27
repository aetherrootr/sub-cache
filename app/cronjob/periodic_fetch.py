import os
import time
from datetime import UTC, datetime

from app.model.subscription import SubscriptionSource
from app.utils.sub_utils import cache_remote_sub

FETCH_SUB_INTERVAL = int(os.getenv("FETCH_INTERVAL", 1800))


def periodic_fetch(database):
    while True:
        with database.session() as session:
            source = session.query(SubscriptionSource).all()
            for sub in source:
                if sub.type == "remote" and sub.url:
                    if cache_remote_sub(sub.id, sub.url):
                        sub.last_successful_fetch_at = datetime.now(UTC)
                        sub.last_fetch_status = "success"
                    else:
                        sub.last_fetch_status = "failed"

        time.sleep(FETCH_SUB_INTERVAL)
