#!/usr/bin/env bash

set -ev

source /cocalc/start-env.sh

sudo hostname `cat /cocalc/conf/hostname`
echo "127.0.0.1 `cat /cocalc/conf/hostname`" | sudo tee -a /etc/hosts

# Ways for background processes to get controlled.

# If cron is installed, start it.
sudo service cron start || true

# If supervisord is there, start it.
if [ -f /etc/supervisor/conf.d/supervisord.conf ]; then
    echo "starting supervisord"
    /usr/bin/supervisord --configuration /etc/supervisor/conf.d/supervisord.conf || true
fi

if [ -f /cocalc/src/compute/compute/start-compute.js ]; then
    node ./start-compute.js
else
    echo "start-compute does not exist. Starting bash."
    bash
fi