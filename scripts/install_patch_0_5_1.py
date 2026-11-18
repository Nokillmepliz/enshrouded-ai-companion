"""Execute the user-approved four-file update, with immutable backup and audit."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.compatibility import file_hash
from companion.integrated_deployment import read_pinned
from companion.integrated_update import preflight,input_fingerprint,verify_updated,rollback_plan
from companion.patch_update_transaction import snapshot,verified_backup,verify_backup,replace_four
from companion.recovery import no_links,write_json_new
from companion.clean_backup import verify as verify_clean_backup
from scripts.prepare_phase_d_backup import GAME,SAVES,live


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute-authorized',action='store_true')
    args=ap.parse_args()
    if not args.execute_authorized:raise ValueError('EXPLICIT_UPDATE_AUTHORIZATION_REQUIRED')
    public=ROOT/'compatibility/updates/1287369/0.5.1'
    approved=read_pinned(public/'update-manifest.json','a6ef7bd5714353b8b6a3da7354baff4581de7effb1f9409fab4b5f983ac4bdf4')
    backup_plan=read_pinned(public/'backup-plan.json','25e8f7b7f043685860eac9b6d11c0b4756a067d29031e1375ba6f840f1d3ebae')
    receipt_template=read_pinned(public/'update-receipt-template.json','476cf14aa05afa1417c9a8cd23cf24c62fa0286c55e325f8bafb3049350f31bd')
    package=Path(approved['local_package'])
    plan_sha=approved['update_plan_sha256'];plan=read_pinned(package/'update-plan.json',plan_sha)
    binding=read_pinned(package/'bridge-binding.json',approved['bridge_binding_sha256'])
    read_pinned(public/'profile.json',plan['identity']['profile_sha256'])
    if binding['plan_id']!=plan['plan_id'] or binding['profile_sha256']!=plan['identity']['profile_sha256']:
        raise ValueError('BINDING_CHANGED')
    parent=ROOT/'compatibility/migration/1287369/phase_e/install-receipt.json'
    prior=ROOT/'runtime/stage10_10_1_phase_f/20261118T122931689254Z/post-close-20261118T124158903825Z/inventory-after.json'
    baseline=read_pinned(prior,plan['identity']['post_close_snapshot_sha256'])
    live();preflight(plan,package,GAME,parent,plan['identity']['parent_receipt_sha256'])
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run=ROOT/'runtime/stage10_10_2/install'/stamp;no_links(run);run.mkdir(parents=True,exist_ok=False)
    backup=ROOT/'runtime/backups'/('stage10_10_2-patch-0.5.1-'+stamp)
    try:
        print('PRECHECK files16/build/closed PASS; hashing original/shadow/LOCAL baseline',flush=True)
        before=dict(game=snapshot(GAME),saves=snapshot(SAVES));live()
        write_json_new(run/'before.json',before)
        if before!=baseline:raise ValueError('POST_CLOSE_BASELINE_CHANGED')
        if input_fingerprint(before['game'],'0.5.0')!=plan['old_fingerprint']:
            raise ValueError('OLD_FINGERPRINT_CHANGED')
        verify_clean_backup(ROOT/'runtime/backups/stage10-10-1-clean-20261118',
                            'd671fd038634433b3400682e0b0f7e513a854111b3ca96e123e76b1d1e59250a')
        if len(backup_plan['files'])!=38 or backup_plan['payload_bytes']!=247154745:
            raise ValueError('EXACT_BACKUP_PLAN_CHANGED')
        print('BASELINE222/LOCAL23/SHADOW66 PASS; creating verified backup38',flush=True)
        bm=verified_backup(backup_plan,{'game':GAME,'LOCAL':SAVES,'project':ROOT},backup,live=live)
        backup_sha=file_hash(backup/'manifest.json')
        write_json_new(run/'backup-verified.json',dict(path=str(backup),sha256=backup_sha,files=38,payload_bytes=bm['payload_bytes']))
        preflight(plan,package,GAME,parent,plan['identity']['parent_receipt_sha256'])
        # Backup reading must not change the protected inventory metadata.
        for group,root in [('game',GAME),('saves',SAVES)]:
            for name,row in before[group].items():
                s=(root/name).stat()
                if (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink)!=(row['volume'],row['file_id'],row['size'],row['mtime_ns'],row['links']):
                    raise ValueError('CHANGED_DURING_BACKUP:'+name)
        print('BACKUP38 SHA PASS; replacing four approved files',flush=True)
        completed=replace_four(plan,package,GAME,backup,run/'journal',authorized=True,live=live)
        print('REPLACEMENTS4 VERIFIED; hashing post-update originals/shadow/LOCAL',flush=True)
        after=dict(game=snapshot(GAME),saves=snapshot(SAVES));live();write_json_new(run/'after.json',after)
        changes={r['destination']:r for r in plan['entries']}
        if set(after['game'])!=set(before['game']) or after['saves']!=before['saves']:
            raise ValueError('POST_UPDATE_SET_OR_LOCAL_CHANGED')
        for name,row in after['game'].items():
            if name not in changes:
                if row!=before['game'][name]:raise ValueError('PROTECTED_FILE_CHANGED:'+name)
            else:
                r=changes[name]
                if (row['sha256'],row['size'],row['mtime_ns'],row['links'])!=(r['new_sha256'],r['new_bytes'],r['new_mtime_ns'],1):
                    raise ValueError('UPDATED_HASH_OR_METADATA_CHANGED')
        fp=input_fingerprint(after['game'],'0.5.1')
        if fp!=plan['projected_fingerprint'] or fp==plan['old_fingerprint']:
            raise ValueError('NEW_FINGERPRINT_MISMATCH')
        if file_hash(backup/'manifest.json')!=backup_sha:raise ValueError('BACKUP_MANIFEST_CHANGED')
        verify_backup(backup,bm)
        if file_hash(parent)!=plan['identity']['parent_receipt_sha256']:raise ValueError('PARENT_RECEIPT_CHANGED')
        receipt=dict(receipt_template,status='UPDATED',executed=True,updated_utc=datetime.now(timezone.utc).isoformat(),
            game_root=str(GAME),backup_path=str(backup),verified_backup_manifest_sha256=backup_sha,
            per_file_before_after_journal=str(run/'journal'),all_16_installed_hashes='PASS',
            actual_content_fingerprint=fp,post_update_originals_LOCAL_shadow_integrity='PASS',
            runtime_validation='NOT_EXECUTED',RUNTIME_RENDER_CONFIRMED='UNKNOWN',spawn_ready=False)
        receipt.pop('required_after_execution')
        verify_updated(plan,plan_sha,receipt,GAME)
        rollback=rollback_plan(plan,GAME,backup/'payload/game')
        write_json_new(run/'rollback-dry-run.json',rollback)
        write_json_new(run/'update-receipt.json',receipt)
        result=dict(status='READY_FOR_REPEAT_LOAD_ONLY_APPROVAL',run=str(run),backup=str(backup),
            backup_files=38,backup_payload_bytes=bm['payload_bytes'],backup_manifest_sha256=backup_sha,
            receipt_path=str(run/'update-receipt.json'),receipt_sha256=file_hash(run/'update-receipt.json'),
            installed_effective_verified=16,updated_files=completed,game_files=222,
            non_target_game_files_unchanged=218,original_resources_unchanged=67,shadow_files_unchanged=66,
            LOCAL_unchanged=23,content_fingerprint=fp,old_shadow_state='PRESERVED_FAILED_0.5.0; NATIVE_REBUILD_PENDING',
            rollback_dry_run='PASS4_NOT_EXECUTED',runtime_validation='NOT_EXECUTED',
            RUNTIME_RENDER_CONFIRMED='UNKNOWN',spawn_ready=False)
        write_json_new(run/'result.json',result)
        output=public/'installation';output.mkdir(exist_ok=False)
        for name,data in [('receipt.json',receipt),('result.json',result),('rollback-dry-run.json',rollback)]:
            write_json_new(output/name,data)
        if file_hash(output/'receipt.json')!=result['receipt_sha256']:raise ValueError('PUBLIC_RECEIPT_CHANGED')
        print(json.dumps(result,indent=2),flush=True)
    except Exception as exc:
        write_json_new(run/'failure.json',dict(status='STOPPED',error=str(exc),backup_path=str(backup),
                                              automatic_rollback=False,game_not_launched=True,spawn_ready=False))
        print('STOPPED; inspect '+str(run/'failure.json'),flush=True)
        raise


if __name__=='__main__':main()
