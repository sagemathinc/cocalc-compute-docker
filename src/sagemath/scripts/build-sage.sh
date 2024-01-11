#!/usr/bin/env bash

set -ev

export SAGE_FAT_BINARY="yes"
export SAGE_INSTALL_GCC="no"
export MAKE="make -j`grep processor /proc/cpuinfo | wc -l`"
cd /usr/local/sage/
make

