from twitter import Twitter, OAuth
from werkzeug.urls import url_decode
from model import OAuthToken, Account, Post
from app import db
from math import inf
from datetime import datetime

def get_login_url(callback='oob', consumer_key=None, consumer_secret=None):
    twitter = Twitter(
            auth=OAuth('', '', consumer_key, consumer_secret),
            format='', api_version=None)
    resp = url_decode(twitter.oauth.request_token(oauth_callback=callback))
    oauth_token = resp['oauth_token']
    oauth_token_secret = resp['oauth_token_secret']

    token = OAuthToken(token = oauth_token, token_secret = oauth_token_secret)
    db.session.merge(token)
    db.session.commit()

    return "https://api.twitter.com/oauth/authenticate?oauth_token=%s" % (oauth_token,)

def receive_verifier(oauth_token, oauth_verifier, consumer_key=None, consumer_secret=None):
    temp_token = OAuthToken.query.get(oauth_token)
    if not temp_token:
        raise Exception("OAuth token has expired")
    twitter = Twitter(
            auth=OAuth(temp_token.token, temp_token.token_secret, consumer_key, consumer_secret),
            format='', api_version=None)
    resp = url_decode(twitter.oauth.access_token(oauth_verifier = oauth_verifier))
    db.session.delete(temp_token)
    new_token = OAuthToken(token = resp['oauth_token'], token_secret = resp['oauth_token_secret'])
    new_token = db.session.merge(new_token)
    new_twitter = Twitter(
            auth=OAuth(new_token.token, new_token.token_secret, consumer_key, consumer_secret))
    remote_acct = new_twitter.account.verify_credentials()
    acct = Account(remote_id = remote_acct['id_str'])
    acct = db.session.merge(acct)

    acct.remote_display_name = remote_acct['name']
    acct.remote_screen_name = remote_acct['screen_name']
    acct.remote_avatar_url = remote_acct['profile_image_url_https']
    new_token.account = acct
    db.session.commit()

    return new_token

def get_twitter_for_acc(account, consumer_key=None, consumer_secret=None):
    token = account.tokens[0]
    t = Twitter(
            auth=OAuth(token.token, token.token_secret, consumer_key, consumer_secret))
    return t

import locale
locale.setlocale(locale.LC_TIME, 'C') # jeez i hate that i have to do this

def fetch_acc(account, cursor, consumer_key=None, consumer_secret=None):
    t = get_twitter_for_acc(account, consumer_key=consumer_key, consumer_secret=consumer_secret)

    user = t.account.verify_credentials()

    account.remote_display_name = user['name']
    account.remote_screen_name = user['screen_name']
    account.remote_avatar_url = user['profile_image_url_https']

    kwargs = { 'user_id': account.remote_id, 'count': 200, 'trim_user': True }
    kwargs.update(cursor or {})

    if 'max_id' not in kwargs:
        most_recent_post = Post.query.order_by(db.desc(Post.created_at)).filter(Post.author_id == account.remote_id).first()
        if most_recent_post:
            kwargs['since_id'] = most_recent_post.remote_id

    print(kwargs)

    tweets = t.statuses.user_timeline(**kwargs)

    print("processing {} tweets for {acc}".format(len(tweets), acc=account))

    if len(tweets) > 0:

        kwargs['max_id'] = +inf

        for tweet in tweets:
            print("TWEET ", tweet['text'])
            post = Post(remote_id=tweet['id_str'])
            post = db.session.merge(post)
            post.created_at = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S %z %Y')
            post.body = tweet['text']
            post.author = account
            kwargs['max_id'] = min(tweet['id'] - 1, kwargs['max_id'])

    else:
        kwargs = None

    db.session.commit()

    return kwargs

