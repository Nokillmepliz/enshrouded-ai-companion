"""Offline continuation plan and fresh LOCAL backup; no installed file writes."""
import json
from pathlib import Path
import sys
import uuid
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.compatibility import file_hash
from companion.integrated_deployment import read_pinned
from companion.experimental_install_check import verify
from companion.experimental_wait import verify_history
from companion.patch_update_transaction import snapshot,verified_backup,verify_backup
from companion.recovery import write_json_new
from scripts.prepare_phase_d_backup import GAME,SAVES,live

def main():
    live()
    public=ROOT/'compatibility/experiments/stage10_11_2'
    private=ROOT/'runtime/stage10_11_2'
    if public.exists() or private.exists():raise ValueError('NEW_OUTPUT_REQUIRED')
    source=ROOT/'runtime/stage10_11_1/live/20261118T155811475946Z/session230172/post-close/inventory-after.json'
    baseline=read_pinned(source,'6cd6ac15025cce3119236b1e52d998a5d850e86c95ec6eace16c1af70e9d23bf')
    binding=verify(ROOT/'dist/stage10_11_first_spawn_0_1_0',
        '6ecc792b6c320dc19f0fa201259c573efd142c4c37a579eab07376dc40b9e1e3',
        ROOT/'compatibility/experiments/stage10_11/installation/receipt.json',
        '3b9d80c0ade318c378584e38809eda54d6c4bc689ef16f1a5af28e5a993fd950',ROOT)
    if (GAME/'emf/mods/aic_first_spawn/attempt.lock').read_bytes()!=('UNUSED:'+binding['key']).encode():
        raise ValueError('LATCH_NOT_UNUSED')
    print('Closed/install/old backup PASS; hashing current baseline',flush=True)
    now=dict(game=snapshot(GAME),saves=snapshot(SAVES));live()
    if now!=baseline:raise ValueError('POST_CLOSE_BASELINE_CHANGED')
    journal=ROOT/'runtime/stage10_11/experiments'/binding['key']
    history={p.relative_to(journal).as_posix():file_hash(p) for p in journal.rglob('*') if p.is_file()}
    old_plan=read_pinned(ROOT/'runtime/stage10_11_1/continuation-plan.json',
        '5f31ce5a6fd718a73d52c7832b3d5f162b4969b075049affc662802e6f7aba0f')
    verify_history(journal,old_plan['history'],old_plan['attempt'])
    probes=[json.loads(p.read_text()) for p in journal.rglob('probe.json')]
    if len(probes)!=2:raise ValueError('EXPECTED_TWO_PRIOR_PROBES')
    old=json.loads((journal/old_plan['attempt']/'probe.json').read_text())
    attempt='attempts/'+uuid.uuid4().hex
    verify_history(journal,history,attempt)
    # Any ambiguous prior mutation disallows continuation even with an unused latch.
    for rel in history:
        if rel.endswith('-request.json'):
            if json.loads((journal/rel).read_text())['command'] not in ('status','probe'):
                raise ValueError('PRIOR_MUTATION_OR_UNKNOWN_REQUEST')
    private.mkdir();public.mkdir(parents=True)
    write_json_new(private/'baseline.json',baseline)
    bp=dict(format='aic_stage10_11_2_local_backup_v1',baseline_inventory_sha256=file_hash(source),
        files=[dict(group='saves',path=n,sha256=r['sha256'],bytes=r['size']) for n,r in sorted(now['saves'].items())])
    write_json_new(public/'backup-plan.json',bp)
    backup=ROOT/'runtime/backups/stage10_11_2-local-before-new-probe'
    bm=verified_backup(bp,{'saves':SAVES},backup,live=live);verify_backup(backup,bm)
    if snapshot(SAVES)!=now['saves']:raise ValueError('SAVES_CHANGED_DURING_BACKUP')
    plan=dict(format='aic_probe_continuation_v1',attempt=attempt,history=history,
        confirmation_mode='local_key_after_ready',previous_sessions=[p['session'] for p in probes],
        previous_session=old['session'],baseline_path=str(private/'baseline.json'),
        baseline_sha256=file_hash(private/'baseline.json'),backup_path=str(backup),
        backup_manifest_sha256=file_hash(backup/'manifest.json'),
        installation_receipt_sha256='3b9d80c0ade318c378584e38809eda54d6c4bc689ef16f1a5af28e5a993fd950',
        spawn_authorized=False,deadline_seconds=20,poll_interval_seconds=0.25,
        minimum_confirmation_seconds=8,send_reserve_seconds=2)
    write_json_new(private/'continuation-plan.json',plan)
    verify_history(journal,history,attempt);live()
    result=dict(status='OFFLINE_CONTINUATION_PREPARED_NOT_LIVE_AUTHORIZED',
        baseline_sha256=plan['baseline_sha256'],game_files=len(now['game']),local_files=len(now['saves']),
        backup_files=len(bm['files']),backup_bytes=bm['payload_bytes'],
        backup_manifest_sha256=plan['backup_manifest_sha256'],
        continuation_plan_sha256=file_hash(private/'continuation-plan.json'),
        preserved_history_files=len(history),installed_verified=23,latch='UNUSED',
        spawn_ready=False,production_spawn_ready=False,spawn_executed=False)
    write_json_new(public/'preparation.json',result)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
