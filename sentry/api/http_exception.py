from sentry.api import bottle
from sentry.openstack.common import jsonutils


class HTTPException(bottle.HTTPResponse):
    def __init__(self, message):
        self.error_message = message
        body = {
            "exception": {
                "code": self.default_status,
                "message": self.error_message,
            }
        }
        super(HTTPException, self).__init__(jsonutils.dumps(body))


class HTTPBadRequest(HTTPException):
    default_status = 400
