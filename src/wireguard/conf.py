#!/usr/bin/env python3
"""
- run this script on network.json to generate all conf files.


- run this on each node to create wireguard interface:

    wg-quick up ./wg`cat /cocalc/conf/compute_server_id`.conf

and if pings[id] is written, also run

    source ./pings3902.sh

to break out of the private network.


- run this to update conf when nodes are added/removed

    id=`cat /cocalc/conf/compute_server_id`
    wg syncconf wg$id <(wg-quick strip ./wg$id.conf)

(and also source pings.)



"""

WG_PORT = 51820

import json, sys


def write_conf(compute_server_id):
    interface = None
    peers = []
    for node in nodes:
        if node['id'] == compute_server_id:
            interface = node
        else:
            peers.append(node)

    if interface == None:
        raise Error("%s must contain node with id %s" %
                    (network_json, compute_server_id))

    conf = f"""
[Interface]
PrivateKey = {interface['wg_private_key']}
ListenPort = {WG_PORT}
Address = {interface['wg_address']}/32
"""

    conf += '\n\n'
    for peer in peers:
        conf += f"""
[Peer]
# id={peer['id']}
PublicKey = {peer['wg_public_key']}
AllowedIPs = {peer['wg_address']}/32
"""
        if 'internal_address' in peer and interface['cloud'] == peer['cloud']:
            conf += f'Endpoint = {peer["internal_address"]}:{WG_PORT}\n'
        elif 'external_address' in peer:
            conf += f'Endpoint = {peer["external_address"]}:{WG_PORT}\n'
        if 'external_address' not in interface:
            # the compute_server_id that we're writing this conf file is behind
            # firewall, so we must set PersistentKeepalive or we will not be
            # able to connect to it.
            conf += 'PersistentKeepalive = 25'

    open(f'wg{compute_server_id}.conf', 'w').write(conf)

    if 'external_address' not in interface:
        # We *have to* make all nodes hidden behind a firewall ping
        # every other node as well by running something like this below,
        # which will ping the targt node every 15 seconds for 2 minutes
        # total, which should be long enough
        #       ExecStart=ping -r -I wg0 -n -i 15 -c 20 10.13.13.1
        pings = '!#/usr/bin/env bash\n\nset -v\n\n'
        for peer in peers:
            pings += f"ping -r -I wg{compute_server_id} -n -i 15 -c 4 {peer['wg_address']} &\n"
        if len(peers) > 0:
            open(f'pings{compute_server_id}.sh', 'w').write(pings)


def write_hosts():
    hosts = ''
    for node in nodes:
        hosts += f'{node["wg_address"]} compute-server-{node["id"]}\n'
        if 'internal_address' in node:
            hosts += f'{node["internal_address"]} internal-{node["id"]}\n'
        if 'external_address' in node:
            hosts += f'{node["external_address"]} external-{node["id"]}\n'

    open('hosts', 'w').write(hosts)


if __name__ == '__main__':
    network_json = sys.argv[1]
    nodes = json.loads(open(network_json).read())
    for node in nodes:
        write_conf(node['id'])
    write_hosts()
