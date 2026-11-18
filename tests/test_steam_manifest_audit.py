import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from companion.steam_manifest_audit import parse, compare, fields


def var(n):
    out = bytearray()
    while n > 127:
        out.append((n & 127) | 128)
        n >>= 7
    return bytes(out) + bytes([n])


def field(k, v):
    return var(k * 8) + var(v) if type(v) is int else var(k * 8 + 2) + var(len(v)) + v


def mapping(name=b'enshrouded.kfc', content=b'fixture', flags=0):
    return b''.join((field(1, name), field(2, len(content)), field(3, flags),
                     field(5, hashlib.sha1(content).digest())))


def manifest(rows=None, depot=1203621, encrypted=0, extra_meta=b'', signature=b''):
    payload = b''.join(field(1, r) for r in (rows if rows is not None else [mapping()]))
    crc = zlib.crc32(struct.pack('<I', len(payload)) + payload)
    metadata = field(1, depot) + field(2, 7226436020230696061) + field(4, encrypted) + field(9, crc) + extra_meta
    return b''.join(struct.pack('<II', m, len(v)) + v for m, v in
                    ((0x71f617d0, payload), (0x1f4812be, metadata), (0x1b81b817, signature))) + struct.pack('<I', 0x32c415ab)


def read(data):
    return parse(data, 1203621, 7226436020230696061)


class SteamCacheTests(unittest.TestCase):
    def test_hashes_are_never_signature_authentication(self):
        for sig in (b'', field(1, b'not-a-real-signature')):
            out = read(manifest(signature=sig))
            self.assertFalse(out['signature_verified'])
            self.assertFalse(out['independent_authenticated_upstream_hashes'])
            self.assertEqual(out['payload_crc'], 'PASS')

    def test_read_only_compare_detects_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'enshrouded.kfc'
            p.write_bytes(b'fixture')
            self.assertTrue(compare(read(manifest()), Path(tmp))['all_files_match'])
            p.write_bytes(b'changed')
            result = compare(read(manifest()), Path(tmp))
            self.assertFalse(result['all_files_match'])
            self.assertEqual(p.read_bytes(), b'changed')

    def test_bad_manifest_identity(self):
        with self.assertRaisesRegex(ValueError, 'IDENTITY'):
            read(manifest(depot=1))

    def test_encrypted_refused(self):
        with self.assertRaisesRegex(ValueError, 'ENCRYPTED'):
            read(manifest(encrypted=1))

    def test_truncation_and_trailing_bytes(self):
        data = manifest()
        for value in (data[:2], data[:20], data[:-1], data + b'extra'):
            with self.subTest(size=len(value)), self.assertRaises(ValueError):
                read(value)

    def test_duplicate_fields(self):
        for data in (manifest(extra_meta=field(1, 1203621)), manifest([mapping() + field(2, 7)])):
            with self.assertRaisesRegex(ValueError, 'DUPLICATE_FIELD'):
                read(data)

    def test_duplicate_paths_case_insensitive(self):
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_MANIFEST_PATH'):
            read(manifest([mapping(), mapping(b'ENSHROUDED.KFC')]))

    def test_path_escape_and_ads(self):
        for name in (b'../x', b'/x', b'C:/x', b'x:y', b'a//b', b'a/./b', b'a\0b'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                read(manifest([mapping(name)]))

    def test_links_directories_and_unsupported_flags(self):
        for flags in (64, 512, 4, 0x8000):
            with self.subTest(flags=flags), self.assertRaises(ValueError):
                read(manifest([mapping(flags=flags)]))
        self.assertEqual(len(read(manifest([mapping(flags=32)]))['files']), 1)

    def test_corrupt_payload_crc(self):
        data = bytearray(manifest())
        data[data.index(b'enshrouded')] = ord('X')
        with self.assertRaisesRegex(ValueError, 'CRC'):
            read(bytes(data))

    def test_empty_and_bad_digest(self):
        for data in (manifest([]), manifest([field(1, b'x') + field(2, 1) + field(5, b'x')])):
            with self.assertRaises(ValueError):
                read(data)

    def test_malformed_protobuf(self):
        for data in (b'\x80', b'\x80' * 10 + b'\x00', b'\x00', b'\x0a\x04ab', b'\x0b'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                fields(data)
