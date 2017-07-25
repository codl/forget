from datetime import datetime

from app import db

class TimestampMixin(object):
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(),  onupdate=db.func.now())

class User(db.Model, TimestampMixin):
    __tablename__ = 'users'

    display_name = db.Column(db.String)
    id = db.Column(db.Integer, primary_key=True)

class Account(db.Model, TimestampMixin):

    user = db.relationship(User)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    service = db.Column(
            db.Enum("twitter", name="enum_services")
            , primary_key=True)
    remote_id = db.Column(db.String, primary_key=True)

    credentials = db.Column(db.JSON)

    policy_enabled = db.Column(db.Boolean, server_default='FALSE', nullable=False)
    policy_keep_younger = db.Column(db.Interval)
    policy_keep_latest = db.Column(db.Integer)
    policy_delete_every = db.Column(db.Interval)
    policy_ignore_favourites = db.Column(db.Boolean, server_default='TRUE')
