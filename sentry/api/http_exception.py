from sentry.api import bottle
from sentry.openstack.common import jsonutils


class HTTPException(bottle.HTTPResponse):
    default_message = 'Internal Exception'
    default_status = 500

    def __init__(self, message=None):
        self.error_message = message or self.default_message
        body = {
            "exception": {
                "code": self.default_status,
                "message": self.error_message,
            }
        }
        super(HTTPException, self).__init__(jsonutils.dumps(body))


class HTTPBadRequest(HTTPException):
    default_status = 400
    default_message = 'HTTP Bad Request'


class HTTPNotFound(HTTPException):
    default_status = 404
    default_message = 'HTTP Not Found'
