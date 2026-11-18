"""Exclusive project-side backup of an explicitly accepted post-Steam baseline."""
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import shutil

from .compatibility import file_hash, fingerprint
from .recovery import measure, no_links, target, write_json_new

GAME_PAYLOAD = ('enshrouded.exe', 'enshrouded.kfc', 'enshrouded.kfc_resources', 'enshrouded_local.json')


def verify(folder, expected_manifest_sha=None):
    no_links(folder)
    path = folder / 'manifest.json'
    if expected_manifest_sha and file_hash(path) != expected_manifest_sha:
        raise ValueError('BACKUP_MANIFEST_CHANGED')
    manifest = json.loads(path.read_text(encoding='utf-8'))
    if manifest.get('format') != 'aic_clean_backup_v1':
        raise ValueError('BACKUP_FORMAT')
    expected = {'manifest.json', 'baseline.json', 'future-targets.json'}
    for name, entry in manifest['payload'].items():
        if measure(target(folder, name)) != entry:
            raise ValueError('BACKUP_PAYLOAD_CHANGED:' + name)
        expected.add(name)
    for name in ('baseline.json', 'future-targets.json'):
        if file_hash(target(folder, name)) != manifest['metadata'][name]:
            raise ValueError('BACKUP_METADATA_CHANGED')
    actual = set()
    for p in folder.rglob('*'):
        no_links(p)
        if p.is_file():
            actual.add(p.relative_to(folder).as_posix())
    if expected != actual:
        raise ValueError('BACKUP_FILE_SET_CHANGED')
    return manifest


def create(folder, roots, baseline, acceptance, future_targets, *, live):
    if acceptance.get('accepted') is not True or acceptance.get('baseline_sha256') != fingerprint(baseline):
        raise ValueError('BASELINE_ACCEPTANCE_REQUIRED')
    folder = folder.absolute()
    no_links(folder)
    if folder.exists() or any(folder.resolve().is_relative_to(p.resolve()) or p.resolve().is_relative_to(folder.resolve()) for p in roots.values()):
        raise ValueError('NEW_NONOVERLAPPING_BACKUP_REQUIRED')
    live()
    entries = {f'game/{n}': baseline['game'][n] for n in GAME_PAYLOAD}
    entries.update({f'saves/{n}': v for n, v in baseline['saves'].items()})
    if shutil.disk_usage(folder.parent).free < sum(v['bytes'] for v in entries.values()) + 16 * 1024 * 1024:
        raise ValueError('INSUFFICIENT_BACKUP_SPACE')
    for dest, row in entries.items():
        group, relative = dest.split('/', 1)
        if measure(target(roots[group], relative)) != {'size': row['bytes'], 'sha256': row['sha256']}:
            raise ValueError('BASELINE_SOURCE_CHANGED')
    folder.mkdir()
    payload = {}
    for dest, row in entries.items():
        live()
        group, relative = dest.split('/', 1)
        src, dst = target(roots[group], relative), target(folder, dest)
        dst.parent.mkdir(parents=True, exist_ok=True)
        with src.open('rb') as a, dst.open('xb') as b:
            shutil.copyfileobj(a, b, 1024 * 1024)
            b.flush()
            os.fsync(b.fileno())
        expected = {'size': row['bytes'], 'sha256': row['sha256']}
        if measure(src) != expected or measure(dst) != expected:
            raise ValueError('BACKUP_COPY_OR_SOURCE_MISMATCH')
        payload[dest] = expected
    write_json_new(folder / 'baseline.json', baseline)
    write_json_new(folder / 'future-targets.json', future_targets)
    manifest = {'format': 'aic_clean_backup_v1', 'created_utc': datetime.now(timezone.utc).isoformat(),
                'acceptance': acceptance, 'payload': payload,
                'metadata': {n: file_hash(folder / n) for n in ('baseline.json', 'future-targets.json')},
                'payload_bytes': sum(v['size'] for v in payload.values()), 'dat_bodies_included': False,
                'restore_policy': 'No automatic resource or LOCAL restore; current-build receipt review required',
                'spawn_ready': False}
    live()
    write_json_new(folder / 'manifest.json', manifest)
    return verify(folder)
