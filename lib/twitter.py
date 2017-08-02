from twitter import Twitter, OAuth
from werkzeug.urls import url_decode
from model import OAuthToken, Account, Post
from app import db, app
from math import inf
from datetime import datetime
import locale

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
    acct = Account(twitter_id = remote_acct['id_str'])
    acct = db.session.merge(acct)

    acct.remote_display_name = remote_acct['name']
    acct.remote_screen_name = remote_acct['screen_name']
    acct.remote_avatar_url = remote_acct['profile_image_url_https']
    new_token.account = acct
    db.session.commit()

    return new_token

def get_twitter_for_acc(account):

    consumer_key = app.config['TWITTER_CONSUMER_KEY']
    consumer_secret = app.config['TWITTER_CONSUMER_SECRET']

    token = OAuthToken.query.with_parent(account).order_by(db.desc(OAuthToken.created_at)).first()
    t = Twitter(
            auth=OAuth(token.token, token.token_secret, consumer_key, consumer_secret))
    return t

locale.setlocale(locale.LC_TIME, 'C')

def tweet_to_post(tweet, post=None):
    if not post:
        post = Post()
    post.twitter_id = tweet['id_str']
    try:
        post.created_at = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S %z %Y')
    except ValueError:
        post.created_at = datetime.strptime(tweet['created_at'], '%Y-%m-%d %H:%M:%S %z')
        #whyyy
    if 'full_text' in tweet:
        post.body = tweet['full_text']
    else:
        post.body = tweet['text']
    post.author_id = 'twitter:{}'.format(tweet['user']['id_str'])
    if 'favorited' in tweet:
        post.favourite = tweet['favorited']
    return post

def fetch_acc(account, cursor, consumer_key=None, consumer_secret=None):
    t = get_twitter_for_acc(account)

    user = t.account.verify_credentials()

    account.remote_display_name = user['name']
    account.remote_screen_name = user['screen_name']
    account.remote_avatar_url = user['profile_image_url_https']

    kwargs = { 'user_id': account.twitter_id, 'count': 200, 'trim_user': True, 'tweet_mode': 'extended' }
    kwargs.update(cursor or {})

    if 'max_id' not in kwargs:
        most_recent_post = Post.query.order_by(db.desc(Post.created_at)).filter(Post.author_id == account.id).first()
        if most_recent_post:
            kwargs['since_id'] = most_recent_post.twitter_id

    tweets = t.statuses.user_timeline(**kwargs)

    print("processing {} tweets for {acc}".format(len(tweets), acc=account))

    if len(tweets) > 0:

        kwargs['max_id'] = +inf

        for tweet in tweets:
            db.session.merge(tweet_to_post(tweet))
            kwargs['max_id'] = min(tweet['id'] - 1, kwargs['max_id'])

    else:
        kwargs = None

    db.session.commit()

    return kwargs


def refresh_posts(posts):
    if not posts:
        return posts

    t = get_twitter_for_acc(posts[0].author)
    tweets = t.statuses.lookup(_id=",".join((post.twitter_id for post in posts)),
            trim_user = True, tweet_mode = 'extended')
    refreshed_posts = list()
    for post in posts:
        tweet = next((tweet for tweet in tweets if tweet['id_str'] == post.twitter_id), None)
        if not tweet:
            session.delete(post)
        else:
            post = db.session.merge(tweet_to_post(tweet))
            refreshed_posts.append(post)

    return refreshed_posts


def delete(post):
    t = get_twitter_for_acc(post.author)
    t.statuses.destroy(id=post.twitter_id)
    db.session.delete(post)
