#!/usr/bin/env bash

set -ev

# Install nodejs, our custom proxy server package, and supervisord
# Proxy by default exposes port 80 on port 443, with a self signed cert,
# and has a random registration token, but things are configurable.
# This gets run in various Dockerfiles.

mkdir -p /opt/proxy/nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | NVM_DIR=/opt/proxy/nvm bash
source /opt/proxy/nvm/nvm.sh
nvm install --no-progress 20

apt-get install -y supervisor

source /opt/proxy/nvm/nvm.sh
npm install -g @cocalc/compute-server-proxy

mkdir -p /var/log/supervisor

# Create a token for testing that is in the Docker container image.
# When used on a compute server, this /cocalc directory will get
# bind mounted over.
mkdir -p /cocalc/conf
echo "test" > /cocalc/conf/auth_token
chmod og-rwx /cocalc/conf/auth_token

# Script to configure what gets run by supervisord.  In addition,
# add your own configuration scripts as
#   /etc/supervisor/conf.d/*
# to start your own processes!

cat <<EOF > /etc/supervisor/supervisord.conf
[supervisord]
nodaemon=false
logfile=/var/log/supervisor/supervisord.log
childlogdir=/var/log/supervisor
user=user

[program:proxy]
redirect_stderr=true
command=sudo -E /opt/proxy/start-proxy.sh

[include]
files = /etc/supervisor/conf.d/*
EOF


# The script mentioned above to start the proxy
# server nodejs process running:

mkdir -p /opt/proxy/
cat <<EOF > /opt/proxy/start-proxy.sh
#!/usr/bin/env bash

source /opt/proxy/nvm/nvm.sh
export PROXY_CONFIG=/opt/proxy/proxy.json
export PROXY_PORT=443
export PROXY_HOSTNAME=0.0.0.0
export PROXY_AUTH_TOKEN_FILE=/cocalc/conf/auth_token
DEBUG=* npx -y @cocalc/compute-server-proxy@latest
EOF

chmod a+x /opt/proxy/start-proxy.sh

# Finally, the proxy.json mentioned above, which is a json-lines file:
cat <<EOF > /opt/proxy/proxy.json
[{ "path": "/", "target": "http://localhost:80", "ws": true }]
EOF

chown -R user:user /var/log/supervisor /etc/supervisor/
