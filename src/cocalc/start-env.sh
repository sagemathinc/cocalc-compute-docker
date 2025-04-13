#!/usr/bin/env bash

set -ev

# Setup env vars about project we will connect to.

# Where to store logs
export LOGS='/tmp/logs'

# The api key that grants access to the project
export API_KEY=`cat /cocalc/conf/api_key`

# The cocalc web server
export API_SERVER=`cat /cocalc/conf/api_server`

# The project to connect to
export PROJECT_ID=`cat /cocalc/conf/project_id`
export COCALC_PROJECT_ID=`cat /cocalc/conf/project_id`

# The numerical id of the compute server
export COMPUTE_SERVER_ID=`cat /cocalc/conf/compute_server_id`

# Disable Jupyter Pool -- it may be buggy/broken or just not necessary with
# compute servers, which are much faster.
# See https://github.com/sagemathinc/cocalc/issues/7529
export COCALC_JUPYTER_POOL_SIZE=0

# Directories that are excluded from sync, i.e., fast local data directories
export EXCLUDE_FROM_SYNC=`cat /cocalc/conf/exclude_from_sync`

# Debug flag which impacts how intense the logging of the filesystem and compute containers is
export DEBUG=$(test -f /cocalc/conf/debug && cat /cocalc/conf/debug || echo "")

# Local cache files used by unionfs-fuse
export UNIONFS_UPPER=/data/.cache

# Where websocketfs is mounted
export UNIONFS_LOWER=/data/.websocketfs

# Where user home directory is mounted
export PROJECT_HOME=/home/user

# websocketfs cach timeout in seconds -- keep small, but not zero.
# if zero, then using nvcc is very slow and ls is very slow.
export WEBSOCKETFS_CACHE_TIMEOUT=7

# For images that use an https proxy server
export PROXY_PORT=443
export PROXY_HOSTNAME=0.0.0.0
export PROXY_AUTH_TOKEN_FILE=/cocalc/conf/auth_token

# Make the cocalc version of nodejs available.
# this is VERY verbose hence "set +v"
set +v
# Usually /cocalc/nvm/ is installed
if [ -f /cocalc/nvm/nvm.sh ]; then
    NVM_DIR=/cocalc/nvm source /cocalc/nvm/nvm.sh
else
    # In some testing situations we only have /nvm
    if [ -f /nvm/nvm.sh ]; then
        NVM_DIR=/nvm source /nvm/nvm.sh
    fi
fi;
set -v

