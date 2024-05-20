#!/usr/bin/env bash
set -ev

sudo mkdir -p /var/run/keydb/ /var/log/keydb/
sudo chown user:user -R /var/run/keydb/ /var/log/keydb/

# Where keydb will store data:
mkdir -p /bucket/keydb/$COMPUTE_SERVER_ID/data
cat <<EOF > /bucket/keydb/$COMPUTE_SERVER_ID/keydb.conf

daemonize yes

loglevel debug
logfile /var/log/keydb/keydb-server.log
pidfile /var/run/keydb/keydb-server.pid

# data
# **NOTE: aof on gcsfuse doesn't work AND causes replication to slow to a crawl!**  We only use
dir /bucket/keydb/$COMPUTE_SERVER_ID/data

# multimaster replication
multi-master yes
active-replica yes

# no password: we only allow access via ssh port forward
# or on localhost internal to the docker container
protected-mode no
bind 127.0.0.1 $INTERFACE
replicaof $PEER1 6379
replicaof $PEER2 6379

EOF

keydb-server /bucket/keydb/$COMPUTE_SERVER_ID/keydb.conf



