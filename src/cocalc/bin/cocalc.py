#!/usr/bin/env python3

import subprocess, shlex, argparse, os, sys

def system(s):
    if isinstance(s, str):
        v = shlex.split(s)
        print(s)
    else:
        v = s
        print(' '.join(s))
    print(v)
    process = subprocess.Popen(v)
    exit_code = process.wait()
    return exit_code


def warmup(paths):
    for path in paths:
        print(f"Performing warmup on {path}")
        w = os.path.abspath(os.curdir)
        system(
            f"docker exec -it -w '{shlex.quote(w)}' cloud-filesystem juicefs warmup '{shlex.quote(path)}'"
        )


def sync(path1, path2):
    print(f"Syncing {path1} with {path2}")
    # Implement sync logic here


def start_compute_server(server_id):
    print(f"Starting compute server with ID {server_id}")
    # Implement compute server start logic here


def main():
    parser = argparse.ArgumentParser(prog='cocalc',
                                     description='CoCalc command line utility')
    subparsers = parser.add_subparsers(dest='command')

    # warmup subcommand
    warmup_parser = subparsers.add_parser('warmup',
                                          help='Perform filesystem warmup')
    warmup_parser.add_argument('paths', nargs='+', help='Paths to warmup')

    # sync subcommand
    sync_parser = subparsers.add_parser('sync', help='Sync directories')
    sync_parser.add_argument('path1', help='Source path')
    sync_parser.add_argument('path2', help='Destination path')

    # compute-server subcommand
    compute_server_parser = subparsers.add_parser('compute-server',
                                                  help='Manage compute server')
    compute_server_parser.add_argument(
        'action',
        choices=['start'],
        help='Action to perform on compute server')
    compute_server_parser.add_argument('--id',
                                       required=True,
                                       help='ID of the compute server')

    # Parse the arguments
    args = parser.parse_args()

    if args.command == 'warmup':
        warmup(args.paths)
    elif args.command == 'sync':
        sync(args.path1, args.path2)
    elif args.command == 'compute-server':
        if args.action == 'start':
            start_compute_server(args.id)


if __name__ == '__main__':
    main()
