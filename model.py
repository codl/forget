import datetime

from app import db

model = db.Model

class User(db.Model):
    __tablename__ = 'users'

    display_name = db.Column(db.String)
    id = db.Column(db.Integer, primary_key=True)

class Account(db.Model):

    user = db.relationship(User)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    remote_id = db.Column(db.String, primary_key=True)
    service = db.Column(
            db.Enum("twitter", name="enum_services")
            , primary_key=True)
    credentials = db.Column(db.JSON)

    policy_enabled = db.Column(db.Boolean, default=False)
    policy_keep_younger = db.Column(db.Interval)
    policy_keep_latest = db.Column(db.Integer)
    policy_delete_every = db.Column(db.Interval)

class Session(db.Model):
    __tablename__ = 'sessions'

    user = db.relationship(User)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    token = db.Column(db.String, primary_key=True)

