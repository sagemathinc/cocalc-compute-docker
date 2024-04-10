#!/usr/bin/env bash

set -v

which zpool

if [ $? -ne 0 ]; then
    # install ZFS
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y zfsutils-linux
fi

zpool status tank

if [ $? -eq 0 ]; then
    # make sure ssd is setup if it exists
    ./zpool-local-ssd.sh
    # pool already exists, so done and ready
    exit 0
fi


zpool import tank -m

if [ $? -eq 0 ]; then
    # make sure ssd is setup if it exists
    ./zpool-local-ssd.sh
    # pool imported fine, so done and ready
    exit 0
fi

set -e

if [ -e /dev/vdc ]; then
    # have local fast ephemeral ssd
    zpool create -f tank /dev/vdc
    # also setup the local ssd to cache the zfs filesystems, etc.
    ./zpool-local-ssd.sh

else

    # do NOT have local fast ssd
    set +e
    umount /ephemeral
    set -e
    zpool create -f tank /dev/vdb
fi

# setup mountpoints, filesystem and compression

# User data:
zfs create -o mountpoint=/data tank/data
zfs set compression=lz4 tank/data

# Docker data:
zfs create -o mountpoint=/var/lib/docker tank/docker
zfs set compression=lz4 tank/docker
mkdir -p /etc/docker
echo '{"storage-driver":"zfs"}' > /etc/docker/daemon.json

# If docker is installed restart it.
set +e
service docker restart
set -e

# OK, all done.
