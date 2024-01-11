#!/usr/bin/env bash

set -ev


export SAGE_FAT_BINARY="yes"
export SAGE_INSTALL_GCC="no"
export MAKE="make -j`grep processor /proc/cpuinfo | wc -l`"
cd /usr/local/sage/

# For now, just sagetex, but maybe we should install most things that aren't too big,
# and at least everything we install on cocalc?

./sage -p sagetex
