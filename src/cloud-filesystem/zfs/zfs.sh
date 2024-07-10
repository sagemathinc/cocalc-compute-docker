#!/usr/bin/env bash

set -ev

if ! which zpool; then
    sudo apt install -y zfsutils-linux
fi

if [ ! -d $2 ]; then
    mkdir $2
    cd $2
    truncate -s$1G 0.img
    sudo zpool create $2 `pwd`/0.img
    sudo zfs set mountpoint=$HOME/$2 $2
    sudo zfs set compression=lz4 $2
    sudo chown `whoami`:`whoami` $HOME/$2
else
    cd $2
    sudo zpool import -d `pwd` -m $2
fi
