from flask import request


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
