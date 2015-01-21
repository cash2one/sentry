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

import sys
import os

from alembic import command as alembic_command
from alembic import config as alembic_config
from alembic import util as alembic_util

from oslo.config import cfg

from sentry.common import config
from sentry.db.sqlalchemy import session
from sentry.openstack.common import log as logging


CONF = cfg.CONF


def do_alembic_command(config, cmd, *args, **kwargs):
    try:
        getattr(alembic_command, cmd)(config, *args, **kwargs)
    except alembic_util.CommandError as e:
        alembic_util.err(str(e))


def do_upgrade_downgrade(config, cmd):
    if not CONF.command.revision and not CONF.command.delta:
        raise SystemExit('You must provide a revision or relative delta')

    revision = CONF.command.revision

    if CONF.command.delta:
        sign = '+' if CONF.command.name == 'upgrade' else '-'
        revision = sign + str(CONF.command.delta)
    else:
        revision = CONF.command.revision

    do_alembic_command(config, cmd, revision, sql=CONF.command.sql)


def do_stamp(config, cmd):
    do_alembic_command(config, cmd,
                       CONF.command.revision,
                       sql=CONF.command.sql)


def do_revision(config, cmd):
    do_alembic_command(config, cmd,
                       message=CONF.command.message,
                       autogenerate=CONF.command.autogenerate,
                       sql=CONF.command.sql)


def do_shell(config, cmd):
    try:
        import IPython
        IPython.embed()
    except ImportError:
        import code
        code.interact()


def add_command_parsers(subparsers):
    for name in ['current', 'history', 'branches']:
        parser = subparsers.add_parser(name)
        parser.set_defaults(func=do_alembic_command)

    for name in ['upgrade', 'downgrade']:
        parser = subparsers.add_parser(name)
        parser.add_argument('--delta', type=int)
        parser.add_argument('--sql', action='store_true')
        parser.add_argument('revision', nargs='?')
        parser.set_defaults(func=do_upgrade_downgrade)

    parser = subparsers.add_parser('stamp')
    parser.add_argument('--sql', action='store_true')
    parser.add_argument('revision')
    parser.set_defaults(func=do_stamp)

    parser = subparsers.add_parser('revision')
    parser.add_argument('-m', '--message')
    parser.add_argument('--autogenerate', action='store_true')
    parser.add_argument('--sql', action='store_true')
    parser.set_defaults(func=do_revision)

    parser = subparsers.add_parser('shell')
    parser.set_defaults(func=do_shell)


command_opt = cfg.SubCommandOpt('command',
                                title='Command',
                                help=('Available commands'),
                                handler=add_command_parsers)

CONF.register_cli_opt(command_opt)
CONF.register_opts([])


def main():
    config.parse_args(sys.argv[1:])
    logging.setup('sentry')
    configx = alembic_config.Config(
         os.path.join(os.path.abspath(os.path.dirname(session.__file__)),
                      'alembic', 'alembic.ini')
    )
    configx.set_main_option('script_location', 'sentry.db.sqlalchemy:alembic')
    configx.set_main_option('sqlalchemy.url', CONF.sql_connection)
    CONF.command.func(configx, CONF.command.name)
