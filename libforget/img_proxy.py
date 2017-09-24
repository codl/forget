import requests
import threading
import redis as libredis
from flask import make_response, abort
import secrets
import hmac
import base64
import pickle # nosec
import re


class ImgProxyCache(object):
    def __init__(self, redis_uri='redis://', timeout=10, expire=60*60,
                 prefix='img_proxy', hmac_hash='sha1'):
        self._redis = None
        self._redis_uri = redis_uri
        self.timeout = timeout
        self.expire = expire
        self.prefix = prefix
        self.hash = hmac_hash
        self.hmac_key = None

    @property
    def redis(self):
        if not self._redis:
            self._redis = libredis.StrictRedis.from_url(self._redis_uri)
            self._redis.client_setname('img_proxy')
        return self._redis

    def key(self, *args):
        return '{prefix}:1:{args}'.format(
                prefix=self.prefix, args=":".join(args))

    def token(self):
        if not self.hmac_key:
            t = self.redis.get(self.key('hmac_key'))
            if not t:
                t = secrets.token_urlsafe().encode('ascii')
                self.redis.set(self.key('hmac_key'), t)
            self.hmac_key = t
        return self.hmac_key

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

        header_whitelist = [
                'content-type',
                'cache-control',
                'etag',
                'date',
                'last-modified',
                ]
        headers = {}

        expire = self.expire
        if 'cache-control' in resp.headers:
            for value in resp.headers['cache-control'].split(','):
                match = re.match(' *max-age *= *([0-9]+) *', value)
                if match:
                    expire = max(self.expire, int(match.group(1)))

        for key in header_whitelist:
            if key in resp.headers:
                headers[key] = resp.headers[key]
        self.redis.set(self.key('headers', url), pickle.dumps(headers, -1),
                       px=expire*1000)
        self.redis.set(self.key('body', url),
                       resp.content, px=expire*1000)

    def respond(self, identifier):
        url = self.url_for(identifier)
        if not url:
            return abort(403)

        x_imgproxy_cache = 'HIT'
        headers = self.redis.get(self.key('headers', url))
        body = self.redis.get(self.key('body', url))

        if not body or not headers:
            x_imgproxy_cache = 'MISS'
            if self.redis.set(
                    self.key('lock', url), 1, nx=True, ex=10*self.timeout):
                t = threading.Thread(target=self.fetch_and_cache, args=(url,))
                t.start()
                t.join(self.timeout)
                headers = self.redis.get(self.key('headers', url))
                body = self.redis.get(self.key('body', url))

        try:
            headers = pickle.loads(headers) # nosec
        except Exception:
            self.redis.delete(self.key('headers', url))
            headers = None

        if not body or not headers:
            return abort(404)

        resp = make_response(body, 200)
        resp.headers.set('x-imgproxy-cache', x_imgproxy_cache)
        resp.headers.set('cache-control', 'max-age={}'.format(self.expire))
        for key, value in headers.items():
            resp.headers.set(key, value)
        return resp
