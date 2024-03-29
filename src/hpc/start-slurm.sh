#!/usr/bin/env bash

# See https://slurm.schedmd.com/quickstart_admin.html

set -ev

# Create munge.key if it does not exist, which it won't initially
if [ ! -f /etc/munge/munge.key ]; then
    /usr/sbin/mungekey
    chown 105 /etc/munge/munge.key
fi

service munge start

# Set the hostname in the slurm conf file. We will use this later
# when we implement clusters.
# sed -i "s/localhost/$(hostname)/g" /etc/slurm/slurm.conf

# And start control daemon
service slurmctld start

# Start node daemon
service slurmd start

scontrol update nodename=localhost state=idle

# Thanks to
#    https://github.com/Supervisor/supervisor/issues/147#issuecomment-454063690
stop_script() {
    service munge stop
    service slurmd stop
    service slurmctld stop
    exit 0
}
# Wait for supervisor to stop script
trap stop_script SIGINT SIGTERM

while true
do
    sleep 1
done