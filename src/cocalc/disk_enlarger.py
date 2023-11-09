#!/usr/bin/env python3
"""
Monitor the dmesg log.  If the /dev/sda or /dev/nvme0n1
devices disk device changes sizes, and if so, resize
the root partition.

THIS is only expected to work on Google cloud.
"""

import os
import sys
import subprocess

# Check if the script is running as root
if not os.geteuid() == 0:
    sys.exit("\nOnly root can run this script\n")

# Run the dmesg -w command
process = subprocess.Popen(['dmesg', '-w'], stdout=subprocess.PIPE)


def run(v):
    print(' '.join(v))
    try:
        subprocess.run(v)
    except e as Exception:
        print("ERROR: ", e)


# Read the output of the dmesg -w command
for line in iter(process.stdout.readline, b''):
    # Check if the disk has been enlarged
    #   [48336.686151] sda: detected capacity change from 125829120 to 167772160
    print(line)
    for dev in ['sda', 'nvme0n1']:
        if line.find(b'%s: detected capacity change' % dev) != -1:
            print("%s disk device changed size -- growing partition" % dev)
            run(['growpart', '/dev/%s' % dev, '1'])
            result = subprocess.run(['df', '/'], stdout=subprocess.PIPE)
            output = result.stdout.decode()
            root_device = output.split('\n')[1].split()[0]
            run(['resize2fs', root_device])
