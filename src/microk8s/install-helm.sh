#!/usr/bin/env bash

set -ev

# Install helm client binary, following
#    https://helm.sh/docs/intro/install/

curl https://baltocdn.com/helm/signing.asc | gpg --dearmor > /usr/share/keyrings/helm.gpg

apt-get install -y apt-transport-https

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" > /etc/apt/sources.list.d/helm-stable-debian.list

apt-get update
apt-get install -y helm