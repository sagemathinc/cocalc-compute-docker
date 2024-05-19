#!/usr/bin/env bash
set -ev

sudo mkdir -p /var/run/keydb/ /var/log/keydb/
sudo chown user:user -R /var/run/keydb/ /var/log/keydb/

# Where keydb will store data:
mkdir -p /bucket/keydb/$COMPUTE_SERVER_ID/data
cat <<EOF > /bucket/keydb/$COMPUTE_SERVER_ID/keydb.conf
daemonize yes

logfile /var/log/keydb/keydb-server.log
pidfile /var/run/keydb/keydb-server.pid

# data
dir /bucket/keydb/$COMPUTE_SERVER_ID/data
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
aof-use-rdb-preamble yes

# multimaster replication
multi-master yes
active-replica yes

# no password: we only allow access via ssh port forward
# or on localhost internal to the docker container
protected-mode no
bind 127.0.0.1

EOF

keydb-server /bucket/keydb/$COMPUTE_SERVER_ID/keydb.conf



