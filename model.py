from datetime import datetime

from app import db

from twitter import Twitter, OAuth
import secrets
from lib import decompose_interval

class TimestampMixin(object):
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(),  onupdate=db.func.now())

    def touch(self):
        self.updated_at=db.func.now()

class RemoteIDMixin(object):
    @property
    def service(self):
        if not self.id:
            return None
        return self.id.split(":")[0]

    @property
    def twitter_id(self):
        if not self.id:
            return None
        if self.service != "twitter":
            raise Exception("wrong service bucko")
        return self.id.split(":")[1]

    @twitter_id.setter
    def twitter_id(self, id):
        self.id = "twitter:{}".format(id)



@decompose_interval('policy_delete_every')
@decompose_interval('policy_keep_younger')
class Account(TimestampMixin, RemoteIDMixin):
    __tablename__ = 'accounts'
    id = db.Column(db.String, primary_key=True)

    policy_enabled = db.Column(db.Boolean, server_default='FALSE', nullable=False)
    policy_keep_latest = db.Column(db.Integer, server_default='0')
    policy_ignore_favourites = db.Column(db.Boolean, server_default='TRUE')
    policy_delete_every = db.Column(db.Interval, server_default='0')
    policy_keep_younger = db.Column(db.Interval, server_default='0')

    remote_display_name = db.Column(db.String)
    remote_screen_name = db.Column(db.String)
    remote_avatar_url = db.Column(db.String)

    last_fetch = db.Column(db.DateTime, server_default='epoch')

    def touch_fetch(self):
        self.last_fetch = db.func.now()

    # backref: tokens
    # backref: twitter_archives

    def __repr__(self):
        return f"<Account({self.id}, {self.remote_screen_name}, {self.remote_display_name})>"

    def post_count(self):
        return Post.query.filter(Post.author_id == self.id).count()


class Account(Account, db.Model):
    pass


class OAuthToken(db.Model, TimestampMixin):
    __tablename__ = 'oauth_tokens'

    token = db.Column(db.String, primary_key=True)
    token_secret = db.Column(db.String, nullable=False)

    account_id = db.Column(db.String, db.ForeignKey('accounts.id'))
    account = db.relationship(Account, backref=db.backref('tokens', order_by=lambda: db.desc(OAuthToken.created_at)))

class Session(db.Model, TimestampMixin):
    __tablename__ = 'sessions'

    id = db.Column(db.String, primary_key=True, default=lambda: secrets.token_urlsafe())

    account_id = db.Column(db.String, db.ForeignKey('accounts.id'))
    account = db.relationship(Account, lazy='joined')

class Post(db.Model, TimestampMixin, RemoteIDMixin):
    __tablename__ = 'posts'

    id = db.Column(db.String, primary_key=True)
    body = db.Column(db.String)

    author_id = db.Column(db.String, db.ForeignKey('accounts.id'))
    author = db.relationship(Account)

class TwitterArchive(db.Model, TimestampMixin):
    __tablename__ = 'twitter_archives'

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.String, db.ForeignKey('accounts.id'), nullable=False)
    account = db.relationship(Account, backref=db.backref('twitter_archives', order_by=lambda: db.desc(TwitterArchive.id)))
    body = db.deferred(db.Column(db.LargeBinary, nullable=False))
    chunks = db.Column(db.Integer)
    chunks_successful = db.Column(db.Integer, server_default='0')
    chunks_failed = db.Column(db.Integer, server_default='0')
