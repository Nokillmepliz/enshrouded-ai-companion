"""Read-only filesystem checks for EMF's private client shadow.

No writer, installation, cleanup, transport or game entry points. Expected file
hashes must come from reviewed readback, not from an untrusted shadow itself.
Filesystem PASS never establishes resource semantics, freshness or rendering.
"""
from pathlib import Path, PurePosixPath
import os
import re
import stat

from .compatibility import SHA, file_hash

DAT = re.compile(r'enshrouded_([0-9]{3,})\.dat\Z')
INDEXES = {'enshrouded.kfc', 'enshrouded.kfc_resources'}
PRIVATE_ROLES = {'PRIVATE_INDEX', 'GENERATED_DAT', 'MOD_COPY', 'CACHE', 'METADATA', 'TEMPORARY'}


class ShadowError(ValueError):
    pass


def no_reparse(path):
    """Hardlinks are permitted; junctions/symlinks at any ancestor are not."""
    for p in (path.absolute(), *path.absolute().parents):
        try:
            s = p.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(s.st_mode) or getattr(s, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ShadowError('REPARSE_POINT')


def contained(root, relative):
    if (not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative
            or PurePosixPath(relative).is_absolute()
            or any(p in ('', '.', '..') or p.endswith(('.', ' ')) for p in relative.split('/'))):
        raise ShadowError('INVALID_PATH')
    for part in relative.split('/'):
        if part.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL', *[f'COM{i}' for i in range(10)], *[f'LPT{i}' for i in range(10)]}:
            raise ShadowError('INVALID_PATH')
    p = root.absolute() / relative
    no_reparse(p)
    if not p.resolve().is_relative_to(root.resolve()):
        raise ShadowError('PATH_ESCAPE')
    return p


def record(path):
    no_reparse(path)
    a = path.stat()
    if not stat.S_ISREG(a.st_mode) or not a.st_ino or not a.st_dev:
        raise ShadowError('FILE_IDENTITY_UNAVAILABLE')
    digest = file_hash(path)
    b = path.stat()
    fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_nlink')
    if any(getattr(a, k) != getattr(b, k) for k in fields):
        raise ShadowError('CHANGED_DURING_READ')
    return dict(sha256=digest, size=b.st_size, volume=b.st_dev, file_id=b.st_ino,
                links=b.st_nlink, mtime_ns=b.st_mtime_ns)


def capture_originals(game):
    """Capture root resource files only. Reject .bak as a trusted clean input."""
    no_reparse(game)
    if not game.is_dir():
        raise ShadowError('GAME_ROOT_MISSING')
    names = {p.name for p in game.iterdir() if p.name in INDEXES | {'enshrouded.exe', 'enshrouded.kfc.bak'} or DAT.fullmatch(p.name)}
    if 'enshrouded.kfc.bak' in names:
        raise ShadowError('UNTRUSTED_BAK_BASE')
    if not INDEXES | {'enshrouded.exe'} <= names:
        raise ShadowError('ORIGINAL_RESOURCE_MISSING')
    dats = {name for name in names if DAT.fullmatch(name)}
    if not dats or dats != {f'enshrouded_{i:03d}.dat' for i in range(len(dats))}:
        raise ShadowError('DAT_SET_REVIEW_REQUIRED')
    return {n: record(contained(game, n)) for n in sorted(names)}


def tree(root):
    no_reparse(root)
    if not root.is_dir():
        raise ShadowError('SHADOW_MISSING')
    result = {}
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            no_reparse(Path(base) / name)
        for name in files:
            p = Path(base) / name
            rel = p.relative_to(root).as_posix()
            result[rel] = record(contained(root, rel))
    return result


def audit_shadow(game, shadow, baseline, expected):
    """Exact file allowlist plus immutable original hashes/identities.

    baseline is captured before installation, with one link per original file.
    expected: relative -> {role, sha256}; BASE_LINK digest is the baseline's.
    Additional links or a server shadow require a separately reviewed contract.
    """
    no_reparse(game)
    no_reparse(shadow)
    if shadow.absolute() != (game.absolute() / 'emf/content/client'):
        raise ShadowError('INCORRECT_SHADOW_PATH')
    originals = capture_originals(game)
    if set(originals) != set(baseline):
        raise ShadowError('ORIGINAL_SET_CHANGED')
    linked = {n for n in baseline if n == 'enshrouded.exe' or DAT.fullmatch(n)}
    for name, prior in baseline.items():
        now = originals[name]
        if any(now[k] != prior[k] for k in ('sha256', 'size', 'volume', 'file_id', 'mtime_ns')):
            raise ShadowError('ORIGINAL_MUTATION:' + name)
        if prior['links'] != 1 or now['links'] != (2 if name in linked else 1):
            raise ShadowError('UNEXPECTED_ORIGINAL_LINK_COUNT:' + name)
    if not expected or len({n.casefold() for n in expected}) != len(expected):
        raise ShadowError('INVALID_ALLOWLIST')
    for name, spec in expected.items():
        contained(shadow, name)
        if set(spec) != {'role', 'sha256'} or not SHA.fullmatch(spec['sha256']):
            raise ShadowError('INVALID_ALLOWLIST')
        role = spec['role']
        if role == 'BASE_LINK':
            if name not in linked or spec['sha256'] != baseline[name]['sha256']:
                raise ShadowError('UNEXPECTED_BASE_LINK')
        elif role not in PRIVATE_ROLES:
            raise ShadowError('UNKNOWN_SHADOW_ROLE')
        elif role == 'PRIVATE_INDEX' and name not in INDEXES | {'enshrouded.kfc.bak'}:
            raise ShadowError('INVALID_INDEX_PATH')
        elif role == 'GENERATED_DAT' and (not DAT.fullmatch(name) or name in baseline):
            raise ShadowError('INVALID_GENERATED_DAT')
        elif role == 'MOD_COPY' and not name.startswith('mods/'):
            raise ShadowError('INVALID_MOD_PATH')
        elif role == 'CACHE' and not name.startswith('.cache/'):
            raise ShadowError('INVALID_CACHE_PATH')
        elif role == 'METADATA' and name not in {'shadow.txt', 'emf_content_state.json'}:
            raise ShadowError('INVALID_METADATA_PATH')
        if role == 'TEMPORARY' or name.endswith('.tmp'):
            raise ShadowError('INCOMPLETE_SHADOW_TEMPORARY_FILE')
    if {n for n, s in expected.items() if s['role'] == 'BASE_LINK'} != linked:
        raise ShadowError('BASE_LINK_SET_MISMATCH')
    if any(expected.get(n, {}).get('role') != 'PRIVATE_INDEX' for n in INDEXES):
        raise ShadowError('PRIVATE_INDEX_MISSING')
    observed = tree(shadow)
    if set(observed) != set(expected):
        raise ShadowError('SHADOW_FILE_SET_MISMATCH')
    original_ids = {(r['volume'], r['file_id']) for r in originals.values()}
    for name, row in observed.items():
        spec = expected[name]
        if row['sha256'] != spec['sha256']:
            raise ShadowError('SHADOW_HASH_MISMATCH:' + name)
        if spec['role'] == 'BASE_LINK':
            src = originals[name]
            if (row['volume'], row['file_id']) != (src['volume'], src['file_id']) or row['links'] != 2:
                raise ShadowError('BASE_LINK_IDENTITY_MISMATCH')
        elif row['links'] != 1 or (row['volume'], row['file_id']) in original_ids:
            raise ShadowError('PRIVATE_FILE_IS_HARDLINK:' + name)
    # Catch mutation during the shadow reads too; this is not an atomic OS lock.
    if capture_originals(game) != originals:
        raise ShadowError('ORIGINAL_CHANGED_DURING_AUDIT')
    return {'filesystem_integrity': 'PASS', 'original_files': originals, 'shadow_files': observed,
            'roles': {n: s['role'] for n, s in expected.items()}, 'read_only': True,
            'writer_completion': 'UNKNOWN', 'redirection': 'UNKNOWN', 'resource_semantics': 'UNKNOWN',
            'runtime_status': 'NOT_EXECUTED', 'RUNTIME_RENDER_CONFIRMED': 'UNKNOWN', 'spawn_ready': False}
