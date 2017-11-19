from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_migrate import Migrate
import version
from libforget.cachebust import cachebust
import mimetypes
import libforget.brotli
import libforget.img_proxy

app = Flask(__name__)

default_config = {
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg2:///forget",
        "HTTPS": True,
        "SENTRY_CONFIG": {},
        "REPO_URL": "https://github.com/codl/forget",
        "COMMIT_URL": "https://github.com/codl/forget/commits/{hash}",
        "REDIS_URI": "redis://",
}

app.config.update(default_config)

app.config.from_pyfile('config.py', True)

metadata = MetaData(naming_convention={
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
})

db = SQLAlchemy(app, metadata=metadata)
migrate = Migrate(app, db)

if 'CELERY_BROKER' not in app.config:
    uri = app.config['REDIS_URI']
    if uri.startswith('unix://'):
        uri = uri.replace('unix', 'redis+socket', 1)
    app.config['CELERY_BROKER'] = uri

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


@app.after_request
def install_security_headers(resp):
    csp = ("default-src 'none';"
           "img-src 'self';"
           "style-src 'self' 'unsafe-inline';"
           "frame-ancestors 'none';"
           )
    if 'SENTRY_DSN' in app.config:
        csp += "script-src 'self' https://cdn.ravenjs.com/;"
        csp += "connect-src 'self' https://sentry.io/;"
    else:
        csp += "script-src 'self';"
        csp += "connect-src 'self';"

    if 'CSP_REPORT_URI' in app.config:
        csp += "report-uri " + app.config.get('CSP_REPORT_URI')

    if app.config.get('HTTPS'):
        resp.headers.set('strict-transport-security',
                         'max-age={}'.format(60*60*24*365))
        csp += "; upgrade-insecure-requests"

    resp.headers.set('Content-Security-Policy', csp)
    resp.headers.set('referrer-policy', 'no-referrer')
    resp.headers.set('x-content-type-options', 'nosniff')
    resp.headers.set('x-frame-options', 'DENY')
    resp.headers.set('x-xss-protection', '1')

    return resp


mimetypes.add_type('image/webp', '.webp')

libforget.brotli.brotli(app)

imgproxy = (
    libforget.img_proxy.ImgProxyCache(redis_uri=app.config.get('REDIS_URI')))
