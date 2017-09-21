import pytest
import libforget.brotli


BEE_SCRIPT = bytes("According to all known laws of aviation,", 'UTF-8')
TIMEOUT_TARGET = 0.2


@pytest.fixture
def app(redisdb):
    from flask import Flask
    app_ = Flask(__name__)
    app_.config['REDIS_URI'] = 'redis://localhost:15487'
    app_.debug = True

    @app_.route('/')
    def hello():
        return 'Hello, world!'
    with app_.app_context():
        yield app_


@pytest.fixture
def br_app(app):
    libforget.brotli.brotli(app, timeout=TIMEOUT_TARGET)
    return app


@pytest.fixture
def br_client(br_app):
    return br_app.test_client()


def test_brotli_static_passthru(br_client):
    resp = br_client.get('/static/bee.txt')
    assert BEE_SCRIPT in resp.data


def test_brotli_static_gzip(br_client):
    from gzip import decompress

    gzip_resp = br_client.get(
            '/static/bee.txt',
            headers=[('accept-encoding', 'gzip')])
    assert gzip_resp.headers.get('content-encoding') == 'gzip'

    assert BEE_SCRIPT in decompress(gzip_resp.data)


def test_brotli_static_br(br_client):
    from brotli import decompress

    br_resp = br_client.get(
            '/static/bee.txt',
            headers=[('accept-encoding', 'gzip, br')])
    assert br_resp.headers.get('content-encoding') == 'br'

    assert BEE_SCRIPT in decompress(br_resp.data)


def test_brotli_dynamic(br_client):
    from brotli import decompress

    resp = br_client.get(
            '/',
            headers=[('accept-encoding', 'gzip, br')])

    assert resp.headers.get('x-brotli-cache') == 'MISS'
    assert resp.headers.get('content-encoding') == 'br'
    assert b"Hello, world!" in decompress(resp.data)


def test_brotli_dynamic_cache(br_client):
    from brotli import decompress
    from time import sleep

    br_client.get(
            '/',
            headers=[('accept-encoding', 'gzip, br')])

    sleep(0.5)

    resp = br_client.get(
            '/',
            headers=[('accept-encoding', 'gzip, br')])

    assert resp.headers.get('x-brotli-cache') == 'HIT'
    assert resp.headers.get('content-encoding') == 'br'
    assert b"Hello, world!" in decompress(resp.data)


def test_brotli_dynamic_timeout(app):
    from secrets import token_urlsafe

    libforget.brotli.brotli(app, timeout=0.01)

    @app.route('/hard_to_compress')
    def hard_to_compress():
        return token_urlsafe(2**14)

    client = app.test_client()

    resp = client.get(
            '/hard_to_compress',
            headers=[('accept-encoding', 'gzip, br')])

    assert resp.headers.get('x-brotli-cache') == 'TIMEOUT'
    assert resp.headers.get('content-encoding') != 'br'


def test_brotli_dynamic_expire(app):
    from time import sleep

    libforget.brotli.brotli(app, expire=0.1)

    client = app.test_client()
    client.get(
            '/',
            headers=[('accept-encoding', 'gzip, br')])

    sleep(1)

    resp = client.get(
            '/',
            headers=[('accept-encoding', 'gzip, br')])

    assert resp.headers.get('x-brotli-cache') != 'HIT'
