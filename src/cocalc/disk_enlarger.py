#!/usr/bin/env python3
"""
Monitor the dmesg log for disk size changes or disks being added.

'google-cloud':
- If the /dev/sda or /dev/nvme0n1 devices disk device changes sizes,
  and if so, resize the root partition.

'hyperstack':
- If a new disk is added, run /cocalc/hyperstack/zpool-add.sh
"""

import os
import sys
import subprocess
import threading

# Check if the script is running as root
if not os.geteuid() == 0:
    sys.exit("\nOnly root can run this script\n")

cloud = os.environ.get("COCALC_CLOUD", "google-cloud")

# Run the dmesg -w command
process = subprocess.Popen(['dmesg', '-w'], stdout=subprocess.PIPE)


def run(v):
    print(' '.join(v))
    try:
        subprocess.run(v)
    except e as Exception:
        print("ERROR: ", e)


def debounce(wait):

    def decorator(fn):

        def debounced(*args, **kwargs):

            def call_fn():
                fn(*args, **kwargs)

            if hasattr(fn, 'debounce_timer'):
                fn.debounce_timer.cancel()
            fn.debounce_timer = threading.Timer(wait, call_fn)
            fn.debounce_timer.start()

        return debounced

    return decorator


# NOTE -- we mount a ramdisk on /tmp because if the disk is full then writing to /tmp is
# not possible, and growpart writes to /tmp!  At least RAM is not full, so this is a workaround.
# See https://stackoverflow.com/questions/59420015/unable-to-growpart-because-no-space-left
# This is a VERY likely edge case to get into, since you only think to enlarge your disk
# when you run out.
def handle_google_cloud(dev):
    print("%s disk device changed size -- growing partition" % dev)
    run([
        'mount', '-o', 'size=10M,rw,nodev,nosuid', '-t', 'tmpfs', 'tmpfs',
        '/tmp'
    ])
    run(['growpart', '/dev/%s' % dev.decode(), '1'])
    result = subprocess.run(['df', '/'], stdout=subprocess.PIPE)
    output = result.stdout.decode()
    root_device = output.split('\n')[1].split()[0]
    run(['resize2fs', root_device])
    run(['umount', '/tmp'])


@debounce(1)
def handle_hyperstack():
    print("new volume likely attached -- adding to ZFS pool")
    run(['zpool', 'status'])
    run(['zpool', 'list'])
    run(['/cocalc/hyperstack/zpool-add.sh'])
    print("after:")
    run(['zpool', 'status'])
    run(['zpool', 'list'])


# Read the output of the dmesg -w command
for line in iter(process.stdout.readline, b''):
    # Check if the disk has been enlarged
    #   [48336.686151] sda: detected capacity change from 125829120 to 167772160
    print(line)
    if cloud == 'google-cloud':
        for dev in [b'sda', b'nvme0n1']:
            if line.find(b'%s: detected capacity change' % dev) != -1:
                handle_google_cloud(dev)
    elif cloud == 'hyperstack':
        # in hyperstack the dmesg line when you add a new volume like this:
        #   '[  519.470940] virtio_blk virtio5: [vdc] 2097152 512-byte logical blocks (1.07 GB/1.00 GiB)'
        # There is also no nontrivial danger or drawback to running handle_hyperstack too
        # much, since it adds disks when it finds them, and does nothing when it doesn't.
        # Plus we use debouncing.
        if line.find(b'virtio_blk virtio') != -1:
            handle_hyperstack()
