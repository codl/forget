import requests
import threading
import redis
from flask import make_response, abort
import secrets
import hmac
import base64


class ImgProxyCache(object):
    def __init__(self, redis_uri='redis://', timeout=1, expire=60*60*24,
                 prefix='img_proxy', hmac_hash='sha1'):
        self.redis = redis.StrictRedis.from_url(redis_uri)
        self.timeout = timeout
        self.expire = expire
        self.prefix = prefix
        self.redis.client_setname('img_proxy')
        self.hash = hmac_hash

    def key(self, *args):
        return '{prefix}:{args}'.format(
                prefix=self.prefix, args=":".join(args))

    def token(self):
        t = self.redis.get(self.key('hmac_key'))
        if not t:
            t = secrets.token_urlsafe().encode('ascii')
            self.redis.set(self.key('hmac_key'), t)
        return t

    def identifier_for(self, url):
        url_hmac = hmac.new(self.token(), url.encode('UTF-8'), self.hash)
        return base64.urlsafe_b64encode(
                '{}:{}'.format(url_hmac.hexdigest(), url)
                .encode('UTF-8')
                ).strip(b'=')

    def url_for(self, identifier):
        try:
            padding = (4 - len(identifier)) % 4
            identifier += padding * '='
            identifier = base64.urlsafe_b64decode(identifier).decode('UTF-8')
            received_hmac, url = identifier.split(':', 1)
            url_hmac = hmac.new(self.token(), url.encode('UTF-8'), self.hash)
            if not hmac.compare_digest(url_hmac.hexdigest(), received_hmac):
                return None
        except Exception:
            return None
        return url

    def fetch_and_cache(self, url):
        resp = requests.get(url)
        if(resp.status_code != 200):
            return
        mime = resp.headers.get('content-type', 'application/octet-stream')
        self.redis.set(self.key('mime', url),
                       mime, px=self.expire*1000)
        self.redis.set(self.key('body', url),
                       resp.content, px=self.expire*1000)

    def respond(self, identifier):
        url = self.url_for(identifier)
        if not url:
            return abort(403)

        x_imgproxy_cache = 'HIT'
        mime = self.redis.get(self.key('mime', url))
        body = self.redis.get(self.key('body', url))
        if not body or not mime:
            x_imgproxy_cache = 'MISS'
            if self.redis.set(
                    self.key('lock', url), 1, nx=True, ex=10*self.timeout):
                t = threading.Thread(target=self.fetch_and_cache, args=(url,))
                t.start()
                t.join(self.timeout)
                mime = self.redis.get(self.key('mime', url))
                body = self.redis.get(self.key('body', url))
        if not body or not mime:
            return abort(404)

        resp = make_response(body, 200)
        resp.headers.set('content-type', mime)
        resp.headers.set('x-imgproxy-cache', x_imgproxy_cache)
        resp.headers.set('cache-control', 'max-age={}'.format(self.expire))
        return resp
