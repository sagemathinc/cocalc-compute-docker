#!/usr/bin/env bash

set -ev

source /cocalc/start-env.sh

# This directory could be anywhere.
mkdir -p $UNIONFS_UPPER/.compute-server/

# Setting it enabled read tracking at the websocketfs level,
# which is then used by our caching level using unionfs to automatically keep
# files locally when they are read, so future reads are fast and free.
export READ_TRACKING_PATH=$UNIONFS_UPPER/.compute-server/read-tracking
echo "" > $READ_TRACKING_PATH

export METADATA_FILE=$UNIONFS_UPPER/.compute-server/meta/meta.lz4

cd /cocalc/src/compute/compute

# Make sure filesystems aren't mounted

umount $UNIONFS_LOWER  2>/dev/null || true
umount $PROJECT_HOME   2>/dev/null || true

if [[ -z "$UNIONFS_UPPER" ]]; then
    # unionfs not configured at all.
    node ./start-filesystem.js
    exit $?
fi

# We are using unionfs.  We can't run the websocketetfs FUSE filesystem
# in the same process as the unionfs cache that makes a websocket connection
# to the project, since this leads to deadlock, at least in docker.
# So we start start-filesystem.js twice, once with unionfs (which doesn't
# mount websocketfs),  and the second time with *just* websocketfs.

mkdir -p /tmp/logs

# process that runs unionfs
exec node ./start-filesystem.js 2>&1 > /tmp/logs/unionfs.log &

# process that runs just websocketfs to mount $UNIONFS_LOWER
export PROJECT_HOME=$UNIONFS_LOWER
unset UNIONFS_UPPER
unset UNIONFS_LOWER
exec node ./start-filesystem.js  2>&1 > /tmp/logs/websocketfs.log &

tail -F /tmp/logs/unionfs.log  /tmp/logs/websocketfs.log