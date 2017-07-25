from app import app
from flask import request, Response
from lib import require_auth

@app.route('/')
@require_auth
def index(viewer):
    return "Hello, %s (%s)" % (viewer.name, viewer.twitter_id)

