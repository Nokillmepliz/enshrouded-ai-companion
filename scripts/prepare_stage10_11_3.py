"""Offline package/manifest/backup PLAN only; never installs or writes game/saves."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.compatibility import file_hash
from companion.experimental_install_check import verify
from companion.experimental_wait import verify_history
from companion.integrated_deployment import read_pinned
from companion.patch_update_transaction import snapshot,validate_backup_plan
from companion.recovery import write_json_new,no_links
from companion.smart_deployment import CHANGED,check_manifest
from scripts.prepare_phase_d_backup import GAME,SAVES,live


def main():
    live()
    private=ROOT/'runtime/stage10_11_3'
    public=ROOT/'compatibility/experiments/stage10_11_3'
    package=ROOT/'dist/stage10_11_first_spawn_0_1_1'
    for out in (private,public,package):
        no_links(out)
        if out.exists():raise ValueError('NEW_OUTPUT_REQUIRED')
    source=ROOT/'runtime/stage10_11_2/live/20261118T161719780155Z/session249976/post-close/inventory-after.json'
    baseline=read_pinned(source,'283893ac38d72220b10af73e9a131d269000031de0259b263d9bef84674daf19')
    receipt_path=ROOT/'compatibility/experiments/stage10_11/installation/receipt.json'
    receipt_sha='3b9d80c0ade318c378584e38809eda54d6c4bc689ef16f1a5af28e5a993fd950'
    binding=verify(ROOT/'dist/stage10_11_first_spawn_0_1_0',
        '6ecc792b6c320dc19f0fa201259c573efd142c4c37a579eab07376dc40b9e1e3',receipt_path,receipt_sha,ROOT)
    if (GAME/'emf/mods/aic_first_spawn/attempt.lock').read_bytes()!=('UNUSED:'+binding['key']).encode():
        raise ValueError('LATCH_NOT_UNUSED')
    print('Closed/install23/backup23 PASS. Reading current inventory...',flush=True)
    now=dict(game=snapshot(GAME),saves=snapshot(SAVES));live()
    if now!=baseline:raise ValueError('POST_CLOSE_BASELINE_CHANGED')
    journal=ROOT/'runtime/stage10_11/experiments'/binding['key']
    prior=read_pinned(ROOT/'runtime/stage10_11_2/continuation-plan.json',
        '2d3cd9c0bbef8cd8135c2775fe1322296b8511bc5368e4a7fdc0e3e9a2448989')
    verify_history(journal,prior['history'],prior['attempt'])
    history={}
    for p in journal.rglob('*'):
        no_links(p)
        if p.is_file():history[p.relative_to(journal).as_posix()]=file_hash(p)
    if len(list(journal.rglob('probe.json')))!=3:raise ValueError('THREE_PREVIOUS_PROBES_REQUIRED')
    for rel in history:
        if rel.endswith('-request.json') and json.loads((journal/rel).read_text())['command'] not in ('status','probe'):
            raise ValueError('PRIOR_MUTATION_OR_UNKNOWN_REQUEST')
    for out in (private,public,package):out.mkdir(parents=True)
    write_json_new(private/'baseline.json',baseline)
    rows=[]
    for name in sorted(CHANGED):
        src=ROOT/'mods/aic_first_spawn'/Path(name).name
        dst=package/'payload'/name;dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open('xb') as stream:stream.write(src.read_bytes())
        if file_hash(dst)!=file_hash(src):raise ValueError('PAYLOAD_CHANGED')
        old=baseline['game'][name]
        rows.append(dict(path=name,source='payload/'+name,sha256=file_hash(dst),bytes=dst.stat().st_size,
                         before_sha256=old['sha256'],before_bytes=old['size']))
    prior16=read_pinned(ROOT/'compatibility/updates/1287369/0.5.1/installation/receipt.json',
        '8fa2fa02ef0ad12b5c3c00864c0e81f21803fc2851872a708dea4e4d8efd2053')
    prior7=read_pinned(receipt_path,receipt_sha)
    paths={r['destination'] for r in prior16['effective_entries']}|{r['path'] for r in prior7['entries']}
    by_name={r['path']:r for r in rows}
    effective=[]
    for name in sorted(paths):
        old=baseline['game'][name];new=by_name.get(name)
        effective.append(dict(path=name,sha256=new['sha256'] if new else old['sha256'],
                              bytes=new['bytes'] if new else old['size']))
    manifest=dict(format='aic_smart_position_update_v1',version='0.1.1',game=str(GAME),
        build=1287369,parent_receipt_sha256=receipt_sha,entries=rows,effective_files=effective,
        baseline_sha256=file_hash(source),installed=False,spawn_ready=False)
    check_manifest(manifest,baseline)
    write_json_new(public/'exact-update-manifest.json',manifest)
    bp=dict(format='aic_smart_position_backup_plan_v1',baseline_sha256=file_hash(source),
        files=[dict(group='saves',path=n,sha256=r['sha256'],bytes=r['size']) for n,r in sorted(baseline['saves'].items())]
        +[dict(group='game',path=n,sha256=baseline['game'][n]['sha256'],bytes=baseline['game'][n]['size']) for n in sorted(CHANGED)])
    validate_backup_plan(bp,{'game':GAME,'saves':SAVES},ROOT/'runtime/backups/stage10_11_3-before-update',live=live)
    write_json_new(public/'backup-plan.json',bp)
    binding_path=ROOT/'dist/stage10_11_first_spawn_0_1_0/client-binding.json'
    plan=dict(format='aic_smart_position_plan_v1',confirmation_mode='local_key_after_ready',
        manifest_path=str(public/'exact-update-manifest.json'),manifest_sha256=file_hash(public/'exact-update-manifest.json'),
        baseline_path=str(private/'baseline.json'),baseline_sha256=file_hash(private/'baseline.json'),
        binding_path=str(binding_path),binding_sha256=file_hash(binding_path),history=history,
        deadline_seconds=20,minimum_confirmation_seconds=8,send_reserve_seconds=2,
        installed=False,spawn_authorized=False)
    write_json_new(private/'smart-position-plan.json',plan)
    verify_history(journal,history,'unused-placeholder')
    live()
    result=dict(status='OFFLINE_SMART_POSITION_PREPARED_INSTALL_APPROVAL_REQUIRED',
        installed_version='0.1.0',prepared_version='0.1.1',changed_files=4,effective_files=23,
        baseline_sha256=file_hash(source),game_files=len(now['game']),local_files=len(now['saves']),
        manifest_sha256=plan['manifest_sha256'],plan_sha256=file_hash(private/'smart-position-plan.json'),
        backup_plan_sha256=file_hash(public/'backup-plan.json'),backup_planned_files=len(bp['files']),
        backup_planned_bytes=sum(r['bytes'] for r in bp['files']),new_backup_created=False,
        preserved_history_files=len(history),preserved_probes=3,latch='UNUSED',
        ground_queries_executed=0,spawn_executed=False,spawn_ready=False,production_spawn_ready=False)
    write_json_new(public/'preparation.json',result)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
