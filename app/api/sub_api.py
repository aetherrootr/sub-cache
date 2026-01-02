from filelock import FileLock
from flask import Blueprint, request, send_file

from app.model.subscription import SubscriptionSource
from app.utils.sub_utils import CACHE_FILE_DIR, cache_remote_sub, save_local_sub
from app.utils.utils import get_database

sub_api = Blueprint('sub', __name__, url_prefix="/sub")

SUB_TYPE = ["remote", "local"]


@sub_api.route("/<int:sub_id>", methods=["GET"])
def get_subscription(sub_id):
    db = get_database()
    with db.session() as session:
        source = session.get(SubscriptionSource, sub_id)
        if not source:
            return {"error": "Subscription source not found"}, 404
        url = source.url

    cache_file = CACHE_FILE_DIR / f"{sub_id}.yml"
    cache_file_lock = CACHE_FILE_DIR / f"{sub_id}.lock"
    if not cache_file.exists() and not cache_remote_sub(sub_id, url):
        return {"error": "Can not get subscription file"}, 500

    with FileLock(cache_file_lock, timeout=5):
        return send_file(cache_file, as_attachment=False)


@sub_api.route("/list", methods=["GET"])
def list_subscriptions():
    db = get_database()
    with db.session() as session:
        sources = session.query(SubscriptionSource).all()
        result = [
            {
                "id": source.id,
                "name": source.name,
                "type": source.type,
                "url": source.url,
                "created_at": source.created_at,
                "updated_at": source.updated_at,
            }
            for source in sources
        ]
    return {"sub_list": result}


@sub_api.route("/update/<int:sub_id>", methods=["POST"])
def update_sub(sub_id: int):
    db = get_database()
    with db.session() as session:
        source = session.get(SubscriptionSource, sub_id)
        if not source:
            return {"error": "Subscription source not found"}, 404
        data = request.get_json(silent=True)

        if "type" not in data or data["type"] not in SUB_TYPE:
            return {"error": "Invalid subscription type"}, 400

        if data["type"] == "remote":
            if "url" not in data or not data["url"]:
                return {"error": "URL is required for remote subscription type"}, 400
            if cache_remote_sub(sub_id, data["url"]):
                source.url = data["url"]
            else:
                return {"error": "Failed to fetch subscription from the provided URL"}, 400
        elif data["type"] == "local":
            if "content" not in data or not data["content"]:
                return {"error": "Content is required for local subscription type"}, 400
            save_local_sub(sub_id, data["content"])
        else:
            return {"error": "Unsupported subscription type"}, 400

        session.commit()
    return {"message": "Subscription updated successfully"}, 200


@sub_api.route("/delete/<int:sub_id>", methods=["DELETE"])
def delete_sub(sub_id: int):
    db = get_database()
    with db.session() as session:
        source = session.get(SubscriptionSource, sub_id)
        if not source:
            return {"error": "Subscription source not found"}, 404

        session.delete(source)
        session.commit()

        cache_file = CACHE_FILE_DIR / f"{sub_id}.yml"
        cache_file_lock = CACHE_FILE_DIR / f"{sub_id}.lock"
        with FileLock(cache_file_lock, timeout=5):
            cache_file.unlink(missing_ok=True)
        cache_file_lock.unlink(missing_ok=True)

    return {"message": "Subscription deleted successfully"}, 200


@sub_api.route("/add", methods=["POST"])
def add_sub():
    db = get_database()
    data = request.json

    if "name" not in data or not data["name"]:
        return {"error": "Name is required"}, 400
    if "type" not in data or data["type"] not in SUB_TYPE:
        return {"error": "Invalid subscription type"}, 400

    new_source = SubscriptionSource(
        name=data["name"],
        type=data["type"],
    )
    with db.session() as session:
        session.add(new_source)
        session.flush()

        if data["type"] == "remote":
            if "url" not in data or not data["url"]:
                return {"error": "URL is required for remote subscription type"}, 400
            if cache_remote_sub(new_source.id, data["url"]):
                new_source.url = data["url"]
            else:
                return {"error": "Failed to fetch subscription from the provided URL"}, 400
        elif data["type"] == "local":
            if "content" not in data or not data["content"]:
                return {"error": "Content is required for local subscription type"}, 400
            save_local_sub(new_source.id, data["content"])
        else:
            return {"error": "Unsupported subscription type"}, 400

        session.commit()
        new_source_id = new_source.id

    return {"message": "Subscription added successfully", "id": new_source_id}, 201


@sub_api.route("/refresh/<int:sub_id>", methods=["POST"])
def refresh_sub_cache(sub_id: int):
    db = get_database()
    with db.session() as session:
        source = session.get(SubscriptionSource, sub_id)
        print(sub_id)
        if not source:
            return {"error": "Subscription source not found"}, 404
        if source.type != "remote" or not source.url:
            return {"error": "Only remote subscriptions can be refreshed"}, 400

        if cache_remote_sub(sub_id, source.url):
            return {"message": "Subscription cache refreshed successfully"}, 200
        else:
            return {"error": "Failed to refresh subscription cache"}, 502
