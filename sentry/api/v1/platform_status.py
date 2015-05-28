from sentry.api.v1.app import route
from sentry.db import api as dbapi


def format_platform_status(db_platform_status):
    result = {"platform_status": []}
    platform_status = {}
    for item in db_platform_status:
        if item.hostname not in platform_status.keys():
            platform_status[item.hostname] = {"vms": {}, "services": {},
                                              "status": None,
                                              "updated_at": None}
        if item.item_type == 'node':
            platform_status[item.hostname]["status"] = item.state
            platform_status[item.hostname]["updated_at"] = item.updated_at
        elif item.item_type == 'service':
            platform_status[item.hostname]["services"].update({item.item_name:
                                                               item.state})
        elif item.item_type == 'vm':
            platform_status[item.hostname]["vms"].update({item.item_name:
                                                          item.state})
    for host in platform_status.keys():
        ps = {}
        ps.update({"hostname": host})
        ps.update({"state": platform_status[host]["status"]})
        ps.update({"updated_at": platform_status[host]["updated_at"]})
        ps.update({"services": []})
        ps.update({"vms": []})
        for vm in platform_status[host]["vms"].keys():
            ps["vms"].append({vm: platform_status[host]["vms"][vm]})
        for s in platform_status[host]["services"].keys():
            ps["services"].append({s: platform_status[host]["services"][s]})
        result["platform_status"].append(ps)

    return result


@route('/platform_status')
def index():
    db_query = dbapi.platform_status_get_all()
    return format_platform_status(db_query)
