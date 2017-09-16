from app import app, db, sentry
from flask import g, render_template, make_response, redirect
import version
import lib.version
from lib.auth import get_viewer_session, set_session_cookie


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
        return dict(sentry=True)
    return dict()


@app.after_request
def touch_viewer(resp):
    if 'viewer' in g and g.viewer:
        set_session_cookie(g.viewer, resp, app.config.get('HTTPS'))
        g.viewer.touch()
        db.session.commit()
    return resp


@app.errorhandler(404)
def not_found(e):
    return (render_template('404.html', e=e), 404)


@app.errorhandler(500)
def internal_server_error(e):
    return (render_template('500.html', e=e), 500)


@app.route('/robots.txt')
def robotstxt():
    resp = make_response('')
    resp.headers.set('content-type', 'text/plain')
    return resp


@app.route('/humans.txt')
def humanstxt():
    return redirect('https://github.com/codl/forget/graph/contributors')
