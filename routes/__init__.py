from flask import render_template, url_for, redirect, request, g,\
                  make_response
from datetime import datetime, timedelta, timezone
import libforget.twitter
import libforget.mastodon
import libforget.misskey
from libforget.auth import require_auth, csrf,\
                     get_viewer
from libforget.session import make_session
from model import Session, TwitterArchive, MastodonApp, MisskeyApp
from app import app, db, sentry, imgproxy
import tasks
from zipfile import BadZipFile
from twitter import TwitterError
from urllib.parse import urlparse
from urllib.error import URLError
import libforget.version
import libforget.settings
import libforget.json
import re


@app.route('/')
def index():
    viewer = get_viewer()
    if viewer:
        return render_template(
                'logged_in.html',
                scales=libforget.interval.SCALES,
                tweet_archive_failed='tweet_archive_failed' in request.args,
                settings_error='settings_error' in request.args,
                viewer_json=libforget.json.account(viewer),
                )
    else:
        return redirect(url_for('about'))


@app.route('/about/')
def about():
    blocklist = app.config.get('HIDDEN_INSTANCES', '').split()
    mastodon_instances = libforget.mastodon.suggested_instances(blocklist=blocklist)
    misskey_instances = libforget.misskey.suggested_instances(blocklist=blocklist)
    return render_template(
            'about.html',
            mastodon_instances=mastodon_instances,
            misskey_instances=misskey_instances,
            twitter_login_error='twitter_login_error' in request.args)


@app.route('/about/privacy')
def privacy():
    return render_template('privacy.html')


@app.route('/login/twitter')
def twitter_login_step1():
    try:
        return redirect(libforget.twitter.get_login_url(
            callback=url_for('twitter_login_step2', _external=True),
            **app.config.get_namespace("TWITTER_")
            ))
    except (TwitterError, URLError):
        if sentry:
            sentry.captureException()
        return redirect(
                url_for('about', twitter_login_error='', _anchor='log_in'))


def login(account_id):
    session = Session(account_id=account_id)
    db.session.add(session)
    db.session.commit()

    session.account.dormant = False
    db.session.commit()

    tasks.fetch_acc.s(account_id).apply_async(routing_key='high')

    return session


@app.route('/login/twitter/callback')
def twitter_login_step2():
    try:
        oauth_token = request.args.get('oauth_token', '')
        oauth_verifier = request.args.get('oauth_verifier', '')
        token = libforget.twitter.receive_verifier(
                oauth_token, oauth_verifier,
                **app.config.get_namespace("TWITTER_"))

        session = login(token.account_id)

        g.viewer = session
        return redirect(url_for('index'))
    except Exception:
        if sentry:
            sentry.captureException()
        return redirect(
                url_for('about', twitter_login_error='', _anchor='log_in'))


@app.route('/upload_tweet_archive', methods=('POST',))
def upload_tweet_archive():
    return 403, 'Tweet archive support is temporarily disabled, see banner on the front page.'


@app.route('/settings', methods=('POST',))
@csrf
@require_auth
def settings():
    viewer = get_viewer()
    try:
        for attr in libforget.settings.attrs:
            if attr in request.form:
                setattr(viewer, attr, request.form[attr])
        db.session.commit()
    except ValueError:
        if sentry:
            sentry.captureException()
        return 400

    return redirect(url_for('index', settings_saved=''))


@app.route('/disable', methods=('POST',))
@csrf
@require_auth
def disable():
    g.viewer.account.policy_enabled = False
    db.session.commit()

    return redirect(url_for('index'))


@app.route('/enable', methods=('POST',))
@csrf
@require_auth
def enable():
    if 'confirm' not in request.form and not g.viewer.account.policy_enabled:
        if g.viewer.account.policy_delete_every == timedelta(0):
            approx = g.viewer.account.estimate_eligible_for_delete()
            return render_template(
                'warn.html',
                message=f"""
                    You've set the time between deleting posts to 0. Every post
                    that matches your expiration rules will be deleted within
                    minutes.
                    { ("That's about " + str(approx) + " posts.") if approx > 0
                        else "" }
                    Go ahead?
                    """)
        if (not g.viewer.account.last_delete or
           g.viewer.account.last_delete <
           datetime.now(timezone.utc) - timedelta(days=365)):
            return render_template(
                    'warn.html',
                    message="""
                        Once you enable Forget, posts that match your
                        expiration rules will be deleted <b>permanently</b>.
                        We can't bring them back. Make sure that you won't
                        miss them.
                        """)

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
    return redirect(url_for('about'))


def domain_from_url(url):
    return urlparse(url).netloc.lower() or urlparse("//"+url).netloc.lower()

@app.route('/login/mastodon', methods=('GET', 'POST'))
def mastodon_login_step1(instance=None):

    instance_url = (request.args.get('instance_url', None)
                    or request.form.get('instance_url', None))

    if not instance_url:
        blocklist = app.config.get('HIDDEN_INSTANCES', '').split()
        instances = libforget.mastodon.suggested_instances(
                limit=30,
                min_popularity=1,
                blocklist=blocklist,
        )
        return render_template(
                'mastodon_login.html', instances=instances,
                address_error=request.method == 'POST',
                generic_error='error' in request.args
                )

    instance_url = domain_from_url(instance_url)

    callback = url_for('mastodon_login_step2',
                       instance_url=instance_url, _external=True)

    try:
        app = libforget.mastodon.get_or_create_app(
                instance_url,
                callback,
                url_for('index', _external=True))
        db.session.merge(app)

        db.session.commit()

        return redirect(libforget.mastodon.login_url(app, callback))

    except Exception:
        if sentry:
            sentry.captureException()
        return redirect(url_for('mastodon_login_step1', error=True))


@app.route('/login/mastodon/callback/<instance_url>')
def mastodon_login_step2(instance_url):
    code = request.args.get('code', None)
    app = MastodonApp.query.get(instance_url)
    if not code or not app:
        return redirect(url_for('mastodon_login_step1', error=True))

    callback = url_for('mastodon_login_step2',
                       instance_url=instance_url, _external=True)

    token = libforget.mastodon.receive_code(code, app, callback)
    account = token.account

    session = login(account.id)

    db.session.commit()

    g.viewer = session

    resp = redirect(url_for('index', _anchor='bump_instance'))
    return resp


@app.route('/login/misskey', methods=('GET', 'POST'))
def misskey_login(instance=None):
    instance_url = (request.args.get('instance_url', None)
                    or request.form.get('instance_url', None))

    if not instance_url:
        blocklist = app.config.get('HIDDEN_INSTANCES', '').split()
        instances = libforget.misskey.suggested_instances(
            limit = 30,
            min_popularity = 1,
            blocklist=blocklist,
        )
        return render_template(
                'misskey_login.html', instances=instances,
                address_error=request.method == 'POST',
                generic_error='error' in request.args
                )

    instance_url = domain_from_url(instance_url)

    callback = url_for('misskey_callback',
                       instance_url=instance_url, _external=True)

    try:
        session = make_session()
        app = libforget.misskey.get_or_create_app(
                instance_url,
                callback,
                url_for('index', _external=True),
                session)
        db.session.merge(app)

        db.session.commit()

        return redirect(libforget.misskey.login_url(app, callback, session))

    except Exception:
        if sentry:
            sentry.captureException()
        return redirect(url_for('misskey_login', error=True))


@app.route('/login/misskey/callback/<instance_url>')
def misskey_callback(instance_url):
    # legacy auth and miauth use different parameter names
    token = request.args.get('token', None) or request.args.get('session', None)
    app = MisskeyApp.query.get(instance_url)
    if not token or not app:
        return redirect(url_for('misskey_login', error=True))

    token = libforget.misskey.receive_token(token, app)
    account = token.account

    session = login(account.id)

    db.session.commit()

    g.viewer = session

    resp = redirect(url_for('index', _anchor='bump_instance'))
    return resp


@app.route('/sentry/setup.js')
def sentry_setup():
    client_dsn = app.config.get('SENTRY_DSN').split('@')
    client_dsn[:1] = client_dsn[0].split(':')
    client_dsn = ':'.join(client_dsn[0:2]) + '@' + client_dsn[3]
    resp = make_response(render_template(
        'sentry.js', sentry_dsn=client_dsn))
    resp.headers.set('content-type', 'text/javascript')
    resp.headers.set('cache-control', 'public; max-age=3600')
    return resp


@app.route('/dismiss', methods={'POST'})
@csrf
@require_auth
def dismiss():
    get_viewer().reason = None
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/avatar/<identifier>')
def avatar(identifier):
    return imgproxy.respond(identifier)
