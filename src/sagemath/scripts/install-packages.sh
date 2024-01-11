#!/usr/bin/env bash

set -ev

apt-get update

export DEBIAN_FRONTEND=noninteractive

apt-get install -y \
       software-properties-common \
       flex \
       bison \
       libreadline-dev \
       make \
       cmake \
       g++ \
       build-essential \
       gfortran \
       dpkg-dev \
       libssl-dev \
       graphviz \
       tachyon \
       python3-pip \
       git