from app import app
import re

version_re = re.compile('(?P<tag>.+)-(?P<commits>[0-9]+)-g(?P<hash>[0-9a-f]+)')


def url_for_version(ver):
    match = version_re.match(ver)
    if not match:
        return app.config['REPO_URL']
    return app.config['COMMIT_URL'].format(**match.groupdict())
