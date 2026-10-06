import os
import sys
from urllib.parse import parse_qs, urlencode

# Ensure root project directory is on sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

class VercelRouteMiddleware:
    """WSGI middleware ensuring correct PATH_INFO when Vercel rewrites requests to serverless entrypoints"""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        qs = environ.get('QUERY_STRING', '')
        if '__route__' in qs:
            params = parse_qs(qs, keep_blank_values=True)
            if '__route__' in params:
                route = params.pop('__route__')[0]
                if not route.startswith('/'):
                    route = '/' + route
                environ['PATH_INFO'] = route
                environ['QUERY_STRING'] = urlencode(params, doseq=True)
        return self.wsgi_app(environ, start_response)

# Apply route middleware to Flask WSGI application
app.wsgi_app = VercelRouteMiddleware(app.wsgi_app)

if __name__ == '__main__':
    app.run()
