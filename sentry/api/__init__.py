import logging as ori_logging

from oslo.config import cfg

from sentry.openstack.common import log as logging

LOG = logging.getLogger(__name__)

api_configs = [
    cfg.IntOpt("listen_port",
               default=7788,
               help="sentry-api listen on the port."),
    cfg.StrOpt("listen_host",
               default="localhost",
               help="sentry-api listen on the host."),
    cfg.BoolOpt("api_debug",
                default=False,
                help="Whether enable builtin api debug mode."),
    cfg.IntOpt("default_items",
               default=20,
               help="Default item return in a API call."),
]
api_group = cfg.OptGroup(name="api", title="Sentry API Options")

CONF = cfg.CONF
CONF.register_group(api_group)
CONF.register_opts(api_configs, api_group)


def run():
    from sentry.api import bottle
    from sentry.api.v1.app import app as v1app

    root_app = bottle.Bottle()
    root_app.mount('/v1', v1app)
    # future v2
    #root_app.mount('/v2', v2.app)

    CONF.log_opt_values(LOG, ori_logging.DEBUG)
    LOG.info("Sentry api start running.")

    for route in root_app.routes:
        LOG.debug(str(route))

    bottle.run(root_app,
               debug=CONF.api.api_debug,
               port=CONF.api.listen_port,
               host=CONF.api.listen_host)