"""
this is an example config file for Forget

copy this file to config.py before editing
"""

"""
DATABASE URI

determines where to connect to the database
see http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls for syntax
only postgresql with psycopg2 driver is officially supported
"""
SQLALCHEMY_DATABASE_URI='postgresql+psycopg2:///forget'

"""
TWITTER CREDENTIALS

get these at apps.twitter.com
blah
"""
TWITTER_CONSUMER_KEY='vdsvdsvds'
TWITTER_CONSUMER_SECRET='hjklhjklhjkl'

"""
this will be necessary so we can tell twitter where to redirect
"""
SERVER_NAME="localhost:5000"

CELERY_BROKER='amqp://'

"""
you can also use any config variable that flask expects here, such as
"""
# SESSION_COOKIE_SECURE=True
# DEBUG=True
