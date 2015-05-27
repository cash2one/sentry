import memcache
import datetime

from oslo.config import cfg

from sentry import cron
from sentry.db import api as dbapi
from sentry.alarm import api as alarm_api
from sentry.openstack.common import log as logging
from sentry.openstack.common import timeutils
from sentry.monitor import state as service_state

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

platform_watcher_opts = [
    cfg.BoolOpt("enabled", default=False,
                help="Whether enable platform status watcher."),
    cfg.ListOpt('memcached_servers',
                default=[],
                help='Memcached servers for caching instance heartbeat.'),
    cfg.IntOpt("watch_interval", default=60,
               help="The interval in seconds watching platform status."),
    cfg.IntOpt("service_abnormal_period", default=330,
               help="When service is abnormal during this period(seconds), "
               "then it's been taken as abnormal for platform watcher."),
    cfg.IntOpt("instance_abnormal_period", default=60,
               help="When instance is abnormal during this period(seconds), "
               "then it's been taken as abnormal for platform watcher."),
    cfg.IntOpt("status_expired_period", default=3600,
               help="When service or instance status is not been updated "
               "during this period(seconds), the status data "
               "should be deprecated."),
    cfg.BoolOpt("alarm_enabled", default=False,
                help="Whether to alarm platform abnormal."),
]
CONF.register_opts(platform_watcher_opts, 'platform_watcher')

SERVICE_STATE_ABNORMAL = 'abnormal'
SERVICE_STATE_NORMAL = 'normal'

VM_HEARTBEAT_ABNORMAL = 'abnormal'
VM_HEARTBEAT_NORMAL = 'normal'

VM_NETWORK_ABNORMAL = 'abnormal'
VM_NETWORK_NORMAL = 'normal'

VM_STATE_NORMAL = 'normal'
VM_STATE_HEARTBEAT_ABNORMAL = 'heartbeat_abnormal'
VM_STATE_NETWORK_ABNORMAL = 'network_abnormal'
VM_STATE_HEARTBEAT_NETWORK_ABNORMAL = 'heartbeat_network_abnormal'

NODE_STATE_NORMAL = 'normal'
NODE_STATE_SERVICE_ABNORMAL = 'service_abnormal'
NODE_STATE_VM_ABNORMAL = 'vm_abnormal'
NODE_STATE_SERVICE_VM_ABNORMAL = 'service_vm_abnormal'
NODE_STATE_NODE_ABNORMAL = 'node_abnormal'


class HostStateInfo(object):
    """
    A thin object contain entire Services and Vms state of a host.
    """
    def __init__(self, hostname):
        self.hostname = hostname

        # key is service binary name, egg. nova-compute
        # value is service state
        self.services = {}

        # key is vm uuid, value is vm state
        self.vms = {}
        self.state = None

    def __repr__(self):
        return "%s" % {"services": self.services,
                       "vms": self.vms,
                       "status": self.state}

    def add_service(self, binary, state):
        self.services[binary] = state

    def add_vm(self, uuid, state):
        self.vms[uuid] = state

    def update_state(self):
        services_num = {SERVICE_STATE_NORMAL: 0,
                        SERVICE_STATE_ABNORMAL: 0,
                        "total": 0}
        vms_num = {VM_STATE_NORMAL: 0,
                   VM_STATE_HEARTBEAT_ABNORMAL: 0,
                   VM_STATE_NETWORK_ABNORMAL: 0,
                   VM_STATE_HEARTBEAT_NETWORK_ABNORMAL: 0,
                   "total": 0}

        for s in self.services.keys():
            services_num["total"] += 1
            if self.services[s] == SERVICE_STATE_NORMAL:
                services_num[SERVICE_STATE_NORMAL] += 1
            else:
                services_num[SERVICE_STATE_ABNORMAL] += 1

        for vm in self.vms.keys():
            vms_num["total"] += 1
            if self.vms[vm] == VM_STATE_NORMAL:
                vms_num[VM_STATE_NORMAL] += 1
            elif self.vms[vm] == VM_STATE_HEARTBEAT_ABNORMAL:
                vms_num[VM_STATE_HEARTBEAT_ABNORMAL] += 1
            elif self.vms[vm] == VM_STATE_NETWORK_ABNORMAL:
                vms_num[VM_STATE_NETWORK_ABNORMAL] += 1
            elif self.vms[vm] == VM_STATE_HEARTBEAT_NETWORK_ABNORMAL:
                vms_num[VM_STATE_HEARTBEAT_NETWORK_ABNORMAL] += 1

        if (services_num[SERVICE_STATE_NORMAL] == services_num["total"]
                and vms_num[VM_STATE_NORMAL] == vms_num["total"]):
            self.state = NODE_STATE_NORMAL
        elif (services_num[SERVICE_STATE_NORMAL] == 0
                and vms_num[VM_STATE_NORMAL] == 0):
            self.state = NODE_STATE_NODE_ABNORMAL
        elif (services_num[SERVICE_STATE_ABNORMAL] != 0
              and vms_num[VM_STATE_NORMAL] == vms_num["total"]):
            self.state = NODE_STATE_SERVICE_ABNORMAL
        elif (services_num[SERVICE_STATE_ABNORMAL] == 0
                and vms_num[VM_STATE_NORMAL] != vms_num["total"]):
            self.state = NODE_STATE_VM_ABNORMAL
        else:
            self.state = NODE_STATE_SERVICE_VM_ABNORMAL


class PlatformWatcherManager(object):

    def __init__(self):
        self.memcache_client = memcache.Client(
            CONF.platform_watcher.memcached_servers)
        self.alarm_api = alarm_api.AlarmAPI()

        # key is hostname, value is HostStateInfo(hostname)
        self.status = {}

    def __repr__(self):
        return "%s" % self.status

    def _get_all_service_status(self):

        db_services = dbapi.service_status_get_all().all()
        for s in db_services:
            state = SERVICE_STATE_NORMAL
            if (s.state != service_state.CHECK_OK
                  or timeutils.is_older_than(
                  timeutils.tz_local_to_utc(s.updated_at).replace(tzinfo=None),
                  CONF.platform_watcher.service_abnormal_period)):
                state = SERVICE_STATE_ABNORMAL

            if s.hostname not in self.status.keys():
                self.status.update({s.hostname: HostStateInfo(s.hostname)})
            self.status[s.hostname].add_service(s.binary, state)

    def _get_instance_list_by_host(self, host):
        return self.memcache_client.get(host).get('uuids', [])

    def _get_instance_network_status(self, uuid):
        db_ins = dbapi.instance_network_status_get_all(
            search_dict={'uuid': uuid}).all()
        if len(db_ins) != 0:
            return VM_NETWORK_ABNORMAL
        return VM_NETWORK_NORMAL

    def _get_instance_heartbeat_status(self, uuid):
        status = VM_HEARTBEAT_ABNORMAL

        cache_key = str(uuid + '_heart')
        cache_value = self.memcache_client.get(cache_key)
        if cache_value:
            last_heartbeat = datetime.datetime.strptime(
                cache_value, '%Y-%m-%d %H:%M:%S')
            interval = CONF.platform_watcher.instance_abnormal_period
            if not timeutils.is_older_than(last_heartbeat, interval):
                status = VM_HEARTBEAT_NORMAL

        return status

    def _get_instance_status(self, uuid):
        heartbeat_status = self._get_instance_heartbeat_status(uuid)
        network_status = self._get_instance_network_status(uuid)
        if (heartbeat_status == VM_HEARTBEAT_NORMAL
                and network_status == VM_NETWORK_NORMAL):
            return VM_STATE_NORMAL
        elif (heartbeat_status == VM_HEARTBEAT_ABNORMAL
                  and network_status == VM_NETWORK_NORMAL):
            return VM_STATE_HEARTBEAT_ABNORMAL
        elif (heartbeat_status == VM_HEARTBEAT_NORMAL
                  and network_status == VM_NETWORK_ABNORMAL):
            return VM_STATE_NETWORK_ABNORMAL
        elif (heartbeat_status == VM_HEARTBEAT_ABNORMAL
                  and network_status == VM_NETWORK_ABNORMAL):
            return VM_STATE_HEARTBEAT_NETWORK_ABNORMAL

    def _update_platform_vms_status(self):
        # update all vms status by host
        for host in self.status.keys():
            for uuid in self._get_instance_list_by_host(str(host)):
                instance_status = self._get_instance_status(uuid)
                self.status[host].add_vm(uuid, instance_status)

    def _update_platform_host_status(self):
        for host in self.status.keys():
            self.status[host].update_state()

    def _update_platform_status_db(self):
        for host in self.status.keys():
            dbapi.platform_status_create_or_update(host, "node", host,
                                                   self.status[host].state)

            dbapi.platform_status_bulk_create_or_update(host, "service",
                                                self.status[host].services)

            dbapi.platform_status_bulk_create_or_update(host, "vm",
                                                self.status[host].vms)

    def send_alarm(self):
        now = timeutils.strtime(timeutils.local_now())

        # NOTE(): abnormal_vms:
        abnormal_vms = {"updated_at": now}
        abnormal_services = {"updated_at": now}
        abnormal_nodes = {"updated_at": now}

        for host in self.status.keys():
            if self.status[host].state == NODE_STATE_NODE_ABNORMAL:
                abnormal_nodes.update({host: NODE_STATE_NODE_ABNORMAL})
            elif self.status[host].state == NODE_STATE_SERVICE_ABNORMAL:
                for s in self.status[host].services.keys():
                    if self.status[host].services[s] == SERVICE_STATE_ABNORMAL:
                        if host not in abnormal_services.keys():
                            abnormal_services[host] = {}
                        abnormal_services[host].update({s:
                                                    SERVICE_STATE_ABNORMAL})
            elif self.status[host].state == NODE_STATE_VM_ABNORMAL:
                for vm in self.status[host].vms.keys():
                    if self.status[host].vms[vm] != VM_STATE_NORMAL:
                        if host not in abnormal_vms.keys():
                            abnormal_vms[host] = {}
                        abnormal_vms[host].update({vm:
                                                   self.status[host].vms[vm]})
            elif self.status[host].state == NODE_STATE_SERVICE_VM_ABNORMAL:
                for s in self.status[host].services.keys():
                    if self.status[host].services[s] == SERVICE_STATE_ABNORMAL:
                        if host not in abnormal_services.keys():
                            abnormal_services[host] = {}
                        abnormal_services[host].update({s:
                                                    SERVICE_STATE_ABNORMAL})
                for vm in self.status[host].vms.keys():
                    if self.status[host].vms[vm] != VM_STATE_NORMAL:
                        if host not in abnormal_vms.keys():
                            abnormal_vms[host] = {}
                        abnormal_vms[host].update({vm:
                                                   self.status[host].vms[vm]})

        LOG.info("abnormal_vms: %s" % abnormal_vms)
        LOG.info("abnormal_services: %s" % abnormal_services)
        LOG.info("abnormal_nodes: %s" % abnormal_nodes)

        if len(abnormal_nodes) != 1:
            self.alarm_api.alarm_nodes_abnormal(abnormal_nodes)
        if len(abnormal_services) != 1:
            self.alarm_api.alarm_services_abnormal(abnormal_services)
        if len(abnormal_vms) != 1:
            self.alarm_api.alarm_vms_abnormal(abnormal_vms)

    def process(self):

        # get all service status
        self._get_all_service_status()
        # get all vms status by host
        self._update_platform_vms_status()
        self._update_platform_host_status()
        LOG.info("platform_status: %s" % self.status)

        if CONF.platform_watcher.alarm_enabled:
            self.send_alarm()

        self._update_platform_status_db()
        self.clean_expired_platform_status()

    def clean_expired_platform_status(self):
        delta = CONF.platform_watcher.status_expired_period
        old_time = timeutils.local_now() - datetime.timedelta(seconds=delta)
        db_platform = dbapi.platform_status_get_by_updated_at(old_time)
        LOG.info("Clean expired platform status: %s" % db_platform.all())
        db_platform.delete()


@cron.cronjob(CONF.platform_watcher.watch_interval)
def watch_platform_status():
    if CONF.platform_watcher.enabled:
        LOG.info("Start to Watch platform status.")
        pw = PlatformWatcherManager()
        pw.process()
