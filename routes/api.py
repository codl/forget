from app import app, db
from lib.auth import require_auth_api, get_viewer
from flask import jsonify, redirect, make_response, request
from model import Account
import lib.settings
import lib.json


@app.route('/api/settings', methods=('PUT',))
@require_auth_api
def api_settings_put():
    viewer = get_viewer()
    data = request.json
    updated = dict()
    for key in lib.settings.attrs:
        if key in data:
            setattr(viewer, key, data[key])
            updated[key] = data[key]
    db.session.commit()
    return jsonify(status='success', updated=updated)


@app.route('/api/viewer')
@require_auth_api
def api_viewer():
    viewer = get_viewer()
    resp = make_response(lib.json.account(viewer))
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
