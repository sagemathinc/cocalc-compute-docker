#!/usr/bin/env bash

set -ev

# This does NOT work if there is already an nvm, and sometimes there is, e.g., for the tensorflow image.
# source /cocalc/nvm/nvm.sh

source /cocalc/start-env.sh

cd /cocalc/src/compute/compute
node ./start-compute.js