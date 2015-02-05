import os
import sys
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
                help="API debug mode will using `wsgiref` to run wsgi, "
                "which make life easier for debuging."),
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

    def debug(self, msg, *args, **kwargs):
        pass

    def access(self, resp, req, environ, request_time):
        """Log access like apache, this method is borrow from gunicorn."""
        status = resp.status.split(None, 1)[0]
        atoms = {
            'h': environ.get('REMOTE_ADDR', '-'),
            'l': '-',
            'u': '-',
            't': self.now(),
            'r': "%s %s %s" % (environ['REQUEST_METHOD'],
                                environ['RAW_URI'],
                                environ["SERVER_PROTOCOL"]),
            's': status,
            'b': str(resp.response_length) or '-',
            'f': environ.get('HTTP_REFERER', '-'),
            'a': environ.get('HTTP_USER_AGENT', '-'),
            'T': str(request_time.seconds),
            'D': str(request_time.microseconds),
            'p': "<%s>" % os.getpid()
        }
        # add request headers
        if hasattr(req, 'headers'):
            req_headers = req.headers
        else:
            req_headers = req

        atoms.update(dict([("{%s}i" % k.lower(), v)
                            for k, v in req_headers]))

        # add response headers
        atoms.update(dict([("{%s}o" % k.lower(), v)
                            for k, v in resp.headers]))

        access_format = ('"%(h)s "%(r)s" %(s)s %(b)s '
                            '"%(f)s" "%(a)s"')
        self.error_log.info(access_format % atoms)


def run():
    """The main point of sentry-api.

    Setup tree like apps, the root app then mount sub-app into some prefix
    urls.
    """
    # NOTE(gtt): We are using eventlet based WSGI server, bottle have some bug
    # with it. It needs monkey patch at the very start.
    # see https://github.com/bottlepy/bottle/issues/317 for more detail.
    import eventlet
    eventlet.monkey_patch(os=False)

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

    # NOTE(gtt): A Hack to work around gunicorn and oslo.config
    # Since gunicorn will parse sys.argv which is not compatible
    # with oslo.config. At this time, oslo have already finished
    # parse sys.argv, so delete it.
    del sys.argv[1:]

    if CONF.api.api_debug:
        LOG.info("API debug mode, running with wsgiref.")
        bottle.run(root_app,
                   server='wsgiref',
                   port=CONF.api.listen_port,
                   host=CONF.api.listen_host)
    else:
        bottle.run(root_app,
                   server='gunicorn',
                   worker_class='eventlet',
                   logger_class=Logging,
                   workers=CONF.api.workers,
                   debug=CONF.api.api_debug,
                   port=CONF.api.listen_port,
                   host=CONF.api.listen_host,
                   quiet=True)
