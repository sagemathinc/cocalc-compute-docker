#!/usr/bin/env bash

set -ev

export SAGE_FAT_BINARY="yes"
export SAGE_INSTALL_GCC="no"
cd /usr/local/sage
make configure
./configure --enable-build-as-root
