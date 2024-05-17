#!/usr/bin/env bash

set -ev

# Install core packages
#
# - libfuse-dev is critical since the cocalc source assumes it is there for websocketfs
# - cron supports having crontab work
# - curl/wget for downloading software
# - python-is-python3 -- since python2 is done.

apt-get update

export DEBIAN_FRONTEND=noninteractive

apt-get install -y \
       cron \
       curl \
       wget \
       fuse \
       libfuse-dev \
       neovim \
       sudo \
       python-is-python3 \
       tmux \
       htop \
       supervisor \
       wireguard

# I want a simple unified experience for our users, where they can just do "pip install"
# in one global simple environment.  This is new in Ubuntu 22.04.  We may change later,
# but we basically install nothing using apt, so this should be fine.
rm -fv /usr/lib/python*/EXTERNALLY-MANAGED

