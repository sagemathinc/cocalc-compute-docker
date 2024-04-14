#!/usr/bin/env bash

# Directions are from https://docs.posit.co/resources/install-r-source/#download-and-extract-r

set -ev

export R_VERSION=$1

echo "R_VERSION=${R_VERSION}"

curl -O https://cran.rstudio.com/src/base/R-4/R-${R_VERSION}.tar.gz
tar -xzvf R-${R_VERSION}.tar.gz
cd R-${R_VERSION}

# configure is inspired by https://discourse.openondemand.org/t/graphics-display-issues-with-r-built-from-source-for-rstudio-server/1123/5
# Also, we need this x, cairo, etc. support so graphics work in R Studio (see https://github.com/sagemathinc/cocalc-compute-docker/issues/9).

./configure \
    --prefix=/usr/local \
    --enable-R-shlib \
    --enable-R-profiling \
    --enable-memory-profiling \
    --with-blas \
    --with-lapack \
    --with-x \
    --with-cairo \
    --with-jpeglib \
    --with-readline \
    --with-tcltk

make -j4

make install

