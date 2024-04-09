#!/usr/bin/env bash

set -ev

# setup ZFS caching on the ephemeral ssd, if necessary
disk="vdb"
device="/dev/${disk}"

# Unmount disk if it happens to be mounted (e.g., as /ephemeral)
set +e
umount $device
set -e

# Clear any existing partition table
dd if=/dev/zero of=$device bs=512 count=1 conv=notrunc

# Create a new partition table
parted -s $device mklabel gpt

# Create partition 1 (20GB)
parted -s $device mkpart primary 0GB 20GB

# Create partition 2 (80GB)
parted -s $device mkpart primary 80GB 100GB

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
zpool add tank cache ${disk}1

# Add ZFS write cache
zpool add tank log ${disk}2

mkfs.ext4 ${disk}3
sed '/\/ephemeral/d' /etc/fstab > /etc/fstab.new
mv /etc/fstab.new /etc/fstab
echo "${disk}3 /ephemeral ext4 defaults,nofail 0 0" >> /etc/fstab
mount /ephemeral


