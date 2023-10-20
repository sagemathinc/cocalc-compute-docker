#!/usr/bin/env bash

set -ev

export PATH=/cocalc/nvm/versions/node/v18.17.1/bin/:$PATH

source /cocalc/start-env.sh
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