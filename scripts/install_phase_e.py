"""Stage10.10.1 Phase E: only the separately approved 16-file plan. No launch."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.clean_backup import verify
from companion.compatibility import file_hash,load_profile
from companion.integrated_deployment import read_pinned,validate_plan,preinstall,rollback_dry_run
from companion.integrated_install import copy_approved
from companion.integrated_writer import content_fingerprint
from companion.recovery import inventory,no_links,measure,target,write_json_new
from companion.residual_quarantine import capture
from scripts.prepare_phase_d_backup import live,GAME,SAVES

APPROVED_PLAN_SHA='82db6fe28bfff96a6580d7a01cd497ad595baf68fe3098312b95181d27ba9463'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--install-approved',action='store_true')
    args=ap.parse_args()
    public=json.loads((ROOT/'compatibility/migration/1287369/exact-install-manifest.json').read_text())
    if public['plan_sha256']!=APPROVED_PLAN_SHA: raise ValueError('NOT_THE_APPROVED_PLAN')
    package=Path(public['local_package'])
    plan=read_pinned(package/'install-plan.json',APPROVED_PLAN_SHA)
    if public['entries']!=plan['entries'] or len(plan['entries'])!=16: raise ValueError('PUBLIC_PLAN_MISMATCH')
    validate_plan(plan,package)
    read_pinned(package/'bridge-binding.json',public['bridge_binding_sha256'])
    profile=load_profile(1287369)
    if file_hash(ROOT/'compatibility/profiles/1287369.json')!=plan['identity']['profile_sha256']:
        raise ValueError('PROFILE_CHANGED')
    for name,sha in plan['identity']['source_hashes'].items():
        if file_hash(ROOT/name)!=sha: raise ValueError('SOURCE_CHANGED:'+name)
    archive=ROOT/'runtime/stage10_10/EMF-0.6.18-manual.zip'
    if file_hash(archive)!=plan['identity']['archive_sha256']: raise ValueError('ARCHIVE_CHANGED')
    backup=Path(plan['backup_path'])
    verify(backup,plan['identity']['backup_manifest_sha256'])
    baseline=json.loads((backup/'baseline.json').read_text())
    live()
    if (GAME/'emf/content/client').exists(): raise ValueError('UNEXPECTED_SHADOW')
    for root in (GAME,SAVES):
        no_links(root)
        for p in root.rglob('*'): no_links(p)
    print('SOURCE_AND_BACKUP_PASS; verifying original game hashes',flush=True)
    preinstall(plan,package,GAME,baseline)
    if file_hash(GAME/'enshrouded.exe')!=profile['exe_sha256']: raise ValueError('EXE_BUILD_CHANGED')
    if set(inventory(SAVES))!=set(baseline['saves']): raise ValueError('LOCAL_FILE_SET_CHANGED')
    for group,root in [('game',GAME),('saves',SAVES)]:
        for name,row in baseline[group].items():
            p=target(root,name)
            if p.stat().st_mtime_ns!=row['mtime_ns']: raise ValueError('BASELINE_MTIME_CHANGED:'+name)
            if group=='saves' and measure(p)!={'sha256':row['sha256'],'size':row['bytes']}:
                raise ValueError('LOCAL_SAVE_CHANGED')
    histories=[ROOT/p for p in ('runtime/backups/stage10-10-1-phase-b-20261118T1035Z',
        'runtime/quarantine/stage10-10-1-phase-b-20261118T1035Z','runtime/quarantine/stage10-10-1-phase-c-20261118T1122Z')]
    history={str(p):inventory(p) for p in histories}
    live()
    if not args.install_approved:
        print('PREFLIGHT_PASS_16_ABSENT_NO_INSTALLATION');return
    run=ROOT/'runtime/stage10_10_1_phase_e'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    no_links(run);run.mkdir(parents=True,exist_ok=False)
    write_json_new(run/'preflight.json',dict(status='PASS',build=1287369,game_files=137,local_files=23,
        backup_files=27,approved_plan_sha256=APPROVED_PLAN_SHA,sources_verified=True,targets_absent=16,
        user_authorized_phase_e=True,spawn_ready=False))
    try:
        receipt=copy_approved(plan,APPROVED_PLAN_SHA,package,GAME,run/'transaction',authorized=True,live=live)
        print('INSTALLED_16_VERIFIED; checking original resources and LOCAL again',flush=True)
        after=capture({'game':GAME,'saves':SAVES})
        installed_names={r['destination'] for r in plan['entries']}
        if set(after['game'])!=set(baseline['game'])|installed_names: raise ValueError('POST_INSTALL_UNEXPECTED_FILE_SET')
        if any(after['game'][n]!=v for n,v in baseline['game'].items()): raise ValueError('POST_INSTALL_ORIGINAL_CHANGED')
        if after['saves']!=baseline['saves']: raise ValueError('POST_INSTALL_LOCAL_CHANGED')
        verify(backup,plan['identity']['backup_manifest_sha256'])
        if history!={str(p):inventory(p) for p in histories}: raise ValueError('HISTORICAL_BACKUP_OR_QUARANTINE_CHANGED')
        live()
        rollback=rollback_dry_run(plan,APPROVED_PLAN_SHA,receipt,GAME)
        write_json_new(run/'after-inventory.json',after)
        write_json_new(run/'rollback-dry-run.json',rollback)
        result=dict(format='aic_phase_e_result_v1',status='READY_FOR_PHASE_F_APPROVAL',run_path=str(run),
            plan_sha256=APPROVED_PLAN_SHA,receipt_path=str(run/'transaction/install-receipt.json'),
            receipt_sha256=file_hash(run/'transaction/install-receipt.json'),installed_files_verified=16,
            original_game_files_unchanged=137,local_files_unchanged=23,clean_backup_verified=27,
            historical_backups_and_quarantines_unchanged=True,rollback_dry_run='PASS_16_OPERATIONS_NOT_EXECUTED',
            content_input_fingerprint=content_fingerprint(GAME),installation_authorized=True,installation_executed=True,
            game_started=False,server_started=False,runtime_status='NOT_EXECUTED',phase_f_authorized=False,spawn_ready=False)
        write_json_new(run/'result.json',result)
        public_dir=ROOT/'compatibility/migration/1287369/phase_e';public_dir.mkdir(exist_ok=False)
        write_json_new(public_dir/'result.json',result)
        write_json_new(public_dir/'install-receipt.json',receipt)
        write_json_new(public_dir/'rollback-dry-run.json',rollback)
        print(json.dumps(result,indent=2))
    except Exception as exc:
        write_json_new(run/'failure.json',dict(status='STOPPED',error=str(exc),automatic_rollback=False))
        print('STOPPED: '+str(exc)+'; evidence='+str(run),flush=True)
        raise


if __name__=='__main__':main()
