from model import User
from flask import request
from functools import update_wrapper

def require_auth(fun):
    # TODO actual auth and session checking and such
    def newfun(*args, **kwargs):
        fun(User.query.get('8080418'), *args, **kwargs)
    update_wrapper(newfun, fun)
    return newfun
