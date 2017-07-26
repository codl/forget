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
SECRET KEY

this key is used to encrypt session cookies
you can generate a random key by running
openssl rand -base64 102 | tr -d "\n"; echo
or if you don't have openssl installed
cat /dev/random | head -c 102 | base64 | tr -d "\n"; echo
the latter might take a while if your system entropy is low, give it time
"""
SECRET_KEY='change me!'

"""
TWITTER CREDENTIALS

get these at apps.twitter.com
blah
"""
TWITTER_CONSUMER_KEY='vdsvdsvds'
TWITTER_CONSUMER_SECRET='hjklhjklhjkl'

"""
blablabl
"""
SERVER_NAME="localhost:5000"

"""
you can also use any config variable that flask expects here, such as
"""
# SESSION_COOKIE_SECURE=True
# DEBUG=True
