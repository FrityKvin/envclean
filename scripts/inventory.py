#!/usr/bin/env python3
"""Collect bounded, read-only disk measurements and compare local baselines."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

DEFAULT_PATHS = (
    '.Trash', 'Library/Caches', 'Library/Logs', 'Library/Application Support/MobileSync/Backup',
    'Library/Developer/Xcode/DerivedData', 'Library/Developer/Xcode/Archives',
    'Library/Developer/CoreSimulator', '.npm/_cacache', '.npm/_npx',
    'Library/pnpm/store', '.cache/uv', 'Library/Caches/ms-playwright',
    '.ollama/models', '/opt/homebrew/Cellar', '/opt/homebrew/Caskroom', '/usr/local/Cellar',
)


def measure_path(path, timeout):
    row = {'path': str(path), 'allocated_bytes': None}
    try:
        path.lstat()
    except FileNotFoundError:
        return row | {'status': 'missing'}
    except OSError:
        return row | {'status': 'inaccessible'}
    try:
        result = subprocess.run(['/usr/bin/du', '-sk', str(path)], capture_output=True, text=True, timeout=timeout)
        size, _, _ = result.stdout.strip().partition('\t')
        if size.isdecimal():
            row['allocated_bytes'] = int(size) * 1024
        status = 'ok' if result.returncode == 0 and row['allocated_bytes'] is not None else 'partial'
    except subprocess.TimeoutExpired:
        status = 'timeout'
    return row | {'status': status}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path', action='append', help='Exact path to measure. Repeat to replace the default roots.')
    parser.add_argument('--volume', default='~', help='Existing path on the target volume, default home.')
    parser.add_argument('--timeout', type=int, default=8, help='Seconds per path, default 8.')
    parser.add_argument('--previous', type=Path, help='Compare with an earlier JSON result from this script.')
    args = parser.parse_args()
    if sys.platform != 'darwin' or args.timeout < 1:
        parser.error('requires macOS and a positive timeout')
    home = Path.home()
    scope = Path(args.volume).expanduser().resolve(strict=True)
    paths = tuple(dict.fromkeys(Path(os.path.abspath(Path(p).expanduser())) for p in args.path)) if args.path else tuple(home / p for p in DEFAULT_PATHS)
    with ThreadPoolExecutor(max_workers=4) as executor:
        measurements = list(executor.map(lambda p: measure_path(p, args.timeout), paths))
    volume = scope.stat()
    fs = os.statvfs(scope)
    device = subprocess.run(['/bin/df', '-k', str(scope)], capture_output=True, text=True, check=True).stdout.splitlines()[1].split()[0]
    output = {
        'schema': 1,
        'observed_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'volume': {'anchor': str(scope), 'filesystem_device': device, 'device_id': volume.st_dev, 'available_bytes': fs.f_bavail * fs.f_frsize},
        'measurements': measurements,
    }
    if args.previous:
        previous = json.loads(args.previous.read_text())
        if previous.get('schema') != 1:
            parser.error('unsupported baseline schema')
        prior_volume = previous['volume']
        keys = ('anchor', 'filesystem_device', 'device_id')
        if all(prior_volume.get(key) == output['volume'][key] for key in keys):
            output['available_delta_bytes'] = output['volume']['available_bytes'] - prior_volume['available_bytes']
        old = {r['path']: r['allocated_bytes'] for r in previous['measurements'] if r['status'] == 'ok'}
        output['growth_bytes'] = {r['path']: r['allocated_bytes'] - old[r['path']] for r in measurements if r['status'] == 'ok' and r['path'] in old}
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
