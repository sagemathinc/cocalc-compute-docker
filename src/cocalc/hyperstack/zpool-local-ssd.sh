#!/usr/bin/env bash

set -ev

if [ ! -e /dev/vdc ]; then
    # there is definitely no local ephemeral disk, since the first data disk
    # has to be /dev/vdc
    exit 0
fi

disk="vdb"
device="/dev/${disk}"
zpool="local-ssd"

# Get rid of any previous or default use of the local ephemeral disk.
# Destroy loUnmount disk if it happens to be mounted (e.g., as /ephemeral)
sed '/\/ephemeral/d' /etc/fstab > /etc/fstab.new
mv /etc/fstab.new /etc/fstab
zpool destroy -f ${zpool} 2>/dev/null || true
zpool remove tank ${disk}1  2>/dev/null || true
zpool remove tank ${disk}2 2>/dev/null || true
umount $device 2>/dev/null || true

# Clear any existing partition table
dd if=/dev/zero of=$device bs=512 count=1 conv=notrunc

# Create a new partition table
parted -s $device mklabel gpt

# Create partition 1 (20GB)
parted -s $device mkpart primary 0GB 20GB

# Create partition 2 (80GB)
parted -s $device mkpart primary 20GB 100GB

# Create partition 3 (Remaining space)
parted -s $device mkpart primary 100GB 100%

# Set partition names
parted -s $device name 1 ${disk}1
parted -s $device name 2 ${disk}2
parted -s $device name 3 ${disk}3

echo "Partitioning completed successfully."
echo "New partition scheme:"
parted -s $device print

# Add ZFS read cache
zpool add -f tank cache ${device}1

# Add ZFS write cache
zpool add -f tank log ${device}2

zpool create -f ${zpool} ${device}3
zfs set compression=lz4 ${zpool}
zfs set mountpoint=/ephemeral ${zpool}
# We disable sync for writes because iops and bandwidth increase massively.
# This is fine to do because this space is **TOTALLY EPHEMERAL**.  It gets wiped
# on reboot, etc.
zfs set sync=disabled ${zpool}




