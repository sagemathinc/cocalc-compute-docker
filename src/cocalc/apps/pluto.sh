#!/usr/bin/env bash

. /cocalc/start-env.sh

set +e

which julia

if [ $? -ne 0 ]; then
    echo "You must install Julia"
    exit 1
fi

echo 'import Pluto' | julia 2>&1 | grep -q 'not found'

if [ $? -eq 0 ]; then
    echo "Installing Pluto"
    echo 'using Pkg; Pkg.add("Pluto");' | julia
fi

set -ev
echo 'import Pluto; Pluto.run(launch_browser=false, require_secret_for_access=false, port='$PORT')' | julia

