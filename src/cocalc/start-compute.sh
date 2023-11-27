#!/usr/bin/env bash

set -ev

source /cocalc/start-env.sh

sudo hostname `cat /cocalc/conf/hostname`
echo "127.0.0.1 `cat /cocalc/conf/hostname`" | sudo tee -a /etc/hosts

# If cron is installed, start it.
sudo service cron start || true

cd /cocalc/src/compute/compute
node ./start-compute.js