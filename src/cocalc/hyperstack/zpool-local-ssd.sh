#!/usr/bin/env bash

set -ev

if [ "$COCALC_LOCAL_SSD"x -eq "x" ]; then
    echo "There is no local ssd so nothing to configure."
    exit 0
fi

disk="vdb"
device="/dev/${disk}"
zpool="local-ssd"

# No matter what when the machine boots up, if we actually need to do something
# and if there is a fast local ssd,
# then /dev/vdb will be mounted as a normal ext4 filesystem as ephemeral.
# If this is not the case, we don't have a fast local ssd.
# Alternatively, everything was already setup and we just rebooted, so don't have
# to do anything either.

set -e

echo "Get rid of any previous or default use of the local ephemeral disk, and set it up."

# Unmount and destroy disk if it happens to be mounted (e.g., as /ephemeral)
# IMPORTANT!! Do not mess with /etc/fstab and remove the line
#      /dev/vdb /ephemeral ext4 defaults,nofail 0 0
# It seems like a good idea, but if you do that, then the boot image somewhere
# or some cloudinit script will put in some other similar MUCH WORSE automount
# thing and totally break the ephemeral disk and this script (with /dev/vdb1 busy).
# So just don't do that!!!

umount $device 2>/dev/null || true
zpool destroy -f ${zpool} 2>/dev/null || true
zpool remove tank ${disk}1  2>/dev/null || true
zpool remove tank ${disk}2 2>/dev/null || true

# Clear any existing partition table
dd if=/dev/zero of=$device bs=512 count=1 conv=notrunc

# Create a new partition table - sometimes we have to keep trying
while ! parted -s $device mklabel gpt
do
    echo "Trying again to unmount $device"
    umount $device || true
    sleep 1
done


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




