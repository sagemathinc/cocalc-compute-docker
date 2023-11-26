#!/usr/bin/env bash

# Directions are from https://docs.posit.co/resources/install-r-source/#download-and-extract-r

set -ev

export R_VERSION=$1

echo "R_VERSION=${R_VERSION}"

curl -O https://cran.rstudio.com/src/base/R-4/R-${R_VERSION}.tar.gz
tar -xzvf R-${R_VERSION}.tar.gz
cd R-${R_VERSION}

./configure \
    --prefix=/usr/local \
    --enable-R-shlib \
    --enable-memory-profiling \
    --with-blas \
    --with-lapack

make -j4

make install

