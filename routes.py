from flask import render_template, url_for, redirect, request, g, Response, jsonify
from datetime import datetime, timedelta
import lib.twitter
import lib.mastodon
import lib
from lib.auth import require_auth, require_auth_api
from lib import set_session_cookie
from lib import get_viewer_session, get_viewer
from model import Account, Session, Post, TwitterArchive, MastodonApp
from app import app, db, sentry, limiter
import tasks
from zipfile import BadZipFile
from twitter import TwitterError
from urllib.error import URLError
import version
import lib.version

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
    return dict(
            version=version.version,
            repo_url=lib.version.url_for_version(version.version),
        )

@app.context_processor
def inject_sentry():
    if sentry:
        client_dsn = app.config.get('SENTRY_DSN').split('@')
        client_dsn[:1] = client_dsn[0].split(':')
        client_dsn = ':'.join(client_dsn[0:2]) + '@' + client_dsn[3]
        return dict(sentry_dsn=client_dsn)
    return dict()

@app.after_request
def touch_viewer(resp):
    if 'viewer' in g and g.viewer:
        set_session_cookie(g.viewer, resp, app.config.get('HTTPS'))
        g.viewer.touch()
        db.session.commit()
    return resp


lib.brotli.brotli(app)

@app.route('/')
def index():
    if g.viewer:
        return render_template('logged_in.html', scales=lib.interval.SCALES,
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
        files = lib.twitter.chunk_twitter_archive(ta.id)

        ta.chunks = len(files)
        db.session.commit()

        assert ta.chunks > 0

        for filename in files:
            tasks.import_twitter_archive_month.s(ta.id, filename).apply_async()


        return redirect(url_for('index', _anchor='recent_archives'))
    except (BadZipFile, AssertionError):
        return redirect(url_for('index', tweet_archive_failed='', _anchor='tweet_archive_import'))

@app.route('/settings', methods=('POST',))
@require_auth
def settings():
    viewer = get_viewer()
    try:
        for attr in lib.settings.attrs:
            if attr in request.form:
                setattr(viewer, attr, request.form[attr])
        db.session.commit()
    except ValueError:
        return 400


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
        if g.viewer.account.next_delete < datetime.now() - timedelta(days=365):
            return render_template('warn.html', message="""Once you enable Forget, posts that match your expiration rules will be deleted <b>permanently</b>. We can't bring them back. Make sure that you won't miss them.""")


    if not g.viewer.account.policy_enabled:
        g.viewer.account.next_delete = datetime.now() + g.viewer.account.policy_delete_every

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

@app.route('/api/settings', methods=('PUT',))
@require_auth_api
def api_settings_put():
    viewer = get_viewer()
    data = request.json
    updated = dict()
    for key in lib.settings.attrs:
        if key in data:
            setattr(viewer, key, data[key])
            updated[key] = data[key]
    db.session.commit()
    return jsonify(status='success', updated=updated)

@app.route('/api/viewer')
@require_auth_api
def api_viewer():
    viewer = get_viewer()
    return jsonify(
            post_count=viewer.post_count(),
            eligible_for_delete_estimate=viewer.estimate_eligible_for_delete(),
            display_name=viewer.display_name,
            screen_name=viewer.screen_name,
            avatar_url=viewer.avatar_url,
            id=viewer.id,
            service=viewer.service,
        )

@app.route('/api/viewer/timers')
@require_auth_api
def api_viewer_timers():
    viewer = get_viewer()
    return jsonify(
            last_refresh=viewer.last_refresh,
            last_refresh_rel=lib.interval.relnow(viewer.last_refresh),
            last_fetch=viewer.last_fetch,
            last_fetch_rel=lib.interval.relnow(viewer.last_fetch),
            next_delete=viewer.next_delete,
            next_delete_rel=lib.interval.relnow(viewer.next_delete),
        )

@app.route('/login/mastodon', methods=('GET', 'POST'))
def mastodon_login_step1():
    if request.method == 'GET':
        return render_template('mastodon_login.html', generic_error = 'error' in request.args)

    if not 'instance_url' in request.form or not request.form['instance_url']:
        return render_template('mastodon_login.html', address_error=True)

    instance_url = request.form['instance_url'].split("@")[-1].lower()

    callback = url_for('mastodon_login_step2', instance=instance_url, _external=True)

    app = lib.mastodon.get_or_create_app(instance_url,
            callback,
            url_for('index', _external=True))
    db.session.merge(app)

    db.session.commit()

    return redirect(lib.mastodon.login_url(app, callback))

@app.route('/login/mastodon/callback/<instance>')
def mastodon_login_step2(instance):
    code = request.args.get('code', None)
    app = MastodonApp.query.get(instance)
    if not code or not app:
        return redirect('mastodon_login_step1', error=True)

    callback = url_for('mastodon_login_step2', instance=instance, _external=True)

    token = lib.mastodon.receive_code(code, app, callback)
    account = token.account

    sess = Session(account = account)
    db.session.add(sess)
    db.session.commit()

    g.viewer = sess
    return redirect(url_for('index'))


@app.route('/debug')
def debug():
    sess = Session(account = Account.query.filter_by(display_name = 'codltest').first())
    db.session.merge(sess)
    db.session.commit()
    return sess.id
