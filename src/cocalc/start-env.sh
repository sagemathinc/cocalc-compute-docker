#!/usr/bin/env bash

set -ev

# Setup env vars about project we will connect to.

unset COCALC_PROJECT_ID
export LOGS='/tmp/logs'
export API_KEY=`cat /cocalc/conf/api_key`
export API_SERVER=`cat /cocalc/conf/api_server`
export PROJECT_ID=`cat /cocalc/conf/project_id`
export COMPUTE_SERVER_ID=`cat /cocalc/conf/compute_server_id`
export DEBUG=$(test -f /cocalc/conf/debug && cat /cocalc/conf/debug || echo "")
export UNIONFS_UPPER=/home/unionfs/upper
export UNIONFS_LOWER=/home/unionfs/lower
export PROJECT_HOME=/home/user

sudo hostname `cat /cocalc/conf/hostname`
echo "127.0.0.1 `cat /cocalc/conf/hostname`" | sudo tee -a /etc/hosts