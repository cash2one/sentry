import os
import functools

from sentry.api import bottle
from sentry import config

template_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),  # alarm directory
    'templates',
)


# Using bottle template mechanism, by setting lookup to ``templates``
template = functools.partial(bottle.template,
                             template_lookup=[template_path])


ERROR_LOG_TEMPLATE = 'errorlog.html'


def render_exception(exc_detail):

    environment = config.get_config('env_name')

    host = config.get_config('pf_prefix')
    uri = config.get_config('pf_uri') + str(exc_detail.uuid)
    pf_url = '%s/%s' % (host, uri)

    return template(
        ERROR_LOG_TEMPLATE,
        exception=exc_detail,
        environment=environment,
        pf_url=pf_url,
    )
