Sentry(NVS Alarm System)
=======
Support for all the systems need to alarm.
Sentry will listen to MQ to catch notifications,
Then will filter the notifications and send alarm
to manage-platform.


Setup
======
    download sentry
    cd sentry

    # For first time:
    run install.sh

    # Reinstall:
    pip uninstall sentry
    pip install .

Openstack setup
================

## nova.conf
```
[DEFAULT]
notify_api_faults=true
notify_on_state_change=vm_and_task_state
notification_driver=nova.openstack.common.notifier.rpc_notifier
```

## glance-api.conf
Note that: Havana glance was not based on 
openstack.common.notifier (oslo.messaging). So it not support HA-rabbitMQ.

```
[DEFAULT]
rabbit_notification_topic = glance_notifications
```

## neutron.conf
```
[DEFAULT]
notification_driver=neutron.openstack.common.notifier.rpc_notifier
notification_topics=neutron_notifications
```

## cinder.conf
```
[DEFAULT]
notification_driver=cinder.openstack.common.notifier.rpc_notifier
notification_topics=cinder_notifications
```

Error aggregation
=================

Sentry collects OpenStack errors from message bus. And it subscribes to a
oelist(OpenStack Error list) which contains a black list error, Sentry
will automatic mark errors in the oelist to on_process, so users will no
longer receive email alarm and not see the error in cloud admin page.
