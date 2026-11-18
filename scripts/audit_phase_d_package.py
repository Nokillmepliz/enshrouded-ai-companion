"""Read-only real preflight + project-local simulated installed rollback audit."""
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.clean_backup import verify
from companion.compatibility import file_hash, load_profile
from companion.integrated_deployment import read_pinned, validate_plan, preinstall, rollback_dry_run
from companion.recovery import measure, inventory, target, write_json_new
from scripts.prepare_phase_d_backup import live,GAME,SAVES


def main():
    public=json.loads((ROOT/'compatibility/migration/1287369/exact-install-manifest.json').read_text())
    package=Path(public['local_package'])
    plan=read_pinned(package/'install-plan.json',public['plan_sha256'])
    validate_plan(plan,package)
    load_profile(1287369)
    if file_hash(ROOT/'compatibility/profiles/1287369.json')!=plan['identity']['profile_sha256']:
        raise ValueError('PROFILE_CHANGED_SINCE_PACKAGE')
    for name,sha in plan['identity']['source_hashes'].items():
        if file_hash(ROOT/name)!=sha: raise ValueError('SOURCE_CHANGED_SINCE_PACKAGE')
    backup=Path(plan['backup_path'])
    verify(backup,plan['identity']['backup_manifest_sha256'])
    baseline=json.loads((backup/'baseline.json').read_text())
    live()
    print('PINNED_PACKAGE_AND_BACKUP_PASS; checking real original hashes',flush=True)
    status=preinstall(plan,package,GAME,baseline)
    if {p.relative_to(SAVES).as_posix() for p in SAVES.rglob('*') if p.is_file()}!=set(baseline['saves']):
        raise ValueError('LOCAL_SAVE_FILE_SET_CHANGED')
    for name,row in baseline['saves'].items():
        if measure(target(SAVES,name))!={'sha256':row['sha256'],'size':row['bytes']}:
            raise ValueError('LOCAL_SAVE_CHANGED')
    history=json.loads((ROOT/'runtime/stage10_10_1_phase_d/accepted-baseline/history-before.json').read_text())
    # The first capture used folder names and collided for backup/quarantine B.
    # Do not rewrite historical evidence; verify the old backup independently
    # against its pinned manifest, receipt and plan as well.
    from scripts.stage10_10_1_phase_c_cleanup import historical_check
    old_plan=json.loads((ROOT/'compatibility/recovery/1287369/cleanup_manifest.json').read_text())
    historical=historical_check(old_plan,ROOT/'runtime/backups/stage10-10-1-phase-b-20261118T1035Z',
                               ROOT/'runtime/quarantine/stage10-10-1-phase-b-20261118T1035Z')
    for path in [ROOT/'runtime/quarantine/stage10-10-1-phase-b-20261118T1035Z',
                 ROOT/'runtime/quarantine/stage10-10-1-phase-c-20261118T1122Z']:
        if inventory(path)!=history[path.name]: raise ValueError('HISTORY_CHANGED')
    live()
    fixture=ROOT/'runtime/stage10_10_1_phase_d/rollback-fixture'
    fixture.mkdir(parents=True,exist_ok=False)
    shutil.copytree(package/'game',fixture/'game')
    receipt=dict(format='aic_integrated_receipt_v1',status='INSTALLED',build=1287369,
                 plan_sha256=public['plan_sha256'],plan_id=plan['plan_id'],entries=plan['entries'])
    rollback=rollback_dry_run(plan,public['plan_sha256'],receipt,fixture/'game')
    # The simulated receipt deliberately stays in memory. No real install receipt
    # is manufactured, and the real game is never passed to a mutation routine.
    result=dict(format='aic_phase_d_verification_v1',preflight=status,
                real_game_files_unchanged=len(baseline['game']),local_saves_unchanged=len(baseline['saves']),
                clean_backup_payload_verified=27,prior_backup_and_quarantines='PASS',
                prior_backup_payload_verified=historical['verified_backup_payload_files'],
                package_files_verified=16,plan_sha256=public['plan_sha256'],
                rollback_scope='PROJECT_FIXTURE_16_FILES_NO_RUNTIME_SHADOW',rollback=rollback,
                real_install_receipt='NOT_CREATED_INSTALLATION_NOT_EXECUTED',
                runtime_status='NOT_EXECUTED',installation_executed=False,spawn_ready=False)
    write_json_new(ROOT/'compatibility/migration/1287369/offline-verification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='rollback'},indent=2))


if __name__=='__main__': main()
