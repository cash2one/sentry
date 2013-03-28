#
# Created on 2012-12-11
#
# @author: hzyangtk@corp.netease.com
#

import time

from sentry.common import utils
from sentry.common import novaclient_helper


def is_instance_down(message, alarm_content):
    alarm_event_type = alarm_content.get('alarm_event_type', {})
    if message.get('event_type') in alarm_event_type.get('InstanceOffLine',
                                                         []):
        return True
    else:
        return False


def is_instance_state_error(message, alarm_content):
    alarm_event_type = alarm_content.get('alarm_event_type', {})
    if message.get('event_type') in alarm_event_type.get('InstanceError',
                                                         []):
        if message.get('payload').get('state') == 'error':
            return True
    return False


def is_nos_connection_failure(message, alarm_content):
    alarm_event_type = alarm_content.get('alarm_event_type', {})
    if message.get('event_type') in alarm_event_type.get('NosError',
                                                         []):
        return True
    else:
        return False


def is_nbs_connection_failure(message, alarm_content):
    alarm_event_type = alarm_content.get('alarm_event_type', {})
    if message.get('event_type') in alarm_event_type.get('NbsError',
                                                         []):
        return True
    else:
        return False


def is_other_alarm(message, alarm_content):
    return False


def get_instance_ip(instance_uuid):
    if instance_uuid == None:
        return '-'
    # NOTE(hzyangtk): call nova client to get isntance detail info
    call_nova_client = novaclient_helper.CallNovaClient()
    instance = call_nova_client.get_instance_by_UUID(instance_uuid)

    try:
        addrName = instance.addresses.keys()[0]
        instance_ip = instance.addresses[addrName][0]['addr']
    except Exception:
        instance_ip = '-'
    return instance_ip


def set_alarm_timestamp(message):
    # NOTE(hzyangtk): change message`s time from datetime string to
    #                 time long
    try:
        datetime_string = message.get('timestamp', None)
        if datetime_string is None:
            message['timestamp'] = long(time.time() * 1000)
        else:
            if not isinstance(datetime_string, str) and \
                    not isinstance(datetime_string, unicode):
                raise TypeError()
            ori_datetime = utils.parse_strtime(datetime_string,
                                               '%Y-%m-%d %H:%M:%S.%f')
            local_datetime = utils.tz_utc_to_local(ori_datetime)
            message['timestamp'] = utils.datetime_to_timestamp(
                                            local_datetime)
    except (ValueError, TypeError):
        # NOTE(hzyangtk): ValueError will be thrown when datetime
        #                 format not match.
        message['timestamp'] = long(time.time() * 1000)
    return message
