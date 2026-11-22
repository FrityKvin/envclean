#!/usr/bin/env python3
"""Preview, move, or restore an explicitly reviewed macOS cleanup list."""
import argparse
import ctypes
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

JOURNAL = 'recovery.jsonl'
CACHE_NAMES = {'Cache', 'Caches', 'Code Cache', 'GPUCache', 'ShaderCache', 'DawnGraphiteCache', 'DawnWebGPUCache', 'Crashpad', 'logs', 'Logs'}
APP_ROOTS = {
    'Library/Application Scripts', 'Library/Containers', 'Library/Group Containers',
    'Library/Preferences', 'Library/Application Support', 'Library/HTTPStorages',
    'Library/WebKit', 'Library/LaunchAgents',
}


def relative_path(text):
    path = Path(text)
    if not path.parts or path.is_absolute() or '..' in path.parts or str(path) != text:
        raise ValueError(f'Expected a canonical home-relative path: {text!r}')
    return path


def exists(path):
    return os.path.lexists(path)


def in_root(path, root):
    return Path(root) in path.parents


def permitted(relative, kind):
    path = relative.as_posix()
    if kind == 'broken-link':
        return str(relative.parent) in ('.local/bin', 'bin')
    if kind == 'dependency-tree':
        return relative.name == 'node_modules' and len(relative.parts) > 2 and relative.parts[0] not in {'Library', 'Applications'} and not relative.parts[0].startswith('.')
    if kind == 'app-remnant':
        parent = str(relative.parent)
        if parent in ('Library/LaunchAgents', 'Library/Preferences'):
            return relative.suffix == '.plist' and not relative.name.startswith('com.apple.')
        return parent in APP_ROOTS and not relative.name.startswith(('com.apple.', 'group.com.apple.', '.'))
    if kind == 'cache':
        return (
            any(in_root(relative, root) for root in ('Library/Caches', 'Library/Logs', '.cache'))
            or path in ('.npm/_cacache', '.npm/_logs')
            or (str(relative.parent) == '.npm/_npx' and bool(re.fullmatch(r'[0-9a-f]{16}', relative.name)))
            or in_root(relative, 'Library/pnpm/store')
            or in_root(relative, 'Library/Developer/Xcode/DerivedData')
            or (in_root(relative, 'Library/Application Support') and len(relative.parts) >= 4 and relative.name in CACHE_NAMES)
        )
    return False


def read_plan(path):
    data = json.loads(path.read_text())
    if not isinstance(data, list) or not data:
        raise ValueError('Plan must be a nonempty JSON array')
    reviewed = {}
    for entry in data:
        relative = relative_path(entry['path'])
        kind = entry['kind']
        if relative in reviewed or not permitted(relative, kind):
            raise ValueError(f'Duplicate or unsupported candidate: {relative}')
        reviewed[relative] = kind
    if any(parent in reviewed for path in reviewed for parent in path.parents):
        raise ValueError('Plan contains overlapping paths')
    return reviewed


def identity(info):
    return (info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode))


def verify_candidate(home, relative, kind, device):
    source = home / relative
    if source.parent.resolve(strict=True) != source.parent:
        raise ValueError('Source has a symbolic-link ancestor')
    info = source.lstat()
    if info.st_uid != os.getuid() or info.st_dev != device:
        raise ValueError('Candidate has a different owner or volume')
    if kind == 'broken-link':
        if not stat.S_ISLNK(info.st_mode):
            raise ValueError('Expected a symbolic link')
        try:
            source.stat()
        except FileNotFoundError:
            return identity(info)
        raise ValueError('Link is usable')
    if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
        raise ValueError('Expected a regular file or directory')
    if kind == 'dependency-tree':
        if not stat.S_ISDIR(info.st_mode):
            raise ValueError('Expected a dependency directory')
        reproducible = (source.parent / 'package.json').is_file() and any((source.parent / name).is_file() for name in ('package-lock.json', 'pnpm-lock.yaml', 'yarn.lock', 'bun.lock', 'bun.lockb'))
        if not reproducible:
            entries = list(source.iterdir())
            if entries:
                if len(entries) != 1 or entries[0].name != '.bin' or entries[0].is_symlink() or not entries[0].is_dir():
                    raise ValueError('Dependency tree does not have a local lockfile')
                for stub in entries[0].iterdir():
                    if not stub.is_symlink():
                        raise ValueError('Untracked dependency tree contains a real file')
                    try:
                        stub.stat()
                    except FileNotFoundError:
                        continue
                    raise ValueError('Untracked dependency tree contains a usable link')
    return identity(info)


def verify_not_open(source, signature):
    # Limit observation to this user's processes. The agent must check higher-level owners separately.
    if signature[2] == stat.S_IFLNK:
        return
    command = ['/usr/sbin/lsof', '-a', '-u', str(os.getuid()), '-Fp']
    if signature[2] == stat.S_IFDIR:
        command.append('+D')
    result = subprocess.run([*command, str(source)], capture_output=True, timeout=20)
    if result.returncode != 1 or result.stdout.strip() or result.stderr.strip():
        raise ValueError('Path is open or lsof could not establish that it is idle')
    result = subprocess.run(['/bin/ps', '-axww', '-o', 'pid=,ppid=,command='], capture_output=True, text=True, check=True, timeout=8)
    for line in result.stdout.splitlines():
        fields = line.split(None, 2)
        if len(fields) == 3 and int(fields[0]) not in {os.getpid(), os.getppid()} and str(source) in fields[2]:
            raise ValueError('A running command references this path')


def rename_exclusive(source, dest):
    rename = ctypes.CDLL(None, use_errno=True).renamex_np
    rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(os.fsencode(source), os.fsencode(dest), 0x00000004):  # Darwin RENAME_EXCL
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))


def log(handle, action, relative, **values):
    handle.write(json.dumps({'action': action, 'path': str(relative), **values}, ensure_ascii=False) + '\n')
    handle.flush()
    os.fsync(handle.fileno())


def move_items(home, trash, plan):
    device = trash.lstat().st_dev
    checked = {}
    failed = False
    for relative, kind in plan.items():
        try:
            signature = verify_candidate(home, relative, kind, device)
            verify_not_open(home / relative, signature)
            checked[relative] = (signature, kind)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            print(f'Skipped {relative}: {error}')
            failed = True
    if not checked:
        return 1
    date = datetime.now().astimezone().strftime('%Y-%m-%d-%H%M%S')
    batch = Path(tempfile.mkdtemp(prefix=f'macos-cleanup-{date}-', dir=trash))
    print(f'Recovery journal: {batch / JOURNAL}', flush=True)
    with (batch / JOURNAL).open('x', encoding='utf-8') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        for relative, (signature, kind) in checked.items():
            source = home / relative
            dest = batch / 'items' / relative
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                if verify_candidate(home, relative, kind, device) != signature:
                    raise ValueError('Candidate changed after inspection')
                verify_not_open(source, signature)
                log(handle, 'planned', relative, kind=kind, signature=list(signature))
                if identity(source.lstat()) != signature:
                    raise ValueError('Candidate changed before move')
                rename_exclusive(source, dest)
                if identity(dest.lstat()) != signature or exists(source):
                    raise ValueError('Move needs manual verification')
                log(handle, 'moved', relative)
                print(f'Moved: {relative}', flush=True)
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                failed = True
                log(handle, 'check', relative)
                print(f'Check {relative}: {error}', flush=True)
    return int(failed)


def restore_items(home, trash, journal, requested):
    journal = Path(os.path.abspath(journal.expanduser()))
    batch = journal.parent
    if journal.name != JOURNAL or batch.parent != trash or not batch.name.startswith('macos-cleanup-') or batch.resolve(strict=True) != batch:
        raise ValueError('Expected a cleanup journal in the current user’s Trash')
    failed = False
    fd = os.open(journal, os.O_RDWR | os.O_APPEND | os.O_NOFOLLOW)
    with os.fdopen(fd, 'a+', encoding='utf-8') as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise ValueError('Recovery journal must be a user-owned regular file')
        fcntl.flock(handle, fcntl.LOCK_EX)
        handle.seek(0)
        # Ignore only an incomplete trailing write. Journal entries are synced before moving.
        lines = handle.readlines()
        if lines and not lines[-1].endswith('\n'):
            lines.pop()
            handle.seek(0)
            handle.truncate(len(''.join(lines).encode('utf-8')))
        entries = [json.loads(line) for line in lines]
        planned = {relative_path(row['path']): row for row in entries if row['action'] == 'planned'}
        selected = [relative_path(text) for text in requested] if requested else list(planned)
        if not selected or any(relative not in planned for relative in selected):
            raise ValueError('Restore selection must be listed in the recovery journal')
        for relative in dict.fromkeys(selected):
            entry = planned[relative]
            source = batch / 'items' / relative
            dest = home / relative
            try:
                if not permitted(relative, entry['kind']):
                    raise ValueError('Journal contains an unsupported target')
                signature = tuple(entry['signature'])
                if not exists(source) and exists(dest) and identity(dest.lstat()) == signature:
                    print(f'Already at original path: {relative}')
                    continue
                if source.parent.resolve(strict=True) != source.parent or dest.parent.resolve(strict=True) != dest.parent:
                    raise ValueError('A parent path is missing or has a symbolic link')
                if identity(source.lstat()) != signature:
                    raise ValueError('Backup identity changed')
                if exists(dest):
                    raise ValueError('Original path exists. Backups never overwrite.')
                rename_exclusive(source, dest)
                if exists(source) or identity(dest.lstat()) != signature:
                    raise ValueError('Restore needs manual verification')
                log(handle, 'restored', relative)
                print(f'Restored: {relative}')
            except (OSError, ValueError) as error:
                failed = True
                print(f'Check {relative}: {error}')
    return int(failed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    plan = commands.add_parser('plan', help='Validate candidates. Never moves files.')
    plan.add_argument('file', type=Path)
    apply = commands.add_parser('apply', help='Move an authorized list to a dedicated Trash folder.')
    apply.add_argument('file', type=Path)
    restore = commands.add_parser('restore', help='Restore selected entries, or the whole recovery set.')
    restore.add_argument('file', type=Path)
    restore.add_argument('--item', action='append', default=[])
    args = parser.parse_args()
    if sys.platform != 'darwin' or os.geteuid() == 0:
        parser.error('requires macOS and a normal user account')
    home = Path.home().resolve(strict=True)
    trash = home / '.Trash'
    try:
        info = trash.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
            raise ValueError('Trash must be a user-owned directory')
        if args.command == 'restore':
            return restore_items(home, trash, args.file, args.item)
        candidates = read_plan(args.file)
        if args.command == 'apply':
            return move_items(home, trash, candidates)
        failed = False
        for relative, kind in candidates.items():
            try:
                signature = verify_candidate(home, relative, kind, info.st_dev)
                verify_not_open(home / relative, signature)
                print(f'Eligible for reviewed move: {relative}')
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                failed = True
                print(f'Skipped {relative}: {error}')
        return int(failed)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'Unable to continue: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
