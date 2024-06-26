#!/usr/bin/env python3

import subprocess, shlex, argparse, os, sys

JUICEFS_THREADS = 100
JUICEFS_FSTYPE = "fuse.juicefs"
CLOUDFS_ONLY = 'CloudFS only'


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
    if not os.path.isdir(path):
        path = os.path.dirname(path)
    (exit_code, _, _) = run(['df', '--type', JUICEFS_FSTYPE, path],
                            check=False)
    return exit_code == 0


def rmr(args):
    raise NotImplementedError


def stats(args):
    (fstype, mountpoint) = filesystem(args.path)
    if fstype == JUICEFS_FSTYPE:
        juicefs(['stats', mountpoint])
    else:
        raise RuntimeError(
            "stats are only currently implemented for CloudFS paths")
        # system(["dstat", mountpoint])


## BACKUPS


def create_backup(path, repo):
    (fstype, mountpoint) = filesystem(path)
    repo = repo if repo else ''
    if fstype == JUICEFS_FSTYPE:
        v = [
            'docker', 'exec', '-it', '-w', '/scripts', 'cloud-filesystem',
            'python3', '-c',
            f"from cloud_filesystem import create_backup; create_backup('{mountpoint}', repo='{repo}')"
        ]
        print(v)
        system(v, check=False)
    else:
        raise RuntimeError(
            "backup is only currently implemented for CloudFS paths")


def rm_backup(path, repo, timestamp):
    (fstype, mountpoint) = filesystem(path)
    repo = repo if repo else ''
    if fstype == JUICEFS_FSTYPE:
        v = [
            'docker', 'exec', '-it', '-w', '/scripts', 'cloud-filesystem',
            'python3', '-c',
            f"from cloud_filesystem import rm_backup; rm_backup('{mountpoint}', timestamp='{timestamp}', repo='{repo}')"
        ]
        system(v, check=False)
    else:
        raise RuntimeError(
            "backup is only currently implemented for CloudFS paths")


def mount_backups(path, repo):
    (fstype, mountpoint) = filesystem(path)
    repo = repo if repo else ''
    if fstype == JUICEFS_FSTYPE:
        v = [
            'docker', 'exec', '-it', '-w', '/scripts', 'cloud-filesystem',
            'python3', '-c',
            f"from cloud_filesystem import mount_backups; mount_backups('{mountpoint}', repo='{repo}')"
        ]
        system(v, check=False)
    else:
        raise RuntimeError(
            "backup is only currently implemented for CloudFS paths")


def backup(args):
    if args.rm:
        for timestamp in args.rm.split(','):
            rm_backup('.', args.repo, timestamp)
    elif args.mount:
        mount_backups('.', args.repo)
    else:
        create_backup('.', args.repo)


def juicefs_fsck(args):
    path = os.path.abspath('.')
    v = [
        'docker', 'exec', '-it', '-w', '/scripts', 'cloud-filesystem',
        'python3', '-c',
        f"from cloud_filesystem import fsck; fsck('{path}',repair={args.repair},recursive={args.recursive},sync_dir_stat={args.sync_dir_stat})"
    ]
    system(v, check=False)


def fsck(args):
    if is_juicefs("."):
        juicefs_fsck(args)
    else:
        raise RuntimeError("fsck only implemented for Cloud Filesystems")


def compact(args):
    if is_juicefs(args.path):
        juicefs(['compact', args.path])
    else:
        raise RuntimeError("compact only implemented for Cloud Filesystems")


def juicefs_gc(args):
    path = os.path.abspath('.')
    v = [
        'docker', 'exec', '-it', '-w', '/scripts', 'cloud-filesystem',
        'python3', '-c',
        f"from cloud_filesystem import gc; gc('{path}',compact={args.compact},delete={args.delete})"
    ]
    system(v, check=False)


def gc(args):
    if is_juicefs('.'):
        juicefs_gc(args)
    else:
        raise RuntimeError("gc only implemented for Cloud Filesystems")


def juicefs(args, **kwds):
    v = [
        'docker', 'exec', '-it', '-w',
        os.path.abspath(os.curdir), 'cloud-filesystem', 'juicefs'
    ] + args
    system(v, **kwds)


def sync(args):
    print(f"sync {args.source} to {args.dest}")
    v = ['sync', '--threads', str(JUICEFS_THREADS)]
    if (args.delete):
        v.append("--delete-dst")
    v.append(args.source)
    v.append(args.dest)
    juicefs(v)


def warmup(path='.'):
    print(f"warmup '{path}'")
    if is_juicefs(path):
        juicefs(['warmup', '--threads', str(JUICEFS_THREADS), path])
    else:
        print(f"warmup is currently {CLOUDFS_ONLY}")


def main():
    parser = argparse.ArgumentParser(prog='cocalc',
                                     description='CoCalc command line utility')
    subparsers = parser.add_subparsers(dest='command')

    ### BACKUP COMMANDS
    backup_parser = subparsers.add_parser(
        'backup',
        help='Create and manage incremental backups',
        description=
        f'By default, creates a new backup of the filesystem containing the current working directory.  Use the --rm option to delete existing backups, the --mount option to mount and browse backups, and the --repo option to specify a repo other than "[filesystem]/.bup".  {CLOUDFS_ONLY}'
    )
    backup_parser.add_argument(
        'repo',
        default='',
        nargs='?',
        help=
        'Optional path to a backup directory. The default is [mountpoint]/.bup inside the filesystem containing the working directory.  You can specify any writable directory, and you can backup multiple filesystems to the same repo.'
    )
    backup_parser.add_argument(
        '--rm',
        help=
        'Instead of creating a backup, delete one more backups.  Separate multiple timestamps with a comma.'
    )
    backup_parser.add_argument(
        '--mount',
        action='store_true',
        help=
        'Instead of creating a new backup, just mount the backups at [mountpoint]/.backups.  This also happens automatically whenever you make a new backup.'
    )

    ### END BACKUP COMMAND

    # Filesystem commands
    cloudfs_parser = subparsers.add_parser(
        'cloudfs',
        help=f'{CLOUDFS_ONLY} management commands')
    cloudfs_subparsers = cloudfs_parser.add_subparsers(dest='cloudfs_command')

    # compact subcommand
    compact_parser = cloudfs_subparsers.add_parser(
        'compact',
        help=f'Clean up non-contiguous slices to improve read performance')
    compact_parser.add_argument('path',
                                nargs='?',
                                default='.',
                                help='Filesystem path to compact')

    # fsck subcommand
    fsck_parser = cloudfs_subparsers.add_parser(
        'fsck', help=f'Check filesystem consistency')
    fsck_parser.add_argument('--repair',
                             action='store_true',
                             help="Repair broken paths")
    fsck_parser.add_argument('--recursive',
                             action='store_true',
                             help='Check directories recursively')
    fsck_parser.add_argument('--sync-dir-stat',
                             action='store_true',
                             help='Sync directory stats')

    # gc subcommand
    gc_parser = cloudfs_subparsers.add_parser(
        'gc', help=f'Garbage collect filesystem objects')
    gc_parser.add_argument('--compact',
                           action='store_true',
                           help="Compact slices")
    gc_parser.add_argument('--delete',
                           action='store_true',
                           help='Delete leaked objects')

    # stats subcommand
    stats_parser = cloudfs_subparsers.add_parser(
        'stats', help=f'Show performance statistics')
    stats_parser.add_argument('path',
                              default='.',
                              nargs='?',
                              help='Path for gathering statistics')

    # sync subcommand
    sync_parser = subparsers.add_parser(
        'sync',
        help='Sync files from one directory to another',
        description=
        'This is similar to rsync, but more aware of filesystem; in particular it is optimized for the Cloud Filesystem.'
    )
    sync_parser.add_argument(
        'source', help='Source path (subdirectory of HOME directory)')
    sync_parser.add_argument(
        'dest', help='Destination path (subdirectory of HOME directory)')
    sync_parser.add_argument('--delete',
                             action='store_true',
                             help='Delete extraneous files')

    # warmup subcommand
    warmup_parser = subparsers.add_parser(
        'warmup',
        help='Warmup filesystem cache',
        description=
        f"Make current working directory FAST by doownloading data to the local cache. Currently {CLOUDFS_ONLY}."
    )

    # Parse the arguments
    args = parser.parse_args()

    if args.command == 'backup':
        return backup(args)
    elif args.command == 'sync':
        return sync(args)
    elif args.command == 'warmup':
        return warmup()
    elif args.command == 'cloudfs':
        if args.cloudfs_command == 'compact':
            return compact(args)
        elif args.cloudfs_command == 'fsck':
            return fsck(args)
        elif args.cloudfs_command == 'gc':
            return gc(args)
        elif args.cloudfs_command == 'stats':
            return stats(args)

    parser.print_help()


if __name__ == '__main__':
    main()
