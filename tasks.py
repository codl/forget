from celery import Celery, Task
from app import app as flaskapp
from app import db
from model import Session, Account, TwitterArchive, Post, OAuthToken,\
                  MastodonInstance
import lib.twitter
import lib.mastodon
from datetime import timedelta, datetime, timezone
from zipfile import ZipFile
from io import BytesIO, TextIOWrapper
import json
from kombu import Queue
import random
import version
from lib.exceptions import PermanentError, TemporaryError
import redis
from functools import wraps
import pickle


app = Celery('tasks', broker=flaskapp.config['CELERY_BROKER'],
             task_serializer='pickle')
app.conf.task_queues = (
        Queue('default', routing_key='celery'),
        Queue('high_prio', routing_key='high'),
        Queue('higher_prio', routing_key='higher'),
)
app.conf.task_default_queue = 'default'
app.conf.task_default_exchange = 'celery'
app.conf.task_default_exchange_type = 'direct'

sentry = None

if 'SENTRY_DSN' in flaskapp.config:
    from raven import Client
    from raven.contrib.celery import register_signal, register_logger_signal
    sentry = Client(flaskapp.config['SENTRY_DSN'], release=version.version)
    register_logger_signal(sentry)
    register_signal(sentry)


class DBTask(Task):
    def __call__(self, *args, **kwargs):
        try:
            super().__call__(*args, **kwargs)
        finally:
            db.session.close()


app.Task = DBTask

def unique(fun):
    r = redis.StrictRedis.from_url(flaskapp.config['REDIS_URI'])

    @wraps(fun)
    def wrapper(*args, **kwargs):
        key = 'celery_unique_lock:{}'.format(pickle.dumps((fun.__name__, args, kwargs)))
        has_lock = False
        try:
            if r.set(key, 1, nx=True, ex=60*5):
                has_lock = True
                return fun(*args, **kwargs)
        finally:
            if has_lock:
                r.delete(key)

    return wrapper



def noop(*args, **kwargs):
    pass


def make_dormant(acc):
    acc.reason = '''
        Your account was temporarily disabled because your {service}
        account was suspended or otherwise inaccessible. By logging into
        it, you have reactivated your account, but be aware that some posts
        may be missing from Forget's database, and it may take some time to
        get back in sync.
    '''.format(service=acc.service)
    acc.dormant = True
    db.session.commit()


@app.task(autoretry_for=(TemporaryError,))
@unique
def fetch_acc(id_, cursor=None):
    acc = Account.query.get(id_)
    print(f'fetching {acc}')
    try:
        action = noop
        if(acc.service == 'twitter'):
            action = lib.twitter.fetch_acc
        elif(acc.service == 'mastodon'):
            action = lib.mastodon.fetch_acc
        cursor = action(acc, cursor)
        if cursor:
            fetch_acc.si(id_, cursor).apply_async()
    except PermanentError:
        db.session.rollback()
        make_dormant(acc)
        if sentry:
            sentry.captureException()
    finally:
        db.session.rollback()
        acc.touch_fetch()
        db.session.commit()


@app.task()
def import_twitter_archive_month(archive_id, month_path):
    ta = TwitterArchive.query.get(archive_id)

    try:

        with ZipFile(BytesIO(ta.body), 'r') as zipfile:
            with TextIOWrapper(zipfile.open(month_path, 'r')) as f:

                # seek past header
                f.readline()

                tweets = json.load(f)

        for tweet in tweets:
            post = lib.twitter.post_from_api_tweet_object(tweet)
            existing_post = db.session.query(Post).get(post.id)

            if post.author_id != ta.account_id or\
               existing_post and existing_post.author_id != ta.account_id:
                raise Exception("Shenanigans!")

            post = db.session.merge(post)

        ta.chunks_successful = TwitterArchive.chunks_successful + 1
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        ta.chunks_failed = TwitterArchive.chunks_failed + 1
        db.session.commit()
        raise e


@app.task()
@unique
def delete_from_account(account_id):
    account = Account.query.get(account_id)
    if account.next_delete > datetime.now(timezone.utc):
        return

    latest_n_posts = (Post.query.with_parent(account)
                      .order_by(db.desc(Post.created_at))
                      .limit(account.policy_keep_latest)
                      .cte(name='latest'))
    posts = (
        Post.query.with_parent(account)
        .filter(
            Post.created_at + account.policy_keep_younger <= db.func.now())
        .filter(~Post.id.in_(db.select((latest_n_posts.c.id,))))
        .order_by(db.func.random())
        .limit(100).with_for_update().all())

    to_delete = None

    action = noop
    if account.service == 'twitter':
        action = lib.twitter.delete
        posts = refresh_posts(posts)
        if posts:
            eligible = list((  # nosec
                post for post in posts if
                (not account.policy_keep_favourites or not post.favourite)
                and (not account.policy_keep_media or not post.has_media)
                ))
            if eligible:
                to_delete = random.choice(eligible)
    elif account.service == 'mastodon':
        action = lib.mastodon.delete
        for post in posts:
            refreshed = refresh_posts((post,))
            if refreshed and \
               (not account.policy_keep_favourites or not post.favourite) \
               and (not account.policy_keep_media or not post.has_media)\
               and (not account.policy_keep_direct or not post.direct):
                to_delete = refreshed[0]
                break

    if to_delete:
        print("deleting {}".format(to_delete))
        account.touch_delete()
        action(to_delete)
    else:
        account.next_delete = db.func.now() + timedelta(minutes=3)

    db.session.commit()


def refresh_posts(posts):
    posts = list(posts)
    if len(posts) == 0:
        return []

    if posts[0].service == 'twitter':
        return lib.twitter.refresh_posts(posts)
    elif posts[0].service == 'mastodon':
        return lib.mastodon.refresh_posts(posts)


@app.task()
@unique
def refresh_account(account_id):
    account = Account.query.get(account_id)

    try:
        limit = 100
        if account.service == 'mastodon':
            limit = 3
        posts = (Post.query.with_parent(account)
                 .order_by(db.asc(Post.updated_at)).limit(limit).all())

        posts = refresh_posts(posts)
        account.touch_refresh()
        db.session.commit()
    except PermanentError:
        db.session.rollback()
        make_dormant(account)
        if sentry:
            sentry.captureException()


@app.task
@unique
def periodic_cleanup():
    # delete sessions after 48 hours
    (Session.query
     .filter(Session.updated_at < (db.func.now() - timedelta(hours=48)))
     .delete(synchronize_session=False))

    # delete twitter archives after 3 days
    (TwitterArchive.query
     .filter(TwitterArchive.updated_at < (db.func.now() - timedelta(days=3)))
     .delete(synchronize_session=False))

    # delete anonymous oauth tokens after 1 day
    (OAuthToken.query
     .filter(OAuthToken.updated_at < (db.func.now() - timedelta(days=1)))
     .filter(OAuthToken.account_id == None)  # noqa: E711
     .delete(synchronize_session=False))

    # disable and log out users with no tokens
    unreachable = (
            Account.query
            .outerjoin(Account.tokens)
            .group_by(Account).having(db.func.count(OAuthToken.token) == 0)
            .filter(Account.policy_enabled == True))  # noqa: E712
    for account in unreachable:
        account.force_log_out()
        account.policy_enabled = False
        account.reason = """
        Your account was disabled because Forget no longer had access to
        your {service} account. Perhaps you had revoked it? By logging in,
        you have restored access and you can now re-enable Forget if you wish.
        """.format(service=account.service.capitalize())

    db.session.commit()


@app.task
@unique
def queue_fetch_for_most_stale_accounts(
        min_staleness=timedelta(minutes=2), limit=20):
    accs = (Account.query
            .join(Account.tokens).group_by(Account)
            .filter(Account.last_fetch < db.func.now() - min_staleness)
            .filter(~Account.dormant)
            .order_by(db.asc(Account.last_fetch))
            .limit(limit)
            )
    for acc in accs:
        fetch_acc.s(acc.id).delay()
    db.session.commit()


@app.task
@unique
def queue_deletes():
    eligible_accounts = (
            Account.query.filter(Account.policy_enabled == True)  # noqa: E712
            .filter(Account.next_delete < db.func.now())
            .filter(~Account.dormant))
    for account in eligible_accounts:
        delete_from_account.s(account.id).apply_async()


@app.task
@unique
def refresh_account_with_oldest_post():
    post = (Post.query.outerjoin(Post.author).join(Account.tokens)
            .filter(~Account.dormant)
            .group_by(Post).order_by(db.asc(Post.updated_at)).first())
    refresh_account(post.author_id)


@app.task
@unique
def refresh_account_with_longest_time_since_refresh():
    acc = (Account.query.join(Account.tokens).group_by(Account)
           .filter(~Account.dormant)
           .order_by(db.asc(Account.last_refresh)).first())
    refresh_account(acc.id)


@app.task
def update_mastodon_instances_popularity():
    # bump score for each active account
    for acct in (
            Account.query
            .filter(Account.policy_enabled)
            .filter(~Account.dormant)
            .filter(Account.id.like('mastodon:%'))):
        instance = MastodonInstance.query.get(acct.mastodon_instance)
        if not instance:
            instance = MastodonInstance(instance=acct.mastodon_instance,
                                        popularity=10)
            db.session.add(instance)
        instance.bump(0.001)

    # normalise scores so the median is 10
    median_pop = (
            db.session.query(
                db.func.percentile_cont(0.5)
                .within_group(MastodonInstance.popularity.desc())).scalar()
            )
    MastodonInstance.query.update({
        MastodonInstance.popularity:
            MastodonInstance.popularity * 10 / median_pop
    })
    db.session.commit()


app.add_periodic_task(120, periodic_cleanup)
app.add_periodic_task(40, queue_fetch_for_most_stale_accounts)
app.add_periodic_task(17, queue_deletes)
app.add_periodic_task(60, refresh_account_with_oldest_post)
app.add_periodic_task(180, refresh_account_with_longest_time_since_refresh)
app.add_periodic_task(61, update_mastodon_instances_popularity)

if __name__ == '__main__':
    app.worker_main()
