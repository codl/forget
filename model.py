from datetime import timedelta, datetime, timezone

from app import db
import secrets
from lib.interval import decompose_interval


class TimestampMixin(object):
    created_at = db.Column(
            db.DateTime(timezone=True), server_default=db.func.now(),
            nullable=False)
    updated_at = db.Column(
            db.DateTime(timezone=True), server_default=db.func.now(),
            onupdate=db.func.now(), nullable=False)

    def touch(self):
        self.updated_at = db.func.now()


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
            raise Exception(
                    "tried to get twitter id for a {} {}"
                    .format(self.service, type(self)))
        return self.id.split(":")[1]

    @twitter_id.setter
    def twitter_id(self, id_):
        self.id = "twitter:{}".format(id_)

    @property
    def mastodon_instance(self):
        if not self.id:
            return None
        if self.service != "mastodon":
            raise Exception(
                    "tried to get mastodon instance for a {} {}"
                    .format(self.service, type(self)))
        return self.id.split(":", 1)[1].split('@')[1]

    @mastodon_instance.setter
    def mastodon_instance(self, instance):
        self.id = "mastodon:{}@{}".format(self.mastodon_id, instance)

    @property
    def mastodon_id(self):
        if not self.id:
            return None
        if self.service != "mastodon":
            raise Exception(
                    "tried to get mastodon id for a {} {}"
                    .format(self.service, type(self)))
        return self.id.split(":", 1)[1].split('@')[0]

    @mastodon_id.setter
    def mastodon_id(self, id_):
        self.id = "mastodon:{}@{}".format(id_, self.mastodon_instance)


@decompose_interval('policy_delete_every')
@decompose_interval('policy_keep_younger')
class Account(TimestampMixin, RemoteIDMixin):
    __tablename__ = 'accounts'
    id = db.Column(db.String, primary_key=True)

    policy_enabled = db.Column(db.Boolean, server_default='FALSE',
                               nullable=False)
    policy_keep_latest = db.Column(db.Integer, server_default='100',
                                   nullable=False)
    policy_keep_favourites = db.Column(db.Boolean, server_default='TRUE',
                                       nullable=False)
    policy_keep_media = db.Column(db.Boolean, server_default='FALSE',
                                  nullable=False)
    policy_delete_every = db.Column(db.Interval, server_default='30 minutes',
                                    nullable=False)
    policy_keep_younger = db.Column(db.Interval, server_default='365 days',
                                    nullable=False)
    policy_keep_direct = db.Column(db.Boolean, server_default='TRUE',
                                   nullable=False)

    display_name = db.Column(db.String)
    screen_name = db.Column(db.String)
    avatar_url = db.Column(db.String)
    reported_post_count = db.Column(db.Integer)

    last_fetch = db.Column(db.DateTime(timezone=True),
                           server_default='epoch', index=True)
    last_refresh = db.Column(db.DateTime(timezone=True),
                             server_default='epoch', index=True)
    last_delete = db.Column(db.DateTime(timezone=True), index=True)
    next_delete = db.Column(db.DateTime(timezone=True), index=True)

    def touch_fetch(self):
        self.last_fetch = db.func.now()

    def touch_delete(self):
        self.last_delete = db.func.now()
        # if it's been more than 1 delete cycle ago that we've deleted a post,
        # reset next_delete to be 1 cycle away
        if (datetime.now(timezone.utc) - self.next_delete
           > self.policy_delete_every):
            self.next_delete = db.func.now() + self.policy_delete_every
        else:
            self.next_delete += self.policy_delete_every

    def touch_refresh(self):
        self.last_refresh = db.func.now()

    @db.validates('policy_keep_younger', 'policy_delete_every')
    def validate_intervals(self, key, value):
        if not (value == timedelta(0) or value >= timedelta(minutes=1)):
            value = timedelta(minutes=1)
        if key == 'policy_delete_every' and \
           self.next_delete and\
           datetime.now(timezone.utc) + value < self.next_delete:
            # make sure that next delete is not in the far future
            self.next_delete = datetime.now(timezone.utc) + value
        return value

    # pylint: disable=R0201
    @db.validates('policy_keep_latest')
    def validate_empty_string_is_zero(self, key, value):
        if isinstance(value, str) and value.strip() == '':
            return 0
        return value

    @db.validates('policy_enabled')
    def reset_next_delete(self, key, enable):
        if not self.policy_enabled and enable:
            self.next_delete = (
                datetime.now(timezone.utc) + self.policy_delete_every)
        return enable

    # backref: tokens
    # backref: twitter_archives
    # backref: posts
    # backref: sessions

    def __str__(self):
        return f"<Account({self.id}, {self.screen_name}, {self.display_name})>"

    def post_count(self):
        return Post.query.with_parent(self).count()

    def estimate_eligible_for_delete(self):
        """
        this is an estimation because we do not know if favourite status has
        changed since last time a post was refreshed and it is unfeasible to
        refresh every single post every time we need to know how many posts are
        eligible to delete
        """
        latest_n_posts = (Post.query.with_parent(self)
                          .order_by(db.desc(Post.created_at))
                          .limit(self.policy_keep_latest))
        query = (Post.query.with_parent(self)
                 .filter(Post.created_at <=
                         db.func.now() - self.policy_keep_younger)
                 .except_(latest_n_posts))
        if(self.policy_keep_favourites):
            query = query.filter_by(favourite=False)
        if(self.policy_keep_media):
            query = query.filter_by(has_media=False)
        return query.count()

    def force_log_out(self):
        Session.query.with_parent(self).delete()
        db.session.commit()


class Account(Account, db.Model):
    pass


class OAuthToken(db.Model, TimestampMixin):
    __tablename__ = 'oauth_tokens'

    token = db.Column(db.String, primary_key=True)
    token_secret = db.Column(db.String, nullable=True)

    account_id = db.Column(db.String,
                           db.ForeignKey('accounts.id', ondelete='CASCADE',
                                         onupdate='CASCADE'),
                           nullable=True, index=True)
    account = db.relationship(
            Account,
            backref=db.backref('tokens',
                               order_by=lambda: db.desc(OAuthToken.created_at))
            )

    # note: account_id is nullable here because we don't know what account a
    # token is for until we call /account/verify_credentials with it


class Session(db.Model, TimestampMixin):
    __tablename__ = 'sessions'

    id = db.Column(db.String, primary_key=True,
                   default=secrets.token_urlsafe)

    account_id = db.Column(
            db.String,
            db.ForeignKey('accounts.id',
                          ondelete='CASCADE', onupdate='CASCADE'),
            nullable=False, index=True)
    account = db.relationship(Account, lazy='joined', backref='sessions')

    csrf_token = db.Column(db.String,
                           default=secrets.token_urlsafe,
                           nullable=False)


class Post(db.Model, TimestampMixin, RemoteIDMixin):
    __tablename__ = 'posts'

    id = db.Column(db.String, primary_key=True)

    author_id = db.Column(
            db.String,
            db.ForeignKey('accounts.id',
                          ondelete='CASCADE', onupdate='CASCADE'),
            nullable=False)
    author = db.relationship(
            Account,
            backref=db.backref('posts',
                               order_by=lambda: db.desc(Post.created_at)))

    favourite = db.Column(db.Boolean, server_default='FALSE', nullable=False)
    has_media = db.Column(db.Boolean, server_default='FALSE', nullable=False)
    direct = db.Column(db.Boolean, server_default='FALSE', nullable=False)

    def __str__(self):
        return '<Post ({}, Author: {})>'.format(self.id, self.author_id)


db.Index('ix_posts_author_id_created_at', Post.author_id, Post.created_at)


class TwitterArchive(db.Model, TimestampMixin):
    __tablename__ = 'twitter_archives'

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(
            db.String,
            db.ForeignKey('accounts.id',
                          onupdate='CASCADE', ondelete='CASCADE'),
            nullable=False)
    account = db.relationship(
            Account,
            backref=db.backref('twitter_archives',
                               order_by=lambda: db.desc(TwitterArchive.id)))
    body = db.deferred(db.Column(db.LargeBinary, nullable=False))
    chunks = db.Column(db.Integer)
    chunks_successful = db.Column(db.Integer,
                                  server_default='0', nullable=False)
    chunks_failed = db.Column(db.Integer, server_default='0', nullable=False)

    def status(self):
        if self.chunks is None or self.chunks_failed > 0:
            return 'failed'
        if self.chunks_successful == self.chunks:
            return 'successful'
        return 'pending'


ProtoEnum = db.Enum('http', 'https', name='enum_protocol')


class MastodonApp(db.Model, TimestampMixin):
    __tablename__ = 'mastodon_apps'

    instance = db.Column(db.String, primary_key=True)
    client_id = db.Column(db.String, nullable=False)
    client_secret = db.Column(db.String, nullable=False)
    protocol = db.Column(ProtoEnum, nullable=False)


class MastodonInstance(db.Model):
    """
    this is for the autocomplete in the mastodon login form

    it isn't coupled with anything else so that we can seed it with
    some popular instances ahead of time
    """
    __tablename__ = 'mastodon_instances'

    instance = db.Column(db.String, primary_key=True)
    popularity = db.Column(db.Float, server_default='10', nullable=False)

    def bump(self):
        self.popularity = (self.popularity or 10) + 1
