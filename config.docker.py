"""
this is an example config file for Forget

copy this file to config.py before editing

lines starting with # demonstrate default or example values
the # should be removed before editing
"""

"""
DATABASE URI

determines where to connect to the database
see <http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls> for syntax
only postgresql with psycopg2 driver is officially supported
"""
SQLALCHEMY_DATABASE_URI='postgresql+psycopg2://postgres:postgres@db/forget'

"""
REDIS URI

see <https://redis-py.readthedocs.io/en/latest/#redis.ConnectionPool.from_url>
for syntax reference
"""
REDIS_URI='redis://redis'

"""
SERVER ADDRESS

This is the address at which forget will be reached.
External services will redirect to this address when logging in.
"""
# SERVER_NAME="0.0.0.0:5000"
# HTTPS=True

"""
TWITTER CREDENTIALS

Apply for api keys on the developer portal <https://developer.twitter.com/en/apps>
When prompted for it, your callback URL is {SERVER_NAME}/login/twitter/callback
"""
# TWITTER_CONSUMER_KEY='yN3DUNVO0Me63IAQdhTfCA'
# TWITTER_CONSUMER_SECRET='c768oTKdzAjIYCmpSNIdZbGaG0t6rOhSFQP0S5uC79g'

"""
SENTRY

If you want to send exceptions to sentry, enter your sentry DSN here
"""
# SENTRY_DSN=''

"""
HIDDEN INSTANCES

The front page shows one-click login buttons for the mastodon and
misskey instances that see the most heavy use. Instances configured in this
list will be prevented from appearing in these buttons.

They will still appear if a user has previously logged into them and their
browser remembers it. A user will still be able to log into them by manually
typing the address into the log in form.

This is a space-delimited list. Example syntax:
HIDDEN_INSTANCES='social.example.com pleroma.example.net mk.example.org'
"""
# HIDDEN_INSTANCES=''

"""
ADVANCED FLASK CONFIG

you can also use any config variable that flask expects here
A list of these config variables is available here:
<http://flask.pocoo.org/docs/1.0/config/#builtin-configuration-values>
"""
# SESSION_COOKIE_SECURE=True
# DEBUG=True
