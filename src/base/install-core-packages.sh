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
       htop