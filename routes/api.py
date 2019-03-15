from app import app, db
from libforget.auth import require_auth_api, get_viewer
from flask import jsonify, redirect, make_response, request, Response
from model import Account
import libforget.settings
import libforget.json
import random

@app.route('/api/health_check')
def health_check():
    try:
        db.session.execute('SELECT 1')
        return 'ok'
    except Exception:
        return ('bad', 500)


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


@app.route('/api/known_instances', methods=('GET', 'DELETE'))
def known_instances():
    if request.method == 'GET':
        known = request.cookies.get('forget_known_instances', '')
        if not known:
            return Response('[]', 404, mimetype='application/json')

        # pad to avoid oracle attacks
        for _ in range(random.randint(0, 1000)):
                known += random.choice((' ', '\t', '\n'))

        return Response(known, mimetype='application/json')

    elif request.method == 'DELETE':
        resp = Response('', 204)
        resp.set_cookie('forget_known_instances', '', max_age=0)
        return resp
