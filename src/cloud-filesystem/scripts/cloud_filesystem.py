#!/usr/bin/env python3
"""

IDEAS: which may or may not be good
   - figure out exactly when keydb has successfully startd and sync'd up
   - mount all filesystems in parallel using threading
   - implement configurability and defaults for how things are mounted and formatted
     (e.g., compression, metadata caching, file caching)
   - automatic updating when configuration changes

How I work on this code in 10 easy steps:

1. I start a compute server running somewhere

2. I get a terminal on that compute server and type in HOME:
     git clone git@github.com:sagemathinc/cocalc-compute-docker.git

3. I edit this file:
     open cocalc-compute-docker/src/cloud-filesystem/scripts/cloud_filesystem.py

4. On that same compute server, I have some cloud filesystems defined.

5. I copy this file to the cloud-filesystem container using this script:

(compute-server-38) ~$ more docker_cp
set -ev
docker cp cocalc-compute-docker/src/cloud-filesystem/scripts/cloud_filesystem.py cloud-filesystem:/scripts/

6. Then restart the container:
    docker stop cloud-filesystem
    docker start cloud-filesystem

7. Observer:  "docker logs -f --tail=100 cloud-filesystem"

8. Sometimes get a shell in cloud-filesystem and poke around
or try commands directly:
    docker exec -it cloud-filesystem

9. When done and ready to deploy, commit, push, pull, etc.,
then append a new version in images.json to the "cloud-filesystem"
config, and on an x86 and arm build host, do
    make cloud-filesystem && make push-cloud-filesystem
and on the x86 host do
    make assemble-cloud-filesystem

10. Point to the new images.json by editing the site settings of
your cocalc server, e.g., make "Compute Servers: Images Spec URL"
point to something like
https://raw.githubusercontent.com/sagemathinc/cocalc-compute-docker/34cf5fd19b3f037064f3929c389a9b44b22d205f/images.json
"""

import argparse, datetime, json, os, random, shutil, signal, subprocess, sys, tempfile, time

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


def log(*args):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S: ")
    print(timestamp, *args)


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


def run(cmd, check=True, env=None, cwd=None):
    """
    Takes as input a shell command, runs it, streaming output to
    stdout and stderr as usual. Basically this is os.system(cmd),
    but it will throw an exception if the exit status is nonzero.
    """
    log(f"run: {cmd}")
    if env is None:
        env = os.environ
    else:
        env = {**os.environ, **env}
    try:
        subprocess.check_call(cmd,
                              shell=isinstance(cmd, str),
                              env=env,
                              cwd=cwd)
    except subprocess.CalledProcessError as e:
        log(f"Command '{cmd}' failed with error code: {e.returncode}", e)
        if check:
            raise


def mkdir(path):
    os.makedirs(path, exist_ok=True)


# Upload source to gs://bucket-name/.../a.gz.
def upload_gzstd(source, target, key_file):
    run(
        ["node", "/scripts/upload-gzstd.js",
         os.path.abspath(source), target],
        cwd='/scripts',  # important so it can install dep the first time called
        check=True,
        env={'GOOGLE_APPLICATION_CREDENTIALS': key_file})


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
    log("MOUNT ALL")
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


# Try to mount the bucket for up to the given amount of time.
# It can initially fail since right when we create the rolebinding
# the permissions can take a while to spread through google cloud
# and actually work.  Since we sometimes create the role binding
# right before mounting, this is particular important to retry.
# Note that officially it can take 7+ minutes for the role binding
# to actually start working
#   https://cloud.google.com/iam/docs/access-change-propagation),
# and if this fails, then it'll get retried in the next update loop.
def mount_bucket(filesystem, max_time=15):
    # write the service account key to a temporary file,
    # being careful about permissions
    # so it is only readable by us.
    key_file = gcs_key(filesystem)
    # use gcsfuse to mount the GCS bucket
    bucket = bucket_fullpath(filesystem)
    mkdir(bucket)
    # implicit dirs is so we can see the juicedb data, so we can tell
    # if the volume is already formatted.
    start = time.time()
    delay = 1
    while True:
        if filesystem['bucket'] in os.popen(f"df {bucket} 2>/dev/null").read():
            # The bucket is already mounted
            return
        try:
            run(f"gcsfuse --implicit-dirs --ignore-interrupts=true --key-file {key_file} {filesystem['bucket']} {bucket}",
                check=True)
        except Exception as e:
            elapsed = time.time() - start
            if elapsed >= max_time:
                raise e
            delay = min(max_time - elapsed, min(delay * 1.2, 5))
            time.sleep(delay)


def keydb_paths(filesystem, network):
    id = filesystem['id']
    paths = {
        # Keydb pid file is located in here
        "run":
        os.path.join(VAR, 'run', f'keydb-{id}'),
        # Keydb log file is here
        "log":
        os.path.join(VAR, 'log', f'keydb-{id}'),
        'dump.rdb':
        os.path.join(VAR, 'data', 'dump.rdb'),
        # Where keydb will persist data:
        "data":
        os.path.join(VAR, 'data'),
        'dump.rdb.gz':
        os.path.join(bucket_fullpath(filesystem), 'keydb', 'dump.rdb.gz'),
    }
    for key in ['run', 'log', 'data']:
        mkdir(paths[key])
    return paths


def start_keydb(filesystem, network):
    paths = keydb_paths(filesystem, network)

    # If there is a dump.rdb file from any other node that
    # is newer than ours, then we replace ours with it.
    # This is scary but necessary, e.g., imagine one server starts,
    # creates a file (say), and is then deprovisioned.  Then another
    # server starts -- the info about that new file can't be replicated
    # over, obviously, since the first server is gone.  However, it's
    # in the dump.rdb file for the first server.
    dump_rdb_gz = paths['dump.rdb.gz']
    log("start_keydb: using dump_rdb_gz = ", dump_rdb_gz)
    dump_rdb = os.path.join(paths['data'], 'dump.rdb')
    if os.path.exists(dump_rdb_gz):
        log(f"{dump_rdb_gz} --> {dump_rdb}")
        for i in range(10):
            try:
                shutil.copyfile(dump_rdb_gz, dump_rdb + '.gz')
                break
            except Exception as e:
                # This can happen as dump_rdb_gz gets updated periodically - so just retry.
                log(f"Problem copying {dump_rdb_gz} to {dump_rdb} -- '{e}'")
                time.sleep(random.random() * 5)
        if os.path.exists(dump_rdb):
            shutil.move(dump_rdb, dump_rdb + '.backup')
        run(["gunzip", dump_rdb + '.gz'])

    keydb_config_file = os.path.join(paths['data'], 'keydb.conf')
    keydb_config_content = f"""
daemonize yes

loglevel debug
logfile {os.path.join(paths['log'], 'keydb-server.log')}
pidfile {os.path.join(paths['run'], 'keydb-server.pid')}

# data
dir {paths['data']}
# Save once per minute, when there is at least 1 change (so some point in saving).
save 60 1

# multimaster replication
multi-master yes
active-replica yes

# no password: we do security by only binding on private encrypted VPN network
protected-mode no
bind 127.0.0.1 {network['interface']}
port {filesystem['port']}

{filesystem.get('keydb_options', '')}
"""
    for peer in network['peers']:
        keydb_config_content += f"replicaof {peer} {filesystem['port']}\n"
    with open(keydb_config_file, 'w') as file:
        file.write(keydb_config_content)
    run(f"keydb-server {keydb_config_file}")


def juicefs_paths(filesystem):
    id = filesystem['id']
    return {
        # juicefs log file is here
        "log": os.path.join(VAR, 'log', f'juicefs-{id}'),
        "cache": os.path.join(VAR, 'cache', f'juicefs-{id}'),
    }


VOLUME = 'juicefs'


def get_trash_days_option(filesystem):
    trash_days = filesystem.get('trash_days', 0)
    if not isinstance(trash_days, int) or trash_days < 0:
        trash_days = 0
    return f" --trash-days={trash_days} "


def get_format_options(filesystem):
    b = filesystem.get('block_size', 4)
    if not isinstance(b, int) or b < 1 or b > 64:
        b = 4
    block_size = 1024 * b

    compression = filesystem.get('compression', 'none')
    if compression != 'lz4' and compression != 'zstd' and compression != 'none':
        compression = 'none'

    options = f"redis://localhost:{filesystem['port']} {VOLUME} --block-size={block_size} {get_trash_days_option(filesystem)} --compress {compression} --storage gs --bucket gs://{filesystem['bucket']}"

    return options


def get_mount_options(filesystem):
    options = filesystem.get('mount_options', '')
    paths = juicefs_paths(filesystem)
    if '--cache-dir' not in options:
        options += f" --cache-dir {paths['cache']} "
    return options


def mount_juicefs(filesystem):
    key_file = gcs_key(filesystem)
    if not os.path.exists(os.path.join(bucket_fullpath(filesystem), VOLUME)):
        run(f"juicefs format {get_format_options(filesystem)}",
            check=False,
            env={'GOOGLE_APPLICATION_CREDENTIALS': key_file})

    paths = juicefs_paths(filesystem)
    for key in paths:
        mkdir(paths[key])

    run(f"juicefs config redis://localhost:{filesystem['port']} --yes --force {get_trash_days_option(filesystem)}",
        check=False,
        env={'GOOGLE_APPLICATION_CREDENTIALS': key_file})

    # The very first time the filesystem starts, multiple compute servers are trying to run this mount_juicefs
    # function at roughly the same time.  This mount could fail with "not formatted" because the format is
    # in progress.  Format is very fast, but not instant.
    for i in range(10):
        try:
            run(f"""
        juicefs mount \
            --background \
            --log {os.path.join(paths['log'], 'juicefs.log')} {get_mount_options(filesystem)} \
            redis://localhost:{filesystem['port']} {mountpoint_fullpath(filesystem)}
        """,
                check=True,
                env={'GOOGLE_APPLICATION_CREDENTIALS': key_file})
            log(f"Successful mounted filesystem at {mountpoint_fullpath(filesystem)}"
                )
            break
        except Exception as e:
            log(f"Problem mounting filesystem at {mountpoint_fullpath(filesystem)} -- '{e}'"
                )
            time.sleep(random.random() * 5)


###
# Update
###


def update():
    log("UPDATE")
    config = read_cloud_filesystem_json()
    if config is None:
        return
    network = config['network']
    should_be_mounted = []
    currently_mounted = mounted_filesystem_paths()
    # ensure that all the ones that should be mountd are mounted
    # and configured properly.
    error = None
    for filesystem in config['filesystems']:
        try:
            path = mountpoint_fullpath(filesystem)
            if path in currently_mounted:
                update_filesystem(filesystem, network)
            else:
                mount_filesystem(filesystem, network)
        except Exception as e:
            log("WARNING: failed to mount/update ", e)
            error = e
        should_be_mounted.append(path)
    should_be_mounted = set(should_be_mounted)

    for path in currently_mounted:
        if path not in should_be_mounted:
            v = get_config(path)
            if v is not None:
                try:
                    unmount_filesystem(v[0], v[1])
                except Exception as e:
                    log("Error unmounting filesystem", path, e)
                    # we just try the next one for now; may try again in the future.
                    # Unmounting will fail if process has a file open.
    if error is not None:
        # something went seriously wrong with a MOUNT attempt.
        # throwing this is important, so that we retry update again
        # soon, rather than waiting for the filesystems state to change.
        raise error


def mounted_filesystem_paths():
    s = subprocess.run(['mount', '-t', 'fuse.juicefs'], capture_output=True)
    if s.returncode:
        raise RuntimeError(s.stderr)
    return [x.split()[2] for x in s.stdout.decode().splitlines()]


def update_filesystem(filesystem, network):
    log('update_filesystem: ', 'id=', filesystem['id'],
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
    log("UNMOUNT ALL")
    config = read_cloud_filesystem_json()
    if config is None:
        return
    network = config['network']
    for filesystem in config['filesystems']:
        try:
            unmount_filesystem(filesystem, network)
        except Exception as e:
            log(f"Error unmounting a filesystem -- '{e}'")


def unmount_path(mountpoint, maxtime=3):
    log(f"unmount {mountpoint}")
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
            log("sleeping a second...")
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
            log(f"sending SIGTERM to keydb with pid {pid}")
            os.kill(pid, signal.SIGTERM)
            try:
                log(f"Wait for {pid} to terminate...")
                os.waitpid(pid, 0)
            except ChildProcessError:
                # Process is already terminated
                pass
            log(f"keydb with pid {pid} has terminated")
            os.unlink(pidfile)
        except Exception as e:
            log(f"Error killing keydb -- '{e}'")

    # unmount the bucket -- be aggressive because keydb already stopped
    unmount_path(bucket_fullpath(filesystem), 3)

    # remove service account secret
    path = gcs_key_path(filesystem)
    if os.path.exists(path):
        os.unlink(path)


def read_cloud_filesystem_json():
    if not os.path.exists(CLOUD_FILESYSTEM_JSON):
        log("no ", CLOUD_FILESYSTEM_JSON, " so nothing to do")
        return None
    with open(CLOUD_FILESYSTEM_JSON) as json_file:
        return json.load(json_file)


def signal_handler(sig, frame):
    log('SIGTERM received! Cleaning up before exit...')
    unmount_all()
    sys.exit(0)


def signal_handler(sig, frame):
    log('SIGTERM received! Cleaning up before exit...')
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
        try:
            mount_all()
        except Exception as e:
            log("Error", e)
            pass
        success = True
        while True:
            try:
                if success:
                    wait_until_file_changes(CLOUD_FILESYSTEM_JSON,
                                            last_known_mtime)
                else:
                    log("failed last time, so will retry mount in 15 seconds")
                    time.sleep(15)
                last_known_mtime = get_mtime(CLOUD_FILESYSTEM_JSON)
                update()
                success = True
            except Exception as e:
                success = False
                log("Error", e)
                pass
    finally:
        #pass
        unmount_all()
