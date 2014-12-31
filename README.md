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

## nova

nova.conf
```
    [DEFAULT]
    notify_api_faults=true
    notify_on_state_change=vm_and_task_state
    notification_driver=nova.openstack.common.notifier.rpc_notifier
```
