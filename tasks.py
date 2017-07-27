from celery import Celery

from app import app as flaskapp
from app import db
from model import Session, Account
from lib.twitter import fetch_posts_for_acc
from datetime import timedelta, datetime

app = Celery('tasks', broker=flaskapp.config['CELERY_BROKER'], task_serializer='pickle')

@app.task
def remove_old_sessions():
    Session.query.filter(Session.updated_at < (db.func.now() - timedelta(hours=12))).\
            delete(synchronize_session=False)
    db.session.commit()

@app.task
def fetch_posts(remote_id):
    fetch_posts_for_acc(Account.query.get(remote_id), **flaskapp.config.get_namespace("TWITTER_"))

@app.task
def queue_fetch_for_most_stale_account(min_staleness=timedelta(minutes=5)):
    acc = Account.query\
            .filter(Account.last_post_fetch < db.func.now() - min_staleness)\
            .order_by(db.asc(Account.last_post_fetch))\
            .first()
    if acc:
        fetch_posts.s(acc.remote_id).delay()
        acc.last_post_fetch = datetime.now()
        db.session.commit()


app.add_periodic_task(10*60, remove_old_sessions)
app.add_periodic_task(20, queue_fetch_for_most_stale_account)




if __name__ == '__main__':
    app.worker_main()
