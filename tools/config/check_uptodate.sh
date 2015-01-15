#!/bin/sh
TEMPDIR=`mktemp -d`
CFGFILE=sentry.conf.sample
tools/config/generate_sample.sh -b ./ -p sentry -o $TEMPDIR
if ! diff $TEMPDIR/$CFGFILE etc/sentry/$CFGFILE
then
    echo "E: tempest.conf.sample is not up to date, please run:"
    echo "tools/generate_sample.sh"
    exit 42
fi
