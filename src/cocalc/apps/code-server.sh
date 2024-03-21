#!/usr/bin/env bash

. /cocalc/start-env.sh

set +e

which code-server

if [ $? -ne 0 ]; then
    echo "Installing code-server"
    curl -fsSL https://code-server.dev/install.sh | sudo sh
fi

set -ev
code-server --auth=none --bind-addr=localhost:$PORT

