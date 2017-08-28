import time
from statsd.defaults.env import statsd

class StatsdMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        timer_name = 'forget.http.{}.{}'.format(
                environ.get('PATH_INFO').replace('/', '.').strip('.') or 'index',
                environ.get('REQUEST_METHOD'))
        with statsd.timer(timer_name):
            response = self.app(environ, start_response)

        return response

