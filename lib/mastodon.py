import mastodon
from mastodon import Mastodon
from model import MastodonApp, Account, OAuthToken
from requests import head
from app import db

def get_or_create_app(instance_url, callback, website):
    instance_url = instance_url
    app = MastodonApp.query.get(instance_url)
    try:
        head('https://{}'.format(instance_url)).raise_for_status()
        proto = 'https'
    except Exception:
        head('http://{}'.format(instance_url)).raise_for_status()
        proto = 'http'

    if not app:
        client_id, client_secret = Mastodon.create_app('forget',
                scopes=('read', 'write'),
                api_base_url='{}://{}'.format(proto, instance_url),
                redirect_uris=callback,
                website=website,
            )
        app = MastodonApp()
        app.instance = instance_url
        app.client_id = client_id
        app.client_secret = client_secret
        app.protocol = proto
    return app

def anonymous_api(app):
    return Mastodon(app.client_id,
            client_secret = app.client_secret,
            api_base_url='{}://{}'.format(app.protocol, app.instance),
            )

def login_url(app, callback):
    return anonymous_api(app).auth_request_url(
            redirect_uris=callback,
            scopes=('read', 'write',)
            )

def receive_code(code, app, callback):
    api = anonymous_api(app)
    access_token = api.log_in(
            code=code,
            scopes=('read', 'write'),
            redirect_uri=callback,
            )

    remote_acc = api.account_verify_credentials()
    acc = Account(
            #id = 'mastodon:{}:{}'.format(app.instance, remote_acc['username']),
            mastodon_instance = app.instance,
            mastodon_id = remote_acc['username'],
            screen_name = remote_acc['username'],
            display_name = remote_acc['display_name'],
            avatar_url = remote_acc['avatar'],
            reported_post_count = remote_acc['statuses_count'],
        )
    token = OAuthToken(account = acc, token = access_token)
    db.session.merge(acc, token)

    return acc


def get_api_for_acc(account):
    app = MastodonApp.query.get(account.mastodon_instance)
    for token in account.tokens:
        api = Mastodon(app.client_id,
                client_secret = app.client_secret,
                api_base_url = '{}://{}'.format(app.protocol, app.instance),
                access_token = token.token,
            )
        try:
            # api.verify_credentials()
            # doesnt error even if the token is revoked lol sooooo
            tl = api.timeline()
            #if 'error' in tl and tl['error'] == 'The access token was revoked':
            #ARRRRRGH
        except mastodon.MastodonAPIError as e:
            raise e
        return api


def fetch_acc(account, cursor=None):
    pass

