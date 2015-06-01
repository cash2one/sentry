# -*- coding: utf8 -*-
"""
A event handler who logging for business inteligent cases.
"""
import os
import collections
import logging as ori_logging
from logging import handlers

from oslo.config import cfg

from sentry import config
from sentry.bi import engine
from sentry.bi import case as bi_case
from sentry.openstack.common import log as logging
from sentry.openstack.common import jsonutils


LOG = logging.getLogger(__name__)

CONF = cfg.CONF
bi_options = [
    cfg.StrOpt('log_file',
               default="sentry-bi.log",
               help="The file name of BI log. Default is sentry_bi.log"),
    cfg.IntOpt('log_interval',
               default=1,
               help="The days that the BI log will holds. Default is 7 days"),
]
CONF.register_opts(bi_options, 'BI')
CONF.import_opt('log_dir', 'sentry.openstack.common.log')


class BILoggerFormatter(ori_logging.Formatter):
    """Output to a json that contains BI informations."""

    def format(self, record):
        # Make sure all keys contains in record
        for key in ('start_at', 'end_at', 'service', 'action_name',
                    'tenant_id', 'tenant_name', 'environment'):
            if key not in record.__dict__:
                record.__dict__[key] = ''

        message = collections.OrderedDict()
        message['start_at'] = record.start_at
        message['end_at'] = record.end_at
        message['action_name'] = record.action_name
        message['tenant_id'] = record.tenant_id
        message['tenant_name'] = record.tenant_name
        message['service'] = record.service
        message['environment'] = record.environment

        return jsonutils.dumps(message)


class Handler(object):

    def __init__(self):
        if not CONF.log_dir:
            LOG.error("config 'log_dir' was not given, BI was disabled")
            self.enable = False
        else:
            self.enable = True

        self._init_logger()

        cases = bi_case.get_taggers()
        self.bi = engine.BIAnalyzer(cases, self.do_log)

    def _init_logger(self):
        # NOTE(gtt): Since this method may be called many times,
        # we need to avoid adding duplicate handlers into bi_log, which
        # results in two logging with the exactly same content.

        self.bi_log = ori_logging.getLogger('bi_log')

        if len(self.bi_log.handlers) >= 1:
            LOG.debug("BI Logging handler already is: %s" %
                      self.bi_log.handlers)
            return

        bi_path = os.path.join(CONF.log_dir, CONF.BI.log_file)
        handler = handlers.TimedRotatingFileHandler(
            bi_path, when='d', interval=CONF.BI.log_interval
        )

        formatter = BILoggerFormatter()
        handler.setFormatter(formatter)

        self.bi_log.addHandler(handler)

    def do_log(self, action):
        """Ungly logging, all information passin using `extra`"""
        self.bi_log.info(
            '',
            extra=dict(
                action_name=action.bi_name,
                start_at=action.start_at,
                end_at=action.end_at,
                tenant_id=action.tenant_id,
                tenant_name=action.tenant_name,
                service='nvs',
                environment=config.get_config('env_name'),
            )
        )

    def handle_message(self, message):
        if not self.enable:
            return

        self.bi.process(message)
