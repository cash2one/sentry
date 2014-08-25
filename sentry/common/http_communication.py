#
# Created on 2013-1-21
#
# @author: hzyangtk@corp.netease.com
#

import time
import httplib
import urllib

from oslo.config import cfg
from sentry.openstack.common import log


LOG = log.getLogger(__name__)
CONF = cfg.CONF


request_configs = [
    cfg.IntOpt('http_retry_count',
               default=3,
               help='Retry counts when http connection failed.'),
    cfg.FloatOpt('http_retry_delay',
                 default=3,
                 help='Retry dealy when http connection failed.'),
]

CONF.register_opts(request_configs)


class HttpCommunication(object):
    '''
        Send datas to monitor server by accesskey authorization.
    '''
    def __init__(self, url=None, request_uri='', headers={}, httpMethod='GET',
                 params_dict={}):
        self.url = url
        self.request_uri = request_uri
        self.headers = headers
        self.httpMethod = httpMethod
        self.params = urllib.urlencode(params_dict)

    def send_request_to_server(self, **kwargs):
        '''
            Send request to server.
        '''
        if not self.url:
            LOG.error("Http Communication error.")
            raise Exception()

        LOG.info(_("Sending alarm...the url is: %s%s, the params is: %s"
                   % (self.url, self.request_uri, self.params)))
        if str(self.url).startswith('http://'):
            self.url = str(self.url).split("http://")[-1]

        attempts = kwargs.get('attempts', CONF.http_retry_count)
        while attempts > 0:
            attempts -= 1
            try:
                conn = httplib.HTTPConnection(self.url)
                conn.request(self.httpMethod, self.request_uri,
                             self.params, self.headers)
                response = conn.getresponse()
                res_content = response.read()
                if isinstance(res_content, unicode):
                    res_content = res_content.encode('UTF-8')
                conn.close()
            except Exception:
                response = None
                LOG.exception("Http communication failed ")
                LOG.warning("Go retrying, left %s time" % attempts)
                time.sleep(CONF.http_retry_delay)
                continue
            if response.status == 200:
                LOG.info("Http send successfully")
                break
            else:
                LOG.warning("Http communication failed ")
                LOG.warning("Http Communication response exception with "
                            "status: %s, message: %s."
                            % (response.status, res_content))
                LOG.warning("Go retrying, left %s time" % attempts)
                time.sleep(CONF.http_retry_delay)
        return response
