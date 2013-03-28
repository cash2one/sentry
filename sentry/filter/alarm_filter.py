#
# Created on 2012-11-16
#
# @author: hzyangtk
#

import json

from sentry.filter.filter import Filter
from sentry.openstack.common import log
from sentry.openstack.common import cfg

CONF = cfg.CONF

alarm_filter_configs = [
    cfg.StrOpt('alarm_filter_config',
               default='/etc/sentry/filter/alarm_filter.conf'),
]

CONF.register_opts(alarm_filter_configs)


LOG = log.getLogger(__name__)


class AlarmFilter(Filter):
    '''
    Filter for alarm system
    '''

    def __init__(self):
        '''
        init filter rules
        '''
        self.init_filter()
        self.register_filter()

    def init_filter(self):
        json_data = open(CONF.alarm_filter_config, 'r').read()
        dict_data = json.loads(json_data)
        self.filter_reject_rule = dict_data['sentry_reject_levels']
        self.filter_accept_rule = dict_data['sentry_accept_levels']

    def register_filter(self):
        self.filters = []
        self.filters.append(self._reject_filter)
        self.filters.append(self._accept_filter)

    def filter(self, flow_data):
        for filter_func in self.filters:
            if flow_data is None:
                return
            flow_data = filter_func(flow_data)
        return flow_data

    def _reject_filter(self, flow_data):
        """black list"""
        if flow_data['alarm_level'] in self.filter_reject_rule:
            if flow_data['alarm_type'] not in \
                    self.filter_reject_rule[flow_data['alarm_level']]:
                return flow_data

    def _accept_filter(self, flow_data):
        """white list"""
        if flow_data['alarm_level'] in self.filter_accept_rule:
            if flow_data['alarm_type'] in \
                        self.filter_accept_rule[flow_data['alarm_level']]:
                return flow_data
