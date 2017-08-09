def set_session_cookie(session, response, secure=True):
    response.set_cookie('forget_sid', session.id,
        max_age=60*60*48,
        httponly=True,
        secure=secure)
