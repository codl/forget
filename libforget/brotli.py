import brotli as brotli_
from flask import request, make_response
from threading import Thread
from hashlib import sha256
import redis as libredis
import os.path
import mimetypes


class BrotliCache(object):
    def __init__(self, redis_uri='redis://', timeout=0.100, expire=60*60*6):
        self._redis = None
        self._redis_uri = redis_uri
        self.timeout = timeout
        self.expire = expire

    @property
    def redis(self):
        if not self._redis:
            self._redis = libredis.StrictRedis.from_url(self._redis_uri)
            self._redis.client_setname('brotlicache')
        return self._redis

    def compress_and_cache(self, cache_key, lock_key, body, mode=brotli_.MODE_GENERIC):
        encbody = brotli_.compress(body, mode=mode)
        self.redis.set(cache_key, encbody, px=int(self.expire*1000))
        self.redis.delete(lock_key)

    def wrap_response(self, response):
        if 'br' not in request.accept_encodings or response.is_streamed:
            return response

        body = response.get_data()
        digest = sha256(body).hexdigest()
        cache_key = 'brotlicache:{}'.format(digest)

        encbody = self.redis.get(cache_key)
        response.headers.set('brotli-cache', 'HIT')
        if not encbody:
            response.headers.set('brotli-cache', 'MISS')
            lock_key = 'brotlicache:lock:{}'.format(digest)
            if self.redis.set(lock_key, 1, nx=True, ex=10):
                mode = (
                    brotli_.MODE_TEXT
                    if response.content_type.startswith('text/')
                    else brotli_.MODE_GENERIC)
                t = Thread(
                    target=self.compress_and_cache,
                    args=(cache_key, lock_key, body, mode))
                t.start()
                if self.timeout > 0:
                    t.join(self.timeout)
                    encbody = self.redis.get(cache_key)
                if not encbody:
                    response.headers.set('brotli-cache', 'TIMEOUT')
            else:
                response.headers.set('brotli-cache', 'LOCKED')
        if encbody:
            response.headers.set('content-encoding', 'br')
            response.headers.set('vary', 'accept-encoding')
            response.set_data(encbody)
            return response

        return response


def brotli(app, static=True, dynamic=True, **kwargs):
    original_static = app.view_functions['static']

    def static_maybe_gzip_brotli(filename=None):
        path = os.path.join(app.static_folder, filename)
        for encoding, extension in (('br', '.br'), ('gzip', '.gz')):
            if encoding not in request.accept_encodings:
                continue
            encpath = path + extension
            if os.path.isfile(encpath):
                resp = make_response(
                    original_static(filename=filename + extension))
                resp.headers.set('content-encoding', encoding)
                resp.headers.set('vary', 'accept-encoding')
                mimetype = (mimetypes.guess_type(filename)[0]
                            or 'application/octet-stream')
                resp.headers.set('content-type', mimetype)
                return resp
        return original_static(filename=filename)
    if static:
        app.view_functions['static'] = static_maybe_gzip_brotli
    if dynamic:
        cache = BrotliCache(redis_uri=app.config.get('REDIS_URI'), **kwargs)
        app.after_request(cache.wrap_response)
