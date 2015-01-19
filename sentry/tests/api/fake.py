from sentry.api import bottle


def fake_request(method, path, query):
    environ = {
        'REQUEST_METHOD': method.upper(),
        'QUERY_STRING': query,
        'PATH_INFO': path,
    }
    return bottle.BaseRequest(environ)
