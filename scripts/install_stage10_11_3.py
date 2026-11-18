"""User-approved 0.1.1 installation only; default is read-only preflight."""
import argparse
import json
from pathlib import Path
import sys
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.compatibility import file_hash
from companion.integrated_deployment import read_pinned
from companion.experimental_install_check import verify as old_verify
from companion.experimental_wait import verify_history
from companion.patch_update_transaction import snapshot,verified_backup,verify_backup,validate_backup_plan
from companion.recovery import write_json_new,target
from companion.smart_deployment import check_manifest,verify,CHANGED
from companion.smart_installation import replace,rollback_dry_run
from scripts.prepare_phase_d_backup import GAME,SAVES,live

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--install-approved',action='store_true');args=ap.parse_args()
    public=ROOT/'compatibility/experiments/stage10_11_3';private=ROOT/'runtime/stage10_11_3'
    plan=read_pinned(private/'smart-position-plan.json','d137680beff2ccc68fedefd87617202075a1d367407ddd34096ae43537d6647c')
    manifest=read_pinned(Path(plan['manifest_path']),plan['manifest_sha256'])
    baseline=read_pinned(Path(plan['baseline_path']),plan['baseline_sha256']);check_manifest(manifest,baseline)
    bp=read_pinned(public/'backup-plan.json','78bf464b9898f2fa81de0c1712f443efba1c6479301af613aed68ffca734735e')
    package=ROOT/'dist/stage10_11_first_spawn_0_1_1';backup=ROOT/'runtime/backups/stage10_11_3-before-update'
    live()
    binding=old_verify(ROOT/'dist/stage10_11_first_spawn_0_1_0',
        '6ecc792b6c320dc19f0fa201259c573efd142c4c37a579eab07376dc40b9e1e3',
        ROOT/'compatibility/experiments/stage10_11/installation/receipt.json',manifest['parent_receipt_sha256'],ROOT)
    history=ROOT/'runtime/stage10_11/experiments'/binding['key']
    verify_history(history,plan['history'],'unused-placeholder')
    if (GAME/'emf/mods/aic_first_spawn/attempt.lock').read_bytes()!=('UNUSED:'+binding['key']).encode():raise ValueError('LATCH_NOT_UNUSED')
    for row in manifest['entries']:
        src=target(package,row['source'])
        if (file_hash(src),src.stat().st_size)!=(row['sha256'],row['bytes']):raise ValueError('PAYLOAD_CHANGED')
    print('Closed/build/install/history PASS; checking full baseline...',flush=True)
    if dict(game=snapshot(GAME),saves=snapshot(SAVES))!=baseline:raise ValueError('BASELINE_CHANGED')
    validate_backup_plan(bp,{'game':GAME,'saves':SAVES},backup,live=live)
    if not args.install_approved:
        print('READ_ONLY_PREFLIGHT_PASS: baseline245/23, installed23, history75, backup plan27, payload4');return
    for p in (backup,private/'installation',public/'installation'):
        if p.exists():raise ValueError('NEW_INSTALL_OUTPUT_REQUIRED')
    live();bm=verified_backup(bp,{'game':GAME,'saves':SAVES},backup,live=live);verify_backup(backup,bm)
    if snapshot(SAVES)!=baseline['saves']:raise ValueError('SAVES_CHANGED_DURING_BACKUP')
    print('Backup27 verified; installing exact4...',flush=True)
    done=replace(manifest,baseline,package,GAME,backup,private/'installation',authorized=True,live=live)
    after=dict(game=snapshot(GAME),saves=snapshot(SAVES));live()
    if set(after['game'])!=set(baseline['game']) or after['saves']!=baseline['saves']:raise ValueError('POST_INSTALL_INVENTORY_CHANGED')
    for name,old in baseline['game'].items():
        if name not in CHANGED and after['game'][name]!=old:raise ValueError('UNRELATED_FILE_CHANGED:'+name)
    for row in manifest['effective_files']:
        actual=after['game'][row['path']]
        if (actual['sha256'],actual['size'])!=(row['sha256'],row['bytes']):raise ValueError('EFFECTIVE_HASH_MISMATCH')
    verify_history(history,plan['history'],'unused-placeholder');verify_backup(backup,bm)
    dry=rollback_dry_run(manifest,GAME,backup)
    write_json_new(private/'installation/inventory-after.json',after)
    public_install=public/'installation';public_install.mkdir()
    receipt=dict(format='aic_smart_position_receipt_v1',status='INSTALLED',manifest_sha256=plan['manifest_sha256'],
        effective_files=manifest['effective_files'],installed_records=done,backup_path=str(backup),
        backup_manifest_sha256=file_hash(backup/'manifest.json'),created_utc=datetime.now(timezone.utc).isoformat(),
        post_install_baseline_path=str(private/'installation/inventory-after.json'),
        post_install_baseline_sha256=file_hash(private/'installation/inventory-after.json'),
        unchanged_game_files=len(after['game'])-4,unchanged_local_files=len(after['saves']),
        preserved_history_files=len(plan['history']),spawn_ready=False,spawn_executed=False)
    write_json_new(public_install/'receipt.json',receipt)
    verify(plan,public_install/'receipt.json',file_hash(public_install/'receipt.json'))
    write_json_new(public_install/'rollback-dry-run.json',dry)
    print(json.dumps(dict(status='INSTALLED_VERIFIED',installed=4,effective=23,backup=27,
        receipt_sha256=file_hash(public_install/'receipt.json'),backup_sha256=receipt['backup_manifest_sha256'],
        baseline_sha256=receipt['post_install_baseline_sha256'],rollback_dry_run=dry['status']),indent=2))

if __name__=='__main__':main()
