#!/usr/bin/env python3
"""

TODOS:
   - figure out exactly when keydb has successfully startd and sync'd up
   - mount all filesystems in parallel using threading
   - implement configurability and defaults for how things are mounted and formated
     (e.g., compression, metadata caching, file caching)
   - use of ~/.local feels wrong. move to somewhere else.
"""

import argparse, json, os, signal, subprocess, tempfile, time

# We poll filesystem for changes to storage_json this frequently:
INTERVAL = 5

# Fallback default filename if not given explicitly
storage_json = 'storage.json'

###
# Utilities
###


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


def run(cmd, check=True, env=None):
    """
    Takes as input a shell command, runs it, streaming output to
    stdout and stderr as usual. Basically this is os.system(cmd),
    but it will throw an exception if the exit status is nonzero.
    """
    print(f"run('{cmd}')")
    if env is None:
        env = os.environ
    else:
        env = {**os.environ, **env}
    try:
        subprocess.check_call(cmd, shell=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"Command '{cmd}' failed with error code: {e.returncode}", e)
        if check:
            raise


def mkdir(path):
    os.makedirs(path, exist_ok=True)


###
# Mount
###


def gcs_key_path(filesystem):
    return os.path.join(os.environ['HOME'], '.local', 'var', 'storage',
                        f"gcs_key-{filesystem['id']}")


def gcs_key(filesystem):
    path = gcs_key_path(filesystem)
    directory = os.path.split(path)[0]
    mkdir(directory)
    os.chmod(directory, 0o700)
    service_account = filesystem["secret_key"]
    open(path, 'w').write(json.dumps(service_account))
    os.chmod(path, 0o600)
    return path


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
    return os.path.join(os.environ['HOME'], '.local', 'mnt',
                        f"storage-bucket-{filesystem['id']}")


def mount_bucket(filesystem):
    # write the service account key to a temporary file, being careful about permissions
    # so it is only readable by us.
    key_file = gcs_key(filesystem)
    # use gcsfuse to mount the GCS bucket
    bucket = bucket_fullpath(filesystem)
    mkdir(bucket)
    # implicit dirs is so we can see the juicedb data, so we can tell
    # if the volume is already formated.
    run(f"gcsfuse --implicit-dirs --key-file {key_file} {filesystem['bucket']} {bucket}"
        )


def keydb_paths(filesystem, network):
    id = filesystem['id']
    return {
        # Keydb pid file is located in here
        "run":
        os.path.join(os.environ['HOME'], '.local', 'var', 'run',
                     f'keydb-{id}'),
        # Keydb log file is here
        "log":
        os.path.join(os.environ['HOME'], '.local', 'var', 'log',
                     f'keydb-{id}'),
        # Where keydb will persist data:
        "data":
        os.path.join(bucket_fullpath(filesystem), 'keydb',
                     network['interface'], 'data')
    }


def start_keydb(filesystem, network):
    paths = keydb_paths(filesystem, network)
    for key in paths:
        mkdir(paths[key])
    keydb_config_file = os.path.join(paths['data'], 'keydb.conf')
    keydb_config_content = f"""
daemonize yes

loglevel debug
logfile {os.path.join(paths['log'], 'keydb-server.log')}
pidfile {os.path.join(paths['run'], 'keydb-server.pid')}

# data
# **NOTE: aof on gcsfuse doesn't work AND causes replication
# to slow to a crawl!**
dir {paths['data']}

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
    # TODO!  We need to confirm here that keydb has fully started up and
    # sync'd with any peers!!!!!
    time.sleep(5)


def juicefs_paths(filesystem):
    id = filesystem['id']
    return {
        # juicefs log file is here
        "log":
        os.path.join(os.environ['HOME'], '.local', 'var', 'log',
                     f'juicefs-{id}'),
        "cache":
        os.path.join(os.environ['HOME'], '.local', 'var', 'cache',
                     f'juicefs-{id}'),
    }


def mount_juicefs(filesystem):
    key_file = gcs_key(filesystem)
    volume = "storage"
    if not os.path.exists(os.path.join(bucket_fullpath(filesystem), volume)):
        run(f"juicefs format redis://localhost:{filesystem['port']} {volume} --storage gs --bucket gs://{filesystem['bucket']}",
            check=False,
            env={'GOOGLE_APPLICATION_CREDENTIALS': key_file})

    paths = juicefs_paths(filesystem)
    for key in paths:
        mkdir(paths[key])

    run(f"""
juicefs mount \
    --background \
    --log {os.path.join(paths['log'], 'juicefs.log')} \
    --writeback \
    --cache-dir {paths['cache']} \
    redis://localhost:{filesystem['port']} {mountpoint_fullpath(filesystem)}
""",
        check=True,
        env={'GOOGLE_APPLICATION_CREDENTIALS': key_file})


###
# Update
###


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


###
# Unmount
###


def unmount_all():
    print("UNMOUNT ALL")
    storage = read_storage_json()
    if storage is None:
        return
    for filesystem in storage['filesystems']:
        unmount_filesystem(filesystem, storage['network'])


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


def unmount_filesystem(filesystem, network):
    # unmount juicefs
    unmount_path(mountpoint_fullpath(filesystem))

    # stop keydb
    paths = keydb_paths(filesystem, network)
    pidfile = os.path.join(paths['run'], 'keydb-server.pid')
    if os.path.exists(pidfile):
        try:
            pid = int(open(pidfile).read())
            os.kill(pid, signal.SIGTERM)
            os.unlink(pidfile)
        except Exception as e:
            print(f"Error killing keydb -- '{e}'")

    # unmount the bucket
    unmount_path(bucket_fullpath(filesystem))

    # remove service account secret
    path = gcs_key_path(filesystem)
    if os.path.exists(path):
        os.unlink(path)


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
        #pass
        unmount_all()
