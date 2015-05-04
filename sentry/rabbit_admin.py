"""
RabbitMQ Admin client
"""

import base64
import urllib2
import urlparse

from oslo.config import cfg

from sentry.openstack.common import jsonutils
from sentry.openstack.common import log as logging

LOG = logging.getLogger(__name__)

CONF = cfg.CONF
CONF.import_opt('rabbit_hosts', 'sentry.openstack.common.rpc.impl_kombu')
CONF.import_opt('rabbit_userid', 'sentry.openstack.common.rpc.impl_kombu')
CONF.import_opt('rabbit_password', 'sentry.openstack.common.rpc.impl_kombu')

rabbit_admin_opts = [
    cfg.IntOpt("rabbit_admin_port", default=55672,
               help="The rabbit_admin page url."),
    cfg.StrOpt("rabbit_admin_userid", default="$rabbit_userid",
               help="The rabbit admin user id."),
    cfg.StrOpt("rabbit_admin_password", default="$rabbit_password",
               help="The rabbit admin user password."),
]
CONF.register_opts(rabbit_admin_opts, 'monitor')


class RabbitQueue(object):
    def __init__(self, raw_json):
        # NOTE(gtt): Only parse the fields that we are instereted.
        self.consumers = raw_json['consumers']
        self.durable = raw_json['durable']
        self.name = raw_json['name']

    @classmethod
    def hydrate(cls, json):
        if isinstance(json, basestring):
            json = jsonutils.loads(json)

        if not isinstance(json, list):
            raise TypeError("First argument should be list.")

        result = []
        for raw_queue in json:
            result.append(cls(raw_queue))
        return result

    def __repr__(self):
        return "<RabbitQueue: %s>" % self.name


class RabbitAdminClient(object):
    """The basic Rabbit admin page client"""

    def __init__(self, url, username='guest', password='guest'):
        self.username = username
        self.root_url = url
        self.password = password

    def __repr__(self):
        return "<RabbitMQ: %s@%s>" % (self.username, self.root_url)

    def _url(self, uri):
        return urlparse.urljoin(self.root_url, uri)

    def _add_authorization_header(self, request):
        authorization = base64.encodestring(
            '%s:%s' % (self.username, self.password)
        ).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % authorization)

    def _get_response(self, uri):
        url = self._url(uri)
        request = urllib2.Request(url)
        self._add_authorization_header(request)
        # Below will raise HTTPError, like 401, 404
        result = urllib2.urlopen(request, timeout=30)
        return result

    def get_queues(self):
        result = self._get_response('/api/queues')
        return jsonutils.loads(result.read())

    def ping(self):
        """Ping service to make sure authorization legal

        return True if everything is ok, if raises mean something wrong.
        """
        result = self._get_response('/api/overview')
        return 200 == result.code


class RabbitAPI(object):

    def __init__(self):
        self._client = None

    def _valid_client(self, client):
        try:
            client.ping()
        except urllib2.URLError as ex:
            LOG.warn("Ping %s failed: %s" % (client, ex))
            return False
        else:
            return True

    @property
    def rabbit_client(self):
        if self._client:
            if self._valid_client(self._client):
                return self._client

        for i in xrange(len(CONF.rabbit_hosts)):
            rabbit_url = CONF.rabbit_hosts[i]
            if ':' in rabbit_url:
                host = rabbit_url.split(':')[0]
            else:
                host = rabbit_url
            url = 'http://%s:%s' % (host, CONF.monitor.rabbit_admin_port)
            LOG.debug("Attemping rabbit admin at %s" % url)
            client = RabbitAdminClient(url,
                                       CONF.monitor.rabbit_admin_userid,
                                       CONF.monitor.rabbit_admin_password)

            if not self._valid_client(client):
                continue

            LOG.debug("Pick Rabbit admin at %s" % url)
            self._client = client
            return self._client

        raise Exception("RabbitMQ management plugin not available. "
                        "Please make sure rabbitmq_management was enabled.")

    def get_queues(self):
        json = self.rabbit_client.get_queues()
        return RabbitQueue.hydrate(json)
