#
# Created on 2012-12-4
#
# @author: hzyangtk@corp.netease.com
#

from sentry.common import utils
from sentry.notification import helper as controller_helper
from oslo.config import cfg
from sentry.openstack.common import importutils
from sentry.openstack.common import log
from sentry.sender import manager as sender_manager


handler_configs = [
    cfg.BoolOpt('enable_alarm', default=True,
                help="Enable alarm when receive ERROR"),
    cfg.StrOpt('alarm_level',
               default='ERROR',
               help='Alarm level'),
    cfg.ListOpt('filter_driver_list',
                default=['sentry.filter.alarm_filter.AlarmFilter',
                         'sentry.filter.owner_filter.OwnerFilter'],
                help='Driver or drivers to filter alarm messages'),
]


CONF = cfg.CONF
CONF.register_opts(handler_configs)
LOG = log.getLogger(__name__)


class Handler(object):

    def __init__(self):
        self._filter_drivers = None

    def handle_message(self, message):
        """
        The notifications Message Example:
        {
          'message_id': str(uuid.uuid4()),
          'event_type': 'compute.create_instance',
          'publisher_id': 'compute.host1',
          'timestamp': timeutils.utcnow(),
          'priority': 'INFO',
          'payload': {'instance_id': 12, ... }
        }
        """
        if not CONF.enable_alarm:
            LOG.debug("Alarm handler was disabled.")
            return

        try:
            # NOTE(hzyangtk): handle message before alarm like notify
            #                 cloud monitor to stop alarm when instance
            #                 was deleted.
            controller_helper.handle_before_alarm(message)

            alarm_levels = utils.get_alarm_level(CONF.alarm_level)
            message_priority = message.get('priority')
            if message_priority in alarm_levels:
                # NOTE(hzyangtk): flow_data is origin data that will be
                #                 filtered alarm_type is like
                #                 compute.create.start
                #                 alarm_level is like ERROR
                #                 alarm_owner is like product_manager,
                #                                     platform_manager
                flow_data = {'alarm_type': message.get('event_type'),
                             'alarm_level': message.get('priority'),
                             'alarm_owner': []}
                flow_data = self._do_filter(flow_data)
                if flow_data is not None:
                    # move flow_data['alarm_owner'] to message
                    message['alarm_owner'] = flow_data['alarm_owner']
                    # send alarm to alarm system
                    self._do_send_alarm(message)
                    LOG.info('Alarm over')
        except Exception:
            LOG.exception("Alarm failed")

    def _do_filter(self, flow_data):
        for driver in self._get_filter_drivers():
            try:
                flow_data = driver.filter(flow_data)
            except Exception, e:
                LOG.exception(_("Attempting to "
                  "do filter with flow data: %(flow_data)s.") %
                                locals())
        return flow_data

    def _get_filter_drivers(self):
        """Instantiate, cache, and return drivers based on the CONF."""
        if self._filter_drivers is None:
            self._filter_drivers = {}
            LOG.debug("Filter list is: %s" % str(CONF.filter_driver_list))
            for filter_driver in CONF.filter_driver_list:
                self._add_filter_driver(filter_driver)

        return self._filter_drivers.values()

    def _add_filter_driver(self, filter_driver):
        """Add a filter driver at runtime."""
        # Make sure the driver list is initialized.
        self._get_filter_drivers()
        if isinstance(filter_driver, basestring):
            # Load and add
            try:
                driver = importutils.import_object(filter_driver)
                self._filter_drivers[filter_driver] = driver
            except ImportError:
                LOG.exception(_("Failed to load filter %s. "
                                "These filters will not be sent.") %
                                filter_driver)
        else:
            # Driver is already loaded; just add the object.
            self._filter_drivers[filter_driver] = filter_driver

    def _reset_filter_drivers(self):
        """Used by unit tests to reset the drivers."""
        self._filter_drivers = None

    def _do_send_alarm(self, message):
        """Send messages to alarm system."""
        sender_manager.send_alarm(message)
