#
# Created on 2012-11-16
#
# @author: hzyangtk
#

import datetime
import os
import time

from dateutil import tz

from sentry.openstack.common import log as logging


LOG = logging.getLogger(__name__)


ALARM_LEVEL = ['INFO', 'WARN', 'ERROR', 'FATAL']
PERFECT_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"


def get_alarm_level(level):
    """
    To get needed alarm levels, like level='ERROR', it
    will return ['ERROR', 'FATAL']
    """
    need_alarm_level = []
    level_index = ALARM_LEVEL.index(level)
    for i in range(level_index, len(ALARM_LEVEL)):
        need_alarm_level.append(ALARM_LEVEL[i])
    return need_alarm_level


def read_cached_file(filename, cache_info, reload_func=None):
    """Read from a file if it has been modified.

    :param cache_info: dictionary to hold opaque cache.
    :param reload_func: optional function to be called with data when
                        file is reloaded due to a modification.

    :returns: data from file

    """
    mtime = os.path.getmtime(filename)
    if not cache_info or mtime != cache_info.get('mtime'):
        LOG.debug(_("Reloading cached file %s") % filename)
        with open(filename) as fap:
            cache_info['data'] = fap.read()
        cache_info['mtime'] = mtime
        if reload_func:
            reload_func(cache_info['data'])
    return cache_info['data']


def utcnow():
    """Overridable version of utils.utcnow."""
    if utcnow.override_time:
        return utcnow.override_time
    return datetime.datetime.utcnow()

utcnow.override_time = None


def tz_utc_to_local(utc):
    """
    Timezone switch, from utc to local
    @param:
        utc: datetime
    """
    # NOTE(hzyangtk): Change format of created_at from utc to local.
    to_zone = tz.tzlocal()
    if utc.tzinfo is None:
        from_zone = tz.tzutc()
        utc = utc.replace(tzinfo=from_zone)
    result = utc.astimezone(to_zone)
    return result


def datetime_to_timestamp(source_time):
    """include microseconds"""
    return long(time.mktime(source_time.timetuple()) * 1000)


def parse_strtime(timestr, fmt=PERFECT_TIME_FORMAT):
    """Turn a formatted time back into a datetime."""
    return datetime.datetime.strptime(timestr, fmt)


def strtime(at=None, fmt=PERFECT_TIME_FORMAT):
    """Returns formatted utcnow."""
    if not at:
        at = utcnow()
    return at.strftime(fmt)


def join_string(*args):
    return ''.join(args)


class Singleton(object):

    def __init__(self, cls):
        self._cls = cls
        self._inst = None

    def __call__(self, *args, **kwargs):
        '''
        Over __call__ method. So the instance of this class
        can be called as a function.
        '''
        if not self._inst:
            self._inst = self._cls(*args, **kwargs)
        return self._inst
