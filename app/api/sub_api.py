from datetime import UTC, datetime
from urllib.parse import urlparse

from filelock import FileLock
from flask import Blueprint, make_response, request, send_file

from app.model.subscription import SubscriptionSource
from app.utils.sub_utils import CACHE_FILE_DIR, cache_remote_sub, save_local_sub
from app.utils.utils import get_database

sub_api = Blueprint('sub', __name__, url_prefix='/sub')

SUB_TYPE = ['remote', 'local']


def mark_successful_fetch(source: SubscriptionSource):
    source.last_successful_fetch_at = datetime.now(UTC)
    source.last_fetch_status = 'success'


def mark_failed_fetch(source: SubscriptionSource):
    source.last_fetch_status = 'failed'


def serialize_datetime(value):
    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


def get_subscription_source(session, sub_key: str):
    source = (
        session.query(SubscriptionSource)
        .filter(SubscriptionSource.subscription_key == sub_key)
        .one_or_none()
    )
    if source or not sub_key.isdecimal():
        return source
    source = session.get(SubscriptionSource, int(sub_key))
    if source:
        return source

    legacy_path = f'/sub/{sub_key}'
    for legacy_source in session.query(SubscriptionSource).filter(SubscriptionSource.url.is_not(None)):
        if urlparse(legacy_source.url).path.rstrip('/') == legacy_path:
            return legacy_source

    return None


@sub_api.route('/<sub_key>', methods=['GET'])
def get_subscription(sub_key: str):
    db = get_database()
    with db.session() as session:
        source = get_subscription_source(session, sub_key)
        if not source:
            return {'error': 'Subscription source not found'}, 404
        sub_id = source.id
        url = source.url

    cache_file = CACHE_FILE_DIR / f'{sub_id}.yml'
    cache_file_lock = CACHE_FILE_DIR / f'{sub_id}.lock'
    if not cache_file.exists():
        if not url or not cache_remote_sub(sub_id, url):
            with db.session() as session:
                source = get_subscription_source(session, sub_key)
                if source:
                    mark_failed_fetch(source)
            return {'error': 'Can not get subscription file'}, 500
        with db.session() as session:
            source = get_subscription_source(session, sub_key)
            if source:
                mark_successful_fetch(source)

    with FileLock(cache_file_lock, timeout=5):
        resp = make_response(
            send_file(
                cache_file,
                mimetype='text/yaml; charset=utf-8',
                download_name=cache_file.name,
                conditional=False,
                etag=False,
                as_attachment=False,
            ),
        )

        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        return resp


@sub_api.route('/list', methods=['GET'])
def list_subscriptions():
    db = get_database()
    with db.session() as session:
        sources = session.query(SubscriptionSource).all()
        result = [
            {
                'subscription_key': source.subscription_key,
                'name': source.name,
                'type': source.type,
                'url': source.url,
                'created_at': source.created_at,
                'updated_at': source.updated_at,
                'last_successful_fetch_at': serialize_datetime(source.last_successful_fetch_at),
                'last_fetch_status': source.last_fetch_status,
            }
            for source in sources
        ]
    return {'sub_list': result}


@sub_api.route('/update/<sub_key>', methods=['POST'])
def update_sub(sub_key: str):
    db = get_database()
    with db.session() as session:
        source = get_subscription_source(session, sub_key)
        if not source:
            return {'error': 'Subscription source not found'}, 404
        sub_id = source.id
        data = request.get_json(silent=True)

        if not data:
            return {'error': 'Request body is required'}, 400

        if 'type' not in data or data['type'] not in SUB_TYPE:
            return {'error': 'Invalid subscription type'}, 400

        if data['type'] == 'remote':
            if 'url' not in data or not data['url']:
                return {'error': 'URL is required for remote subscription type'}, 400
            if cache_remote_sub(sub_id, data['url']):
                source.type = data['type']
                source.url = data['url']
                mark_successful_fetch(source)
            else:
                mark_failed_fetch(source)
                return {'error': 'Failed to fetch subscription from the provided URL'}, 400
        elif data['type'] == 'local':
            if 'content' not in data or not data['content']:
                return {'error': 'Content is required for local subscription type'}, 400
            save_local_sub(sub_id, data['content'])
            source.type = data['type']
            source.url = None
            source.last_successful_fetch_at = None
            source.last_fetch_status = None
        else:
            return {'error': 'Unsupported subscription type'}, 400

        session.commit()
    return {'message': 'Subscription updated successfully'}, 200


@sub_api.route('/delete/<sub_key>', methods=['DELETE'])
def delete_sub(sub_key: str):
    db = get_database()
    with db.session() as session:
        source = get_subscription_source(session, sub_key)
        if not source:
            return {'error': 'Subscription source not found'}, 404
        sub_id = source.id

        session.delete(source)
        session.commit()

        cache_file = CACHE_FILE_DIR / f'{sub_id}.yml'
        cache_file_lock = CACHE_FILE_DIR / f'{sub_id}.lock'
        with FileLock(cache_file_lock, timeout=5):
            cache_file.unlink(missing_ok=True)
        cache_file_lock.unlink(missing_ok=True)

    return {'message': 'Subscription deleted successfully'}, 200


@sub_api.route('/add', methods=['POST'])
def add_sub():
    db = get_database()
    data = request.json

    if 'name' not in data or not data['name']:
        return {'error': 'Name is required'}, 400
    if 'type' not in data or data['type'] not in SUB_TYPE:
        return {'error': 'Invalid subscription type'}, 400

    new_source = SubscriptionSource(
        name=data['name'],
        type=data['type'],
    )
    with db.session() as session:
        session.add(new_source)
        session.flush()

        if data['type'] == 'remote':
            if 'url' not in data or not data['url']:
                return {'error': 'URL is required for remote subscription type'}, 400
            if cache_remote_sub(new_source.id, data['url']):
                new_source.url = data['url']
                mark_successful_fetch(new_source)
            else:
                return {'error': 'Failed to fetch subscription from the provided URL'}, 400
        elif data['type'] == 'local':
            if 'content' not in data or not data['content']:
                return {'error': 'Content is required for local subscription type'}, 400
            save_local_sub(new_source.id, data['content'])
        else:
            return {'error': 'Unsupported subscription type'}, 400

        session.commit()
        new_source_key = new_source.subscription_key

    return {'message': 'Subscription added successfully', 'subscription_key': new_source_key}, 201


@sub_api.route('/refresh/<sub_key>', methods=['POST'])
def refresh_sub_cache(sub_key: str):
    db = get_database()
    with db.session() as session:
        source = get_subscription_source(session, sub_key)
        if not source:
            return {'error': 'Subscription source not found'}, 404
        sub_id = source.id
        if source.type != 'remote' or not source.url:
            return {'error': 'Only remote subscriptions can be refreshed'}, 400

        if cache_remote_sub(sub_id, source.url):
            mark_successful_fetch(source)
            return {'message': 'Subscription cache refreshed successfully'}, 200
        else:
            mark_failed_fetch(source)
            return {'error': 'Failed to refresh subscription cache'}, 502
