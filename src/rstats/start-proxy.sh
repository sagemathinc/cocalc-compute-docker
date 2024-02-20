#!/usr/bin/env bash

source /opt/proxy/nvm/nvm.sh
export PROXY_CONFIG=/app/proxy.json
DEBUG=* npx @cocalc/compute-server-proxy