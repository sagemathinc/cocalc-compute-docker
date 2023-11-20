#!/usr/bin/env bash

set -ev

source /cocalc/start-env.sh


# Install ssh keys into cache for user account, so they will be there
# in the union mount.
mkdir -p $UNIONFS_UPPER/.ssh
cp -v /cocalc/conf/authorized_keys $UNIONFS_UPPER/.ssh/authorized_keys

# This directory could be anywhere.
mkdir -p $UNIONFS_UPPER/.compute-server/

# Setting it enabled read tracking at the websocketfs level,
# which is then used by our caching level using unionfs to automatically keep
# files locally when they are read, so future reads are fast and free.
export READ_TRACKING_FILE=$UNIONFS_UPPER/.compute-server/read-tracking
echo "" > $READ_TRACKING_FILE

# WARNING/DANGER! This must match with what is done in
#    cocalc/src/packages/sync-fs/lib/handle-api-call.ts
# or the filesystem will "silently" become 1000x slower...
export METADATA_FILE=$UNIONFS_LOWER/.compute-servers/$COMPUTE_SERVER_ID/meta/meta.lz4

cd /cocalc/src/compute/compute

# Make sure filesystems aren't mounted
umount $UNIONFS_LOWER  2>/dev/null || true
umount $PROJECT_HOME   2>/dev/null || true
fusermount -uz $UNIONFS_LOWER  2>/dev/null || true
fusermount -uz $PROJECT_HOME   2>/dev/null || true

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