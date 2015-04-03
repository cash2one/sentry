# -*- coding:utf8 -*-
from datetime import datetime

from sentry import marvel
from sentry.db import api as dbapi
from sentry.common import exception

_ENGINE = None
CACHE_AGE = 10


def cache(function):
    """The cache wrapper for get_config() method."""
    def inner(*args, **kwargs):
        obj_self = args[0]
        key = args[1]
        cached = getattr(obj_self, 'cached', {})

        (value, updated_at) = cached.get(key, (None, None))

        if (not value is None and not updated_at is None):
            delta = datetime.now() - updated_at
            if delta.seconds <= CACHE_AGE:
                return value

        # Access database to get date
        value = function(*args, **kwargs)
        now = datetime.now()
        cached[key] = (value, now)
        return value

    return inner


class Config(object):

    def __init__(self, name, default_value, secret=False):
        self.name = name
        self.default_value = default_value
        self.secret = secret
        self._value = None

    def load(self, value):
        self._value = value

    @property
    def value(self):
        if self._value is not None:
            return self._value
        else:
            return self.default_value


class ConfigEngine(object):
    """A Config engine who get/set config items from/to database.

    Before using a config item, you should register it. An item can
    not be registered twice.
    """

    def __init__(self):
        self.configs = {}
        self.cached = {}

    def register(self, config):
        key = config.name
        if key in self.configs.keys():
            raise exception.ConfigDuplicated(name=key)

        self.configs[key] = config

    @cache
    def get_config(self, key):
        """Get config from database, if not in database, initiate with default
        value."""
        self._validate_key(key)
        default = self.configs[key]

        db_key = dbapi.config_get_by_key(key)
        if db_key is None:
            self.set_config(key, default.default_value)
        else:
            default.load(db_key.value)

        return default.value

    def _validate_key(self, key):
        if key not in self.configs.keys():
            raise exception.ConfigNotFound(name=key)

    def set_config(self, key, value):
        self._validate_key(key)
        return dbapi.config_set(key, value)

    def keys(self):
        return self.configs.keys()

    def iteritems(self, hide_secret=True):
        for key, config in self.configs.iteritems():
            if config.secret:
                value = '******'
            else:
                value = self.get_config(key)
            yield key, value

    def items(self, hide_secret=True):
        return dict(
            [(key, value) for (key, value) in self.iteritems(hide_secret)]
        )


def _engine():
    global _ENGINE
    if not _ENGINE:
        _ENGINE = ConfigEngine()
    return _ENGINE


def get_config(key):
    return _engine().get_config(key)


def register_configs(configs):
    for config in configs:
        _engine().register(config)


def set_config(key, value):
    return _engine().set_config(key, value)


def keys():
    return _engine().keys()


def items():
    return _engine().items()


# Please setting all default config here
CONFIG = [
    Config('smtp_host', ''),
    Config('smtp_ssl', True),
    Config('smtp_username', ''),
    Config('smtp_password', '', secret=True),
    Config('alarm_receivers', ['hzgaott@corp.netease.com']),
    Config('env_name', marvel.pick_up()),
]

PF_CONFIGS = [
    Config('pf_prefix', 'http://admin.cloud-dev.netease.com'),
    Config('pf_uri', 'ops/service#/m/exlogs/detail/?id='),
]

register_configs(CONFIG)
register_configs(PF_CONFIGS)
