web: gunicorn -w 9 -t 3600 -b 127.0.0.1:42157 forget:app
worker: celery -A tasks worker --autoscale=64,8
beat: celery -A tasks beat
