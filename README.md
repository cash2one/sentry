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