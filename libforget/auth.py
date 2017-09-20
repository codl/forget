from flask import g, redirect, jsonify, make_response, abort, request
from functools import wraps


def require_auth(fun):
    @wraps(fun)
    def wrapper(*args, **kwargs):
        if not g.viewer:
            return redirect('/')
        return fun(*args, **kwargs)
    return wrapper


def require_auth_api(fun):
    @wraps(fun)
    def wrapper(*args, **kwargs):
        if not g.viewer:
            return make_response((
                jsonify(status='error', error='not logged in'),
                403))
        return fun(*args, **kwargs)
    return wrapper


def csrf(fun):
    @wraps(fun)
    def wrapper(*args, **kwargs):
        if request.form.get('csrf-token') != g.viewer.csrf_token:
            return abort(403)
        return fun(*args, **kwargs)
    return wrapper


def set_session_cookie(session, response, secure=True):
    response.set_cookie(
        'forget_sid', session.id,
        max_age=60*60*48,
        httponly=True,
        secure=secure)


def get_viewer_session():
    from model import Session
    sid = request.cookies.get('forget_sid', None)
    if sid:
        return Session.query.get(sid)


def get_viewer():
    session = get_viewer_session()
    if session:
        return session.account
