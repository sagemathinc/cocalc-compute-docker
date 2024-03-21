#!/usr/bin/env bash

set -ev

sudo hostname `cat /cocalc/conf/hostname`
echo "127.0.0.1 `cat /cocalc/conf/hostname`" | sudo tee -a /etc/hosts

# Make sure conf directory exists so proxy works (it needs path to
# exist to watch for creation of proxy.json)
sudo mkdir -p /cocalc/conf

# Create user ownd /var/run/supervisor, where the socket
# and pid files go, and also log files
sudo mkdir -p /var/run/supervisor /var/log/supervisor
sudo chown user:user -R /var/run/supervisor  /var/log/supervisor

# We use supervisord running as user to manage all the processes.

# First ensure it is installed (just in case it isn't for some
# minimal container -- usually or eventually it always will be).
if [ ! -f /usr/bin/supervisord ]; then
   sudo apt-get update
   sudo DEBIAN_FRONTEND=noninteractive apt-get install -y supervisor
fi

# Ensure that there isn't a weird supervisord.conf in the default location,
# since we want to be able to run supervisorctl without explicitly specifying
# the path to the socket.
sudo cp /cocalc/supervisor/supervisord.conf /etc/supervisor/

/usr/bin/supervisord --nodaemon -c /cocalc/supervisor/supervisord.conf
