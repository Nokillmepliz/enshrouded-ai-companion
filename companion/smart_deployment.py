"""Pinned, read-only installation gate for the four-file 0.1.1 update."""
from pathlib import Path
from .compatibility import file_hash
from .integrated_deployment import read_pinned
from .patch_update_transaction import verify_backup
from .recovery import target

PREFIX='emf/mods/aic_first_spawn/'
CHANGED={PREFIX+n for n in ('controller.lua','main.lua','mod.json','README.md')}


def check_manifest(manifest, baseline):
    rows=manifest.get('entries',[])
    if (manifest.get('format')!='aic_smart_position_update_v1'
            or manifest.get('version')!='0.1.1' or len(rows)!=4
            or {r['path'] for r in rows}!=CHANGED):raise ValueError('EXACT_FOUR_FILE_UPDATE_REQUIRED')
    effective=manifest['effective_files']
    if len(effective)!=23 or len({r['path'] for r in effective})!=23:
        raise ValueError('EFFECTIVE_23_REQUIRED')
    changed={r['path']:r for r in rows}
    for row in effective:
        path=row['path'];old=baseline['game'][path]
        if path in changed:
            new=changed[path]
            if (new['before_sha256'],new['before_bytes'])!=(old['sha256'],old['size']):
                raise ValueError('UPDATE_BASELINE_MISMATCH')
            expected=(new['sha256'],new['bytes'])
        else:expected=(old['sha256'],old['size'])
        if (row['sha256'],row['bytes'])!=expected:raise ValueError('EFFECTIVE_HASH_MISMATCH')
    if not CHANGED.issubset({r['path'] for r in effective}):raise ValueError('MISSING_UPDATED_FILES')


def verify(plan, receipt_path, receipt_sha):
    manifest=read_pinned(Path(plan['manifest_path']),plan['manifest_sha256'])
    baseline=read_pinned(Path(plan['baseline_path']),plan['baseline_sha256'])
    check_manifest(manifest,baseline)
    receipt=read_pinned(receipt_path,receipt_sha)
    if (receipt.get('format')!='aic_smart_position_receipt_v1' or receipt.get('status')!='INSTALLED'
            or receipt.get('manifest_sha256')!=plan['manifest_sha256']
            or receipt.get('effective_files')!=manifest['effective_files']):
        raise ValueError('VERIFIED_0_1_1_RECEIPT_REQUIRED')
    binding=read_pinned(Path(plan['binding_path']),plan['binding_sha256'])
    game=Path(manifest['game'])
    for row in manifest['effective_files']:
        path=target(game,row['path'])
        if file_hash(path)!=row['sha256'] or path.stat().st_size!=row['bytes']:
            raise ValueError('INSTALLED_FILE_CHANGED:'+row['path'])
    latch=target(game,PREFIX+'attempt.lock')
    if latch.read_bytes()!=('UNUSED:'+binding['key']).encode():raise ValueError('LATCH_NOT_UNUSED')
    backup=Path(receipt['backup_path'])
    bm=read_pinned(backup/'manifest.json',receipt['backup_manifest_sha256'])
    expected={'saves/'+p:(r['sha256'],r['size']) for p,r in baseline['saves'].items()}
    expected.update({'game/'+p:(baseline['game'][p]['sha256'],baseline['game'][p]['size']) for p in CHANGED})
    if {r['relative']:(r['sha256'],r['bytes']) for r in bm['files']}!=expected:
        raise ValueError('FRESH_BACKUP_BASELINE_MISMATCH')
    verify_backup(backup,bm)
    return binding,game
