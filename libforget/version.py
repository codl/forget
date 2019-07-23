from app import app

def url_for_version(ver):
    return app.config['CHANGELOG_URL'].format(hash=ver['full-revisionid'])
