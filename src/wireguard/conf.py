#!/usr/bin/env python3
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

    open(f'wg{compute_server_id}.conf', 'w').write(conf)


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
