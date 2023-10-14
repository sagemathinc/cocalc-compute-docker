#!/usr/bin/env bash

set -ev

export PATH=/cocalc/nvm/versions/node/v18.17.1/bin/:$PATH

export API_KEY=`cat /cocalc/conf/api_key`
export PROJECT_ID=`cat /cocalc/conf/project_id`
export COMPUTE_SERVER_ID=`cat /cocalc/conf/compute_server_id`

cd /cocalc/src/compute/compute
node ./start-filesystem.js