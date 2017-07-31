from flask import g, redirect

def require_auth(fun, redir=True):

    from functools import update_wrapper
    def wrapper(*args, **kwargs):
        if not g.viewer:
            if redir:
                return redirect('/')
            else:
                return 403
        else:
            return fun(*args, **kwargs)

    update_wrapper(wrapper, fun)
    return wrapper


