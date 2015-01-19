from oslo.config import cfg
from sentry.api import utils

CONF = cfg.CONF
CONF.import_opt('listen_port', 'sentry.api', 'api')
CONF.import_opt('listen_host', 'sentry.api', 'api')
app = utils.create_bottle_app()


@app.route('/')
def index():
    return {
        "versions": {
            "values": [{
                "id": "v1",
                "links": [{
                    "href": "http://%(host)s:%(port)s/v1/" %
                    {'host': CONF.api.listen_host,
                     'port': CONF.api.listen_port},
                    "rel": "self"
                }],
                "status": "stable",
                "updated": "2015-01-19T00:00:00Z"
            }]
        }
    }
