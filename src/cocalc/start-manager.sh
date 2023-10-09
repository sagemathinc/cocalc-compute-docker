#!/usr/bin/env bash

set -ev

# This does NOT work if there is already an nvm, and sometimes there is, e.g., for the tensorflow image.
# source /cocalc/nvm/nvm.sh

# This always works:
export PATH=/cocalc/nvm/versions/node/v18.17.1/bin/:$PATH
cd /cocalc/src/compute/compute
node ./start-manager.js