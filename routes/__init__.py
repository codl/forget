from flask import render_template, url_for, redirect, request, g,\
                  make_response
from datetime import datetime, timedelta, timezone
import libforget.twitter
import libforget.mastodon
from libforget.auth import require_auth, csrf,\
                     get_viewer
from model import Session, TwitterArchive, MastodonApp
from app import app, db, sentry, imgproxy
import tasks
from zipfile import BadZipFile
from twitter import TwitterError
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
    instances = libforget.mastodon.suggested_instances()
    return render_template(
            'about.html',
            mastodon_instances=instances,
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


class TweetArchiveEmptyException(Exception):
    pass


@app.route('/upload_tweet_archive', methods=('POST',))
@require_auth
def upload_tweet_archive():
    ta = TwitterArchive(
            account=g.viewer.account,
            body=request.files['file'].read())
    db.session.add(ta)
    db.session.commit()

    try:
        files = libforget.twitter.chunk_twitter_archive(ta.id)

        ta.chunks = len(files)
        db.session.commit()

        if not ta.chunks > 0:
            raise TweetArchiveEmptyException()

        for filename in files:
            tasks.import_twitter_archive_month.s(ta.id, filename).apply_async()

        return redirect(url_for('index', _anchor='recent_archives'))
    except (BadZipFile, TweetArchiveEmptyException):
        if sentry:
            sentry.captureException()
        return redirect(
                url_for('index', tweet_archive_failed='',
                        _anchor='tweet_archive_import'))


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


@app.route('/login/mastodon', methods=('GET', 'POST'))
def mastodon_login_step1(instance=None):

    instance_url = (request.args.get('instance_url', None)
                    or request.form.get('instance_url', None))

    if not instance_url:
        instances = libforget.mastodon.suggested_instances(
                limit=30,
                min_popularity=1
        )
        return render_template(
                'mastodon_login.html', instances=instances,
                address_error=request.method == 'POST',
                generic_error='error' in request.args
                )

    instance_url = instance_url.lower()
    # strip protocol
    instance_url = re.sub('^https?://', '', instance_url,
                          count=1, flags=re.IGNORECASE)
    # strip username
    instance_url = instance_url.split("@")[-1]
    # strip trailing path
    instance_url = instance_url.split('/')[0]

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

    resp = redirect(url_for('index'))
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
