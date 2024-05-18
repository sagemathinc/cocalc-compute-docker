#!/usr/bin/env bash

set -ev

# Install official upstream docker from docker.com, which is new and
# has the most features.

apt-get update

export DEBIAN_FRONTEND=noninteractive

apt-get install -y ca-certificates curl gnupg

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin


# Ensure that the Docker group has gid 999 in this container.
# In Ubuntu 22.04 this was true, but it changed to be pretty random
# in other versions, and really could depend on what we have installed already.
# This gid 999 assumption is ALSO enforced on the hosting VM via similar
# code in the file
#   src/packages/server/compute/cloud/startup-script.ts
# that is run basically on startup to configure everything.
docker_gid=`getent group docker | cut -d: -f3`
# docker_gid is *something* since we just install docker above
if [ $docker_gid != '999' ]; then
    group999=`getent group 999 | cut -d: -f1`
    if [ ! -z $group999 ]; then
        # something else has group 999, e.g., systemd-journal in ubuntu 24.04, so
        # we move it to an available group:
        for i in $(seq 998 -1 100); do
            if ! getent group $i > /dev/null; then
                echo "Available GID: $i"
                groupmod -g $i $group999
                break
            fi
        done
    fi
    groupmod -g 999 docker
fi
