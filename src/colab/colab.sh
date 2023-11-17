#!/usr/bin/env bash
set -xeuo pipefail

## APT environment

apt-get update
apt-get install -qq -y \
    apt-utils \
    lsb-release \
    python3-pip \
    python3-dev \
    pkg-config \
    build-essential \
    software-properties-common \
    dirmngr \
    wget \
    curl \
    git \
    vim

## Setup R's CRAN40 repo
## NOTE: we skip this for now ... also note the grep -v 'r-cran-' below
#wget -qO- https://cloud.r-project.org/bin/linux/ubuntu/marutter_pubkey.asc | sudo tee -a /etc/apt/trusted.gpg.d/#cran_ubuntu_key.asc
#add-apt-repository "deb https://cloud.r-project.org/bin/linux/ubuntu $(lsb_release -cs)-cran40/"
#apt-get update
#apt-get install -y -qq r-base r-recommended r-base-dev

# 2023-11-17: only jammy and jammy-updates (for Ubuntu 22.04)
# we --ignore-missing because some R packages are not in that repo, or I don't know yet how to find them
cat apt.txt | tail -n +2 | grep "/$(lsb_release -s -c)" | grep -v 'r-cran-' | cut -d'/' -f1 | xargs -n 32 apt-get install --ignore-missing -y

apt-get clean autoclean
apt-get autoremove --yes
rm -rf /var/lib/{apt,dpkg,cache,log}/

## Python environment

# Colab runs Python 3.10
#python -V

pip install -U pip
# we get rid of google colab itself
sed -i '/google-colab @ file/d' pip.txt

pip --no-cache-dir install -r pip.txt

# pip.txt should contain an ipykernel, we just ensure it is here, no updating!
pip install ipykernel
jupyter kernelspec remove -y python3
python3 -m ipykernel install --sys-prefix --name python3 --display-name "Python 3 (Colab)"

pip cache purge
