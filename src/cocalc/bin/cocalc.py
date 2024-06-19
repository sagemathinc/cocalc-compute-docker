#!/usr/bin/env python3

import subprocess, shlex, argparse, os, sys

JUICEFS_THREADS = 100
JUICEFS_FSTYPE = "fuse.juicefs"


def system(s, check=True):
    if isinstance(s, str):
        v = shlex.split(s)
    else:
        v = s
    process = subprocess.Popen(v)
    exit_code = process.wait()
    if exit_code and check:
        sys.exit(exit_code)


def run(s, check=True):
    if isinstance(s, str):
        v = shlex.split(s)
    else:
        v = s
    process = subprocess.Popen(v,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    exit_code = process.wait()
    if exit_code and check:
        sys.exit(exit_code)
    return exit_code, stdout.decode(), stderr.decode()


def filesystem(path):
    """
    Returns filesystem type as the first argument and the mountpoint as the second.
    """
    (_, stdout, _) = run(['df', '--output=fstype,target', path], check=True)
    v = stdout.splitlines()[-1]
    return v.split()


def is_juicefs(path):
    (exit_code, _, _) = run(['df', '--type', 'fuse.juicefs', path],
                            check=False)
    return exit_code == 0


def rmr(args):
    raise NotImplementedError


def stats(args):
    (fstype, mountpoint) = filesystem(args.path)
    if fstype == JUICEFS_FSTYPE:
        system(["juicefs", "stats", mountpoint])
    else:
        raise RuntimeError(
            "stats are only available right now for CloudFS paths")
        # system(["dstat", mountpoint])


def sync(args):
    print(f"sync {args.source} to {args.dest}")
    v = [
        'docker', 'exec', '-it', '-w',
        os.path.abspath(os.curdir), 'cloud-filesystem', 'juicefs', 'sync',
        '--threads',
        str(JUICEFS_THREADS)
    ]
    if (args.delete):
        v.append("--delete-dst")
    v.append(args.source)
    v.append(args.dest)
    system(v)


def warmup(paths):
    for path in paths:
        print(f"warmup '{path}'")
        if is_juicefs(path):
            system([
                'docker', 'exec', '-it', '-w',
                os.path.abspath(os.curdir), 'cloud-filesystem', 'juicefs',
                'warmup', '--threads',
                str(JUICEFS_THREADS), path
            ])
        else:
            print(
                f"warmup currently only implemented for Cloud Filesystems - excluding '{path}'"
            )


def main():
    parser = argparse.ArgumentParser(prog='cocalc',
                                     description='CoCalc command line utility')
    subparsers = parser.add_subparsers(dest='command')

    # rmr subcommand
#     rmr_parser = subparsers.add_parser('rmr',
#                                        help='Remove directories recursively.')
#     rmr_parser.add_argument(
#         'paths',
#         nargs='+',
#         help=
#         'Paths to remove. This is more efficient than "rm -rf" for CloudFS directories.'
#     )

    # stats subcommand
    stats_parser = subparsers.add_parser(
        'stats', help='Show realtime performance statistics of a filesystem.')
    stats_parser.add_argument(
        'path',
        help=
        'Filesystem path.  Statistics will be shown for the filesystem containing this path.  For CloudFS this includes information about objects being uploaded/downloaded to cloud storage.'
    )

    # sync subcommand
    sync_parser = subparsers.add_parser(
        'sync',
        help=
        'Efficiently sync files from a source directory to a dest directory (similar to rsync).  This is the most efficient way to copy files to/from/between CloudFS directories, but can be used anywhere.'
    )
    sync_parser.add_argument('source', help='Source path')
    sync_parser.add_argument('dest', help='Destination path')
    sync_parser.add_argument('--delete',
                             action='store_true',
                             help='Delete extraneous files from dest dirs')

    # warmup subcommand
    warmup_parser = subparsers.add_parser(
        'warmup',
        help=
        'Perform filesystem warmup for network mounted paths.  For CloudFS, this downloads all the chunks for the given path to local cache (the cache uses up to 90%% of your disk) for much faster subsequent access.  Currently only implemented for CloudFS.'
    )
    warmup_parser.add_argument('paths', nargs='+', help='Paths to warmup')

    # Parse the arguments
    args = parser.parse_args()

    if args.command == 'warmup':
        warmup(args.paths)
    elif args.command == 'sync':
        sync(args)
    elif args.command == 'rmr':
        rmr(args)
    elif args.command == 'stats':
        stats(args)


if __name__ == '__main__':
    main()
