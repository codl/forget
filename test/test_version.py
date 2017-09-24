import re
import version


def test_version_looks_like_a_version():
    assert re.match(
        'v?[0-9]+.[0-9]+.[0-9]+(-[A-Za-z0-9\-.]+)?',
        version.version)


def test_libversion_url():
    import libforget.version
    assert libforget.version.url_for_version(version.version)
