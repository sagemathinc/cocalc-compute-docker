#!/usr/bin/env bash

set -ev

export PATH=/cocalc/nvm/versions/node/v18.17.1/bin/:$PATH

source /cocalc/start-env.sh

cd /cocalc/src/compute/compute
node ./start-filesystem.js