#!/usr/bin/env python3
"""


"""

import argparse, json, os, signal, subprocess, tempfile, time

INTERVAL = 5

storage_json = 'storage.json'


def get_mtime(path):
    return None if not os.path.exists(path) else os.path.getmtime(path)


def wait_until_file_changes(path, last_known_mtime):
    while True:
        time.sleep(INTERVAL)
        if not os.path.exists(path):
            # File doesn't exist, continue until file is created
            last_known_mtime = None
            continue

        mtime = get_mtime(path)
        if last_known_mtime != mtime:
            return
        last_known_mtime = mtime


def mount_all():
    print("MOUNT ALL", storage_json)
    storage = read_storage_json()
    if storage is None:
        print("no ", storage_json, " so nothing to do")
        return
    for filesystem in storage['filesystems']:
        mount_filesystem(filesystem, storage['network'])


def mount_filesystem(filesystem, network):
    mount_bucket(filesystem)
    start_keydb(filesystem, network)
    mount_juicefs(filesystem)


def mountpoint_fullpath(filesystem):
    return os.path.join(os.environ['HOME'], filesystem['mountpoint'])


def bucket_fullpath(filesystem):
    return os.path.join('/mnt', f"bucket-{filesystem['id']}")


def run(cmd, check=True):
    """
    Takes as input a shell command, runs it, streaming output to
    stdout and stderr as usual. Basically this is os.system(cmd),
    but it will throw an exception if the exit status is nonzero.
    """
    print(f"run('{cmd}')")
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Command '{cmd}' failed with error code: {e.returncode}")
        if check:
            raise


def mount_bucket(filesystem):
    # write the service account key to a temporary file, being careful about permissions
    # so it is only readable by us.
    service_account = filesystem["secret_key"]
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
            print(temp.name)
            os.chmod(temp.name, 0o600)  # set file permissions to -rw-------
            temp.write(json.dumps(service_account))
            temp.close()
            # use gcsfuse to mount the GCS bucket
            bucket = bucket_fullpath(filesystem)
            run(f"sudo mkdir -p '{bucket}'")
            run(f"sudo chown user:user '{bucket}'")
            run(f"gcsfuse --key-file {temp.name} {filesystem['bucket']} {bucket}"
                )
    finally:
        # Remove the service account key from the filesystem
        if os.path.isfile(temp.name):
            os.remove(temp.name)
        pass


def start_keydb(filesystem, network):
    id = filesystem['id']
    run(f"sudo mkdir -p /var/run/keydb-{id}/ /var/log/keydb-{id}/")
    run(f"sudo chown user:user -R /var/run/keydb-{id}/ /var/log/keydb-{id}/")
    # Where keydb will persist data:
    data = f"{bucket_fullpath(filesystem)}/.keydb/{network['interface']}/data"
    run(f"mkdir -p '{data}'")
    keydb_config_file = f"{data}/keydb.conf"
    keydb_config_content = f"""
daemonize yes

loglevel debug
logfile /var/log/keydb-{id}/keydb-server.log
pidfile /var/run/keydb-{id}/keydb-server.pid

# data
# **NOTE: aof on gcsfuse doesn't work AND causes replication to slow to a crawl!**
dir {data}

# multimaster replication
multi-master yes
active-replica yes

# no password: we do security by only binding on private encrypted VPN network
protected-mode no
bind 127.0.0.1 {network['interface']}
port {filesystem['port']}
"""
    for peer in network['peers']:
        keydb_config_content += f"replicaof {peer} {filesystem['port']}\n"
    with open(keydb_config_file, 'w') as file:
        file.write(keydb_config_content)
    run(f"keydb-server {keydb_config_file}")


def mount_juicefs(filesystem):
    pass


def update():
    print("UPDATE", storage_json)
    storage = read_storage_json()
    if storage is None:
        print("no ", storage_json, " so nothing to do")
        return
    for filesystem in storage['filesystems']:
        update_filesystem(filesystem, storage['network'])


def update_filesystem(filesystem, network):
    print('update_filesystem: TODO')
    pass


def unmount_all():
    print("UNMOUNT ALL")
    storage = read_storage_json()
    if storage is None:
        return
    for filesystem in storage['filesystems']:
        unmount_filesystem(filesystem)


def unmount_path(mountpoint):
    print(f"unmount {mountpoint}")
    try:
        if mountpoint not in os.popen(f"df {mountpoint} 2>/dev/null").read():
            return
    except:
        return
    while True:
        try:
            run(f"fusermount -u {mountpoint}")
        except:
            print("sleeping a second...")
            time.sleep(1)
            continue
        break


def unmount_filesystem(filesystem):
    # unmount juicefs
    unmount_path(mountpoint_fullpath(filesystem))

    # stop keydb
    id = filesystem['id']
    pidfile = f"/var/run/keydb-{id}/keydb-server.pid"
    if os.path.exists(pidfile):
        try:
            pid = int(open(pidfile).read())
            os.kill(pid, signal.SIGKILL)
            os.unlink(pidfile)
        except Exception as e:
            print(f"Error killing keydb -- '{e}'")

    # unmount the bucket
    unmount_path(bucket_fullpath(filesystem))


def read_storage_json():
    if not os.path.exists(storage_json):
        return None
    with open(storage_json) as json_file:
        return json.load(json_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=
        "Monitor and update CoCalc networked storage based on contents of storage.json file"
    )
    parser.add_argument('--storage-json',
                        type=str,
                        default=storage_json,
                        help="Path to the storage.json configuration file")

    args = parser.parse_args()
    storage_json = args.storage_json
    last_known_mtime = get_mtime(storage_json)
    try:
        mount_all()
        while True:
            try:
                wait_until_file_changes(storage_json, last_known_mtime)
                last_known_mtime = get_mtime(storage_json)
                update()
            except Exception as e:
                print(f"Error -- '{cmd}'", e)
                pass
    finally:
        unmount_all()