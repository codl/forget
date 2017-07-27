from celery import Celery

from app import app as flaskapp
from app import db
from model import Session
from datetime import timedelta

app = Celery('tasks', broker=flaskapp.config['CELERY_BROKER'], task_serializer='pickle')

@app.task
def remove_old_sessions():
    Session.query.filter(Session.updated_at < (db.func.now() - timedelta(minutes=30))).\
            delete(synchronize_session=False)
    db.session.commit()

@app.task
def fetch_posts(remote_id):
    pass

app.add_periodic_task(60*60, remove_old_sessions)




if __name__ == '__main__':
    app.worker_main()
