#!/usr/bin/env python3
"""


"""

import argparse, json, os, subprocess, tempfile, time

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


def init(storage_json):
    print("INIT", storage_json)
    storage = read_storage_json(storage_json)
    if storage is None:
        print("no ", storage_json, " so nothing to do")
        return
    for filesystem in storage['filesystems']:
        init_filesystem(filesystem, storage['network'])


def init_filesystem(filesystem, network):
    mount_bucket(filesystem)
    start_keydb(filesystem, network)
    mount_juicefs(filesystem)


def bucket_path(filesystem):
    return f"/mnt/bucket-{filesystem['id']}"


def run(cmd):
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
            bucket = bucket_path(filesystem)
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
    pass


def mount_juicefs(filesystem):
    pass


def update(storage_json):
    print("UPDATE", storage_json)
    storage = read_storage_json(storage_json)
    if storage is None:
        print("no ", storage_json, " so nothing to do")
        return
    for filesystem in storage['filesystems']:
        update_filesystem(filesystem, storage['network'])


def update_filesystem(filesystem, network):
    print('update_filesystem: TODO')
    pass


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
    init(storage_json)
    while True:
        try:
            wait_until_file_changes(storage_json, last_known_mtime)
            last_known_mtime = get_mtime(storage_json)
            update(storage_json)
        except Exception as e:
            print(f"Error -- '{cmd}'")
            pass
