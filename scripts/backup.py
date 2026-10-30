"""Read-only plan by default. Explicit execution copies into a new folder; no restore/delete API."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
from uuid import uuid4


def metadata(path):
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
        raise ValueError('Symlink/reparse point refused: ' + str(path))
    return info


def inventory(sources):
    entries, missing = {}, []
    for label, item in sources.items():
        if not re.fullmatch(r'[a-z][a-z0-9_]*', label):
            raise ValueError('Invalid source label')
        root = Path(item['path']).absolute()
        # Reject links in parents too, before resolve can hide them.
        for parent in reversed([root, *root.parents]):
            if parent.exists():
                metadata(parent)
        if not root.exists():
            if item['required']:
                raise FileNotFoundError(root)
            missing.append(str(root))
            continue
        def visit(path):
            info = metadata(path)
            if path.is_dir():
                for child in sorted(path.iterdir()):
                    visit(child)
            elif path.is_file():
                relative = path.relative_to(root) if root.is_dir() else Path(root.name)
                entries[(Path(label) / relative).as_posix()] = {
                    'source': str(path), 'bytes': info.st_size, 'mtime_ns': info.st_mtime_ns}
            else:
                raise ValueError('Unsupported file: ' + str(path))
        visit(root)
        if item['required'] and not any(key.startswith(label + '/') for key in entries):
            raise ValueError('Required source is empty: ' + str(root))
    return entries, missing


def ensure_closed():
    if os.name != 'nt':
        raise RuntimeError('Backup execution requires Windows process checks')
    check = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
        "$ErrorActionPreference='Stop'; Get-Process | Where-Object { $_.ProcessName -in @('enshrouded','enshrouded_server','steam') } | Select-Object -ExpandProperty ProcessName"],
        capture_output=True, text=True, check=True)
    if check.stdout.strip():
        raise RuntimeError('Close game/server and exit Steam after sync: ' + check.stdout.strip())


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare(config):
    destination = Path(config['destination']).absolute()
    for parent in reversed([destination, *destination.parents]):
        if parent.exists():
            metadata(parent)
    destination = destination.resolve()
    for item in config['sources'].values():
        source = Path(item['path']).resolve()
        if destination.is_relative_to(source) or source.is_relative_to(destination):
            raise ValueError('Backup/source paths overlap')
    entries, missing = inventory(config['sources'])
    existing = destination
    while not existing.exists():
        existing = existing.parent
    total = sum(item['bytes'] for item in entries.values())
    free = shutil.disk_usage(existing).free
    if free < total + 1024**3:
        raise OSError('Insufficient space (requires copy size plus 1 GiB)')
    return destination, entries, {'mode': 'plan_only', 'files': len(entries), 'bytes': total,
                                'free_bytes': free, 'destination': str(destination),
                                'missing_optional': missing, 'sources': config['sources']}


def execute(config):
    ensure_closed()
    destination, entries, report = prepare(config)
    output = destination / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid4().hex[:8])
    output.mkdir(parents=True, exist_ok=False)
    manifest = output / 'manifest.json'
    report.update(mode='copy_in_progress', verified=False, entries=entries)
    manifest.write_text(json.dumps(report, indent=2), encoding='utf-8')
    for key, entry in entries.items():
        src, dst = Path(entry['source']), output / key
        before = metadata(src)
        if (before.st_size, before.st_mtime_ns) != (entry['bytes'], entry['mtime_ns']):
            raise RuntimeError('Source changed since planning: ' + str(src))
        dst.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        with src.open('rb') as reader, dst.open('xb') as writer:
            while block := reader.read(4 * 1024 * 1024):
                digest.update(block)
                writer.write(block)
            writer.flush()
            os.fsync(writer.fileno())
        # Read source again as well as destination: never certify an unstable copy.
        expected = digest.hexdigest()
        if sha256(src) != expected or sha256(dst) != expected:
            raise RuntimeError('Hash mismatch: ' + str(src))
        entry['sha256'] = expected
    ensure_closed()
    after, _ = inventory(config['sources'])
    if {key: {k: v for k, v in entry.items() if k != 'sha256'} for key, entry in entries.items()} != after:
        raise RuntimeError('Source tree changed during backup; copy is not verified')
    report.update(mode='completed', verified=True)
    manifest.write_text(json.dumps(report, indent=2), encoding='utf-8')
    return {'ok': True, 'verified': True, 'manifest': str(manifest), 'files': len(entries)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='config/first-test-backup.json')
    parser.add_argument('--execute', action='store_true', help='Copy after closing game and Steam')
    args = parser.parse_args()
    try:
        config = json.loads(Path(args.config).read_text(encoding='utf-8'))
        result = execute(config) if args.execute else prepare(config)[2]
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc), 'verified': False}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
