#!/usr/bin/env python3
"""


"""

import argparse, json, os, time

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
    print('init')
    pass


def update(storage_json):
    print('update')
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
