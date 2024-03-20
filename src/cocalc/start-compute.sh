#!/usr/bin/env bash

set -ev

source /cocalc/start-env.sh

sudo hostname `cat /cocalc/conf/hostname`
echo "127.0.0.1 `cat /cocalc/conf/hostname`" | sudo tee -a /etc/hosts

# We use supervisord to manage all the processes.

# First ensure it is installed (just in case it isn't for some
# minimal container -- usually or eventually it always will be).
if [ ! -f /usr/bin/supervisord ]; then
   sudo apt-get update
   sudo DEBIAN_FRONTEND=noninteractive apt-get install -y supervisor
fi

sudo /usr/bin/supervisord --nodaemon -c /cocalc/supervisor/supervisord.conf

# # If cron is installed, start it.
# sudo service cron start || true

# # for backward compatibility with older layout
# if [ -f /etc/supervisor/conf.d/supervisord.conf ]; then
#     echo "starting supervisord"
#     /usr/bin/supervisord --configuration /etc/supervisor/conf.d/supervisord.conf || true
# else
#     # If supervisord is installed, try to start it, if possible.
#     # NOTE: supervisord *is* installed in basically all of our containers, and it's
#     # now configured by default to include everything in /etc/supervisor/conf.d/,
#     # so if you want to run any custom daemons, this is the way to do it.
#     if [ -f /usr/bin/supervisord ]; then
#         echo "starting supervisord"
#         sudo mkdir -p /var/log/supervisor
#         sudo chown user:user -R /var/log/supervisor
#         /usr/bin/supervisord || true
#     fi
# fi

# if [ -f /cocalc/src/compute/compute/start-compute.js ]; then
#     cd /cocalc/src/compute/compute/
#     node ./start-compute.js
# else
#     echo "Starting dev bash shell because /cocalc/src/compute/compute/start-compute.js does not exist."
#     bash
# fi