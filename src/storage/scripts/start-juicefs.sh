#!/usr/bin/env bash
set -ev

# This is non-destructive so we don't have to worry about having already
# done it before.
# We use the maximal large block size to reduce the number of distinct objects
# stored in GCS, since there are a lot of per-object charges.  I didn't notice
# any performance issues with doing this.
juicefs format redis://localhost jfs --block-size=65536 --compress lz4 --storage gs --bucket gs://$BUCKET || true

sudo mkdir -p /var/log/juicefs/ /var/cache/juicefs/
sudo chown user:user -R /var/log/juicefs/ /var/cache/juicefs/

juicefs mount \
    --background \
    --log /var/log/juicefs/juicefs.log \
    --writeback \
    --attr-cache 1 \
    --entry-cache 1 \
    --dir-entry-cache 1 \
    --open-cache 1 \
    --open-cache-limit 25000 \
    --buffer-size 600 \
    --cache-dir /var/cache/juicefs/ \
    --cache-size 10000 \
    --free-space-ratio 0.1 \
    redis://localhost $MOUNT
