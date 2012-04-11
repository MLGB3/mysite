_application = django.core.handlers.wsgi.WSGIHandler()
from gematria.settings import URL_PREFIX
def application(environ, start_response):
    environ['SCRIPT_NAME'] = '/' + URL_PREFIX[:-1]
    environ['PATH_INFO'] = environ['SCRIPT_NAME'] + environ['PATH_INFO']
    return _application(environ, start_response)