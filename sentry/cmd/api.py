import sys

from sentry import api
from sentry.common import config
from sentry.openstack.common import log


def main():
    config.parse_args(sys.argv[1:])
    log.setup('sentry')
    api.run()
