from celery import Celery, Task
from app import app as flaskapp
from app import db
from model import Session, Account, TwitterArchive, Post, OAuthToken,\
                  MastodonInstance
import libforget.twitter
import libforget.mastodon
from datetime import timedelta, datetime, timezone
from zipfile import ZipFile
from io import BytesIO, TextIOWrapper
import json
from kombu import Queue
import version
from libforget.exceptions import PermanentError, TemporaryError
import redis
from functools import wraps
import pickle

app = Celery(
    'tasks',
    broker=flaskapp.config['CELERY_BROKER'],
    task_serializer='pickle',
    task_soft_time_limit=600,
    task_time_limit=1200,
)
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
    sentry = Client(
        flaskapp.config['SENTRY_DSN'],
        release=version.get_versions()['version'])
    register_logger_signal(sentry)
    register_signal(sentry)


class DBTask(Task):
    def __call__(self, *args, **kwargs):
        try:
            super().__call__(*args, **kwargs)
        finally:
            db.session.close()


app.Task = DBTask

r = None


def unique(fun):
    global r
    if not r:
        r = redis.StrictRedis.from_url(flaskapp.config['REDIS_URI'])

    @wraps(fun)
    def wrapper(*args, **kwargs):
        key = 'celery_unique_lock:{}'.format(
            pickle.dumps((fun.__name__, args, kwargs)))
        has_lock = False
        result = None
        try:
            if r.set(key, 1, nx=True, ex=60 * 5):
                has_lock = True
                result = fun(*args, **kwargs)
        finally:
            if has_lock:
                r.delete(key)
        return result

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


@app.task(autoretry_for=(TemporaryError, ))
@unique
def fetch_acc(id_):
    account = Account.query.get(id_)
    print("Fetching {}".format(account))
    try:
        if not account.fetch_history_complete:
            oldest = (db.session.query(Post)
                      .with_parent(account, 'posts')
                      .order_by(db.asc(Post.created_at))
                      .first())
            # ^ None if this is our first fetch ever, otherwise the oldest post
            if oldest:
                max_id = oldest.remote_id
            else:
                max_id = None
            since_id = None
        elif account.fetch_current_batch_end:
            oldest = (db.session.query(Post)
                      .with_parent(account, 'posts')
                      .filter(Post.created_at > account.fetch_current_batch_end.created_at)
                      .order_by(db.asc(Post.created_at))
                      .first())
            # ^ None if this is our first fetch of this batch, otherwise oldest of this batch
            if oldest:
                max_id = oldest.remote_id
            else:
                max_id = None
            since_id = account.fetch_current_batch_end.remote_id
        else:
            # we shouldn't get here unless the user had no posts on the service last time we fetched
            max_id = None
            latest = (db.session.query(Post)
                      .with_parent(account, 'posts')
                      .order_by(db.desc(Post.created_at))
                      .limit(1)
                      .scalar())
            # ^ should be None considering the user has no posts
            #   will be the latest post in the off chance that something goes weird
            if latest:
                since_id = latest.remote_id
            else:
                since_id = None


        fetch_posts = noop
        if (account.service == 'twitter'):
            fetch_posts = libforget.twitter.fetch_posts
        elif (account.service == 'mastodon'):
            fetch_posts = libforget.mastodon.fetch_posts
        posts = fetch_posts(account, max_id, since_id)

        if posts is None:
            # ???
            raise TemporaryError("Fetching posts went horribly wrong")

        if len(posts) == 0:
            # we either finished the historic fetch
            # or we finished the current batch
            account.fetch_history_complete = True
            batch_end = (Post.query.with_parent(account, 'posts').order_by(
                db.desc(Post.created_at)).first())
            if batch_end:
                account.fetch_current_batch_end_id = batch_end.id
            else:
                account.fetch_current_batch_end_id = None
            db.session.commit()

        else:
            for post in posts:
                db.session.merge(post)
            db.session.commit()

            if not account.fetch_history_complete:
                # reschedule immediately if we're still doing the historic fetch
                fetch_acc.apply_async((id_,))


    except TemporaryError:
        db.session.rollback()
        account.backoff()
    except PermanentError:
        db.session.rollback()
        make_dormant(account)
        if sentry:
            sentry.captureException()
    finally:
        db.session.rollback()
        account.touch_fetch()
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
            post = libforget.twitter.post_from_api_tweet_object(tweet)
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

    latest_n_posts = (Post.query.with_parent(account, 'posts').order_by(
        db.desc(Post.created_at)).limit(account.policy_keep_latest)
                      .cte(name='latest'))
    posts = (
        Post.query.with_parent(account, 'posts')
        .filter(Post.created_at + account.policy_keep_younger <= db.func.now())
        .filter(~Post.id.in_(db.select((latest_n_posts.c.id, )))).order_by(
            db.func.random()).limit(100).all())

    to_delete = None

    def is_eligible(post):
        return (post.is_reblog or (
            (account.policy_keep_favourites == 'none' or
             (account.policy_keep_favourites == 'keeponly'
              and not post.favourite) or
             (account.policy_keep_favourites == 'deleteonly'
              and post.favourite)) and
            (account.policy_keep_media == 'none' or
             (account.policy_keep_media == 'keeponly' and not post.has_media)
             or (account.policy_keep_media == 'deleteonly' and post.has_media))
            and (not account.policy_keep_direct or not post.direct)))

    try:
        action = noop
        if account.service == 'twitter':
            action = libforget.twitter.delete
            posts = refresh_posts(posts)
            to_delete = next(filter(is_eligible, posts), None)
        elif account.service == 'mastodon':
            action = libforget.mastodon.delete
            for post in posts:
                refreshed = refresh_posts((post, ))
                if refreshed and is_eligible(refreshed[0]):
                    to_delete = refreshed[0]
                    break

        if to_delete:
            print("Deleting {}".format(to_delete))
            account.touch_delete()
            action(to_delete)
            account.reset_backoff()
        else:
            account.next_delete = db.func.now() + timedelta(minutes=3)

    except TemporaryError:
        db.session.rollback()
        account.backoff()

    finally:
        db.session.commit()


def refresh_posts(posts):
    posts = list(posts)
    if len(posts) == 0:
        return []

    if posts[0].service == 'twitter':
        return libforget.twitter.refresh_posts(posts)
    elif posts[0].service == 'mastodon':
        return libforget.mastodon.refresh_posts(posts)


@app.task()
@unique
def refresh_account(account_id):
    account = Account.query.get(account_id)

    print("Refreshing account {}".format(account))

    try:
        limit = 100
        if account.service == 'mastodon':
            limit = 3
        posts = (Post.query.with_parent(account, 'posts').order_by(
            db.asc(Post.updated_at)).limit(limit).all())

        posts = refresh_posts(posts)
        account.touch_refresh()
        account.reset_backoff()
    except TemporaryError:
        db.session.rollback()
        account.backoff()
    except PermanentError:
        db.session.rollback()
        make_dormant(account)
        if sentry:
            sentry.captureException()
    except Exception as e:
        db.session.rollback()
        account.backoff()
        db.session.commit()
        raise e
    finally:
        db.session.commit()


@app.task
@unique
def periodic_cleanup():
    # delete sessions after 48 hours
    (Session.query.filter(
        Session.updated_at < (db.func.now() - timedelta(hours=48)))
     .delete(synchronize_session=False))

    # delete twitter archives after 3 days
    (TwitterArchive.query.filter(
        TwitterArchive.updated_at < (db.func.now() - timedelta(days=3)))
     .delete(synchronize_session=False))

    # delete anonymous oauth tokens after 1 day
    (OAuthToken.query.filter(
        OAuthToken.updated_at < (db.func.now() - timedelta(days=1))).filter(
            OAuthToken.account_id == None)  # noqa: E711
     .delete(synchronize_session=False))

    # disable and log out users with no tokens
    unreachable = (
        Account.query.outerjoin(Account.tokens)
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
    accs = (Account.query.join(Account.tokens).group_by(Account)
            .filter(Account.last_fetch < db.func.now() - min_staleness)
            .filter(Account.backoff_until < db.func.now())
            .filter(~Account.dormant).order_by(db.asc(
                Account.last_fetch)).limit(limit))
    for acc in accs:
        fetch_acc.s(acc.id).delay()
    db.session.commit()


@app.task
@unique
def queue_deletes():
    eligible_accounts = (
        Account.query.filter(Account.policy_enabled == True)  # noqa: E712
        .filter(Account.next_delete < db.func.now())
        .filter(Account.backoff_until < db.func.now())
        .filter(~Account.dormant))
    for account in eligible_accounts:
        delete_from_account.s(account.id).apply_async()


@app.task
@unique
def refresh_account_with_oldest_post():
    post = (Post.query.outerjoin(Post.author).join(Account.tokens)
            .filter(Account.backoff_until < db.func.now())
            .filter(~Account.dormant).group_by(Post).order_by(
                db.asc(Post.updated_at)).first())
    if post:
        refresh_account(post.author_id)


@app.task
@unique
def refresh_account_with_longest_time_since_refresh():
    acc = (Account.query.join(Account.tokens).group_by(Account)
           .filter(Account.backoff_until < db.func.now())
           .filter(~Account.dormant).order_by(db.asc(
               Account.last_refresh)).first())
    if acc:
        refresh_account(acc.id)


@app.task
def update_mastodon_instances_popularity():
    # bump score for each active account
    for acct in (Account.query.options(db.joinedload(Account.sessions))
                 .filter(~Account.dormant).filter(
                     Account.id.like('mastodon:%'))):
        instance = MastodonInstance.query.get(acct.mastodon_instance)
        if not instance:
            instance = MastodonInstance(
                instance=acct.mastodon_instance, popularity=10)
            db.session.add(instance)
        amount = 0.01
        if acct.policy_enabled:
            amount = 0.5
        for _ in acct.sessions:
            amount += 0.1
        instance.bump(amount / max(1, instance.popularity))

    # normalise scores so the top is 20
    top_pop = (db.session.query(db.func.max(MastodonInstance.popularity))
               .scalar())
    MastodonInstance.query.update({
        MastodonInstance.popularity:
        MastodonInstance.popularity * 20 / top_pop
    })
    db.session.commit()


app.add_periodic_task(40, queue_fetch_for_most_stale_accounts)
app.add_periodic_task(9, queue_deletes)
app.add_periodic_task(25, refresh_account_with_oldest_post)
app.add_periodic_task(50, refresh_account_with_longest_time_since_refresh)
app.add_periodic_task(300, periodic_cleanup)
app.add_periodic_task(300, update_mastodon_instances_popularity)

if __name__ == '__main__':
    app.worker_main()
