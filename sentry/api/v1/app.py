from sentry.api import bottle
from sentry.openstack.common import jsonutils

app = bottle.Bottle(autojson=False)
app.install(bottle.JSONPlugin(jsonutils.dumps))
