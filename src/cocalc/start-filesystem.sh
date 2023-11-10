#!/usr/bin/env bash

set -ev

source /cocalc/start-env.sh

# This directory could be anywhere.  Setting it enabled read tracking at the websocketfs level,
# which is then used by our caching level using unionfs to automatically keep
# files locally when they are read, so future reads are fast and free.
mkdir -p /home/unionfs/upper/.compute-server/
export READ_TRACKING_PATH=/home/unionfs/upper/.compute-server/read-tracking
echo "" > $READ_TRACKING_PATH

cd /cocalc/src/compute/compute

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

# process that runs just websocketfs to mount /home/unionfs/lower
export PROJECT_HOME=$UNIONFS_LOWER
unset UNIONFS_UPPER
unset UNIONFS_LOWER
exec node ./start-filesystem.js  2>&1 > /tmp/logs/websocketfs.log &

tail -F /tmp/logs/unionfs.log  /tmp/logs/websocketfs.log