#!/usr/bin/env python
# -*- coding: utf8 -*-

#
#          The Animal Protects No Bug
#               ~~~      ~~~
#             __| |______| |__```
#            |                |
#            |                | ````
#            |     `````      | ```````
#            |   ████--████   | `````
#            |                | ```
#            |      _[_       |
#            |                |
#            |____        ____|
#                 |      |
#                 |      |
#                 |      |  `
#                 |      |  `
#                 |      |  ```
#                 |      |  ```
#                 |      |   `````
#                 |      |   ```````
#                 |      |__________````
#                 |                 |__``
#                 |                 |__|```
#                 |_________________|
#                   | | |   | | |
#                   |`|`|   |`|`|
#                   |_|_|   |_|_|          -gtt116
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
NVS Alarm module
"""

import os
import sys
import traceback


# If ../sentry/__init__.py exists, add ../ to Python search path, so that
# it will override what happens to be installed in /usr/(local/)lib/python...
possible_topdir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                   os.pardir, os.pardir))
if os.path.exists(os.path.join(possible_topdir, 'sentry', '__init__.py')):
    sys.path.insert(0, possible_topdir)

import logging as std_logging
from oslo.config import cfg

from sentry.common import config
from sentry.controller import manager
from sentry.openstack.common import log
from sentry.openstack.common.rpc import impl_kombu  # noqa

LOG = log.getLogger(__name__)
CONF = cfg.CONF


def fail(returncode, e):
    sys.stderr.write("ERROR: %s\n" % e)
    sys.stderr.write(traceback.format_exc())
    sys.exit(returncode)


def main():
    try:
        config.parse_args(sys.argv[1:])
        log.setup('sentry')

        mgr = manager.Manager()
        # After manager instantiated, some handler will be imported
        CONF.log_opt_values(LOG, std_logging.DEBUG)
        server = mgr.create()
        server.wait()
    except KeyboardInterrupt as ex:
        sys.stderr.write("Receive terminate signal, exit.\n")
        sys.exit(0)
    except Exception as ex:
        fail(1, ex)
