#!/usr/bin/env bash

set -ev

source /cocalc/start-env.sh

sudo hostname `cat /cocalc/conf/hostname`
echo "127.0.0.1 `cat /cocalc/conf/hostname`" | sudo tee -a /etc/hosts

# Ways for background processes to get controlled.

# If cron is installed, start it.
sudo service cron start || true

# for backward compatibility with older layout
if [ -f /etc/supervisor/conf.d/supervisord.conf ]; then
    echo "starting supervisord"
    /usr/bin/supervisord --configuration /etc/supervisor/conf.d/supervisord.conf || true
else
    # If supervisord is installed, try to start it, if possible.
    if [ -f /usr/bin/supervisord ]; then
        echo "starting supervisord"
        /usr/bin/supervisord || true
    fi
fi

if [ -f /cocalc/src/compute/compute/start-compute.js ]; then
    cd /cocalc/src/compute/compute/
    node ./start-compute.js
else
    echo "Starting dev bash shell because /cocalc/src/compute/compute/start-compute.js does not exist."
    bash
fi