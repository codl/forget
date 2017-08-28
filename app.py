from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, event
from sqlalchemy.engine import Engine
from flask_migrate import Migrate
import version
from lib import cachebust
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from lib import get_viewer
import os
import mimetypes

app = Flask(__name__)

default_config = {
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg2:///forget",
        "SECRET_KEY": "hunter2",
        "CELERY_BROKER": "redis://",
        "HTTPS": True,
        "SENTRY_CONFIG": {},
        "RATELIMIT_STORAGE_URL": "redis://",
        "REPO_URL": "https://github.com/codl/forget",
        "COMMIT_URL": "https://github.com/codl/forget/commits/{hash}",
}

app.config.update(default_config)

app.config.from_pyfile('config.py', True)

metadata = MetaData(naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
})

db = SQLAlchemy(app, metadata=metadata)
migrate = Migrate(app, db)

if 'SQLALCHEMY_LOG_QUERIES_TO' in app.config:
    @event.listens_for(Engine, 'after_cursor_execute', named=True)
    def log_queries(statement='', **kwargs):
        with open(app.config['SQLALCHEMY_LOG_QUERIES_TO'], 'a') as f:
            f.write(statement.replace('\n', ' ') + ';\n')
            os.sync()

sentry = None
if 'SENTRY_DSN' in app.config:
    from raven.contrib.flask import Sentry
    app.config['SENTRY_CONFIG']['release'] = version.version
    sentry = Sentry(app, dsn=app.config['SENTRY_DSN'])

url_for = cachebust(app)

@app.context_processor
def inject_static():
    def static(filename, **kwargs):
        return url_for('static', filename=filename, **kwargs)
    return {'st': static}

def rate_limit_key():
    viewer = get_viewer()
    if viewer:
        return viewer.id
    for address in request.access_route:
        if address != '127.0.0.1':
            print(address)
            return address
    return request.remote_addr

limiter = Limiter(app, key_func=rate_limit_key)

@app.after_request
def install_security_headers(resp):
    csp = "default-src 'none'; img-src 'self' https:; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'"
    if 'CSP_REPORT_URI' in app.config:
        csp += "; report-uri " + app.config.get('CSP_REPORT_URI')

    if app.config.get('HTTPS'):
        resp.headers.set('strict-transport-security', 'max-age={}'.format(60*60*24*365))
        csp += "; upgrade-insecure-requests"

    resp.headers.set('Content-Security-Policy', csp)
    resp.headers.set('referrer-policy', 'no-referrer')
    resp.headers.set('x-content-type-options', 'nosniff')
    resp.headers.set('x-frame-options', 'DENY')
    resp.headers.set('x-xss-protection', '1')

    return resp

mimetypes.add_type('image/webp', '.webp')
