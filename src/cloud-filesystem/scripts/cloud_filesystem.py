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

import argparse, datetime, gzip, json, os, random, shutil, signal, subprocess, sys, tempfile, time
from google.cloud import storage

# We poll filesystem for changes to CLOUD_FILESYSTEM_JSON at most
# this frequently in seconds.
INTERVAL_S = 5

# Delete locally cached files if filesystem is in the "not automount"
# state or deleted for this many minutes.
FREE_NOT_MOUNTED_M = 60

VAR = '/var/cloud-filesystem'
SECRETS = '/secrets'
BUCKETS = '/buckets'

# Where data about cloud filesystem configuration is loaded from
CLOUD_FILESYSTEM_JSON = '/cocalc/conf/cloud-filesystem.json'

MAX_REPLICA_LAG_S = 3

###
# Utilities
###


def log(*args):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S: ")
    print(timestamp, *args)


def get_mtime(path, zero=None):
    return zero if not os.path.exists(path) else os.path.getmtime(path)


def wait_until_file_changes(path, last_known_mtime):
    while True:
        t = time.time()
        update_keydbs()
        time.sleep(max(0.1, INTERVAL_S - (time.time() - t)))
        if not os.path.exists(path):
            # File doesn't exist, continue until file is created
            last_known_mtime = None
            continue

        mtime = get_mtime(path)
        if last_known_mtime != mtime:
            return
        last_known_mtime = mtime


def system(s, check=True, env=None):
    if isinstance(s, str):
        v = shlex.split(s)
    else:
        v = [str(x) for x in s]
    if env is None:
        env = os.environ
    else:
        env = {**os.environ, **env}
    process = subprocess.Popen(v, env=env)
    exit_code = process.wait()
    if exit_code and check:
        sys.exit(exit_code)


def run(cmd, check=True, env=None, cwd=None):
    """
    Takes as input a shell command, runs it, streaming output to
    stdout and stderr as usual. Basically this is os.system(cmd),
    but it will throw an exception if the exit status is nonzero.
    """
    if isinstance(cmd, str):
        log(f"run: {cmd}")
    else:
        cmd = [str(x) for x in cmd]
        log(f"run: {' '.join(cmd)}")
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


def is_process_running(pid):
    try:
        # Signal 0 in a kill command is a null signal, it does not affect the process
        os.kill(pid, 0)
    except OSError:
        return False  # Process is definitely not alive
    else:
        return True  # Process responded, hence it's alive


def upload_gzstd(source, target, key_file):
    log("upload_gzstd: ", source, " --> ", target)
    # Client initialization with service account JSON key file
    client = storage.Client.from_service_account_json(key_file)

    # Extract the bucket name and destination filename from the target URL
    assert target.startswith("gs://"), "Target must start with gs://"
    bucket_name, dest_filename = target[5:].split("/", 1)

    # Ensure the destination filename ends with '.gz'
    if not dest_filename.endswith('.gz'):
        dest_filename += '.gz'

    # Access bucket and blob objects
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(dest_filename)

    # Compress file content and upload
    with open(source, 'rb') as f_in:
        with gzip.open(source + '.gz', 'wb', compresslevel=1) as f_out:
            f_out.writelines(f_in)

    # Upload the compressed file
    with open(source + '.gz', 'rb') as f_gz:
        blob.upload_from_file(f_gz,
                              content_type='application/gzip',
                              predefined_acl='private')

    # Optionally, remove the temporary gzip file
    os.remove(source + '.gz')

    log(f"Uploaded {source} as {dest_filename} to gs://{bucket_name}/{dest_filename}"
        )


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
            run([
                "gcsfuse", "--implicit-dirs", "--ignore-interrupts=true",
                "--key-file", key_file, filesystem['bucket'], bucket
            ],
                check=True)
        except Exception as e:
            elapsed = time.time() - start
            if elapsed >= max_time:
                raise e
            delay = max(0.1, min(max_time - elapsed, min(delay * 1.2, 5)))
            time.sleep(delay)


def local_keydb_paths(filesystem):
    id = filesystem['id']
    data = os.path.join(VAR, 'data', f'keydb-{id}')
    return {
        # Keydb pid file is located in here
        "run": os.path.join(VAR, 'run', f'keydb-{id}'),
        # Keydb log file is here
        "log": os.path.join(VAR, 'log', f'keydb-{id}'),
        'dump.rdb': os.path.join(data, 'dump.rdb'),
        # Where keydb will persist data:
        "data": data
    }


def keydb_paths(filesystem):
    paths = local_keydb_paths(filesystem)
    bucket = filesystem['bucket']
    paths['dump.rdb.gz'] = os.path.join(bucket_fullpath(filesystem), 'keydb',
                                        'dump.rdb.gz')
    paths['bucket_dump_rdb_gz'] = f'gs://{bucket}/keydb/dump.rdb.gz'
    for key in ['run', 'log', 'data']:
        mkdir(paths[key])
    return paths


## Metrics


def get_stats_path(filesystem):
    return os.path.join(mountpoint_fullpath(filesystem), '.stats')


METRICS = {
    'juicefs_object_request_data_bytes_PUT': 'bytes_put',
    'juicefs_object_request_data_bytes_GET': 'bytes_get',
    'juicefs_object_request_durations_histogram_seconds_PUT_total':
    'objects_put',
    'juicefs_object_request_durations_histogram_seconds_GET_total':
    'objects_get',
    'juicefs_object_request_durations_histogram_seconds_DELETE_total':
    'objects_delete',
    'juicefs_used_space': 'bytes_used',
    'juicefs_uptime': 'process_uptime'
}


def get_filesystem_metrics(filesystem):
    path = get_stats_path(filesystem)
    if not os.path.exists(path):
        return None
    metrics = {'cloud_filesystem_id': filesystem['id']}
    for x in open(path).readlines():
        v = x.split()
        if len(v) >= 2:
            key = METRICS.get(v[0], None)
            if key == 'process_uptime':
                metrics[key] = float(v[1])
            elif key is not None:
                metrics[key] = int(v[1])
    return metrics


import requests
from requests.auth import HTTPBasicAuth

API_KEY = open('/cocalc/conf/api_key').read().strip()
API_SERVER = open('/cocalc/conf/api_server').read().strip()
COMPUTE_SERVER_ID = int(open('/cocalc/conf/compute_server_id').read().strip())


def submit_metrics(filesystem):
    metrics = get_filesystem_metrics(filesystem)
    url = f"{API_SERVER}/api/v2/internal/compute/cloud-filesystem/set-metrics"
    headers = {"Content-Type": "application/json"}
    auth = HTTPBasicAuth(API_KEY, '')
    data = dict(metrics)
    data['compute_server_id'] = COMPUTE_SERVER_ID
    response = requests.post(url,
                             json=data,
                             headers=headers,
                             auth=auth,
                             verify=False)
    print(response.status_code)
    print(response.json())


# State tracking for purposes of uploading dump.rdb file only when necessary.
# We normally only upload the keydb state file to cloud storage
# when something has changed in the filesystem state, as evidenced
# by one of these metrics changing.  This avoids constantly uploading
# the keydb dump.rdb over a thousand times a day for no reason.
# Of course, we always save dump.rdb on exit.

STATE_KEYS = set([
    'juicefs_object_request_durations_histogram_seconds_DELETE_total',
    'juicefs_object_request_data_bytes_GET',
    'juicefs_object_request_data_bytes_PUT', 'juicefs_meta_ops_total_Link',
    'juicefs_meta_ops_total_Mknod', 'juicefs_meta_ops_total_Rename',
    'juicefs_meta_ops_total_SetAttr', 'juicefs_meta_ops_total_SetXattr',
    'juicefs_meta_ops_total_Unlink', 'juicefs_meta_ops_total_Write',
    'juicefs_fuse_ops_total_write', 'juicefs_fuse_ops_total_create'
])


def get_filesystem_state(filesystem):
    path = get_stats_path(filesystem)
    if not os.path.exists(path):
        return None
    state = {}
    for x in open(path).readlines():
        v = x.split()
        if len(v) >= 2 and v[0] in STATE_KEYS:
            state[v[0]] = v[1]
    return state


filesystem_state = {}
last_filesystem_state = {}


def clear_state(filesystem):
    global filesystem_state, last_filesystem_state
    del filesystem_state[filesystem['id']]
    del last_filesystem_state[filesystem['id']]


def has_state_changed_since_calling_save_filesystem_state(filesystem):
    global filesystem_state, last_filesystem_state
    try:
        state = get_filesystem_state(filesystem)
        if state is None:
            # e.g., when the filesystem is not mounted, always assume this
            return True
    except Exception as e:
        log(f"WARNING -- can't get filesystem state {e}")
        return True
    id = filesystem['id']
    # save the new state we just got for if save_filesystem_state is called
    last_filesystem_state[id] = state
    # we compare with filesystem_state.get(id, {}), which
    # is the last state where save_filesystem_state was called.
    return state != filesystem_state.get(id, {})


def save_filesystem_state(filesystem):
    global filesystem_state, last_filesystem_state
    id = filesystem['id']
    filesystem_state[id] = last_filesystem_state.get(id, {})


# last timestamp of keydb we changed, mapping from id to time
last_keydb_time = {}


def update_keydb_dump(filesystem):
    if not has_state_changed_since_calling_save_filesystem_state(filesystem):
        # do not clutter the logs
        #    log("update_keydb_dump", filesystem['id'], 'no state change')
        return
    paths = keydb_paths(filesystem)
    if not os.path.exists(paths['dump.rdb']):
        log("update_keydb_dump", filesystem['id'],
            'filesystem state change - no dump.rdb')
        return
    t_keydb = get_mtime(paths['dump.rdb'])
    if last_keydb_time.get(filesystem['id'], 0) == t_keydb:
        log("update_keydb_dump", filesystem['id'],
            'filesystem state change - but dump.rdb is unchanged')
        # file is unchanged
        return

    # once has_state_changed returns true, it keeps returning true
    # until we call save_filesystem_state, which sets the last state
    # we used for the decision to be the new state.
    save_filesystem_state(filesystem)

    log(f"update_keydb_dump: filesystem state change - compressing and uploading dump.rdb"
        )

    # Important - we do not want to touch the actual bucket unless necessary,
    # since it costs money.  Hence the last_keydb_time cache above.
    t_keydb_gz = get_mtime(paths['dump.rdb.gz'])
    if t_keydb is None:
        t_keydb = 0
    if t_keydb_gz is None:
        t_keydb_gz = 0
    if t_keydb_gz >= time.time() + 10 * 60:
        # TODO: much better than this would be if we can just get the
        # actual object creation time via the google cloud storage api,
        # and then instead of depending on client clocks, we depend only
        # on GCS's clock.
        log(f"update_keydb_dump: weirdly {paths['dump.rdb.gz']} is 10 minutes in future, so a clock is way off, we copy anyways!"
            )
    elif t_keydb <= t_keydb_gz:
        log("update_keydb_dump: our dump is older than latest, so nothing to do"
            )
        return
    log("update_keydb_dump: ours is newer, so backup")
    upload_gzstd(paths['dump.rdb'], paths['bucket_dump_rdb_gz'],
                 gcs_key(filesystem))
    last_keydb_time[filesystem['id']] = t_keydb

    log("update_keydb_dump: submitting metrics to cocalc server")
    try:
        submit_metrics(filesystem)
    except Exception as e:
        log(
            f"WARNING: issue submitting metrics for filesystem {filesystem['id']}",
            e)


def start_keydb(filesystem, network):
    paths = keydb_paths(filesystem)

    # If there is a dump.rdb file from any other node that
    # is newer than ours, then we replace ours with it.
    # This is scary but necessary, e.g., imagine one server starts,
    # creates a file (say), and is then deprovisioned.  Then another
    # server starts -- the info about that new file can't be replicated
    # over, obviously, since the first server is gone.  However, it's
    # in the dump.rdb file for the first server.
    dump_rdb_gz = paths['dump.rdb.gz']
    if os.path.exists(dump_rdb_gz):
        # We use the dump_rdb_gz exactly if it is newer than the dump.rdb file.
        dump_rdb = os.path.join(paths['data'], 'dump.rdb')
        t_dump_rdb = get_mtime(dump_rdb, 0)
        t_dump_rdb_gz = get_mtime(dump_rdb_gz)

        log("t_dump_rdb=", t_dump_rdb, "t_dump_rdb_gz=", t_dump_rdb_gz)
        if t_dump_rdb < t_dump_rdb_gz:
            log("start_keydb: using dump_rdb_gz = ", dump_rdb_gz,
                " since it is newer")
            log(f"{dump_rdb_gz} --> {dump_rdb}")
            for i in range(10):
                try:
                    shutil.copyfile(dump_rdb_gz, dump_rdb + '.gz')
                    break
                except Exception as e:
                    # This can happen as dump_rdb_gz gets updated periodically - so just retry.
                    log(f"Problem copying {dump_rdb_gz} to {dump_rdb} -- '{e}'"
                        )
                    time.sleep(random.random() * 5)
            if os.path.exists(dump_rdb):
                shutil.move(dump_rdb, dump_rdb + '.backup')
            run(["gunzip", dump_rdb + '.gz'])
    else:
        log("start_keydb: starting from whatever is local, if anything")

    keydb_config_file = os.path.join(paths['data'], 'keydb.conf')
    keydb_config_content = f"""
daemonize yes

loglevel debug
logfile {os.path.join(paths['log'], 'keydb-server.log')}
pidfile {os.path.join(paths['run'], 'keydb-server.pid')}

# data
dir {paths['data']}
# Save once per minute, when there is at least 1 change (so some point in saving).
# Because of timestamps (?) there is always at least 1 change, so this
# does save every minute no matter what.
save 60 1

# Enabling appendonly constantly broke things.  I don't understand why, but
# I think things don't work if the file is missing -- i.e., you can't just
# delete it to reset to a different state from another node.  So it's not
# sufficient for us.  Instead we have to accept the potential of slight
# data loss.   Note that the rdb file always gets saved every 60s from the
# above configuration.
appendonly no

# See https://juicefs.com/docs/community/databases_for_metadata#redis
maxmemory-policy noeviction

# We only allow writes when a quorum of replicas are available and
# fully working.  This prevents split brain, which can lead to filesystem
# inconsistencies/corruption.
min-replicas-to-write {get_quorum(network) - 1}
min-replicas-max-lag {MAX_REPLICA_LAG_S}

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
    run(["keydb-server", keydb_config_file])


def is_keydb_running(filesystem):
    paths = keydb_paths(filesystem)
    pidfile = os.path.join(paths['run'], 'keydb-server.pid')
    if os.path.exists(pidfile):
        try:
            pid = int(open(pidfile).read())
            if is_process_running(pid):
                return True
        except:
            pass
    return False


def ensure_keydb_running(filesystem, network):
    if not is_keydb_running(filesystem):
        start_keydb(filesystem, network)


def stop_keydb(filesystem):
    paths = keydb_paths(filesystem)
    pidfile = os.path.join(paths['run'], 'keydb-server.pid')
    if not os.path.exists(pidfile):
        return
    try:
        t = get_mtime(paths['dump.rdb'])
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
        if os.path.exists(paths['dump.rdb']):
            # wait up to 10 seconds for the timestamp to change
            # due to saving. I think it always saves out the file,
            # but somehow does it in a forked process, which we don't
            # detect above?!  This is very important so we don't drop
            # the last few changes to the filesystem!
            w = time.time()
            while time.time() - w <= 10 and get_mtime(paths['dump.rdb']) == t:
                log(f"stop_keydb: waiting for {paths['dump.rdb']} to update")
                time.sleep(0.5)

    except Exception as e:
        log(f"Error killing keydb -- '{e}'")


def stop_extra_keydbs(filesystems):
    """
    If there are any keydb servers running that should not be running,
    stop them.

    When pushing/testing really hard constantly mounting/unmounting,
    etc. I noticed sometimes I got things into a state where there were
    keydb's running when they should have been stopped.  Given how
    synchronous this code is and that there delays, this seems like it
    could reasonably happen.  This function just checks the process table
    for all running keydb's, and if any shouldn't be running according
    to filesystems, it kills them.

    We just send each SIGTERM and that's it.
    """
    ports = set([filesystem['port'] for filesystem in filesystems])
    for line in os.popen(
            "pgrep -f 'keydb-server 127.0.0.1:' --list-full").readlines():
        pid = int(line.split(' ')[0])
        port = int(line.split(':')[-1])
        if port not in ports:
            try:
                log(f"stop_extra_keydbs -- SIGTERM to {pid} serving on port {port}"
                    )
                os.kill(pid, signal.SIGTERM)
            except:
                pass


def juicefs_paths(filesystem):
    id = filesystem['id']
    return {
        # juicefs log file is here
        "log": os.path.join(VAR, 'log', f'juicefs-{id}'),
        # IMPORTANT: In update_not_mounted_filesystems we assume
        # this location and name for the cache directories!!!
        "cache": os.path.join(VAR, 'cache', f'juicefs-{id}'),
    }


VOLUME = 'juicefs'


def get_trash_days_option(filesystem):
    trash_days = filesystem.get('trash_days', 0)
    if not isinstance(trash_days, int) or trash_days < 0:
        trash_days = 0
    return ['--trash-days', trash_days]


def get_redis_url(filesystem):
    return f"redis://localhost:{filesystem['port']}"


def get_format_options(filesystem):
    b = filesystem.get('block_size', 4)
    if not isinstance(b, int) or b < 1 or b > 64:
        b = 4
    block_size = 1024 * b

    compression = filesystem.get('compression', 'none')
    if compression != 'lz4' and compression != 'zstd' and compression != 'none':
        compression = 'none'

    options = [get_redis_url(filesystem), VOLUME, "--block-size", block_size
               ] + get_trash_days_option(filesystem) + [
                   '--compress', compression, '--storage', 'gs', '--bucket',
                   f"gs://{filesystem['bucket']}"
               ]

    return options


def get_mount_options(filesystem):
    options = filesystem.get('mount_options', '').split()
    paths = juicefs_paths(filesystem)
    if '--cache-dir' not in options:
        options.append('--cache-dir')
        options.append(paths['cache'])
    if '--client-id' not in options:
        # it could be very bad if the user specifies client-id, but user specified mount options are clearly labeled as
        # dangerous, and I want the option for testing/dev to customize anything.
        options.append('--client-id')
        options.append(filesystem['client_id'])
    return options


def mount_juicefs(filesystem):
    key_file = gcs_key(filesystem)
    first_time = not os.path.exists(
        os.path.join(bucket_fullpath(filesystem), VOLUME))
    if first_time:
        run(["juicefs", "format"] + get_format_options(filesystem),
            check=False,
            env={'GOOGLE_APPLICATION_CREDENTIALS': key_file})

    paths = juicefs_paths(filesystem)
    for key in paths:
        mkdir(paths[key])

    # The very first time the filesystem starts, multiple compute servers are trying to run this mount_juicefs
    # function at roughly the same time.  This mount could fail with "not formatted" because the format is
    # in progress.  Format is very fast, but not instant.
    mountpoint = mountpoint_fullpath(filesystem)
    error = None
    for i in range(10 if first_time else 1):
        try:
            mount_options = get_mount_options(filesystem)
            run([
                "juicefs", "config",
                get_redis_url(filesystem), "--yes", "--force"
            ] + get_trash_days_option(filesystem),
                check=False,
                env={'GOOGLE_APPLICATION_CREDENTIALS': key_file})

            run([
                "juicefs", "mount", "--background", "--log",
                os.path.join(paths['log'], 'juicefs.log')
            ] + mount_options +
                [get_redis_url(filesystem), mountpoint],
                check=True,
                env={'GOOGLE_APPLICATION_CREDENTIALS': key_file})
            log(f"Successful mounted filesystem at {mountpoint}")
            if 'allow_other' in mount_options:
                # These permissions are only important when the allow_other option
                # is set, and even then, they are just cosmetic for our purposes.
                run(["sudo", "chown", "user:user", mountpoint], check=False)
                run(["sudo", "chmod", "og-rwx", mountpoint], check=False)
            return
        except Exception as e:
            error = e
            log(f"Problem mounting filesystem at {mountpoint} -- '{e}'")
            time.sleep(random.random() * 5)
    if error is not None:
        raise error


###
# Update
###


def update():
    log("UPDATE")
    config = read_cloud_filesystem_json()
    if config is None:
        return
    network = config['network']
    filesystems = config['filesystems']
    update_mounted_filesystems(filesystems, network)
    update_caches([filesystem['id'] for filesystem in filesystems])


def update_mounted_filesystems(filesystems, network):
    should_be_mounted = []
    currently_mounted = mounted_filesystem_paths()
    # ensure that all the ones that should be mounted are mounted
    # and configured properly.
    error = None
    for filesystem in filesystems:
        if is_keydb_running(filesystem):
            # ensure replication for any running keydb always properly setup, since otherwise
            # that could block mounting below.
            update_replication(filesystem, network)
        try:
            path = mountpoint_fullpath(filesystem)
            if path in currently_mounted:
                update_filesystem(filesystem, network)
            else:
                mount_filesystem(filesystem, network)
        except Exception as e:
            log("WARNING: failed to mount/update ", e)
            error = e
            try:
                log("Something is wrong: attempt to ensure keydb running")
                # it can terminate in theory in hopefully very rare edge cases --
                # we start it again, potentially using
                # state from another server over the network.  self healing.
                ensure_keydb_running(filesystem, network)
            except Exception as e:
                log("WARNING: that failed too ", e)
        should_be_mounted.append(path)
    should_be_mounted = set(should_be_mounted)

    for path in currently_mounted:
        if path not in should_be_mounted:
            v = get_config(path)
            if v is not None:
                try:
                    unmount_filesystem(v[0])
                except Exception as e:
                    log("Error unmounting filesystem", path, e)
                    # we just try the next one for now; may try again in the future.
                    # Unmounting will fail if process has a file open.
    if error is not None:
        # something went seriously wrong with a MOUNT attempt.
        # throwing this is important, so that we retry update again
        # soon, rather than waiting for the filesystems state to change.
        raise error


def update_caches(filesystem_ids):
    # for cache location, see juicefs_paths
    cache = os.path.join(VAR, 'cache')
    for path in os.listdir(cache):
        if path.startswith('juicefs-'):
            try:
                id = int(path.split('-')[1])
                if id not in filesystem_ids:
                    update_filesystem_cache({'id': id})
            except Exception as e:
                log(f"update_caches: WARNING -- id={id}", e)


def update_filesystem_cache(filesystem):
    """
    Right now -- nothing for mounted
    For non-mounted filesystem, if it hasn't been mounted
    for FREE_NOT_MOUNTED_M minutes, we delete any local cache
    files.  Why:
      - Otherwise, the cache could use a lot of space, and the filesystem
        might be deleted or never used again.  A user could in theory
        clear the cache, but that's tedious.
      - We don't immediately delete the cache, because the user might just
        be unmounting the filesystem to make some configuration changes.
      - We could complicate the algorithm and data structures a lot and
        better take into account if the filesystem was deleted, etc.

    For now, we do not delete the rdb data file, since it is small and
    could be useful for disaster recovery.
    """
    log("update_filesystem_cache: ", filesystem['id'])
    cache = juicefs_paths(filesystem)['cache']
    if not os.path.exists(cache):
        log("update_filesystem_cache: cache dir does not exist", cache)
        return
    # For unmounted we check the time of last rbd file, and if it
    # longer than FREE_NOT_MOUNTED_M, we delete the cache
    paths = local_keydb_paths(filesystem)
    dump_rdb = paths['dump.rdb']
    last_active = get_mtime(dump_rdb, 0)
    if time.time() - last_active < FREE_NOT_MOUNTED_M * 60:
        log("update_filesystem_cache: active so don't mess with it",
            filesystem['id'])
        return
    log(f"update_filesystem_cache: not active, so deleting", filesystem['id'])
    try:
        shutil.rmtree(cache)
    except Exception as e:
        log(f"update_filesystem_cache: WARNING -- problem clearing cache for filesystem {filesystem['id']} -- '{e}'"
            )


# This should get done periodically, probably every 5s-20s, and
# at least once per minute.  It:
#   - copies keydb.rdb files to the bucket
#   - starts keydb if it crashes for some reason; keydb in multimaster mode
#     is not as robust as juicefs.  E.g., I observed a crash
#     " Internal error in RDB reading offset 800240, function at rdb.c:420 -> Invalid LZF compressed string . Terminating server after rdb file reading failure."
#     when stress testing with lots of nodes at once.  While down the filesystem
#     paused. Starting that same keydb again and things resumed fine.
#    - stops any "rogue" keydb's if somehow they got setup to run, but should not be.
def update_keydbs():
    config = read_cloud_filesystem_json()
    if config is None:
        return
    network = config['network']
    mounted = set(mounted_filesystem_paths())
    filesystems = config['filesystems']
    # Start or saving any that should be running.
    for filesystem in filesystems:
        path = mountpoint_fullpath(filesystem)
        if path not in mounted:
            # IMPORTANT: never do update_keydb_dump for an unmounted
            # filesystem (except right when unmounted) or we might
            # save bad or blank state, deleting all metadata
            continue
        try:
            update_keydb_dump(filesystem)
        except Exception as e:
            log("WARNING: failed to update_keydb_dump", e)
        ensure_keydb_running(filesystem, network)
    # Stop any that should not be running
    stop_extra_keydbs(filesystems)


def mounted_filesystem_paths():
    s = subprocess.run(['mount', '-t', 'fuse.juicefs'], capture_output=True)
    if s.returncode:
        raise RuntimeError(s.stderr)
    return [x.split()[2] for x in s.stdout.decode().splitlines()]


def update_juicefs_config(filesystem):
    key_file = gcs_key(filesystem)
    run(["juicefs", "config",
         get_redis_url(filesystem), "--yes", "--force"] +
        get_trash_days_option(filesystem),
        check=False,
        env={'GOOGLE_APPLICATION_CREDENTIALS': key_file})


def update_filesystem(filesystem, network):
    log('update_filesystem: ', 'id=', filesystem['id'],
        filesystem['mountpoint'])
    save_config(filesystem, network)
    update_replication(filesystem, network)
    update_keydb_dump(filesystem)
    update_juicefs_config(filesystem)


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


def get_quorum(network):
    num_nodes = 1 + len(network['peers'])
    # this is a quorum - we need 1 less than this slaves working to
    # have a quorum, since we count ourselves.
    quorum = int(num_nodes / 2) + 1
    return quorum


def add_replica(host, port):
    run(['keydb-cli', '-p', port, "replicaof", host, port])


def remove_replica(host, port):
    run(['keydb-cli', '-p', port, "replicaof", "remove", host, port])


def update_replication(filesystem, network):
    """
    Ensure that this keydb node is aware of every other running compute server
    on the VPN.  We're using a fully connected topology.  There are potential issues
    with speed, though for even a filesystem with 1 million+ files, the amount of
    data is really small.

    IMPORTANT: We have to do this when the network changes, even if the filesystem
    is not mounted!  Otherwise, we could get in a race condition where the filesystem
    can't mount because it's waiting on keydb to become writable, which is waiting
    on the wrong number of quorum members.
    """
    # First update the replicas that should be in our cluster
    port = filesystem['port']
    replicas = set(get_replicas(port))
    peers = set(network['peers'])
    for host in peers:
        if host not in replicas:
            add_replica(host, port)
    for host in replicas:
        if host not in peers:
            remove_replica(host, port)
    # Also update the quorum size so that writes stop if we are not part
    # of a quorum of replicas.  NOTE: This functionality uses my fork of keydb!
    run([
        'keydb-cli', '-p', port, 'CONFIG', 'SET', 'min-replicas-to-write',
        get_quorum(network) - 1
    ])


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
            unmount_filesystem(filesystem)
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
            run(["fusermount", "-u", mountpoint], check=True)
            return
        except:
            log("sleeping a second...")
            time.sleep(1)
            continue
    # always do this at least
    run(["umount", "-l", mountpoint], check=False)
    #raise RuntimeError(f"failed to unmount {mountpoint}")


def unmount_filesystem(filesystem):
    mountpoint = mountpoint_fullpath(filesystem)
    # unmount juicefs
    unmount_path(mountpoint)

    # stop keydb
    stop_keydb(filesystem)

    # copy over keydb dump to bucket -- there should be a new dump since it just ended
    clear_state(filesystem)
    update_keydb_dump(filesystem)

    # unmount the bucket -- be aggressive because keydb already stopped
    unmount_path(bucket_fullpath(filesystem), 3)

    # remove service account secret
    path = gcs_key_path(filesystem)
    if os.path.exists(path):
        os.unlink(path)

    # try to remove the directory if it happens to be empty
    # but no problem if this fails
    if os.path.exists(mountpoint):
        try:
            os.rmdir(mountpoint)
        except Exception as e:
            log(f"Could not remove {mountpoint} -- '{e}'")


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


###
# Maintenance
###


def filesystem_with_path(path):
    """
    Find the filesystem that has this path in it.
    """
    if not os.path.exists(path):
        raise ValueError(f"path '{path}' does not exist")
    abspath = os.path.abspath(path)
    config = read_cloud_filesystem_json()
    filesystems = config['filesystems']
    for filesystem in filesystems:
        if abspath.startswith(mountpoint_fullpath(filesystem)):
            return filesystem
    raise ValueError(f"unable to find filesystem whose mount contains {path}")


def fsck(path, repair=False, recursive=False, sync_dir_stat=False):
    filesystem = filesystem_with_path(path)
    mountpoint = mountpoint_fullpath(filesystem)
    abspath = os.path.abspath(path)
    if mountpoint == abspath:
        juicefs_abspath = '/'
    else:
        juicefs_abspath = abspath[len(mountpoint):]

    key_file = gcs_key(filesystem)

    cmd = ["juicefs", "fsck", get_redis_url(filesystem)]
    if juicefs_abspath != '/' or repair or recursive:
        cmd.append("--path")
        cmd.append(juicefs_abspath)
    if repair:
        cmd.append("--repair")
    if recursive:
        cmd.append("--recursive")
    if sync_dir_stat:
        cmd.append("--sync-dir-stat")
    log(' '.join(cmd))
    system(cmd, check=False, env={'GOOGLE_APPLICATION_CREDENTIALS': key_file})


def gc(path, compact=False, delete=False):
    filesystem = filesystem_with_path(path)
    key_file = gcs_key(filesystem)
    cmd = ["juicefs", "gc", get_redis_url(filesystem)]
    if compact:
        cmd.append("--compact")
    if delete:
        cmd.append("--delete")
    log(' '.join(cmd))
    system(cmd, check=False, env={'GOOGLE_APPLICATION_CREDENTIALS': key_file})


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
        default=INTERVAL_S,
        help=
        f"{CLOUD_FILESYSTEM_JSON} is polled every this many seconds for changes (default: {INTERVAL_S}s)"
    )

    args = parser.parse_args()
    CLOUD_FILESYSTEM_JSON = args.cloud_filesystem_json
    VAR = args.var
    SECRETS = args.secrets
    BUCKETS = args.buckets
    INTERVAL_S = args.interval

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
                    log(f"failed last time, so will retry mount in {INTERVAL_S} seconds"
                        )
                    time.sleep(INTERVAL_S)
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
