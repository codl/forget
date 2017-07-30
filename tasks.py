from celery import Celery

from app import app as flaskapp
from app import db
from model import Session, Account, TwitterArchive
import lib.twitter
from twitter import TwitterError
from urllib.error import URLError
from datetime import timedelta, datetime
from zipfile import ZipFile
from io import BytesIO, TextIOWrapper
import csv

app = Celery('tasks', broker=flaskapp.config['CELERY_BROKER'], task_serializer='pickle')

@app.task
def remove_old_sessions():
    Session.query.filter(Session.updated_at < (db.func.now() - timedelta(hours=48))).\
            delete(synchronize_session=False)
    db.session.commit()

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
        acc.last_fetch = db.func.now()
    db.session.commit()

app.add_periodic_task(10*60, remove_old_sessions)
app.add_periodic_task(60, queue_fetch_for_most_stale_accounts)

@app.task
def import_twitter_archive(id):
    ta = TwitterArchive.query.get(id)

    with ZipFile(BytesIO(ta.body), 'r') as zipfile:
        tweetscsv = TextIOWrapper(zipfile.open('tweets.csv', 'r'))

    for tweet in csv.DictReader(tweetscsv):
        tweet = lib.twitter.csv_tweet_to_json_tweet(tweet, ta.account)
        post = lib.twitter.tweet_to_post(tweet)
        db.session.merge(post)
        db.session.commit()

    db.session.delete(ta)
    db.session.commit()



if __name__ == '__main__':
    app.worker_main()
