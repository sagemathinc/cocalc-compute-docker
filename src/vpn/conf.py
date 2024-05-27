#!/usr/bin/env python3
"""

This script generates WireGuard configuration files based on a specified JSON file.

Usage:
    python conf.py --vpn-json /path/to/vpn.json --compute-server-id <id>

Arguments:
    --vpn-json: Path to the VPN JSON configuration file. [default: /cocalc/conf/vpn.json]
    --compute-server-id: ID of the compute server. If not provided, reads from /cocalc/conf/compute_server_id.

---

- run this script on /cocalc/conf/vpn.json to generate all conf files.

- The file /cocalc/conf/vpn.json should be an array of these:

export interface VpnItem {
  id: number;
  cloud: Cloud;
  dns?: string;
  vpn_ip: string;
  private_key: string;
  public_key: string;
  internal_ip?: string;
  external_ip?: string;
}


- run this on each node to create wireguard interface:

    wg-quick up ./wg`cat /cocalc/conf/compute_server_id`.conf

and if pings.sh is written, also run

    source ./pings.sh

to break out of the private network.


- run this to update conf when nodes are added/removed

    id=`cat /cocalc/conf/compute_server_id`
    wg syncconf wg$id <(wg-quick strip ./wg$id.conf)

(and also the pings script as above)




"""

WG_PORT = 51820

import argparse, json, sys


def write_conf(compute_server_id, nodes):
    # first we divide the nodes into
    #  - an interface = this node, and
    #  - all other peers = the other nodes:

    interface = None
    peers = []
    for node in nodes:
        if node['id'] == compute_server_id:
            interface = node
        else:
            peers.append(node)

    if interface == None:
        raise Error("%s must contain node with id %s" %
                    (vpn_json, compute_server_id))

    conf = f"""
[Interface]
PrivateKey = {interface['private_key']}
ListenPort = {WG_PORT}
Address = {interface['vpn_ip']}/32
"""

    conf += '\n\n'
    for peer in peers:
        conf += f"""
[Peer]
# id={peer['id']}
PublicKey = {peer['public_key']}
AllowedIPs = {peer['vpn_ip']}/32
"""
        if 'internal_ip' in peer and interface['cloud'] == peer[
                'cloud'] and peer["internal_ip"]:
            conf += f'Endpoint = {peer["internal_ip"]}:{WG_PORT}\n'
        elif 'external_ip' in peer and peer["external_ip"]:
            conf += f'Endpoint = {peer["external_ip"]}:{WG_PORT}\n'
        if 'external_ip' not in interface:
            # the compute_server_id that we're writing this conf file is behind
            # firewall, so we must set PersistentKeepalive or we will not be
            # able to connect to it.
            conf += 'PersistentKeepalive = 25'

    open(f'wg{compute_server_id}.conf', 'w').write(conf)

    if 'external_ip' not in interface:
        # We *have to* make all nodes hidden behind a firewall ping
        # every other node as well by running something like this below,
        # which will ping the targt node every 15 seconds for 2 minutes
        # total, which should be long enough
        #       ExecStart=ping -r -I wg0 -n -i 15 -c 20 10.13.13.1
        pings = '!#/usr/bin/env bash\n\nset -v\n\n'
        for peer in peers:
            pings += f"ping -r -I wg{compute_server_id} -n -i 15 -c 4 {peer['vpn_ip']} &\n"
        if len(peers) > 0:
            open(f'pings.sh', 'w').write(pings)


HOSTS_COMMENT = '### COCALC VPN -- EVERYTHING BELOW IS AUTOGENERATED -- DO NOT EDIT'


def write_hosts(nodes):
    hosts = HOSTS_COMMENT + '\n'
    for node in nodes:
        if 'vpn_ip' in node and node["vpn_ip"]:
            hosts += f'{node["vpn_ip"]} compute-server-{node["id"]}\n'
            if 'dns' in node and node['dns']:
                hosts += f'{node["vpn_ip"]} {node["dns"]}\n'
        if 'internal_ip' in node and node["internal_ip"]:
            hosts += f'{node["internal_ip"]} internal-{node["id"]}\n'
        if 'external_ip' in node and node["external_ip"]:
            hosts += f'{node["external_ip"]} external-{node["id"]}\n'

    open('hosts', 'w').write(hosts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Generate WireGuard configuration and /etc/hosts")
    parser.add_argument('--vpn-json',
                        type=str,
                        default='/cocalc/conf/vpn.json',
                        help="Path to the VPN JSON configuration file")
    parser.add_argument(
        '--compute-server-id',
        type=int,
        help=
        "ID of the compute server (falls back to /cocalc/conf/compute_server_id)"
    )

    args = parser.parse_args()

    vpn_json = args.vpn_json
    compute_server_id = args.compute_server_id

    if compute_server_id is None:
        with open('/cocalc/conf/compute_server_id') as id_file:
            compute_server_id = int(id_file.read().strip())

    with open(vpn_json) as json_file:
        nodes = json.load(json_file)['nodes']

    write_conf(compute_server_id, nodes)
    write_hosts(nodes)
