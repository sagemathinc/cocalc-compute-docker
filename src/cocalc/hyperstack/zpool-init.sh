#!/usr/bin/env bash

set -v

# check for ephemeral local ssd -- this works right when we boot up, but not later,
# due to cloud init (?) always reinitializing the local ssd.
df -h /ephemeral | grep /dev/vdb
if [ $? -ne 0 ]; then
    # above was an error, so there's no ephemeral local ssd to deal with
    local_ssd=no
    first_volume=/dev/vdb
else
    # yes, there is the local ssd.
    local_ssd=yes
    first_volume=/dev/vdc
fi

# Wait for first external volume to be visible.  This can be totally random -- usually it is
# already there, but sometimes it takes a little while.  It's VERY important to wait, since
# otherwise we can end up assuming an already configured ZFS disk is new, and delete all
# user data!

while ! stat $first_volume
do
    echo "User data volume not available yet. Retrying in 1 second..."
    sleep 1
done
sleep 1
# We can now assume that the external volume is plugged in.

which zpool

if [ $? -ne 0 ]; then
    # install ZFS
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y zfsutils-linux
fi

zpool status tank

if [ $? -eq 0 ]; then
    # This case would happen if the VM is rebooted.

    # Make sure ssd is setup if it exists
    if [ $local_ssd = 'yes' ]; then
        ./zpool-local-ssd.sh
    fi
    ./zpool-add.sh
    # pool already exists, so done and ready
    exit 0
fi

# Determine whether or not ZFS has already been setup by
# looking at the partition table to see if there is a zfs
# partition table on the first external volume
parted -m $first_volume print | grep :zfs:

if [ $? -eq 0 ]; then
    # zfs is definitely there!  Import it.
    # The -f is important since each time we start the compute server
    # the root file system is reset, so without -f we get this error
    #     cannot import 'tank': pool was previously in use from another system.
    #
    while ! zpool import tank -m -f
    do
        echo "Tank zfs pool failed to import. Retrying in 1 second..."
        sleep 1
    done
    # there is a tank already, so just make sure local SSD caching is configured properly.
    if [ $local_ssd = 'yes' ]; then
        ./zpool-local-ssd.sh
    else
        # Remove any faulted cache/log devices due to not having a local ssd anymore.
        # This happens the first time when we switch from having a local ssd to not.
        zpool remove tank `zpool status tank | awk '/cache/ {p=1} p && /FAULTED/ {print $1}' | tr -d ' '` || true
        zpool remove tank `zpool status tank | awk '/logs/ {p=1} p && /UNAVAIL/ {print $1}' | tr -d ' '` || true
    fi
    # pool imported fine, so done and ready
    ./zpool-add.sh

    # If docker is installed, restart it (since it could have started before we setup our zpool).
    service docker restart
    exit 0
fi

set -e
if [ $local_ssd = 'yes' ]; then
    # have local fast ephemeral ssd
    zpool create -f tank $first_volume
    # also setup the local ssd to cache the zfs filesystems, etc.
    ./zpool-local-ssd.sh

else

    # do NOT have local fast ssd
    umount /ephemeral
    zpool create -f tank /dev/vdb
fi

# add other disks (since can't resize yet)
./zpool-add.sh

# setup mountpoints, filesystem and compression

# User data:
zfs create -o mountpoint=/data tank/data
zfs set compression=lz4 tank/data

# Docker data:
zfs create -o mountpoint=/var/lib/docker tank/docker
zfs set compression=lz4 tank/docker
mkdir -p /etc/docker
echo '{"storage-driver":"zfs"}' > /etc/docker/daemon.json

# If docker is installed, restart it.
service docker restart || true
