#!/bin/bash

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi

CONF_DIR=/etc/sentry
LOG_DIR=/var/log/sentry

mkdir -p $LOG_DIR
chown nova:nova $LOG_DIR
mkdir -p $CONF_DIR
cp etc/sentry/* $CONF_DIR -vr
chown nova:nova $CONF_DIR -R

chmod 755 tools/sentry
chmod 755 tools/sentry-api
cp tools/sentry /etc/init.d/
cp tools/sentry-api /etc/init.d/

pip install .
