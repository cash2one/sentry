#
# Created on 2012-11-16
#
# @author: hzyangtk
#


import eventlet
from eventlet import greenpool

from sentry.api import wsgi
from sentry.openstack.common import log
from sentry.openstack.common import cfg

"""
    Sentry api for http request
"""

FLAGS = cfg.CONF

manager_configs = [
    cfg.StrOpt('sentry_api_listen',
               default="0.0.0.0",
               help='IP address for metadata api to listen'),
    cfg.IntOpt('sentry_api_listen_port',
               default=9901,
               help='port for metadata api to listen'),
    cfg.IntOpt('sentry_api_workers',
               default=None,
               help='Number of workers for metadata service'),
]

FLAGS.register_opts(manager_configs)


LOG = log.getLogger(__name__)


class Manager(object):

    def __init__(self, name, loader=None):
        self.name = name
        self.loader = loader or wsgi.Loader()
        self.app = self.loader.load_app(name)
        self.host = FLAGS.sentry_api_listen
        self.port = FLAGS.sentry_api_listen_port
        self.workers = FLAGS.sentry_api_workers
        self.server = wsgi.Server(name,
                                  self.app,
                                  host=self.host,
                                  port=self.port)
        # Pull back actual port used
        self.port = self.server.port

    def serve(self):
        """
        Sentry api serve.
        """
        LOG.info('Start sentry api')
        self.server.start()
        self.server.wait()

    def create(self):
        return eventlet.spawn(self.serve())

    def cleanup(self):
        LOG.info('Cleanup sentry')
