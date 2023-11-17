#!/usr/bin/env bash

set -ev

# Setup env vars about project we will connect to.

unset COCALC_PROJECT_ID
export LOGS='/tmp/logs'
export API_KEY=`cat /cocalc/conf/api_key`
export API_SERVER=`cat /cocalc/conf/api_server`
export PROJECT_ID=`cat /cocalc/conf/project_id`
export COMPUTE_SERVER_ID=`cat /cocalc/conf/compute_server_id`
export EXCLUDE_FROM_SYNC=`cat /cocalc/conf/exclude_from_sync`
export DEBUG=$(test -f /cocalc/conf/debug && cat /cocalc/conf/debug || echo "")
export UNIONFS_UPPER=/data/.cache
export UNIONFS_LOWER=/data/.websocketfs
export PROJECT_HOME=/home/user

# Make the cocalc version of nodejs available.
# this is VERY verbose hence "set +v"
set +v
NVM_DIR=/cocalc/nvm source /cocalc/nvm/nvm.sh
set -v

# if there is a compute image specific init script, source it
if [ -f /cocalc-compute-init.sh ]; then
    source /cocalc-compute-init.sh
fi
