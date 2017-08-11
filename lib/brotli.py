import brotli
from flask import request
from functools import wraps
from threading import Thread
from hashlib import sha256
import redis

class BrotliCache(object):
    def __init__(self, redis_kwargs={}):
        self.redis = redis.StrictRedis(**redis_kwargs)

    def compress(self, cache_key, lock_key, body):
        encbody = brotli.compress(body)
        self.redis.set(cache_key, encbody, ex=3600)
        self.redis.delete(lock_key)

    def wrap_response(self, response):
        if 'br' not in request.accept_encodings or response.is_streamed:
            return response

        body = response.get_data()
        digest = sha256(body).hexdigest()
        cache_key = 'brotlicache:{}'.format(digest)

        encbody = self.redis.get(cache_key)
        if encbody:
            response.headers.set('content-encoding', 'br')
            response.headers.set('vary', 'content-encoding')
            response.set_data(encbody)
            return response
        else:
            lock_key = 'brotlicache:lock:{}'.format(digest)
            if self.redis.set(lock_key, 1, nx=True, ex=60):
                t = Thread(target=self.compress, args=(cache_key, lock_key, body))
                t.run()

        return response
