#!/usr/bin/env python3
"""

TODOS:
   - figure out exactly when keydb has successfully startd and sync'd up
   - mount all filesystems in parallel using threading
   - implement configurability and defaults for how things are mounted and formated
     (e.g., compression, metadata caching, file caching)
   - automatic updating when configuration changes
"""

import argparse, json, os, random, shutil, signal, subprocess, sys, tempfile, time

# We poll filesystem for changes to CLOUD_FILESYSTEM_JSON this frequently:
INTERVAL = 5

VAR = '/var/cloud-filesystem'
SECRETS = '/secrets'
BUCKETS = '/buckets'

# Where data about cloud filesystem configuration is loaded from
CLOUD_FILESYSTEM_JSON = 'cloud-filesystem.json'

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
    print(f"run: {cmd}")
    if env is None:
        env = os.environ
    else:
        env = {**os.environ, **env}
    try:
        subprocess.check_call(cmd, shell=isinstance(cmd, str), env=env)
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
    return os.path.join(SECRETS, f"gcs_key-{filesystem['id']}")


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
    print("MOUNT ALL")
    config = read_cloud_filesystem_json()
    if config is None:
        return
    for filesystem in config['filesystems']:
        mount_filesystem(filesystem, config['network'])


configs = {}


def save_config(filesystem, network):
    configs[mountpoint_fullpath(filesystem)] = [filesystem, network]


def get_config(fullmountpath):
    return configs.get(fullmountpath, None)


def mount_filesystem(filesystem, network):
    save_config(filesystem, network)
    mount_bucket(filesystem)
    start_keydb(filesystem, network)
    mount_juicefs(filesystem)


def mountpoint_fullpath(filesystem):
    return os.path.join(os.environ['HOME'], filesystem['mountpoint'])


def bucket_fullpath(filesystem):
    return os.path.join(BUCKETS, f"storage-bucket-{filesystem['id']}")


def mount_bucket(filesystem):
    # write the service account key to a temporary file, being careful about permissions
    # so it is only readable by us.
    key_file = gcs_key(filesystem)
    # use gcsfuse to mount the GCS bucket
    bucket = bucket_fullpath(filesystem)
    mkdir(bucket)
    # implicit dirs is so we can see the juicedb data, so we can tell
    # if the volume is already formated.
    run(f"gcsfuse --implicit-dirs --ignore-interrupts=true --key-file {key_file} {filesystem['bucket']} {bucket}"
        )


def keydb_paths(filesystem, network):
    id = filesystem['id']
    persist = os.path.join(bucket_fullpath(filesystem), 'keydb')
    return {
        # Keydb pid file is located in here
        "run": os.path.join(STORAGE, 'run', f'keydb-{id}'),
        # Keydb log file is here
        "log": os.path.join(STORAGE, 'log', f'keydb-{id}'),
        # Where keydb will persist data:
        "data": os.path.join(persist, network['interface'], 'data'),
        # Where all keydbs persist their data:
        "persist": persist
    }


def newest_dump_rdb_path(persist):
    if not os.path.exists(persist):
        return None
    mtime = 0
    newest_dump_rdb = None
    for ip in os.listdir(persist):
        path = os.path.join(persist, ip, 'data', 'dump.rdb')
        t = get_mtime(path)
        print(t, path)
        if not t:
            continue
        # Check if the file is at least 10KB
        if os.path.getsize(path) < 10240:  # 10KB = 10240 bytes
            continue
        if t > time.time() + 30:
            # Paranoid: what is some VM with their clock way off (a time traveler!) writes a dump
            # file with a far future timestamp and causes havoc.  We do aggressively fix the
            # clock on all compute servers, so this would likely get fixed quickly.
            continue
        if t > mtime:
            newest_dump_rdb = path
            mtime = t
    return newest_dump_rdb


def start_keydb(filesystem, network):
    paths = keydb_paths(filesystem, network)
    for key in paths:
        mkdir(paths[key])

    # If there is a dump.rdb file from any other node that
    # is newer than ours, then we replace ours with it.
    # This is scary but necessary, e.g., imagine one server starts,
    # creates a file (say), and is then deprovisioned.  Then another
    # server starts -- the info about that new file can't be replicated
    # over, obviously, since the first server is gone.  However, it's
    # in the dump.rdb file for the first server.
    newest_dump_rdb = newest_dump_rdb_path(paths['persist'])
    print("start_keydb: using newest_dump_rdb = ", newest_dump_rdb)
    dump_rdb = os.path.join(paths['data'], 'dump.rdb')
    if newest_dump_rdb is not None and dump_rdb != newest_dump_rdb:
        print(f"{newest_dump_rdb} --> {dump_rdb}")
        for i in range(10):
            try:
                shutil.copyfile(newest_dump_rdb, dump_rdb)
                break
            except Exception as e:
                # This can happen as newest_dump_rdb gets moved into place periodically - so just retry.
                print(
                    f"Problem copying {newest_dump_rdb} to {dump_rdb} -- '{e}'"
                )
                time.sleep(random.random() * 5)

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
# Save once per minute, when there are at least 100 changes.
save 60 100
# Save once per 5 minutes, if there are is at least 1 change.
save 300 1

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


#    wait_until_keydb_replication_is_stable(filesystem['port'])

# def get_keydb_replication_info(port):
#     s = subprocess.run(['keydb-cli', '-p',
#                         str(port), "INFO", "replication"],
#                        capture_output=True)
#     if s.returncode:
#         raise RuntimeError(s.stderr)
#     v = [x for x in str(s.stdout.decode()).splitlines() if ':' in x]
#     return dict([x.split(':') for x in v])

# def wait_until_keydb_replication_is_stable(port):
#     while True:
#         info = get_keydb_replication_info(port)
#         if info.get('role', '') == 'master':
#             # no other peers, so nothing to wait for
#             return
#         if info.get("master_link_status",'') == 'up' and info.get("master_sync_in_progress","") == '0'
#         time.sleep(1)


def juicefs_paths(filesystem):
    id = filesystem['id']
    return {
        # juicefs log file is here
        "log": os.path.join(STORAGE, 'log', f'juicefs-{id}'),
        "cache": os.path.join(STORAGE, 'cache', f'juicefs-{id}'),
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

    # The very first time the filesystem starts, multiple compute servers are trying to run this mount_juicefs
    # function at roughly the same time.  This mount could fail with "not formatted" because the format is
    # in progress.  Format is very fast, but not instant.
    for i in range(10):
        try:
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
            print(
                f"Successful mounted filesystem at {mountpoint_fullpath(filesystem)}"
            )
            break
        except Exception as e:
            print(
                f"Problem mounting filesystem at {mountpoint_fullpath(filesystem)} -- '{e}'"
            )
            time.sleep(random.random() * 5)


###
# Update
###


def update():
    print("UPDATE")
    config = read_cloud_filesystem_json()
    if config is None:
        return
    network = config['network']
    should_be_mounted = []
    currently_mounted = mounted_filesystem_paths()
    # ensure that all the ones that should be mountd are mounted
    # and configured properly.
    for filesystem in config['filesystems']:
        path = mountpoint_fullpath(filesystem)
        if path in currently_mounted:
            update_filesystem(filesystem, network)
        else:
            mount_filesystem(filesystem, network)
        should_be_mounted.append(path)
    should_be_mounted = set(should_be_mounted)

    for path in currently_mounted:
        if path not in should_be_mounted:
            v = get_config(path)
            if v is not None:
                try:
                    unmount_filesystem(v[0], v[1])
                except Exception as e:
                    print("Error unmounting filesystem", path, e)
                    # we just pass for now; may try again in the future.
                    # Unmounting will fail if process has a file open.
                    pass


def mounted_filesystem_paths():
    s = subprocess.run(['mount', '-t', 'fuse.juicefs'], capture_output=True)
    if s.returncode:
        raise RuntimeError(s.stderr)
    return [x.split()[2] for x in s.stdout.decode().splitlines()]


def update_filesystem(filesystem, network):
    print('update_filesystem: ', 'id=', filesystem['id'],
          filesystem['mountpoint'])
    save_config(filesystem, network)
    update_replication(filesystem, network)


def get_replicas(port):
    s = subprocess.run(['keydb-cli', '-p',
                        str(port), "INFO", "replication"],
                       capture_output=True)
    if s.returncode:
        raise RuntimeError(s.stderr)
    return [
        x.split(':')[1] for x in str(s.stdout.decode()).splitlines()
        if x.startswith('master') and 'host:' in x
    ]


def add_replica(host, port):
    run(['keydb-cli', '-p', str(port), "replicaof", host, str(port)])


def remove_replica(host, port):
    run(['keydb-cli', '-p', str(port), "replicaof", "remove", host, str(port)])


def update_replication(filesystem, network):
    """
    Ensure that this keydb node is connected to every other running compute server
    on the VPN.  We're using a fully connected topology, at least for now, since
    it maximizes the chances of no data loss, etc.  There are potential issues
    with speed, though for even a filesystem with 1million+ files, the amount of
    data is really small.  We will potentially revisit this network topology
    based on performance testing.
    """
    port = filesystem['port']
    replicas = set(get_replicas(port))
    peers = set(network['peers'])
    for host in peers:
        if host not in replicas:
            add_replica(host, port)
    for host in replicas:
        if host not in peers:
            remove_replica(host, port)


###
# Unmount
###


def unmount_all():
    print("UNMOUNT ALL")
    config = read_cloud_filesystem_json()
    if config is None:
        return
    network = config['network']
    for filesystem in config['filesystems']:
        try:
            unmount_filesystem(filesystem, network)
        except Exception as e:
            print(f"Error unmounting a filesystem -- '{e}'")


def unmount_path(mountpoint, maxtime=3):
    print(f"unmount {mountpoint}")
    try:
        if mountpoint not in os.popen(f"df {mountpoint} 2>/dev/null").read():
            return
    except:
        return
    for i in range(maxtime):
        try:
            run(f"fusermount -u {mountpoint}", check=True)
            return
        except:
            print("sleeping a second...")
            time.sleep(1)
            continue
    # always do this at least
    run(f"umount -l {mountpoint}", check=False)
    #raise RuntimeError(f"failed to unmount {mountpoint}")


def unmount_filesystem(filesystem, network):
    # unmount juicefs
    unmount_path(mountpoint_fullpath(filesystem))

    # stop keydb
    paths = keydb_paths(filesystem, network)
    pidfile = os.path.join(paths['run'], 'keydb-server.pid')
    if os.path.exists(pidfile):
        try:
            pid = int(open(pidfile).read())
            print(f"sending SIGTERM to keydb with pid {pid}")
            os.kill(pid, signal.SIGTERM)
            try:
                print(f"Wait for {pid} to terminate...")
                os.waitpid(pid, 0)
            except ChildProcessError:
                # Process is already terminated
                pass
            print(f"keydb with pid {pid} has terminated")
            os.unlink(pidfile)
        except Exception as e:
            print(f"Error killing keydb -- '{e}'")

    # unmount the bucket -- be aggressive because keydb already stopped
    unmount_path(bucket_fullpath(filesystem), 3)

    # remove service account secret
    path = gcs_key_path(filesystem)
    if os.path.exists(path):
        os.unlink(path)


def read_cloud_filesystem_json():
    if not os.path.exists(CLOUD_FILESYSTEM_JSON):
        print("no ", CLOUD_FILESYSTEM_JSON, " so nothing to do")
        return None
    with open(CLOUD_FILESYSTEM_JSON) as json_file:
        return json.load(json_file)


def signal_handler(sig, frame):
    print('SIGTERM received! Cleaning up before exit...')
    unmount_all()
    sys.exit(0)


def signal_handler(sig, frame):
    print('SIGTERM received! Cleaning up before exit...')
    unmount_all()
    sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=
        f"Monitor and update CoCalc's Cloud Filesystem based on the contents of '{CLOUD_FILESYSTEM_JSON}'"
    )

    parser.add_argument(
        '--cloud-filesystem-json',
        type=str,
        default=CLOUD_FILESYSTEM_JSON,
        help=
        
        f"Path to the cloud-filesystem.json configuration file (default: '{CLOUD_FILESYSTEM_JSON}')"
    
    )

    parser.add_argument(
        '--var',
        type=str,
        default=VAR,
        help=
        f"Path to ephemeral directory used for runtime caching and state.  Especially critical is '{VAR}/cache', which is where files are cached, and '{VAR}/log' where there are log files.  Must be writable by user (uid=2001)."
    )
    parser.add_argument(
        '--secrets',
        type=str,
        default=SECRETS,
        help="Path to secrets directory, used for storing secrets")
    parser.add_argument(
        '--buckets',
        type=str,
        default=BUCKETS,
        help=f"Where cloud storage buckets are mounted (default: '{BUCKETS}')")
    parser.add_argument(
        '--interval',
        type=int,
        default=INTERVAL,
        help=
        f"{CLOUD_FILESYSTEM_JSON} is polled every this many seconds for changes (default: {INTERVAL}s)"
    )

    args = parser.parse_args()
    CLOUD_FILESYSTEM_JSON = args.cloud_filesystem_json
    VAR = args.var
    SECRETS = args.secrets
    BUCKETS = args.buckets
    INTERVAL = args.interval

    last_known_mtime = get_mtime(CLOUD_FILESYSTEM_JSON)
    try:
        # ensure we clean up on exit, in context of docker:
        signal.signal(signal.SIGTERM, signal_handler)
        mount_all()
        while True:
            try:
                wait_until_file_changes(CLOUD_FILESYSTEM_JSON,
                                        last_known_mtime)
                last_known_mtime = get_mtime(CLOUD_FILESYSTEM_JSON)
                update()
            except Exception as e:
                print("Error", e)
                pass
    finally:
        #pass
        unmount_all()