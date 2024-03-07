#!/usr/bin/env bash

set -ev


# Setup a normal user account (not root) that matches cocalc.com (so uid=gid=2001),
# give it superpowers.

/usr/sbin/groupadd --gid=2001 -o user
/usr/sbin/useradd  --home-dir=/home/user --gid=2001 --uid=2001 --shell=/bin/bash user
mkdir -p /home/user
chown 2001:2001 -R /home/user

# passwordless root
echo '%user ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

# ability to mount fuse filesystems.
sed -i 's/#user_allow_other/user_allow_other/g' /etc/fuse.conf

# use docker without sudo.
usermod -aG docker user

# use the right version of nodejs, if installed
echo "[ -f /cocalc/nvm/nvm.sh ] && source /cocalc/nvm/nvm.sh" >> /etc/bash.bashrc

# We run supervisord as the normal user and log to /var/log/supervisor/:
cat <<EOF > /etc/supervisor/supervisord.conf
[supervisord]
nodaemon=false
pidfile=%(here)s/supervisord.pid
logfile=/var/log/supervisor/supervisord.log
childlogdir=/var/log/supervisor
user=user

[include]
files = /etc/supervisor/conf.d/*
EOF

mkdir -p /var/log/supervisor/
chown user:user -R /var/log/supervisor/ /etc/supervisor/
