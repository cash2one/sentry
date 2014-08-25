#
# Created on 2012-11-16
#
# @author: hzyangtk@corp.netease.com
#

import hashlib
import hmac
import httplib
import time
import urllib

from oslo.config import cfg
from sentry.openstack.common import log


LOG = log.getLogger(__name__)
CONF = cfg.CONF

request_configs = [
    cfg.StrOpt('url_port',
               default=None,
               help='Alarm system url and port.'),
    cfg.StrOpt('platform_request_uri',
               default=None,
               help='Alarm system platform manager request uri.'),
    cfg.StrOpt('product_request_uri',
               default=None,
               help='Alarm system product manager request uri.'),
    cfg.StrOpt('access_key',
               default=None,
               help='Alarm system access key.'),
    cfg.StrOpt('access_secret',
               default=None,
               help='Alarm system access secret key.'),
]

CONF.register_opts(request_configs)


def product_send_alarm(data):
    SEND_REQUEST.request_uri = CONF.product_request_uri
    SEND_REQUEST.send_request_to_server(data)


def platform_send_alarm(data):
    SEND_REQUEST.request_uri = CONF.platform_request_uri
    SEND_REQUEST.send_request_to_server(data)


class SendRequest(object):
    '''
        Send datas to monitor server by accesskey authorization.
    '''
    def __init__(self):
        self.url = CONF.url_port
        self.request_uri = ''
        self.headers = {'Content-type': 'application/x-www-form-urlencoded'}
        self.httpMethod = 'POST'
        self.access_key = CONF.access_key
        self.access_secret = CONF.access_secret

    def send_request_to_server(self, format_data):
        '''
            Send alarm datas to collect server by POST request.
        '''
        if self.url is None:
            LOG.exception("Alarm http configuration error.")
            # TODO(hzyangtk): raise exception
            raise Exception()

        LOG.info(_("Sending alarm...the url is: %s%s, the format data is: %s"
                   % (self.url, self.request_uri, str(format_data))))
        params = urllib.urlencode({
                'projectId': format_data['projectId'],
                'namespace': format_data['namespace'],
                'alarmType': format_data['alarmType'],
                "alarmTime": format_data['alarmTime'],
                "alarmContent": format_data['alarmContent'],
                "alarmContentSummary": format_data['alarmContentSummary'],
                "identifier": format_data['identifier'],
                #'AccessKey': self.access_key,
                #'Signature': self.generate_signature(format_data)
        })
        if str(self.url).startswith('http://'):
            self.url = str(self.url).split("http://")[-1]

        attempts = CONF.http_retry_count
        while attempts > 0:
            attempts -= 1
            try:
                conn = httplib.HTTPConnection(self.url)
                conn.request(self.httpMethod, self.request_uri,
                             params, self.headers)
                response = conn.getresponse()
                res_content = response.read()
                if isinstance(res_content, unicode):
                    res_content = res_content.encode('UTF-8')
                conn.close()
            except Exception:
                response = None
                LOG.exception("Alarm send failed ")
                LOG.warning("Go retrying, left %s time" % attempts)
                time.sleep(CONF.http_retry_delay)
                continue
            if response.status == 200:
                LOG.info("Alarm send successfully")
                break
            else:
                LOG.warning("Alarm send failed")
                LOG.warning("Alarm Sender response exception with "
                            "status: %s, message: %s."
                            % (response.status, res_content))
                LOG.warning("Go retrying, left %s time" % attempts)
                time.sleep(CONF.http_retry_delay)
        return response

    def generate_stringToSign(self, format_data):
        '''
            Generate stringToSign for signature.
        '''
        CanonicalizedHeaders = ''
        # TODO(hzyangtk): need to modify the content to match the params
        CanonicalizedResources = \
                'AccessKey=%s&MetricDatasJson=%s&Namespace=%s&ProjectId=%s' % \
                    (self.access_key, format_data['alarmType'],
                     format_data['namespace'], format_data['projectId'])

        StringToSign = '%s\n%s\n%s\n%s\n' % \
                      (self.httpMethod, self.requestURI,
                       CanonicalizedHeaders, CanonicalizedResources)

        return StringToSign

    def generate_signature(self, format_data):
        '''
            Generate signature for authorization.
            Use hmac SHA-256 to calculate signature string and encode
            into base64.
            @return String
        '''
        stringToSign = self.generate_stringToSign(format_data)
        hashed = hmac.new(str(self.access_secret),
                          stringToSign,
                          hashlib.sha256)
        s = hashed.digest()
        signature = s.encode('base64').rstrip()
        return signature


SEND_REQUEST = SendRequest()
