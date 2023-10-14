#!/usr/bin/env bash

set -ev

# Setup env vars about project we will connect to.

export API_KEY=`cat /cocalc/conf/api_key`
export API_SERVER=`cat /cocalc/conf/api_server`
export PROJECT_ID=`cat /cocalc/conf/project_id`
export COMPUTE_SERVER_ID=`cat /cocalc/conf/compute_server_id`
export HOSTNAME=`cat /cocalc/conf/hostname`

