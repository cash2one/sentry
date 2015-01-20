import logging as ori_logging

from gunicorn import glogging
from oslo.config import cfg

from sentry.api import bottle
from sentry.openstack.common import log as logging

LOG = logging.getLogger(__name__)

api_configs = [
    cfg.IntOpt("listen_port",
               default=7788,
               help="sentry-api listen on the port."),
    cfg.StrOpt("listen_host",
               default="0.0.0.0",
               help="sentry-api listen on the host."),
    cfg.BoolOpt("api_debug",
                default=False,
                help="Whether enable builtin api debug mode."),
    cfg.IntOpt("workers",
               default=1,
               help="The number of forked works"),
    cfg.IntOpt("threads",
               default=10,
               help="The number of eventlet threads"),
    cfg.IntOpt("default_items",
               default=20,
               help="Default item return in a API call."),
]
api_group = cfg.OptGroup(name="api", title="Sentry API Options")

CONF = cfg.CONF
CONF.register_group(api_group)
CONF.register_opts(api_configs, api_group)


def run():

    class Logging(glogging.Logger):
        """
        Some hack to override gunicorn's logging
        """
        def __init__(self, cfg):
            self.cfg = cfg
            self.error_log = LOG
            self.access_log = LOG

        def setup(self, cfg):
            pass

    from sentry.api import root
    from sentry.api.v1.app import app as v1app

    root_app = root.app
    root_app.mount('/v1', v1app)
    # future v2
    #root_app.mount('/v2', v2.app)

    CONF.log_opt_values(LOG, ori_logging.DEBUG)
    LOG.info("Sentry API start running.")

    for route in root_app.routes:
        LOG.debug(str(route))

    bottle.run(root_app,
               server='gunicorn',
               worker_class='eventlet',
               logger_class=Logging,
               workers=CONF.api.workers,
               threads=CONF.api.threads,
               debug=CONF.api.api_debug,
               port=CONF.api.listen_port,
               host=CONF.api.listen_host)
