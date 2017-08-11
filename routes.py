from flask import render_template, url_for, redirect, request, g, Response
from datetime import datetime, timedelta
import lib.twitter
import lib
from lib import require_auth
from lib import set_session_cookie
from lib import get_viewer_session
from model import Account, Session, Post, TwitterArchive
from app import app, db, sentry, limiter
import tasks
from zipfile import BadZipFile
from twitter import TwitterError
from urllib.error import URLError
import version
import lib.brotli

@app.before_request
def load_viewer():
    g.viewer = get_viewer_session()
    if g.viewer and sentry:
        sentry.user_context({
                'id': g.viewer.account.id,
                'username': g.viewer.account.screen_name,
                'service': g.viewer.account.service
            })

@app.context_processor
def inject_version():
    return dict(version=version.version)

@app.after_request
def touch_viewer(resp):
    if 'viewer' in g and g.viewer:
        set_session_cookie(g.viewer, resp, app.config.get('HTTPS'))
        g.viewer.touch()
        db.session.commit()
    return resp

app.after_request(lib.brotli.compress_response)

@app.route('/')
def index():
    if g.viewer:
        return render_template('logged_in.html', scales=lib.interval_scales,
                tweet_archive_failed = 'tweet_archive_failed' in request.args,
                settings_error = 'settings_error' in request.args
                )
    else:
        return render_template('index.html',
                twitter_login_error = 'twitter_login_error' in request.args)

@app.route('/login/twitter')
@limiter.limit('3/minute')
def twitter_login_step1():
    try:
        return redirect(lib.twitter.get_login_url(
            callback = url_for('twitter_login_step2', _external=True),
            **app.config.get_namespace("TWITTER_")
            ))
    except (TwitterError, URLError):
        return redirect(url_for('index', twitter_login_error='', _anchor='log_in'))

@app.route('/login/twitter/callback')
@limiter.limit('3/minute')
def twitter_login_step2():
    try:
        oauth_token = request.args['oauth_token']
        oauth_verifier = request.args['oauth_verifier']
        token = lib.twitter.receive_verifier(oauth_token, oauth_verifier, **app.config.get_namespace("TWITTER_"))

        session = Session(account_id = token.account_id)
        db.session.add(session)
        db.session.commit()

        tasks.fetch_acc.s(token.account_id).apply_async(routing_key='high')

        resp = Response(status=302, headers={"location": url_for('index')})
        set_session_cookie(session, resp, app.config.get('HTTPS'))
        return resp
    except (TwitterError, URLError):
        return redirect(url_for('index', twitter_login_error='', _anchor='log_in'))

@app.route('/upload_tweet_archive', methods=('POST',))
@limiter.limit('10/10 minutes')
@require_auth
def upload_tweet_archive():
    ta = TwitterArchive(account = g.viewer.account,
            body = request.files['file'].read())
    db.session.add(ta)
    db.session.commit()

    try:
        tasks.chunk_twitter_archive(ta.id)

        assert ta.chunks > 0

        return redirect(url_for('index', _anchor='recent_archives'))
    except (BadZipFile, AssertionError):
        return redirect(url_for('index', tweet_archive_failed='', _anchor='tweet_archive_import'))

@app.route('/settings', methods=('POST',))
@require_auth
def settings():
    for attr in (
            'policy_keep_favourites',
            'policy_keep_latest',
            'policy_delete_every_scale',
            'policy_delete_every_significand',
            'policy_keep_younger_scale',
            'policy_keep_younger_significand',
            'policy_keep_media',
            ):
        try:
            if attr in request.form:
                setattr(g.viewer.account, attr, request.form[attr])
        except ValueError:
            return redirect(url_for('index', settings_error=''))

    db.session.commit()

    return redirect(url_for('index', settings_saved=''))

@app.route('/disable', methods=('POST',))
@require_auth
def disable():
    g.viewer.account.policy_enabled = False
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/enable', methods=('POST',))
@require_auth
def enable():

    risky = False
    if not 'confirm' in request.form and not g.viewer.account.policy_enabled:
        if g.viewer.account.policy_delete_every == timedelta(0):
            approx = g.viewer.account.estimate_eligible_for_delete()
            return render_template('warn.html', message=f"""You've set the time between deleting posts to 0. Every post that matches your expiration rules will be deleted within minutes.
                    { ("That's about " + str(approx) + " posts.") if approx > 0 else "" }
                    Go ahead?""")
        if g.viewer.account.last_delete < datetime.now() - timedelta(days=365):
            return render_template('warn.html', message="""Once you enable Forget, posts that match your expiration rules will be deleted <b>permanently</b>. We can't bring them back. Make sure that you won't miss them.""")


    if not g.viewer.account.policy_enabled:
        g.viewer.account.last_delete = db.func.now()

    g.viewer.account.policy_enabled = True
    db.session.commit()

    return redirect(url_for('index'))


@app.route('/logout')
@require_auth
def logout():
    if(g.viewer):
        db.session.delete(g.viewer)
        db.session.commit()
        g.viewer = None
    return redirect(url_for('index'))
