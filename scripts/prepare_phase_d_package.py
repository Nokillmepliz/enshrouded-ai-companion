"""Build the exact offline Phase D candidate. Never write into the game."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from companion.clean_backup import verify
from companion.compatibility import file_hash, fingerprint, load_profile
from companion.integrated_deployment import validate_plan
from companion.recovery import no_links, target, write_json_new
from scripts.prepare_integrated_components import ARCHIVE_SHA, PREFIX, GAME_FILES, LICENSES, verified_members
from scripts.prepare_phase_d_backup import TARGETS


def lua(value):
    if isinstance(value, bool): return str(value).lower()
    if value is None: return 'nil'
    if isinstance(value, (int, float)): return str(value)
    if isinstance(value, str): return json.dumps(value, ensure_ascii=True)
    if isinstance(value, list): return '{'+','.join(lua(v) for v in value)+'}'
    return '{'+','.join('['+lua(k)+']='+lua(v) for k,v in sorted(value.items()))+'}'


def build(output):
    no_links(output)
    if output.exists() or not output.resolve().is_relative_to((ROOT/'dist').resolve()):
        raise ValueError('NEW_PROJECT_DIST_REQUIRED')
    accepted = json.loads((ROOT/'compatibility/recovery/1287369/post_steam/accepted-backup.json').read_text())
    verify(Path(accepted['backup_path']), accepted['manifest_sha256'])
    profile = load_profile(1287369)
    profile_sha = file_hash(ROOT/'compatibility/profiles/1287369.json')
    source = profile['expected_resource_metadata']
    token = uuid.uuid4().hex
    source_files = ['experimental/integrated_humanoid/'+n for n in ('patch.lua','mod.json','README.md')]
    source_files += ['mods/aic_integrated_observer/'+n for n in ('main.lua','mod.json','README.md')]
    source_files += ['experimental/integrated_content/'+n for n in ('emf_core.ini','lua.ini','observer.ini')]
    identity = dict(build=1287369, profile_sha256=profile_sha,
                    baseline_sha256=accepted['acceptance']['baseline_sha256'],
                    backup_manifest_sha256=accepted['manifest_sha256'], archive_sha256=ARCHIVE_SHA,
                    run_token_sha256=hashlib.sha256(token.encode()).hexdigest(), targets=TARGETS,
                    source_hashes={n:file_hash(ROOT/n) for n in source_files})
    plan_id = fingerprint(identity)
    expected = dict(run_token=token, plan_id=plan_id, profile_sha256=profile_sha,
        baseline_sha256=identity['baseline_sha256'], source_guid=profile['source_guid'], clone_guid=profile['clone_guid'],
        component_count=source['component_count'], component_fingerprint=source['component_fingerprint_fnv32'],
        hashkeys={k:v['value'] for k,v in source['character_setup'].items() if isinstance(v,dict)},
        animation_graph=source['animation']['animationGraph'], gender=source['character_setup']['gender'],
        use_new_proportions=source['character_setup']['useNewProportions'], npc_id=profile['npc_id'],
        dependencies_resolved=len(profile['dependencies']), dependency_set_sha256=profile['dependency_set_sha256'],
        npc_collision_scan=12269,hierarchy_guid=source['hierarchy_guid'],joint_count=source['joints'],
        visual_reference_count=len(source['decoded_preset_references']))
    contract = dict(expected, accepted_limited_baseline=True,
        game_version='1287369|^/game38/branches/release_1.0|2026-11-04T11:17:54.051725Z',
        dependencies=profile['dependencies'], template_count=12269,
        visual_references=source['decoded_preset_references'],
        preset_collection_guid='a1bea7fc-2122-4dd3-a471-2b815a65134b')
    members = {f'game/{n}':PREFIX+'game/'+n for n in GAME_FILES}
    members.update({n:PREFIX+n for n in LICENSES})
    data = verified_members(ROOT/'runtime/stage10_10/EMF-0.6.18-manual.zip',ARCHIVE_SHA,members.values())
    index = {e['path']:e for e in json.loads((ROOT/'compatibility/audits/1287369/release-files.json').read_text())}
    payload = {}
    for dest, src in members.items():
        if hashlib.sha256(data[src]).hexdigest()!=index[src]['sha256'] or len(data[src])!=index[src]['bytes']:
            raise ValueError('OFFICIAL_MEMBER_CHANGED')
        payload[dest] = data[src]
    for src,dest in [('emf_core.ini','emf/emf_core.ini'),('lua.ini','emf/config/lua.ini'),
                     ('observer.ini','emf/config/aic_integrated_observer.ini')]:
        payload['game/'+dest]=(ROOT/'experimental/integrated_content'/src).read_bytes()
    for name in ('mod.json','README.md'):
        payload['game/mods/aic_eml_humanoid/'+name]=(ROOT/'experimental/integrated_humanoid'/name).read_bytes()
    patch = (ROOT/'experimental/integrated_humanoid/patch.lua').read_text(encoding='utf-8')
    payload['game/mods/aic_eml_humanoid/src/mod.lua']=(
        'local patch=(function()\n'+patch+'\nend)()\nlocal profile='+lua(contract)+'\npatch.run(game,loader,profile,print)\n').encode()
    for name in ('main.lua','mod.json','README.md'):
        payload['game/emf/mods/aic_integrated_observer/'+name]=(ROOT/'mods/aic_integrated_observer'/name).read_bytes()
    binding = {k:expected[k] for k in ('run_token','plan_id','profile_sha256')}
    payload['game/emf/mods/aic_integrated_observer/binding.lua']=('return '+lua(dict(binding,schema=8))+'\n').encode()
    if {p[5:] for p in payload if p.startswith('game/')} != set(TARGETS):
        raise ValueError('BACKUP_DESTINATION_PLAN_DIVERGED')
    output.mkdir(parents=True)
    for name, raw in payload.items():
        dest=target(output,name); dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as stream: stream.write(raw)
    entries=[]
    for name in TARGETS:
        p=output/'game'/name
        entries.append(dict(source='game/'+name,destination=name,sha256=file_hash(p),bytes=p.stat().st_size,
            before_sha256=None,owner='EMF_0.6.18_OFFICIAL' if name in GAME_FILES else 'AIC_PHASE_D',
            purpose=GAME_FILES.get(name,'Pinned integrated patch, observer or minimal configuration'),
            backup='VERIFIED_ABSENT_IN_CLEAN_BACKUP_FUTURE_TARGETS',
            rollback='REMOVE_ONLY_IF_INSTALLED_HASH_MATCHES',
            runtime_effect='LOAD_ONLY_RESOURCE_BUILD_OR_READ_ONLY_OBSERVER',original_resource_write=False))
    plan=dict(format='aic_integrated_install_v1',build=1287369,plan_id=plan_id,identity=identity,entries=entries,
              backup_path=accepted['backup_path'],formal_baseline='CLEAN_BASELINE_PARTIAL',
              limited_baseline_accepted=True,installation_authorized=False,installation_executed=False,
              runtime_validation='NOT_EXECUTED',spawn_ready=False)
    write_json_new(output/'install-plan.json',plan)
    write_json_new(output/'bridge-binding.json',dict(expected,plan_sha256=file_hash(output/'install-plan.json')))
    validate_plan(plan,output)
    # Publish metadata and hashes only, never the token, licence payload or DLLs.
    public=ROOT/'compatibility/migration/1287369/exact-install-manifest.json'
    write_json_new(public,dict(plan,local_package=str(output),plan_sha256=file_hash(output/'install-plan.json'),
                               bridge_binding_sha256=file_hash(output/'bridge-binding.json')))
    return {'package':str(output),'files_for_game':len(entries),'licences_not_for_game':len(LICENSES),
            'plan_sha256':file_hash(output/'install-plan.json'),'spawn_ready':False}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    print(json.dumps(build(ap.parse_args().output.absolute())))
