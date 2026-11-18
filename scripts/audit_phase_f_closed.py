"""Read-only post-run inventory for the reviewed Phase F session; no cleanup."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from companion.clean_backup import verify
from companion.integrated_deployment import read_pinned, installed, validate_plan
from companion.recovery import write_json_new
from companion.shadow_integrity import capture_originals, no_reparse, record
from scripts.prepare_phase_d_backup import live, GAME, SAVES


def differences(before, after):
    common = before.keys() & after.keys()
    return dict(added=sorted(after.keys() - before.keys()),
                removed=sorted(before.keys() - after.keys()),
                content_changed=sorted(n for n in common if any(before[n][k] != after[n][k] for k in ('sha256', 'size'))),
                metadata_changed=sorted(n for n in common if any(before[n][k] != after[n][k] for k in ('volume', 'file_id', 'mtime_ns', 'links'))))


def main():
    live()
    run = ROOT / 'runtime/stage10_10_1_phase_f/20261118T122931689254Z'
    out = run / datetime.now(timezone.utc).strftime('post-close-%Y%m%dT%H%M%S%fZ')
    out.mkdir(exist_ok=False)
    approved = json.loads((ROOT / 'compatibility/migration/1287369/exact-install-manifest.json').read_text())
    phase_e = json.loads((ROOT / 'compatibility/migration/1287369/phase_e/result.json').read_text())
    plan_sha = '82db6fe28bfff96a6580d7a01cd497ad595baf68fe3098312b95181d27ba9463'
    receipt_sha = 'c3cd5da70e01fd073553b6dcc2598e8ede867693087b67c285d65253c59d70fc'
    package = Path(approved['local_package'])
    plan = read_pinned(package / 'install-plan.json', plan_sha)
    validate_plan(plan, package)
    receipt = read_pinned(Path(phase_e['receipt_path']), receipt_sha)
    installed(plan, plan_sha, receipt, GAME)
    verify(Path(plan['backup_path']), plan['identity']['backup_manifest_sha256'])
    print('CLOSED; installed16 and backup27 PASS; hashing original resources', flush=True)
    before = json.loads((run / 'inventory-before.json').read_text())
    originals_before = json.loads((run / 'originals-before.json').read_text())
    originals = capture_originals(GAME)
    write_json_new(out / 'originals-after.json', originals)
    # Original hardlinks may legitimately have gained their EMF shadow link.
    # Cache only identical stat identities in this audit, never a previous hash.
    files = dict(originals)
    cache = {(r['volume'], r['file_id'], r['size'], r['mtime_ns'], r['links']): r for r in files.values()}
    for p in GAME.rglob('*'):
        no_reparse(p)
        if not p.is_file():
            continue
        n = p.relative_to(GAME).as_posix()
        if n in files:
            continue
        s = p.stat()
        key = (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_nlink)
        files[n] = cache[key] if key in cache else record(p)
    saves = {}
    for p in SAVES.rglob('*'):
        no_reparse(p)
        if p.is_file():
            saves[p.relative_to(SAVES).as_posix()] = record(p)
    live()
    # Ensure the metadata observed while hashing remains stable at completion.
    for root, inventory in ((GAME, files), (SAVES, saves)):
        if {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()} != set(inventory):
            raise ValueError('FILE_SET_CHANGED_DURING_AUDIT')
        for name, r in inventory.items():
            no_reparse(root / name)
            s = (root / name).stat()
            if (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_nlink) != (r['volume'], r['file_id'], r['size'], r['mtime_ns'], r['links']):
                raise ValueError('FILE_CHANGED_DURING_AUDIT:' + name)
    write_json_new(out / 'inventory-after.json', dict(game=files, saves=saves))
    base = {f'enshrouded_{i:03d}.dat' for i in range(55)} | {'enshrouded.exe'}
    shadow = {n.removeprefix('emf/content/client/'): r for n, r in files.items() if n.startswith('emf/content/client/')}
    link_errors = []
    for n, r in originals.items():
        old = originals_before[n]
        if any(r[k] != old[k] for k in ('sha256', 'size', 'volume', 'file_id', 'mtime_ns')):
            link_errors.append('ORIGINAL_CHANGED:' + n)
        if r['links'] != (2 if n in base else 1):
            link_errors.append('LINK_COUNT:' + n)
        if n in base and shadow.get(n) != r:
            link_errors.append('SHADOW_LINK:' + n)
    ids = {(r['volume'], r['file_id']) for r in originals.values()}
    for n, r in shadow.items():
        if n not in base and (r['links'] != 1 or (r['volume'], r['file_id']) in ids):
            link_errors.append('PRIVATE_SHADOW_LINK:' + n)
    result = dict(format='aic_phase_f_post_close_v1', checked_utc=datetime.now(timezone.utc).isoformat(),
        private_evidence=str(out), game_server_closed=True, installed_verified=16, backup_verified=27,
        original_resources=differences(originals_before, originals), original_resource_count=len(originals),
        game_inventory_count=len(files), game_changes=differences(before['game'], files),
        local_inventory_count=len(saves), local_changes=differences(before['saves'], saves),
        shadow_files=len(shadow), expected_base_links=len(base), link_errors=link_errors,
        shadow_semantics='NOT_VALIDATED_BUILD_FAILED', runtime_validation='BLOCKED_CONTENT_BUILD',
        rollback_executed=False, spawn_ready=False)
    write_json_new(out / 'result.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
