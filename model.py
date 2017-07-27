from datetime import datetime

from app import db

from twitter import Twitter, OAuth
import secrets

class TimestampMixin(object):
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(),  onupdate=db.func.now())

    def touch(self):
        self.updated_at=db.func.now()


class Account(db.Model, TimestampMixin):
    __tablename__ = 'accounts'
    remote_id = db.Column(db.String, primary_key=True)

    # policy_enabled = db.Column(db.Boolean, server_default='FALSE', nullable=False)
    # policy_keep_younger = db.Column(db.Interval)
    # policy_keep_latest = db.Column(db.Integer)
    # policy_delete_every = db.Column(db.Interval)
    # policy_ignore_favourites = db.Column(db.Boolean, server_default='TRUE')

    remote_display_name = db.Column(db.String)
    remote_avatar_url = db.Column(db.String)

    last_post_fetch = db.Column(db.DateTime, server_default='epoch')

    # backref: tokens

class OAuthToken(db.Model, TimestampMixin):
    __tablename__ = 'oauth_tokens'

    token = db.Column(db.String, primary_key=True)
    token_secret = db.Column(db.String, nullable=False)

    remote_id = db.Column(db.String, db.ForeignKey('accounts.remote_id'))
    account = db.relationship(Account, backref=db.backref('tokens', order_by=lambda: db.desc(OAuthToken.created_at)))

class Session(db.Model, TimestampMixin):
    __tablename__ = 'sessions'

    id = db.Column(db.String, primary_key=True, default=lambda: secrets.token_urlsafe())

    account_id = db.Column(db.String, db.ForeignKey('accounts.remote_id'))
    account = db.relationship(Account, lazy='joined')

class Post(db.Model, TimestampMixin):
    __tablename__ = 'posts'

    remote_id = db.Column(db.String, primary_key=True)
    body = db.Column(db.String)

    author_id = db.Column(db.String, db.ForeignKey('accounts.remote_id'))
    author = db.relationship(Account)
