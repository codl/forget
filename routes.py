from app import app
from flask import render_template, session, url_for, redirect, request
from datetime import datetime
import lib.twitter
from model import Account
from app import db

@app.route('/')
def index():
    viewer = None
    if 'remote_id' in session:
        viewer = Account.query.get(session['remote_id'])
        viewer.touch()
        db.session.commit()
    return render_template('index.html', viewer = viewer)

@app.route('/login/twitter')
def twitter_login_step1():
    return redirect(lib.twitter.get_login_url(
        callback = url_for('twitter_login_step2', _external=True),
        **app.config.get_namespace("TWITTER_")
        ))

@app.route('/login/twitter/callback')
def twitter_login_step2():
    oauth_token = request.args['oauth_token']
    oauth_verifier = request.args['oauth_verifier']
    token = lib.twitter.receive_verifier(oauth_token, oauth_verifier, **app.config.get_namespace("TWITTER_"))
    session['remote_id'] = token.remote_id
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    keys = list(session.keys())
    for key in keys:
        del session[key]
    return redirect(url_for('index'))
