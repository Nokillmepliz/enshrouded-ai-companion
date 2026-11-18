"""Prepare four changed files in project/dist. Never install or clean shadow."""
import hashlib
import json
import os
from pathlib import Path
import sys
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.compatibility import file_hash,fingerprint
from companion.integrated_deployment import read_pinned,installed
from companion.integrated_update import TARGETS,check_plan,input_fingerprint,preflight
from companion.recovery import no_links,write_json_new
from scripts.prepare_phase_d_backup import GAME,live
from scripts.prepare_phase_d_package import lua


def main():
    live()
    public=ROOT/'compatibility/updates/1287369/0.5.1'
    package=ROOT/'dist/stage10_10_2_patch_0_5_1'
    no_links(package)
    if package.exists():raise ValueError('NEW_PACKAGE_REQUIRED')
    parent_sha='c3cd5da70e01fd073553b6dcc2598e8ede867693087b67c285d65253c59d70fc'
    parent=ROOT/'compatibility/migration/1287369/phase_e/install-receipt.json'
    receipt=read_pinned(parent,parent_sha)
    old=ROOT/'dist/stage10_10_1_phase_d_20261118'
    old_plan=read_pinned(old/'install-plan.json','82db6fe28bfff96a6580d7a01cd497ad595baf68fe3098312b95181d27ba9463')
    installed(old_plan,file_hash(old/'install-plan.json'),receipt,GAME)
    snapshot=ROOT/'runtime/stage10_10_1_phase_f/20261118T122931689254Z/post-close-20261118T124158903825Z/inventory-after.json'
    facts=json.loads(snapshot.read_text())
    profile=json.loads((public/'profile.json').read_text())
    profile_sha=file_hash(public/'profile.json')
    token=uuid.uuid4().hex
    source=ROOT/'experimental/integrated_humanoid_0_5_1'
    identity=dict(targets=sorted(TARGETS),parent_receipt_sha256=parent_sha,profile_sha256=profile_sha,
                  run_token_sha256=hashlib.sha256(token.encode()).hexdigest(),
                  post_close_snapshot_sha256=file_hash(snapshot),
                  source_sha256={n:file_hash(source/n) for n in ('patch.lua','README.md','mod.json')})
    plan_id=fingerprint(identity)
    expected=read_pinned(old/'bridge-binding.json','9b06a725b8daba270db31d99120f91be6dc5878f6ea42c37d10ee504033237b4')
    expected.pop('plan_sha256')
    expected.update(run_token=token,plan_id=plan_id,profile_sha256=profile_sha,patch_version='0.5.1')
    source_meta=profile['expected_resource_metadata']
    contract=dict(expected,accepted_limited_baseline=True,
        game_version='1287369|^/game38/branches/release_1.0|2026-11-04T11:17:54.051725Z',
        dependencies=profile['dependencies'],template_count=12269,
        visual_references=source_meta['decoded_preset_references'],
        preset_collection_guid='a1bea7fc-2122-4dd3-a471-2b815a65134b')
    payload={}
    for n in ('mod.json','README.md'):payload['mods/aic_eml_humanoid/'+n]=(source/n).read_bytes()
    payload['mods/aic_eml_humanoid/src/mod.lua']=(
        'local patch=(function()\n'+(source/'patch.lua').read_text()+'\nend)()\nlocal profile='+lua(contract)+'\npatch.run(game,loader,profile,print)\n').encode()
    binding={k:expected[k] for k in ('run_token','plan_id','profile_sha256')}
    payload['emf/mods/aic_integrated_observer/binding.lua']=('return '+lua(dict(binding,schema=8))+'\n').encode()
    package.mkdir(parents=True)
    rows=[]
    # Fixed package FILETIME: future authorized updater must preserve it and
    # recompute the fingerprint, not rely on a projected value alone.
    timestamp=1795006800000000000
    for name,raw in sorted(payload.items()):
        p=package/'game'/name;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(raw)
        os.utime(p,ns=(timestamp,timestamp))
        current=facts['game'][name]
        rows.append(dict(destination=name,current_sha256=current['sha256'],current_bytes=current['size'],
                         current_mtime_ns=current['mtime_ns'],new_sha256=file_hash(p),new_bytes=len(raw),new_mtime_ns=p.stat().st_mtime_ns,
                         reason='Patch 0.5.1 typed references and diagnostics' if name.startswith('mods/') else 'Fresh run/profile/plan binding; observer code unchanged',
                         backup='VERIFIED_COPY_REQUIRED_BEFORE_UPDATE',restore='ONLY_IF_NEW_HASH_MATCHES; restore verified old bytes/mtime'))
    projected=dict(facts['game'])
    for r in rows:projected[r['destination']]=dict(size=r['new_bytes'],mtime_ns=r['new_mtime_ns'])
    old_fp=input_fingerprint(facts['game'],'0.5.0');new_fp=input_fingerprint(projected,'0.5.1')
    if old_fp==new_fp:raise ValueError('FINGERPRINT_NOT_INVALIDATED')
    plan=dict(format='aic_patch_update_v1',patch_version='0.5.1',build=1287369,identity=identity,plan_id=plan_id,
              entries=rows,current_install_entries=receipt['entries'],old_fingerprint=old_fp,projected_fingerprint=new_fp,
              fingerprint_policy='PRESERVE_PACKAGE_MTIME_AND_RECOMPUTE_AT_AUTHORIZED_UPDATE',
              shadow_policy='NATIVE_REBUILD_ON_NEXT_SEPARATELY_AUTHORIZED_MANUAL_START; NO_MANUAL_CLEANUP',
              installation_authorized=False,installation_executed=False,runtime_validation='NOT_EXECUTED',spawn_ready=False)
    write_json_new(package/'update-plan.json',plan)
    write_json_new(package/'bridge-binding.json',dict(expected,update_plan_sha256=file_hash(package/'update-plan.json')))
    check_plan(plan,package)
    preflight(plan,package,GAME,parent,parent_sha)
    write_json_new(public/'update-manifest.json',dict(plan,local_package=str(package),update_plan_sha256=file_hash(package/'update-plan.json'),bridge_binding_sha256=file_hash(package/'bridge-binding.json')))
    shadow={n:r for n,r in facts['game'].items() if n.startswith('emf/content/client/')}
    write_json_new(public/'shadow-attribution.json',dict(snapshot_sha256=file_hash(snapshot),files=shadow,
        cleanup_authorized=False,action='PRESERVE_NOW; UPSTREAM_REBUILD_LATER',spawn_ready=False))
    backup=[dict(group='game',path=r['destination'],sha256=r['current_sha256'],bytes=r['current_bytes']) for r in rows]
    backup += [dict(group='game',path=n,sha256=r['sha256'],bytes=r['size']) for n,r in shadow.items() if r['links']==1]
    backup += [dict(group='LOCAL',path=n,sha256=r['sha256'],bytes=r['size']) for n,r in facts['saves'].items()]
    backup += [dict(group='project',path=str(parent.relative_to(ROOT)),sha256=parent_sha,bytes=parent.stat().st_size)]
    write_json_new(public/'backup-plan.json',dict(files=backup,payload_bytes=sum(r['bytes'] for r in backup),
        created=False,policy='NEW_VERIFIED_BACKUP_BEFORE_UPDATE; preserve old backups/quarantines; no save restore'))
    effective=[];changed={r['destination']:r for r in rows}
    for row in receipt['entries']:
        r=dict(row)
        if r['destination'] in changed:
            v=changed[r['destination']];r.update(sha256=v['new_sha256'],bytes=v['new_bytes'])
        effective.append(r)
    write_json_new(public/'update-receipt-template.json',dict(format='aic_patch_update_receipt_v1',status='TEMPLATE_NOT_EXECUTED',
        parent_receipt_sha256=parent_sha,update_plan_sha256=file_hash(package/'update-plan.json'),plan_id=plan_id,
        effective_entries=effective,required_after_execution=['verified_backup_manifest_sha256','per_file_before_after_journal',
            'all_16_installed_hashes','actual_content_fingerprint','post_update_originals_LOCAL_shadow_integrity','timestamp'],
        executed=False,spawn_ready=False))
    write_json_new(public/'rollback-plan.json',dict(status='PREPARED_NOT_EXECUTED',operations=[
        dict(path=r['destination'],only_if_sha256=r['new_sha256'],restore_sha256=r['current_sha256'],
             restore_mtime_ns=r['current_mtime_ns']) for r in reversed(rows)],
        shadow='No automatic cleanup or reuse. Fresh audit required after any manual game start.',
        originals='NO_WRITE',LOCAL='NO_RESTORE',full_live_rollback_ready=False))
    print(json.dumps(dict(files=len(rows),backup_files=len(backup),backup_bytes=sum(r['bytes'] for r in backup),
                         fingerprint_changed=old_fp!=new_fp,package=str(package))))


if __name__=='__main__':main()
