from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_migrate import Migrate

app = Flask(__name__)

default_config = {
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg2:///forget",
        "SECRET_KEY": "hunter2",
        "CELERY_BROKER": "amqp://",
        "HTTPS": True
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
