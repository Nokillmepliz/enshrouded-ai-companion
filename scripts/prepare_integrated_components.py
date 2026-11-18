"""Stage a pinned EMF component subset under project/dist; never install/run it.

This is not the complete migration package: clean patch/observer/receipt pending.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from companion.compatibility import file_hash
from companion.recovery import no_links, target, write_json_new
from companion.stage10 import audit_pe

ARCHIVE_SHA = '12bbcae2e52386bcd7f1747701bb6d1ec8a64fab061e6e33ce994b6ee29c926b'
PREFIX = 'EMF-0.6.18-manual/'
GAME_FILES = {
    'dinput8.dll': 'EMF loader, single content owner selection',
    'emf/emf_core.dll': 'EMF core API46 and protocol1 bridge',
    'emf/emf_content.dll': 'Integrated EML build in private shadow',
    'emf/mods/lua/lua.dll': 'Lua host1.39.0',
    'emf/mods/lua/mod.json': 'Lua host discovery manifest',
    'emf/known_tools.txt': 'Known loader/tool classification metadata',
}
LICENSES = ('LICENSE.txt', 'licenses/Alegreya-OFL.txt', 'licenses/Apache-2.0.txt',
            'licenses/CascadiaMono-OFL.txt', 'licenses/DearImGui-LICENSE.txt',
            'licenses/EML-LICENSE.txt', 'licenses/Lua-LICENSE.txt', 'licenses/MinHook-LICENSE.txt',
            'licenses/rust-crates.html', 'licenses/THIRD_PARTY_NOTICES.md',
            'licenses/Vulkan-Headers-LICENSE.md', 'licenses/WebView2-LICENSE.txt')


def verified_members(archive, expected_sha, members):
    no_links(archive)
    if file_hash(archive) != expected_sha:
        raise ValueError('ARCHIVE_DIGEST_MISMATCH')
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len({n.casefold() for n in names}) != len(names):
            raise ValueError('DUPLICATE_ARCHIVE_ENTRY')
        result = {name: z.read(name) for name in members}
    if file_hash(archive) != expected_sha:
        raise ValueError('ARCHIVE_CHANGED_DURING_READ')
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    output = args.output.absolute()
    no_links(output)
    if not output.resolve().is_relative_to((ROOT / 'dist').resolve()) or output.exists():
        raise ValueError('NEW_PROJECT_DIST_DIRECTORY_REQUIRED')
    archive = ROOT / 'runtime/stage10_10/EMF-0.6.18-manual.zip'
    sources = {f'game/{n}': PREFIX + 'game/' + n for n in GAME_FILES}
    sources.update({n: PREFIX + n for n in LICENSES})
    data = verified_members(archive, ARCHIVE_SHA, sources.values())
    index = {e['path']: e for e in json.loads((ROOT / 'compatibility/audits/1287369/release-files.json').read_text())}
    for source, raw in data.items():
        expected = index[source]
        if hashlib.sha256(raw).hexdigest() != expected['sha256'] or len(raw) != expected['bytes']:
            raise ValueError('RELEASE_MEMBER_CHANGED')
    output.mkdir(parents=True)
    entries = []
    for relative, source in sources.items():
        path = target(output, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as f:
            f.write(data[source])
        if file_hash(path) != index[source]['sha256']:
            raise ValueError('STAGING_HASH_MISMATCH')
        row = {'staging_relative_path': relative, 'archive_source': source,
               'sha256': file_hash(path), 'bytes': path.stat().st_size,
               'game_destination': relative[5:] if relative.startswith('game/') else None,
               'purpose': GAME_FILES.get(relative[5:], 'Package licence/notice; do not copy to game'),
               'copy_to_game_authorized': False}
        if path.suffix == '.dll':
            row['static_pe'] = audit_pe(path)
            if row['static_pe']['machine'] != '0x8664' or row['static_pe']['magic'] != '0x20b':
                raise ValueError('WRONG_ARCHITECTURE')
        entries.append(row)
    for src, rel in (('emf_core.ini', 'game/emf/emf_core.ini'), ('lua.ini', 'game/emf/config/lua.ini')):
        raw = (ROOT / 'experimental/integrated_content' / src).read_bytes()
        path = target(output, rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as f:
            f.write(raw)
        entries.append({'staging_relative_path': rel, 'repository_source': 'experimental/integrated_content/' + src,
                        'sha256': file_hash(path), 'bytes': len(raw), 'game_destination': rel[5:],
                        'purpose': 'Clean candidate configuration; no legacy settings inheritance',
                        'copy_to_game_authorized': False})
    result = {'format': 'aic_integrated_components_v1', 'created_utc': datetime.now(timezone.utc).isoformat(),
              'release': 'EMF0.6.18', 'archive_sha256': ARCHIVE_SHA,
              'archive_url': 'https://github.com/matenm/emf-enshrouded/releases/download/v0.6.18/EMF-0.6.18-manual.zip',
              'entries': entries, 'complete_migration_package': False,
              'missing': ['clean_baseline', 'patch0.5.0', 'observer_bootstrap', 'bridge_capture', 'exact_install_receipt'],
              'installation_authorized': False, 'installation_executed': False, 'spawn_ready': False}
    write_json_new(output / 'component-manifest.json', result)
    print(json.dumps({'output': str(output), 'staged_files': len(entries), 'game_candidates': len(GAME_FILES) + 2,
                      'complete_migration_package': False}))


if __name__ == '__main__':
    main()
