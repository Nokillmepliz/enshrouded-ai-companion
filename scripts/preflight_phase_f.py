"""Read-only Phase F checkpoint; no bridge connection, game launch or mutation."""
from datetime import datetime,timezone
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.clean_backup import verify
from companion.compatibility import file_hash,load_profile
from companion.integrated_deployment import read_pinned,validate_plan,installed,rollback_dry_run
from companion.integrated_writer import content_fingerprint
from companion.shadow_integrity import capture_originals,record,no_reparse
from companion.recovery import write_json_new,no_links
from scripts.prepare_phase_d_backup import live,GAME,SAVES


def main():
    live()
    approved=json.loads((ROOT/'compatibility/migration/1287369/exact-install-manifest.json').read_text())
    phase_e=json.loads((ROOT/'compatibility/migration/1287369/phase_e/result.json').read_text())
    if approved['plan_sha256']!='82db6fe28bfff96a6580d7a01cd497ad595baf68fe3098312b95181d27ba9463':
        raise ValueError('APPROVED_PLAN_CHANGED')
    if phase_e['receipt_sha256']!='c3cd5da70e01fd073553b6dcc2598e8ede867693087b67c285d65253c59d70fc':
        raise ValueError('PHASE_E_RECEIPT_CHANGED')
    package=Path(approved['local_package'])
    plan=read_pinned(package/'install-plan.json',approved['plan_sha256'])
    validate_plan(plan,package)
    read_pinned(package/'bridge-binding.json',approved['bridge_binding_sha256'])
    receipt=read_pinned(Path(phase_e['receipt_path']),phase_e['receipt_sha256'])
    installed(plan,approved['plan_sha256'],receipt,GAME)
    rollback=rollback_dry_run(plan,approved['plan_sha256'],receipt,GAME)
    load_profile(1287369)
    if file_hash(ROOT/'compatibility/profiles/1287369.json')!=plan['identity']['profile_sha256']:
        raise ValueError('PROFILE_CHANGED')
    backup=Path(plan['backup_path'])
    verify(backup,plan['identity']['backup_manifest_sha256'])
    baseline=json.loads((backup/'baseline.json').read_text())
    print('RECEIPT_16_AND_BACKUP_27_PASS; capturing original hashes and file identities',flush=True)
    # Reuse the original snapshot for the whole inventory, avoiding a second
    # full read of the same large DAT files in this checkpoint.
    originals=capture_originals(GAME)
    files=dict(originals)
    for p in GAME.rglob('*'):
        no_reparse(p)
        if p.is_file():
            name=p.relative_to(GAME).as_posix()
            if name not in files:files[name]=record(p)
    if any(v['links']!=1 for v in files.values()):raise ValueError('PREEXISTING_HARDLINK')
    targets={r['destination'] for r in plan['entries']}
    if set(files)!=set(baseline['game'])|targets:raise ValueError('GAME_FILE_SET_CHANGED')
    for name,row in baseline['game'].items():
        now=files[name]
        if (now['sha256'],now['size'],now['mtime_ns'])!=(row['sha256'],row['bytes'],row['mtime_ns']):
            raise ValueError('ORIGINAL_CHANGED:'+name)
    saves={}
    for p in SAVES.rglob('*'):
        no_links(p)
        if p.is_file():saves[p.relative_to(SAVES).as_posix()]=record(p)
    if set(saves)!=set(baseline['saves']):raise ValueError('LOCAL_FILE_SET_CHANGED')
    for name,row in baseline['saves'].items():
        now=saves[name]
        if (now['sha256'],now['size'],now['mtime_ns'])!=(row['sha256'],row['bytes'],row['mtime_ns']):
            raise ValueError('LOCAL_CHANGED:'+name)
    selection=[]
    for relative,name in [('default/character0.ksd','Body Test'),('default/world0.ksd','AI Body Test')]:
        raw=(SAVES/relative).read_bytes()
        if raw.count(name.encode('utf-8'))!=1:raise ValueError('LOCAL_NAME_NOT_CONFIRMED')
        selection.append(dict(relative_path=relative,name=name,slot=1,storage='LOCAL',sha256=saves[relative]['sha256'],
            basis='EXACT_BASELINE_SAVE_HASH_AND_UTF8_NAME; prior Stage10.7 runtime association',
            current_runtime_identity='REQUIRES_BRIDGE_STATE_AFTER_MANUAL_LOAD'))
    live()
    timestamp=datetime.now(timezone.utc)
    run=ROOT/'runtime/stage10_10_1_phase_f'/timestamp.strftime('%Y%m%dT%H%M%S%fZ')
    no_links(run);run.mkdir(parents=True,exist_ok=False)
    write_json_new(run/'originals-before.json',originals)
    write_json_new(run/'inventory-before.json',dict(game=files,saves=saves))
    write_json_new(run/'rollback-before.json',rollback)
    result=dict(format='aic_phase_f_preflight_v1',status='READY_FOR_MANUAL_START',
        checked_utc=timestamp.isoformat(),run_path=str(run),build=1287369,steam_build='26430625',
        receipt_sha256=phase_e['receipt_sha256'],installed_files_verified=16,clean_backup_verified=27,
        original_game_files_unchanged=137,local_files_unchanged=23,resource_identity_snapshot=len(originals),
        rollback_dry_run='PASS_NOT_EXECUTED',content_input_fingerprint=content_fingerprint(GAME),
        local_selection=selection,phase_f_authorized=True,game_start_by='USER_ONLY',
        runtime_validation='WAITING_FOR_MANUAL_START',spawn_ready=False)
    write_json_new(run/'preflight.json',result)
    public=ROOT/'compatibility/migration/1287369/phase_f';public.mkdir(exist_ok=False)
    write_json_new(public/'preflight.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
