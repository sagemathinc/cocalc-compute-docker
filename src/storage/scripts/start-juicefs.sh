#!/usr/bin/env bash
set -ev

# this is non-destructive so we don't have to worry about having already
# done it before.
juicefs format redis://localhost jfs --compress lz4 --storage gs --bucket gs://$BUCKET

sudo mkdir -p /var/log/juicefs/ /var/cache/juicefs/
sudo chown user:user -R /var/log/juicefs/ /var/cache/juicefs/

juicefs mount \
    --background \
    --log /var/log/juicefs/juicefs.log \
    --writeback \
    --attr-cache 3 \
    --entry-cache 3 \
    --dir-entry-cache 3 \
    --open-cache 3 \
    --open-cache-limit 25000 \
    --buffer-size 600 \
    --cache-dir /var/cache/juicefs/ \
    --cache-size 10000 \
    --free-space-ratio 0.1 \
    redis://localhost $MOUNT
