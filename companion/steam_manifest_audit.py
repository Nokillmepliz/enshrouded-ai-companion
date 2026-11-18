"""Read-only plaintext Steam depot-cache comparison, not signature authentication.

Wire schema: SteamTracking/Protobufs steam/content_manifest.proto.
Framing: SteamRE/SteamKit SteamKit2/SteamKit2/Types/DepotManifest.cs.
No decryption, download, Steam command, or game write is performed here.
"""
import hashlib
import struct
import zlib

from .recovery import target


def fields(data):
    pos = 0

    def varint():
        nonlocal pos
        value = 0
        for shift in range(0, 70, 7):
            if pos >= len(data):
                raise ValueError('TRUNCATED_VARINT')
            byte = data[pos]
            pos += 1
            value |= (byte & 127) << shift
            if not byte & 128:
                if value > 0xffffffffffffffff:
                    break
                return value
        raise ValueError('INVALID_VARINT')

    result = {}
    while pos < len(data):
        tag = varint()
        number, wire = tag >> 3, tag & 7
        if not number:
            raise ValueError('INVALID_FIELD')
        if wire == 0:
            value = varint()
        elif wire in (1, 2, 5):
            size = varint() if wire == 2 else (8 if wire == 1 else 4)
            if size > len(data) - pos:
                raise ValueError('TRUNCATED_FIELD')
            value = data[pos:pos + size]
            pos += size
        else:
            raise ValueError('UNSUPPORTED_WIRE_TYPE')
        result.setdefault(number, []).append(value)
    return result


def one(data, key, kind, default=None):
    values = data.get(key, [default])
    if len(values) != 1 or type(values[0]) is not kind:
        raise ValueError('INVALID_OR_DUPLICATE_FIELD')
    return values[0]


def parse(data, depot_id, manifest_id):
    if len(data) > 32 * 1024 * 1024:
        raise ValueError('MANIFEST_TOO_LARGE')
    sections, pos = {}, 0
    for magic in (0x71f617d0, 0x1f4812be, 0x1b81b817):
        if pos + 8 > len(data):
            raise ValueError('TRUNCATED_SECTION')
        actual, size = struct.unpack_from('<II', data, pos)
        pos += 8
        if actual != magic or size > len(data) - pos:
            raise ValueError('INVALID_SECTION')
        sections[magic] = data[pos:pos + size]
        pos += size
    if data[pos:] != struct.pack('<I', 0x32c415ab):
        raise ValueError('INVALID_MANIFEST_END')
    payload = sections[0x71f617d0]
    meta = fields(sections[0x1f4812be])
    if one(meta, 1, int) != depot_id or one(meta, 2, int) != manifest_id:
        raise ValueError('DEPOT_IDENTITY_MISMATCH')
    if one(meta, 4, int, 0) != 0:
        raise ValueError('ENCRYPTED_NAMES_UNSUPPORTED')
    crc = one(meta, 9, int)
    if zlib.crc32(struct.pack('<I', len(payload)) + payload) != crc:
        raise ValueError('PAYLOAD_CRC_MISMATCH')
    mappings, seen = [], set()
    for raw in fields(payload).get(1, []):
        row = fields(raw)
        name = one(row, 1, bytes).decode('utf-8').replace('\\', '/')
        # Resolve containment again at read time; no filesystem writes occur.
        from pathlib import PurePosixPath
        parts = name.split('/')
        if (not name or PurePosixPath(name).is_absolute() or
                any(p in ('', '.', '..') or ':' in p or '\0' in p for p in parts)):
            raise ValueError('UNSAFE_MANIFEST_PATH')
        if name.casefold() in seen:
            raise ValueError('DUPLICATE_MANIFEST_PATH')
        seen.add(name.casefold())
        flags = one(row, 3, int, 0)
        if flags & 512 or one(row, 7, bytes, b''):
            raise ValueError('LINK_ENTRY_UNSUPPORTED')
        if flags not in (0, 32):
            raise ValueError('NON_REGULAR_ENTRY_UNSUPPORTED')
        digest = one(row, 5, bytes)
        if len(digest) != 20:
            raise ValueError('INVALID_SHA1')
        mappings.append({'path': name, 'bytes': one(row, 2, int), 'sha1': digest.hex()})
    if not mappings:
        raise ValueError('EMPTY_MANIFEST')
    sig = fields(sections[0x1b81b817])
    signature = one(sig, 1, bytes, b'')
    return {'depot_id': depot_id, 'manifest_id': str(manifest_id),
            'manifest_sha256': hashlib.sha256(data).hexdigest(),
            'payload_crc': 'PASS', 'signature_bytes': len(signature),
            'signature_verified': False, 'provenance': 'LOCAL_STEAM_DEPOT_CACHE',
            'independent_authenticated_upstream_hashes': False, 'files': mappings}


def compare(manifest, game):
    rows = []
    for entry in manifest['files']:
        path = target(game, entry['path'])
        before = path.stat()
        h1, h256 = hashlib.sha1(), hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
                h1.update(block)
                h256.update(block)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            raise ValueError('FILE_CHANGED_DURING_READ')
        rows.append({**entry, 'actual_sha1': h1.hexdigest(), 'sha256': h256.hexdigest(),
                     'match': after.st_size == entry['bytes'] and h1.hexdigest() == entry['sha1']})
    return {**manifest, 'files': rows, 'all_files_match': all(r['match'] for r in rows)}
