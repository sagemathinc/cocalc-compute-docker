#!/usr/bin/env bash

set -ev

# Setup env vars about project we will connect to.

# avoid possible confusion
unset COCALC_PROJECT_ID

# Where to tstore logs
export LOGS='/tmp/logs'

# The api key that grants access to the project
export API_KEY=`cat /cocalc/conf/api_key`

# The cocalc web server
export API_SERVER=`cat /cocalc/conf/api_server`

# The project to connect to
export PROJECT_ID=`cat /cocalc/conf/project_id`

# The numerical id of the compute server
export COMPUTE_SERVER_ID=`cat /cocalc/conf/compute_server_id`

# Directories that are excluded from sync, i.e., fast local data directories
export EXCLUDE_FROM_SYNC=`cat /cocalc/conf/exclude_from_sync`

# Debug flag which impacts how intense the logging of the filesystem and compute containers is
export DEBUG=$(test -f /cocalc/conf/debug && cat /cocalc/conf/debug || echo "")

# Local cache files used by unionfs-fuse
export UNIONFS_UPPER=/data/.cache

# Where websocketfs is mounted
export UNIONFS_LOWER=/data/.websocketf

# Where user home directory is mounted
export PROJECT_HOME=/home/user

# websocketfs cach timeout in seconds -- keep small, but not zero.
# if zero, then using nvcc is very slow and ls is very slow.
export WEBSOCKETFS_CACHE_TIMEOUT=3

# Make the cocalc version of nodejs available.
# this is VERY verbose hence "set +v"
set +v
NVM_DIR=/cocalc/nvm source /cocalc/nvm/nvm.sh
set -v

