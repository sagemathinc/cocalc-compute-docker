#!/usr/bin/env bash
set -v

export SERVICE_ACCOUNT=/secrets/google-service-account.json
export BUCKET=compute-server-storage-2
export COMPUTE_SERVER_ID=3767
export MOUNT=/home/user/jfs

df $MOUNT | grep $MOUNT | grep JuiceFS:jfs

if [ $? -eq 0 ]; then
    set -e
    # it is mounted
    while ! fusermount -u $MOUNT
    do
       echo "Waiting 1s..."
       sleep 1
    done
    echo "Successfully unmounted $MOUNT"
    set +e
fi

if [ -f /var/run/keydb/keydb-server.pid ]; then
    kill `cat /var/run/keydb/keydb-server.pid` || true
fi

sleep 1

df /bucket | grep /bucket

if [ $? -eq 0 ]; then
    set -e
    while ! fusermount -u /bucket
    do
       echo "Waiting 1s..."
       sleep 1
    done
    echo "Successfully unmounted /bucket"
    set +e
fi
