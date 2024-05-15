#!/usr/bin/env bash
set -ev

./check-env.sh

if $MOUNT | grep $MOUNT | grep JuiceFS:jfs; then
    # it is mounted
    while ! fusermount -u $MOUNT
    do
       echo "Waiting 1s..."
       sleep 1
    done
    echo "Successfully unmounted $MOUNT"
fi

if [ -f /var/run/keydb/keydb-server.pid ]; then
    kill `cat /var/run/keydb/keydb-server.pid` || true
fi

sleep 1

if df /bucket | grep /bucket; then
    while ! fusermount -u /bucket
    do
       echo "Waiting 1s..."
       sleep 1
    done
    echo "Successfully unmounted /bucket"
fi
