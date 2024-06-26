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
            "stats are only available right now for CloudFS paths")
        # system(["dstat", mountpoint])


def create_backup(args):
    (fstype, mountpoint) = filesystem(args.mountpoint)
    repo = args.repo if args.repo else ''
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
            "backup is only implemented right now for CloudFS paths")


def rm_backup(args):
    (fstype, mountpoint) = filesystem(args.mountpoint)
    repo = args.repo if args.repo else ''
    if fstype == JUICEFS_FSTYPE:
        v = [
            'docker', 'exec', '-it', '-w', '/scripts', 'cloud-filesystem',
            'python3', '-c',
            f"from cloud_filesystem import rm_backup; rm_backup('{mountpoint}', timestamp='{args.timestamp}', repo='{repo}')"
        ]
        system(v, check=False)
    else:
        raise RuntimeError(
            "backup is only implemented right now for CloudFS paths")


def mount_backups(args):
    (fstype, mountpoint) = filesystem(args.mountpoint)
    repo = args.repo if args.repo else ''
    if fstype == JUICEFS_FSTYPE:
        v = [
            'docker', 'exec', '-it', '-w', '/scripts', 'cloud-filesystem',
            'python3', '-c',
            f"from cloud_filesystem import mount_backups; mount_backups('{mountpoint}', repo='{repo}')"
        ]
        system(v, check=False)
    else:
        raise RuntimeError(
            "backup is only implemented right now for CloudFS paths")


def juicefs_fsck(args):
    path = os.path.abspath(args.path)
    v = [
        'docker', 'exec', '-it', '-w', '/scripts', 'cloud-filesystem',
        'python3', '-c',
        f"from cloud_filesystem import fsck; fsck('{path}',repair={args.repair},recursive={args.recursive},sync_dir_stat={args.sync_dir_stat})"
    ]
    system(v, check=False)


def fsck(args):
    if is_juicefs(args.path):
        juicefs_fsck(args)
    else:
        raise RuntimeError("fsck only implemented for Cloud Filesystems")


def compact(args):
    if is_juicefs(args.path):
        juicefs(['compact', args.path])
    else:
        raise RuntimeError("compact only implemented for Cloud Filesystems")


def juicefs_gc(args):
    path = os.path.abspath(args.path)
    v = [
        'docker', 'exec', '-it', '-w', '/scripts', 'cloud-filesystem',
        'python3', '-c',
        f"from cloud_filesystem import gc; gc('{path}',compact={args.compact},delete={args.delete})"
    ]
    system(v, check=False)


def gc(args):
    if is_juicefs(args.path):
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


def warmup(paths):
    for path in paths:
        print(f"warmup '{path}'")
        if is_juicefs(path):
            juicefs(['warmup', '--threads', str(JUICEFS_THREADS), path])
        else:
            print(
                f"warmup currently only implemented for Cloud Filesystems - excluding '{path}'"
            )


def main():
    parser = argparse.ArgumentParser(prog='cocalc',
                                     description='CoCalc command line utility')
    subparsers = parser.add_subparsers(dest='command')

    ### BACKUP COMMANDS
    backup_parser = subparsers.add_parser('backup', help='Backup commands')
    backup_subparsers = backup_parser.add_subparsers(dest='backup_command')

    create_backup_parser = backup_subparsers.add_parser(
        'create',
        help=
        'Create a backup of a Cloud Filesystem and mount backups at [mountpoint]/.backups'
    )
    create_backup_parser.add_argument(
        '--mountpoint',
        default='.',
        help='Path in filesystem to backup (default: current working directory)'
    )
    create_backup_parser.add_argument(
        '--repo',
        help=
        "Path to backup repository.  This defaults to [mountpoint]/.bup inside the Cloud Filesystem, but you can specify any writable directory.  You can backup many different cloud filesystems to the same repo, and the backups will be efficiently deduplicated between them."
    )

    rm_backup_parser = backup_subparsers.add_parser(
        'rm', help='Delete a backup of a Cloud Filesystem')
    rm_backup_parser.add_argument(
        '--mountpoint',
        default='.',
        help=
        'Path in filesystem to backup.  (default: current working directory)')
    rm_backup_parser.add_argument('--repo', help="Path to backup repository.")
    rm_backup_parser.add_argument('timestamp', help='Timestamp of the backup.')

    mount_backup_parser = backup_subparsers.add_parser(
        'mount',
        help=
        'Mount backups of a Cloud Filesystem so you can browse them at [mountpoint]/.backups'
    )
    mount_backup_parser.add_argument(
        '--mountpoint',
        default='.',
        help=
        'Path in filesystem whose backups we will mount (default: current working directory)'
    )
    mount_backup_parser.add_argument('--repo',
                                     help="Path to backup repository.")

    ### END BACKUP COMMANDS

    # Filesystem commands
    fs_parser = subparsers.add_parser('filesystem',
                                      aliases=['fs'],
                                      help='Filesystem commands')
    fs_subparsers = fs_parser.add_subparsers(dest='fs_command')

    # compact subcommand
    compact_parser = fs_subparsers.add_parser(
        'compact',
        help=
        'Clean up non-contiguous slices to improve read performance (CloudFS only) '
    )
    compact_parser.add_argument('path', help='Filesystem path to compact')

    # fsck subcommand
    fsck_parser = fs_subparsers.add_parser(
        'fsck', help='Check filesystem consistency (CloudFS only)')
    fsck_parser.add_argument(
        'path', help='Path to a cloud filesystem or files/directories in one')
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
    gc_parser = fs_subparsers.add_parser(
        'gc', help='Garbage collect filesystem objects (CloudFS only) ')
    gc_parser.add_argument('path', help='Path to a cloud filesystem')
    gc_parser.add_argument('--compact',
                           action='store_true',
                           help="Compact slices")
    gc_parser.add_argument('--delete',
                           action='store_true',
                           help='Delete leaked objects')

    # stats subcommand
    stats_parser = fs_subparsers.add_parser(
        'stats', help='Show performance statistics (CloudFS only) ')
    stats_parser.add_argument('path', help='Path for gathering statistics')

    # sync subcommand
    sync_parser = fs_subparsers.add_parser(
        'sync', help='Efficiently sync files (similar to rsync)')
    sync_parser.add_argument('source', help='Source path')
    sync_parser.add_argument('dest', help='Destination path')
    sync_parser.add_argument('--delete',
                             action='store_true',
                             help='Delete extraneous files')

    # warmup subcommand
    warmup_parser = fs_subparsers.add_parser(
        'warmup', help='Filesystem warmup (CloudFS only) ')
    warmup_parser.add_argument('paths', nargs='+', help='Paths to warm up')

    # Parse the arguments
    args = parser.parse_args()

    if args.command == 'backup':
        if args.backup_command == 'create':
            return create_backup(args)
        elif args.backup_command == 'rm':
            return rm_backup(args)
        elif args.backup_command == 'mount':
            return mount_backups(args)
    elif args.command == 'fs':
        if args.fs_command == 'compact':
            return compact(args)
        elif args.fs_command == 'fsck':
            return fsck(args)
        elif args.fs_command == 'gc':
            return gc(args)
        elif args.fs_command == 'stats':
            return stats(args)
        elif args.fs_command == 'sync':
            return sync(args)
        elif args.fs_command == 'warmup':
            return warmup(args.paths)

    parser.print_help()


if __name__ == '__main__':
    main()
