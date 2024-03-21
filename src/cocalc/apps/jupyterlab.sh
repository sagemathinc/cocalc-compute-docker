#!/usr/bin/env bash

. /cocalc/start-env.sh

set +e

function run_jupyter() {
    jupyter lab --NotebookApp.token='' --NotebookApp.password='' --ServerApp.disable_check_xsrf=True --no-browser --NotebookApp.allow_remote_access=True --NotebookApp.base_url='/lab' --ip=localhost --port=$PORT
}

run_jupyter

if [ $? -ne 0 ]; then
    echo "Installing jupyerlab and try again"
    sudo apt-get update
    sudo DEBIAN_FRONTEND=noninteractive apt-get -y install python3-pip
    sudo pip3 install jupyterlab
    run_jupyter
fi
