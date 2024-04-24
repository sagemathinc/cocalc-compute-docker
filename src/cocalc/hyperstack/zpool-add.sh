#!/usr/bin/env bash

echo "add any newly added disks to the pool..."
for drive in c d e f g h i j k l m n o p q r s t u v w x y z; do
    device=/dev/vd${drive}
    if [ "$device"x != "$COCALC_LOCAL_SSD"x ]; then
        zpool add tank /dev/vd${drive} 2>/dev/null || true
    fi
done