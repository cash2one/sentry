import sys
import traceback

from sentry import api
from sentry.common import config
from sentry.openstack.common import log


def fail(returncode, e):
    sys.stderr.write("ERROR: %s\n" % e)
    sys.stderr.write(traceback.format_exc())
    sys.exit(returncode)


def main():
    try:
        config.parse_args(sys.argv[1:])
        log.setup('sentry')
        api.run()
    except KeyboardInterrupt as ex:
        sys.stderr.write("Receive terminate signal, exit.\n")
        sys.exit(0)
    except Exception as ex:
        fail(1, ex)
