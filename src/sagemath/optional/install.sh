#!/usr/bin/env bash

set -ev

echo "sage -i $*"

MAKE="make -j`grep processor /proc/cpuinfo | wc -l`" sage -i $*