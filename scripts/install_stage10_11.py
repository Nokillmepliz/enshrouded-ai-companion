"""Approved additive installation; no launch/spawn, save restore or rollback."""
import argparse
from datetime import datetime,timezone
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.compatibility import file_hash
from companion.experimental_install import validate,copy_seven,removal_dry_run,PATHS
from companion.experimental_install_check import verify
from companion.integrated_deployment import read_pinned
from companion.integrated_update import check_plan,verify_updated
from companion.patch_update_transaction import snapshot,verified_backup,verify_backup,validate_backup_plan
from companion.recovery import write_json_new
from scripts.prepare_phase_d_backup import live,GAME,SAVES

PUBLIC=ROOT/'compatibility/experiments/stage10_11'
MANIFEST_SHA='6ecc792b6c320dc19f0fa201259c573efd142c4c37a579eab07376dc40b9e1e3'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--install-authorized',action='store_true')
    args=ap.parse_args()
    live()
    m=read_pinned(PUBLIC/'exact-install-manifest.json',MANIFEST_SHA)
    package=Path(m['package']);read_pinned(package/'exact-install-manifest.json',MANIFEST_SHA)
    if Path(m['game'])!=GAME:raise ValueError('GAME_ROOT_MISMATCH')
    validate(m,package,GAME,absent=True)
    binding=read_pinned(package/'client-binding.json',m['client_binding_sha256'])
    if (package/'payload/emf/mods/aic_first_spawn/attempt.lock').read_bytes()!=('UNUSED:'+binding['key']).encode():
        raise ValueError('INITIAL_LATCH_REQUIRED')
    if (ROOT/'runtime/stage10_11/experiments'/binding['key']).exists():raise ValueError('EXPERIMENT_ALREADY_EXISTS')
    baseline=read_pinned(Path(m['baseline_source']),m['baseline_inventory_sha256'])
    old=ROOT/'compatibility/updates/1287369/0.5.1'
    approved=read_pinned(old/'update-manifest.json','a6ef7bd5714353b8b6a3da7354baff4581de7effb1f9409fab4b5f983ac4bdf4')
    op=Path(approved['local_package']);plan=read_pinned(op/'update-plan.json',approved['update_plan_sha256']);check_plan(plan,op)
    oldreceipt=read_pinned(old/'installation/receipt.json',m['prior_receipt_sha256'])
    verify_updated(plan,approved['update_plan_sha256'],oldreceipt,GAME)
    print('Closed/build/package7/existing16/destinations PASS; hashing pre-install baseline',flush=True)
    before=dict(game=snapshot(GAME),saves=snapshot(SAVES));live()
    if before!=baseline:raise ValueError('BASELINE_CHANGED')
    bp=read_pinned(PUBLIC/'backup-plan.json',m['backup_plan_sha256'])
    backup=Path(m['backup_destination'])
    if backup.exists():raise ValueError('NEW_BACKUP_REQUIRED')
    validate_backup_plan(bp,{'saves':SAVES},backup,live=live)
    if not args.install_authorized:
        print('READ_ONLY_PREFLIGHT_PASS; no backup or installation performed',flush=True);return
    public=PUBLIC/'installation'
    if public.exists():raise ValueError('NEW_PUBLIC_RESULT_REQUIRED')
    run=ROOT/'runtime/stage10_11/install'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run.mkdir(parents=True,exist_ok=False)
    write_json_new(run/'inventory-before.json',before)
    write_json_new(run/'authorization.json',dict(install_only=True,test_world_disposable_accepted=True,
        backup_files=23,new_files=7,spawn_authorized=False,rollback_authorized=False))
    try:
        bm=verified_backup(bp,{'saves':SAVES},backup,live=live);verify_backup(backup,bm)
        print('Verified LOCAL backup23 PASS; copying seven exclusive destinations',flush=True)
        # Recheck saves immediately before writes; no save restoration is present.
        if snapshot(SAVES)!=before['saves']:raise ValueError('SAVES_CHANGED_BEFORE_INSTALL')
        rows=copy_seven(m,package,GAME,run/'journal',authorized=True,live=live)
        print('Copied7 PASS; hashing full post-install inventory',flush=True)
        after=dict(game=snapshot(GAME),saves=snapshot(SAVES));live()
        write_json_new(run/'inventory-after.json',after)
        if after['saves']!=before['saves']:raise ValueError('LOCAL_CHANGED')
        if set(after['game'])!=set(before['game'])|PATHS:raise ValueError('UNEXPECTED_GAME_FILE_SET')
        if any(after['game'][n]!=r for n,r in before['game'].items()):raise ValueError('EXISTING_FILE_CHANGED')
        for r in rows:
            if after['game'][r['path']]!=r['record']:raise ValueError('NEW_FILE_CHANGED')
        verify_updated(plan,approved['update_plan_sha256'],oldreceipt,GAME)
        verify_backup(backup,bm)
        receipt=dict(format='aic_experiment_receipt_v1',status='INSTALLED',manifest_sha256=MANIFEST_SHA,
            entries=m['entries'],installed_records=rows,backup_path=str(backup),backup_manifest_sha256=file_hash(backup/'manifest.json'),
            created_utc=datetime.now(timezone.utc).isoformat(),private_evidence=str(run),
            baseline_inventory_sha256=m['baseline_inventory_sha256'],post_install_inventory_sha256=file_hash(run/'inventory-after.json'),
            installation_authorized=True,spawn_authorized=False,experimental_spawn_executed=False)
        write_json_new(run/'receipt.json',receipt)
        verify(package,MANIFEST_SHA,run/'receipt.json',file_hash(run/'receipt.json'),ROOT)
        dry=removal_dry_run(m,receipt,GAME)
        write_json_new(run/'removal-dry-run.json',dry)
        result=dict(status='INSTALLED_READY_FOR_MANUAL_START_PREFLIGHT',checked_utc=datetime.now(timezone.utc).isoformat(),
            manifest_sha256=MANIFEST_SHA,receipt_sha256=file_hash(run/'receipt.json'),
            backup_verified=23,backup_bytes=bm['payload_bytes'],new_installed_files=7,existing_installed_verified=16,
            existing_game_records_unchanged=235,original_resources_unchanged=67,shadow_records_unchanged=77,
            LOCAL_records_unchanged=23,game_files_after=242,private_evidence=str(run),
            post_install_inventory_sha256=file_hash(run/'inventory-after.json'),removal_dry_run=dry['status'],
            game_server_closed=True,game_launched=False,rollback_executed=False,
            experimental_spawn_executed=False,production_spawn_ready=False,spawn_ready=False,RUNTIME_RENDER_CONFIRMED='UNKNOWN')
        write_json_new(run/'result.json',result)
        public.mkdir()
        for name,value in [('receipt.json',receipt),('removal-dry-run.json',dry),('result.json',result)]:write_json_new(public/name,value)
        print(result,flush=True)
    except Exception as exc:
        write_json_new(run/'blocked.json',dict(status='INSTALLATION_BLOCKED',error=str(exc),rollback_executed=False))
        raise


if __name__=='__main__':main()
