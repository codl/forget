import requests
import threading
import redis
from flask import make_response, abort


class ImgProxyCache(object):
    def __init__(self, redis_uri='redis://', timeout=1, expire=60*60*6,
                 prefix='img_proxy'):
        self.redis = redis.StrictRedis.from_url(redis_uri)
        self.timeout = timeout
        self.expire = expire
        self.prefix = prefix
        self.redis.client_setname('img_proxy')

    def key(self, keytype, url):
        return '{prefix}:{keytype}:{url}'.format(
                prefix=self.prefix,
                keytype=keytype,
                url=url)

    def fetch_and_cache(self, url):
        resp = requests.get(url)
        if(resp.status_code != 200):
            return
        mime = resp.headers.get('content-type', 'application/octet-stream')
        self.redis.set(self.key('mime', url), mime, px=self.expire)
        self.redis.set(self.key('body', url), resp.content, px=self.expire)

    def respond(self, url):
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
        return resp
