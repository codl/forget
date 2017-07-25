from app import app
from flask import render_template, session, url_for, redirect
from datetime import datetime

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login/twitter')
def debug_login():
    session['display_name'] = 'codl'
    session['created_at'] = datetime.now()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    keys = list(session.keys())
    for key in keys:
        del session[key]
    return redirect(url_for('index'))
