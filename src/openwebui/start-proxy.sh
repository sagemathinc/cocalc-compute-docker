#!/usr/bin/env bash

source /opt/proxy/nvm/nvm.sh
export PROXY_CONFIG=/app/proxy.json
export PROXY_AUTH_TOKEN_FILE=/cocalc/conf/auth_token
DEBUG=* npx -y @cocalc/compute-server-proxy@latest