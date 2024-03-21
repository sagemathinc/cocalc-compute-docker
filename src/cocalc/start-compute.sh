#!/usr/bin/env bash

set -ev

sudo hostname `cat /cocalc/conf/hostname`
echo "127.0.0.1 `cat /cocalc/conf/hostname`" | sudo tee -a /etc/hosts

# Make sure conf directory exists so proxy works.
sudo mkdir -p /cocalc/conf

# We use supervisord to manage all the processes.

# First ensure it is installed (just in case it isn't for some
# minimal container -- usually or eventually it always will be).
if [ ! -f /usr/bin/supervisord ]; then
   sudo apt-get update
   sudo DEBIAN_FRONTEND=noninteractive apt-get install -y supervisor
fi

sudo /usr/bin/supervisord --nodaemon -c /cocalc/supervisor/supervisord.conf
