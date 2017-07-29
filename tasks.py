from celery import Celery

from app import app as flaskapp
from app import db
from model import Session, Account
import lib.twitter
from twitter import TwitterError
from urllib.error import URLError
from datetime import timedelta, datetime

app = Celery('tasks', broker=flaskapp.config['CELERY_BROKER'], task_serializer='pickle')

@app.task
def remove_old_sessions():
    Session.query.filter(Session.updated_at < (db.func.now() - timedelta(hours=12))).\
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




if __name__ == '__main__':
    app.worker_main()
