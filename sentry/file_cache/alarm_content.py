#
#    Created on 2012-10-30
#
#    @author: hzyangtk@corp.netease.com
#

import os

from sentry.common import exception
from sentry.common import utils
from oslo.config import cfg
from sentry.openstack.common import jsonutils


alarm_content_opts = [
    cfg.StrOpt('alarm_content_file',
               default='alarm_content.json',
               help='JSON file representing different type alarm contents'),
    ]


FLAGS = cfg.CONF
FLAGS.register_opts(alarm_content_opts)

_ALARM_CONTENT_PATH = None
_ALARM_CONTENT_CACHE = {}
_ALARM_CONTENT_DICT = {}


def reset():
    global _ALARM_CONTENT_PATH
    global _ALARM_CONTENT_CACHE
    _ALARM_CONTENT_PATH = None
    _ALARM_CONTENT_CACHE = {}


def init():
    global _ALARM_CONTENT_PATH
    global _ALARM_CONTENT_CACHE
    if not _ALARM_CONTENT_PATH:
        _ALARM_CONTENT_PATH = FLAGS.alarm_content_file
        if not os.path.exists(_ALARM_CONTENT_PATH):
            _ALARM_CONTENT_PATH = FLAGS.find_file(_ALARM_CONTENT_PATH)
        if not _ALARM_CONTENT_PATH:
            raise exception.ConfigNotFound(path=FLAGS.alarm_content_file)
    utils.read_cached_file(_ALARM_CONTENT_PATH, _ALARM_CONTENT_CACHE,
                           reload_func=_load_alarm_content)


def _load_alarm_content(data):
    global _ALARM_CONTENT_DICT
    try:
        _ALARM_CONTENT_DICT = jsonutils.loads(data)
    except ValueError:
        raise exception.Invalid()


def get_alarm_content():
    global _ALARM_CONTENT_DICT
    init()
    return _ALARM_CONTENT_DICT
