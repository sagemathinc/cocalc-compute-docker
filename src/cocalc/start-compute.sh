#!/usr/bin/env bash

set -ev

# This does NOT work if there is already an nvm, and sometimes there is, e.g., for the tensorflow image.
# source /cocalc/nvm/nvm.sh

source /cocalc/start-env.sh

sudo hostname `cat /cocalc/conf/hostname`
echo "127.0.0.1 `cat /cocalc/conf/hostname`" | sudo tee -a /etc/hosts

cd /cocalc/src/compute/compute
node ./start-compute.js