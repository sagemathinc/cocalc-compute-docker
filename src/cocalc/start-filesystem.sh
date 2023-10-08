#!/usr/bin/env bash

set -ev

source /cocalc/nvm/nvm.sh
cd /cocalc/src/compute/compute
node ./start-filesystem.js