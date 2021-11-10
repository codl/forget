from app import db, sentry
from model import MisskeyApp, MisskeyInstance, Account, OAuthToken
from uuid import uuid4
from hashlib import sha256
from libforget.exceptions import TemporaryError, PermanentError
from libforget.session import make_session

def get_or_create_app(instance_url, callback, website, session):
    instance_url = instance_url
    app = MisskeyApp.query.get(instance_url)
    
    if not app:
        # check if the instance uses https while getting instance infos
        try:
            r = session.post('https://{}/api/meta'.format(instance_url))
            r.raise_for_status()
            proto = 'https'
        except Exception:
            r = session.post('http://{}/api/meta'.format(instance_url))
            r.raise_for_status()
            proto = 'http'
        
        # check if miauth is available or we have to use legacy auth
        miauth = 'miauth' in r.json()['features']
        
        app = MisskeyApp()
        app.instance = instance_url
        app.protocol = proto
        app.miauth = miauth
        
        if miauth:
            # apps do not have to be registered for miauth
            app.client_secret = None
        else:
            # register the app
            r = session.post('{}://{}/api/app/create'.format(app.protocol, app.instance), json = {
                'name': 'forget',
                'description': website,
                'permission': ['read:favorites', 'write:notes'],
                'callbackUrl': callback
            })
            r.raise_for_status()
            app.client_secret = r.json()['secret']

    return app

def login_url(app, callback, session):
    if app.miauth:
        return "{}://{}/miauth/{}?name=forget&callback={}&permission=read:favorites,write:notes".format(app.protocol, app.instance, uuid4(), callback)
    else:
        # will use the callback we gave the server in `get_or_create_app`
        r = session.post('{}://{}/api/auth/session/generate'.format(app.protocol, app.instance), json = {
            'appSecret': app.client_secret
        })
        r.raise_for_status()
        # we already get the retrieval token here, but we get it again later so
        # we do not have to store it
        return r.json()['url']

def receive_token(token, app):
    session = make_session()

    if app.miauth:
        r = session.get('{}://{}/api/miauth/{}/check'.format(app.protocol, app.instance, token))
        r.raise_for_status()
        
        token = r.json()['token']

        acc = account_from_user(r.json()['user'])
        acc = db.session.merge(acc)
        token = OAuthToken(token = r.json()['token'])
        token = db.session.merge(token)
        token.account = acc
    else:
        r = session.post('{}://{}/api/auth/session/userkey'.format(app.protocol, app.instance), json = {
            'appSecret': app.client_secret,
            'token': token
        })
        r.raise_for_status()
        
        token = sha256(r.json()['accessToken'].encode('utf-8') + app.client_secret.encode('utf-8')).hexdigest()
        
    acc = account_from_user(r.json()['user'])
    acc = db.session.merge(acc)
    token = OAuthToken(token = token)
    token = db.session.merge(token)
    token.account = acc

    return token

def check_auth(account, app, session):
    if app.miauth:
        r = session.get('{}://{}/api/miauth/{}/check'.format(app.protocol, app.instance, account.token))

        if r.status_code != 200:
            raise TemporaryError("{} {}".format(r.status_code, r.body))

        if not r.json()['ok']:
            if sentry:
                sentry.captureMessage(
                    'Misskey auth revoked or incorrect',
                    extra=locals())
            db.session.delete(token)
            db.session.commit()
            raise PermanentError("Misskey auth revoked")
    else: 
        # there is no such check for legacy auth, instead we check if we can
        # get the user info
        r = session.post('{}://{}/api/i'.format(app.protocol, app.instance), json = {'i': account.token})

        if r.status_code != 200:
            raise TemporaryError("{} {}".format(r.status_code, r.body))

        if r.json()['isSuspended']:
            # this is technically a temporary error, but like for twitter
            # its handled as permanent to not make useless API calls
            raise PermanentError("Misskey account suspended")

def account_from_user(user):
    return Account(
            misskey_instance=user['host'],
            misskey_id=user['id'],
            screen_name='{}@{}'.format(user['username'], user['host']),
            display_name=obj['name'],
            avatar_url=obj['avatarUrl'],
            reported_post_count=obj['notesCount'],
        )

def post_from_api_object(obj):
    return Post(
            misskey_instance=user['host'],
            misskey_id=user['id'],
            favourite=obj['myReaction'] is not None,
            has_media=('fileIds' in obj
                       and bool(obj['fileIds'])),
            created_at=obj['createdAt'],
            author_id=account_from_user(obj['user']).id,
            direct=obj['visibility'] == 'specified',
            is_reblog=obj['renoteId'] is not None,
        )

def fetch_posts(acc, max_id, since_id):
    app = MisskeyApp.query.get(acc.misskey_instance)
    session = make_session()
    check_auth(acc, app, session)
    if not verify_credentials(acc, app):
        raise PermanentError()
    try:
        kwargs = dict(limit=40)
        if max_id:
            kwargs['untilId'] = max_id
        if since_id:
            kwargs['sinceId'] = since_id

        notes = session.post('{}://{}/api/users/notes'.format(app.protocol, app.misskey_instance), json=kwargs)
        notes.raise_for_status()

        return [post_from_api_object(status) for note in notes.json()]

    except Exception as e:
        raise TemporaryError(e)


def refresh_posts(posts):
    acc = posts[0].author
    app = MisskeyApp.query.get(acc.misskey_instance)
    session = make_session()
    check_auth(acc, app, session)

    new_posts = list()
    with db.session.no_autoflush:
        for post in posts:
            print('Refreshing {}'.format(post))
            r = session.post('{}://{}/api/notes/show'.format(app.protocol, app.misskey_instance), json={
                'noteId': post.misskey_id
            })
            if r.status_code != 200:
                try:
                    if r.json()['error']['code'] == 'NO_SUCH_NOTE':
                        db.session.delete(post)
                        continue
                except Exception as e:
                    raise TemporaryError(e)
                raise TemporaryError('{} {}'.format(r.status_code, r.body))

            new_post = db.session.merge(post_from_api_object(r.json()))
            new_post.touch()
            new_posts.append(new_post)
    return new_posts

def delete(post):
    app = MisskeyApp.query.get(post.misskey_instance)
    session = make_session()
    if not app:
        # how? if this happens, it doesnt make sense to repeat it,
        # so use a permanent error
        raise PermanentError("instance not registered for delete")

    r = session.post('{}://{}/api/notes/delete'.format(app.protocol, app.misskey_instance), json = {
        'noteId': post.misskey_id
    })
    
    if r.status_code != 204:
        raise TemporaryError("{} {}".format(r.status_code, r.body))
    
    db.session.delete(post)

def suggested_instances(limit=5, min_popularity=5, blocklist=tuple()):
    return tuple((ins.instance for ins in (
            MisskeyInstance.query
            .filter(MisskeyInstance.popularity > min_popularity)
            .filter(~MisskeyInstance.instance.in_(blocklist))
            .order_by(db.desc(MisskeyInstance.popularity),
                      MisskeyInstance.instance)
            .limit(limit).all())))
