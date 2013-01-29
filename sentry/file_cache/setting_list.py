#
#    Created on 2012-10-30
#
#    @author: hzyangtk@corp.netease.com
#

import os

from sentry.common import exception
from sentry.common import utils
from sentry.openstack.common import cfg
from sentry.openstack.common import jsonutils


setting_list_opts = [
    cfg.StrOpt('setting_list_file',
               default='setting_list.json',
               help='JSON file representing setting list contents'),
    ]


FLAGS = cfg.CONF
FLAGS.register_opts(setting_list_opts)

_SETTING_LIST_PATH = None
_SETTING_LIST_CACHE = {}
_SETTING_LIST_DICT = {}


def reset():
    global _SETTING_LIST_PATH
    global _SETTING_LIST_CACHE
    _SETTING_LIST_PATH = None
    _SETTING_LIST_CACHE = {}


def init():
    global _SETTING_LIST_PATH
    global _SETTING_LIST_CACHE
    if not _SETTING_LIST_PATH:
        _SETTING_LIST_PATH = FLAGS.setting_list_file
        if not os.path.exists(_SETTING_LIST_PATH):
            _SETTING_LIST_PATH = FLAGS.find_file(_SETTING_LIST_PATH)
        if not _SETTING_LIST_PATH:
            raise exception.ConfigNotFound(path=FLAGS.setting_list_file)
    utils.read_cached_file(_SETTING_LIST_PATH, _SETTING_LIST_CACHE,
                           reload_func=_load_setting_list)


def _load_setting_list(data):
    global _SETTING_LIST_DICT
    try:
        _SETTING_LIST_DICT = jsonutils.loads(data)
    except ValueError:
        raise exception.Invalid()


def get_setting_list():
    global _SETTING_LIST_DICT
    init()
    return _SETTING_LIST_DICT
