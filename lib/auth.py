from flask import g, redirect, jsonify, make_response
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
            return make_response((jsonify(status='error', error='not logged in'), 403))
        return fun(*args, **kwargs)
    return wrapper


