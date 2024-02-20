#!/usr/bin/env bash

set -ev

echo "user:$(sudo cat /cocalc/conf/auth_token)" | sudo chpasswd
sudo chown user:user -R /var/run/rstudio* /var/lib/rstudio-server/
sudo sh -c "echo 'server-user=user' > /etc/rstudio/server.conf"
# Yes, this is quite a hack!
sudo sed -i '/rstudio-server/c\rstudio-server:x:2001:2001::/home/user:/bin/bash' /etc/passwd

USER=user rstudio-server start
sleep infinity