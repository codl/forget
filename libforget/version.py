from app import app

def url_for_version(ver):
    return app.config['COMMIT_URL'].format(hash=ver['full-revisionid'])
