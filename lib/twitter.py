from twitter import Twitter, OAuth
from werkzeug.urls import url_decode
from model import OAuthToken, Account
from app import db

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
    acct.remote_avatar_url = remote_acct['profile_image_url_https']
    new_token.account = acct
    db.session.commit()
    return new_token
