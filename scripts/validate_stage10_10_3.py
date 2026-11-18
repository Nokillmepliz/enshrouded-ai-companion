"""Offline re-evaluation of the reviewed 0.5.1 session; historical results immutable."""
from datetime import datetime,timezone
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.compatibility import file_hash
from companion.integrated_deployment import read_pinned
from companion.integrated_update import verify_updated,check_plan,input_fingerprint
from companion.integrated_writer import validate_state
from companion.integrated_evidence import verdict
from companion.patch_update_transaction import snapshot,verify_backup
from companion.shadow_integrity import audit_shadow
from companion.recovery import write_json_new
from companion.runtime_validation import semantic_readback,reassess_post_close,redirection
from scripts.prepare_phase_d_backup import live,GAME,SAVES


def main():
    live()
    work=ROOT/'runtime/stage10_10_3';decoded=work/'decoded'
    public=ROOT/'compatibility/updates/1287369/0.5.1'
    oldrun=ROOT/'runtime/stage10_10_2/load_only/20261118T134435140530Z'
    postrun=oldrun/'post-close-20261118T135045278853Z'
    before=read_pinned(oldrun/'inventory-before.json','fa172fc1c270ac4cd5751fdc185211149d8053adac8227fa03b1aa46d3204d18')
    current=json.loads((work/'before.json').read_text())
    if current!=json.loads((postrun/'inventory-after.json').read_text()):raise ValueError('LATEST_BASELINE_MISMATCH')
    profile=read_pinned(public/'profile.json','c8bb6fd1776f1c8a35ef8fc6d0f9c464e6102d43f4295721732f7728941bbc8b')
    approved=read_pinned(public/'update-manifest.json','a6ef7bd5714353b8b6a3da7354baff4581de7effb1f9409fab4b5f983ac4bdf4')
    package=Path(approved['local_package']);plan=read_pinned(package/'update-plan.json',approved['update_plan_sha256']);check_plan(plan,package)
    receipt=read_pinned(public/'installation/receipt.json','8fa2fa02ef0ad12b5c3c00864c0e81f21803fc2851872a708dea4e4d8efd2053')
    verify_updated(plan,approved['update_plan_sha256'],receipt,GAME)
    backup=Path(receipt['backup_path']);verify_backup(backup,read_pinned(backup/'manifest.json',receipt['verified_backup_manifest_sha256']))
    exe=ROOT/'.tools/kfc-inspector/target/release/kfc-readonly-inspect.exe'
    if file_hash(exe)!='81531333e5b73d7c1fed55dcfb8284c874deb2e4f84a6a68dbe4bed79314f075':raise ValueError('INSPECTOR_CHANGED')
    load=lambda name:json.loads((decoded/(name+'.json')).read_text())
    semantic=semantic_readback(load('source-original'),load('source-shadow'),load('clone'),load('hierarchy'),load('presets'),[load('dependency-%02d'%i) for i in range(63)],profile)
    for name,old in [('hierarchy','humanoid_hierarchy'),('presets','character_preset_collection')]:
        baseline=json.loads((ROOT/'runtime/stage10_10_1_post_steam/20261118-audit/resources'/(old+'.json')).read_text())
        if load(name)['resource']!=baseline['resource']:raise ValueError('VISUAL_BASELINE_CHANGED:'+name)
    db=load('database-audit')
    if db['container_count']!=64 or db['duplicate_resource_ids'] or db['templates_decoded']!=12270 or db['requested_npc_id']!=profile['npc_id'] or db['npc_collisions']!=[profile['clone_guid']]:
        raise ValueError('DATABASE_AUDIT_MISMATCH')
    shadow={n.removeprefix('emf/content/client/'):r for n,r in current['game'].items() if n.startswith('emf/content/client/')}
    base={f'enshrouded_{i:03}.dat' for i in range(55)}|{'enshrouded.exe'}
    generated={f'enshrouded_{i:03}.dat' for i in range(55,64)}
    roles={n:'BASE_LINK' for n in base}
    roles.update({n:'GENERATED_DAT' for n in generated})
    roles.update({n:'PRIVATE_INDEX' for n in ['enshrouded.kfc','enshrouded.kfc.bak','enshrouded.kfc_resources']})
    roles.update({f'mods/aic_eml_humanoid/{n}':'MOD_COPY' for n in ['mod.json','README.md','src/mod.lua']})
    roles.update({n:'CACHE' for n in ['.cache/files.json','.cache/types.json','.cache/lua/base.lua','.cache/lua/types.lua']})
    roles.update({n:'METADATA' for n in ['shadow.txt','emf_content_state.json']})
    if set(shadow)!=set(roles) or len(shadow)!=77:raise ValueError('EXACT_SHADOW77_SET')
    for c in db['containers']:
        if shadow[c['path']]['size']!=c['bytes']:raise ValueError('DATABASE_CONTAINER_SIZE')
    for n,role in roles.items():
        if role=='MOD_COPY' and shadow[n]['sha256']!=current['game'][n]['sha256']:raise ValueError('MOD_COPY_CHANGED')
    if shadow['enshrouded.kfc.bak']['sha256']!=current['game']['enshrouded.kfc']['sha256']:raise ValueError('SHADOW_BASE_BACKUP_CHANGED')
    manifest=(GAME/'emf/content/client/shadow.txt').read_text()
    actual=[line for line in manifest.splitlines() if line and not line.startswith('#')]
    expected=[f"source {n} {current['game'][n]['size']} {current['game'][n]['mtime_ns']//100+116444736000000000}" for n in ['enshrouded.exe','enshrouded.kfc','enshrouded.kfc_resources']]+['dat_count 64']
    if actual!=expected:raise ValueError('SHADOW_MANIFEST_MISMATCH')
    fp=input_fingerprint(current['game'],'0.5.1')
    if fp!=receipt['actual_content_fingerprint']:raise ValueError('FINGERPRINT_CHANGED')
    state=json.loads((GAME/'emf/content/client/emf_content_state.json').read_text())
    writer=validate_state(state,fp,not_before=datetime.fromisoformat('2026-11-18T13:44:35+00:00'),not_after=datetime.fromisoformat('2026-11-18T13:50:45+00:00'),patch_version='0.5.1')
    prefix=oldrun/'post-close-20261118T135045278853Z'
    ns=lambda s:int(datetime.fromisoformat(s).timestamp()*1e9)
    attribution=reassess_post_close(before['game'],current['game'],archive='backup/enshrouded_2026-11-18T16-46-15.log',session_start_ns=ns('2026-11-18T13:46:13+00:00'),session_end_ns=ns('2026-11-18T13:49:21+00:00'))
    redirect=redirection((prefix/'file_opens.log').read_text(),str(GAME),{'enshrouded.kfc','enshrouded.kfc_resources'}|base-{'enshrouded.exe'}|generated,started_local='2026-11-18 16:46:15')
    print('Semantic readback / attribution v2 / redirected read opens PASS; auditing shadow77 and originals',flush=True)
    original_base=json.loads((ROOT/'runtime/stage10_10_1_phase_f/20261118T122931689254Z/originals-before.json').read_text())
    filesystem=audit_shadow(GAME,GAME/'emf/content/client',original_base,{n:dict(role=r,sha256=shadow[n]['sha256']) for n,r in roles.items()},base_dat_count=55)
    print('Existing audit_shadow PASS; hashing final game/LOCAL inventory',flush=True)
    after=dict(game=snapshot(GAME),saves=snapshot(SAVES));live()
    write_json_new(work/'after.json',after)
    if after!=current:raise ValueError('FILES_CHANGED_DURING_OFFLINE_READBACK')
    gates={k:dict(status='PASS',source='stage10.10.3 offline readback and exact post-close inventory; see result fields') for k in
        ['original_integrity','single_content_owner','shadow_integrity','writer_finalized','content_unloaded','fresh_state','shadow_readback','resource_redirection','no_legacy_artifacts']}
    if redirect['status']!='PASS':gates['resource_redirection']['status']='UNKNOWN'
    evidence=json.loads((public/'load-only/runtime-result.json').read_text())['build_evidence']
    result=dict(stage='10.10.3',checked_utc=datetime.now(timezone.utc).isoformat(),status='OFFLINE_VALIDATION_COMPLETE_RUNTIME_BRIDGE_PENDING',
        game_server_closed=True,post_close_validator=attribution,shadow_readback=semantic,writer=writer,
        shadow_filesystem=filesystem['filesystem_integrity'],shadow_files=77,base_hardlinks=56,
        generated_dat={n:dict(bytes=shadow[n]['size'],sha256=shadow[n]['sha256']) for n in sorted(generated)},
        database_audit={k:v for k,v in db.items() if k!='containers'},resource_redirection=redirect,
        original_files_unchanged=67,installed_verified=16,backup_verified=38,
        offline_game_records_unchanged=len(after['game']),offline_LOCAL_records_unchanged=len(after['saves']),
        before_sha256=file_hash(work/'before.json'),after_sha256=file_hash(work/'after.json'),
        historical_blocked_result_preserved=True,decoded_hashes={p.name:file_hash(p) for p in decoded.glob('*.json')},
        shadow_attribution={n:dict(role=roles[n],**shadow[n]) for n in sorted(shadow)},
        verdict=verdict(evidence,gates),spawn_ready=False,RUNTIME_RENDER_CONFIRMED='UNKNOWN')
    output=ROOT/'compatibility/updates/1287369/0.5.1/stage10_10_3';output.mkdir(exist_ok=False)
    write_json_new(output/'result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['shadow_attribution','decoded_hashes','resource_redirection','generated_dat']},indent=2),flush=True)


if __name__=='__main__':main()
