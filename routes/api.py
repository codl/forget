from app import app, db, imgproxy
from libforget.auth import require_auth_api, get_viewer
from flask import jsonify, redirect, make_response, request, Response
from model import Account
import libforget.settings
import libforget.json
import random

@app.route('/api/health_check') # deprecated 2021-03-12
@app.route('/api/status_check')
def api_status_check():
    try:
        db.session.execute('SELECT 1')
    except Exception:
        return ('PostgreSQL bad', 500)

    try:
        imgproxy.redis.set('forget-status-check', 'howdy', ex=5)
    except Exception:
        return ('Redis bad', 500)

    if db.session.execute(db.text("""
        SELECT 1 FROM accounts
        WHERE last_delete > now() - '60 minutes'::INTERVAL
        OR last_fetch > now() - '60 minutes'::INTERVAL
        OR last_refresh > now() - '60 minutes'::INTERVAL
        LIMIT 1;
    """)).fetchone() is None:
        return ('Celery stalled', 500)

    return 'OK'


@app.route('/api/settings', methods=('PUT',))
@require_auth_api
def api_settings_put():
    viewer = get_viewer()
    data = request.json
    updated = dict()
    for key in libforget.settings.attrs:
        if key in data:
            if (
                    isinstance(getattr(viewer, key), bool) and
                    isinstance(data[key], str)):
                data[key] = data[key] == 'true'
            setattr(viewer, key, data[key])
            updated[key] = data[key]
    db.session.commit()
    return jsonify(status='success', updated=updated)


@app.route('/api/viewer')
@require_auth_api
def api_viewer():
    viewer = get_viewer()
    resp = make_response(libforget.json.account(viewer))
    resp.headers.set('content-type', 'application/json')
    return resp


@app.route('/api/reason', methods={'DELETE'})
@require_auth_api
def delete_reason():
    get_viewer().reason = None
    db.session.commit()
    return jsonify(status='success')


@app.route('/api/badge/users')
def users_badge():
    count = (
        Account.query.filter(Account.policy_enabled)
        .filter(~Account.dormant)
        .count()
        )
    return redirect(
            "https://img.shields.io/badge/active%20users-{}-blue.svg"
            .format(count))
