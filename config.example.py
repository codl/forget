"""
this is an example config file for Forget

copy this file to config.py before editing
"""

"""
DATABASE URI

determines where to connect to the database
see <http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls> for syntax
only postgresql with psycopg2 driver is officially supported
"""
# SQLALCHEMY_DATABASE_URI='postgresql+psycopg2:///forget'

"""
REDIS URI

see <https://redis-py.readthedocs.io/en/latest/#redis.ConnectionPool.from_url>
for syntax reference
"""
# REDIS_URI='redis://'

"""
TWITTER CREDENTIALS

Apply for api keys on the developer portal <https://developer.twitter.com/en/apps>
Twitter locked me out of it so I can't guide you more than that. Sorry.
"""
# TWITTER_CONSUMER_KEY='yN3DUNVO0Me63IAQdhTfCA'
# TWITTER_CONSUMER_SECRET='c768oTKdzAjIYCmpSNIdZbGaG0t6rOhSFQP0S5uC79g'

"""
SERVER ADDRESS

This is the address at which forget will be reached.
External services will redirect to this address when logging in.
"""
# SERVER_NAME="localhost:5000"
# HTTPS=True


"""
SENTRY

If you want to send exceptions to sentry, enter your sentry DSN here
"""
# SENTRY_DSN=

"""
ADVANCED FLASK CONFIG

you can also use any config variable that flask expects here
A list of these config variables is available here:
<http://flask.pocoo.org/docs/1.0/config/#builtin-configuration-values>
"""
# SESSION_COOKIE_SECURE=True
# DEBUG=True
