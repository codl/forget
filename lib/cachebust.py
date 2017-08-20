from flask import url_for, abort
import os
def cachebust(app):
    @app.route('/static-<int:timestamp>/<path:filename>')
    def static_cachebust(timestamp, filename):
        path = os.path.join(app.static_folder, filename)
        try:
            mtime = os.stat(path).st_mtime
        except Exception:
            return abort(404)
        if abs(mtime - timestamp) > 1:
            abort(404)
        else:
            resp = app.view_functions['static'](filename=filename)
            resp.headers.set('cache-control', 'public, immutable, max-age=%s' % (60*60*24*365,))
            if 'expires' in resp.headers:
                resp.headers.remove('expires')
            return resp

    @app.context_processor
    def replace_url_for():
        return dict(url_for = cachebust_url_for)

    def cachebust_url_for(endpoint, **kwargs):
        if endpoint == 'static':
            endpoint = 'static_cachebust'
            path = os.path.join(app.static_folder, kwargs.get('filename'))
            kwargs['timestamp'] = int(os.stat(path).st_mtime)
        return url_for(endpoint, **kwargs)

    return cachebust_url_for
