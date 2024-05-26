#!/usr/bin/env bash
set -ev

# put the generated files in /root
cd /root

# this parses contents of /cocalc/conf and creates:
#   hosts, wg{id}.conf, pings.sh
python3 /conf.py

# put hosts in /cocalc/conf so it can be processed externally in
# various ways -- it is what to append to the end of /etc/hosts
cp -v hosts /cocalc/conf/hosts

# also if pings.sh was written, copy it over as well, so the host
# can run it
if [ -e pings.sh ]; then
   cp -v pings.sh /cocalc/conf
   chmod a+x /cocalc/conf/pings.sh
fi

# actually do the configuration -- if up doesn't work, e.g., because
# the interface already exists, we strip and update it as explained
# in the wg-quick manpage.
id=`cat /cocalc/conf/compute_server_id`
if ! wg-quick up ./wg${id}.conf; then
    wg syncconf wg$id <(wg-quick strip ./wg$id.conf)
fi
