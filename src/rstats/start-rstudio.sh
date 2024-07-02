#!/usr/bin/env bash

set -ev

# RSTUDIO_WHICH_R
#  - https://github.com/sagemathinc/cocalc-compute-docker/issues/9
#  - https://forum.posit.co/t/use-a-different-r-version-temporarily-in-rstudio/20848/7
export RSTUDIO_WHICH_R=/usr/local/bin/R

echo "user:$(sudo cat /cocalc/conf/auth_token)" | sudo chpasswd
sudo chown user:user -R /var/run/rstudio* /var/lib/rstudio-server/
sudo bash -c "echo 'server-user=user' > /etc/rstudio/server.conf"
# Yes, this is quite a hack!
sudo sed -i '/rstudio-server/c\rstudio-server:x:2001:2001::/home/user:/bin/bash' /etc/passwd

USER=user rstudio-server start
sleep infinity