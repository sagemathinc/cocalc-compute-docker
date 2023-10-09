#!/usr/bin/env bash

set -ev

#source /cocalc/nvm/nvm.sh

export PATH=/cocalc/nvm/versions/node/v18.17.1/bin/:$PATH
cd /cocalc/src/compute/compute
node ./start-filesystem.js