from celery import Celery

from app import app as flaskapp
from app import db
from model import Session, Account, TwitterArchive, Post
import lib.twitter
from twitter import TwitterError
from urllib.error import URLError
from datetime import timedelta, datetime
from zipfile import ZipFile
from io import BytesIO, TextIOWrapper
import json

app = Celery('tasks', broker=flaskapp.config['CELERY_BROKER'], task_serializer='pickle')

@app.task(autoretry_for=(TwitterError, URLError))
def fetch_acc(id, cursor=None):
    acc = Account.query.get(id)
    print(f'fetching {acc}')
    try:
        if(acc.service == 'twitter'):
            cursor = lib.twitter.fetch_acc(acc, cursor, **flaskapp.config.get_namespace("TWITTER_"))
            if cursor:
                fetch_acc.si(id, cursor).apply_async()
    finally:
        db.session.rollback()
        acc.last_fetch = db.func.now()
        db.session.commit()

@app.task
def queue_fetch_for_most_stale_accounts(min_staleness=timedelta(minutes=5), limit=20):
    accs = Account.query\
            .filter(Account.last_fetch < db.func.now() - min_staleness)\
            .order_by(db.asc(Account.last_fetch))\
            .limit(limit)
    for acc in accs:
        fetch_acc.s(acc.id).delay()
        acc.touch_fetch()
    db.session.commit()

@app.task
def import_twitter_archive(archive_id):
    ta = TwitterArchive.query.get(archive_id)

    with ZipFile(BytesIO(ta.body), 'r') as zipfile:
        files = [filename for filename in zipfile.namelist() if filename.startswith('data/js/tweets/') and filename.endswith('.js')]

    files.sort()

    ta.chunks = len(files)
    db.session.commit()

    for filename in files:
        import_twitter_archive_month.s(archive_id, filename).apply_async()


@app.task
def import_twitter_archive_month(archive_id, month_path):
    ta = TwitterArchive.query.get(archive_id)

    try:

        with ZipFile(BytesIO(ta.body), 'r') as zipfile:
            with TextIOWrapper(zipfile.open(month_path, 'r')) as f:

                # seek past header
                f.readline()

                tweets = json.load(f)

        for tweet in tweets:
            post = lib.twitter.tweet_to_post(tweet)
            existing_post = db.session.query(Post).get(post.id)

            if post.author_id != ta.account_id \
            or existing_post and existing_post.author_id != ta.account_id:
                raise Exception("Shenanigans!")

            post = db.session.merge(post)

        ta.chunks_successful = TwitterArchive.chunks_successful + 1
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        ta.chunks_failed = TwitterArchive.chunks_failed + 1
        db.session.commit()
        raise e


@app.task
def periodic_cleanup():
    Session.query.filter(Session.updated_at < (db.func.now() - timedelta(hours=48))).\
            delete(synchronize_session=False)
    TwitterArchive.query.filter(TwitterArchive.updated_at < (db.func.now() - timedelta(days=7))).\
            delete(synchronize_session=False)
    db.session.commit()

app.add_periodic_task(6*60*60, periodic_cleanup)
app.add_periodic_task(60, queue_fetch_for_most_stale_accounts)

if __name__ == '__main__':
    app.worker_main()
