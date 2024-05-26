#!/usr/bin/env python3
import os


def update_hosts():
    # Update /etc/hosts on the base VM:
    if os.path.exists('/cocalc/conf/hosts'):
        hosts = open('/cocalc/conf/hosts').read()
        HOSTS_COMMENT = hosts.splitlines()[0]
        etc_hosts = open('/etc/hosts').read()
        new_etc_hosts = etc_hosts.split(
            HOSTS_COMMENT)[0].strip() + '\n\n' + hosts
        if new_etc_hosts != etc_hosts:
            open('/etc/hosts', 'w').write(new_etc_hosts)


if __name__ == '__main__':
    update_hosts()
