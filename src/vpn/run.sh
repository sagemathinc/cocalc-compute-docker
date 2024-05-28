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
# can run it -- these take a while so we can't run them here.
if [ -e pings.sh ]; then
   cp -v pings.sh /cocalc/conf
else
   # ensure it is not there if not needed
   rm -f /cocalc/conf/pings.sh
fi

# actually do the configuration -- if up doesn't work, e.g., because
# the interface already exists, we strip and update it as explained
# in the wg-quick manpage.
#   https://www.reddit.com/r/WireGuard/comments/fodgpi/adding_peer_without_having_to_restart_service/
if ! wg-quick up ./wg.conf; then
    wg syncconf wg <(wg-quick strip ./wg.conf)
    if [ -f ./add-routes.sh ]; then
        # We MUST add the following (ignoring errors) for every other node
        # since syncconf doesn't do this:
        #    ip -4 route add 10.11.200.100/32 dev wg || true
        ./add-routes.sh
    fi
fi
