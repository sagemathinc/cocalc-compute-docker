#!/usr/bin/env bash

set -ev

sudo apt update
sudo apt install -y zfsutils-linux

mkdir $2
cd $2

echo $@
truncate -s$1G 0.img
sudo zpool create $2 `pwd`/0.img
sudo zfs set mountpoint=$HOME/$2 $2
sudo zfs set compression=lz4 $2
sudo chown `whoami`:`whoami` $HOME/$2