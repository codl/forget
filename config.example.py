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
# SQLALCHEMY_DATABASE_URI='postgresql+psycopg2:///forget'

"""
TWITTER CREDENTIALS

get these at apps.twitter.com
blah
"""
# TWITTER_CONSUMER_KEY='vdsvdsvds'
# TWITTER_CONSUMER_SECRET='hjklhjklhjkl'

"""
this will be necessary so we can tell twitter where to redirect
"""
# SERVER_NAME="localhost:5000"

# CELERY_BROKER='redis://'

# HTTPS=True

# SENTRY_DSN='https://foo:bar@sentry.io/69420'

'''
you can set this to memory:// if you only have one web process
or if you don't care about people exhausting your twitter api
key and your celery workers by making hundreds of login
requests and uploading hundreds of bogus tweet archives

docs here <https://flask-limiter.readthedocs.io/en/stable/#configuration>
'''
# RATELIMIT_STORAGE_URL='redis://'

# REDIS=dict(
#        db=0
#
#        host='localhost'
#        port=6379
#        # or...
#        unix_socket_path='/var/run/redis/redis.sock'
#        # see `pydoc redis.StrictRedis.__init__` for full list of arguments
#     )

"""
you can also use any config variable that flask expects here, such as
"""
# SESSION_COOKIE_SECURE=True
# DEBUG=True
