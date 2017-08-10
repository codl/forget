from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_migrate import Migrate
import version
from lib import cachebust
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from lib import get_viewer

app = Flask(__name__)

default_config = {
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg2:///forget",
        "SECRET_KEY": "hunter2",
        "CELERY_BROKER": "amqp://",
        "HTTPS": True,
        "SENTRY_CONFIG": {},
        "RATELIMIT_STORAGE_URL": "redis://",
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
