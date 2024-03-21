#!/usr/bin/env bash

. /cocalc/start-env.sh

set +e

which xpra

if [ $? -ne 0 ]; then
    echo "Installing xpra"
    sudo apt-get update
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y xpra xterm
fi

set -ev
xpra start --bind-tcp=localhost:$PORT --daemon=no --start=xterm

