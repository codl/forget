import re
import version


def test_libversion_url():
    import libforget.version
    assert libforget.version.url_for_version(version.get_versions())
