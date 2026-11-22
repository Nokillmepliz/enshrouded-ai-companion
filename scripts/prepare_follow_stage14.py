"""Build an offline exact update package from the accepted post-close baseline."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.compatibility import file_hash
from companion.integrated_deployment import read_pinned
from companion.recovery import no_links


def main():
    baseline_path=ROOT/'runtime/stage10_13/session471612/post-close/inventory.json'
    sha='5bd9a38b88ce73de91bbd600af4ea7ee0baa5839a23487725be0ea43a48fc31e'
    baseline=read_pinned(baseline_path,sha)
    package=ROOT/'dist/stage10_14_movement_0_3_0';no_links(package)
    package.mkdir(parents=True,exist_ok=True)
    prefix='emf/mods/aic_companion_movement/'
    token='a1c10140000000000000000000000001'
    names=('main.lua','mod.json','README.md','follow.lua','follow_config.lua','follow-stage10-14.lock')
    entries=[]
    for name in names:
        data=('UNUSED:'+token).encode() if name.endswith('.lock') else (ROOT/'mods/aic_companion_movement'/name).read_bytes().replace(b'\r\n',b'\n')
        p=package/name;no_links(p);p.write_bytes(data)
        old=baseline['game'].get(prefix+name)
        entries.append(dict(path=prefix+name,source=name,sha256=file_hash(p),bytes=len(data),
                            operation='replace' if old else 'add',before_sha256=old['sha256'] if old else None))
    selected={n:r for n,r in baseline['game'].items() if n.startswith(('emf/mods/','emf/config/','mods/')) or n in {
        'dinput8.dll','emf/emf_core.dll','emf/emf_content.dll','emf/emf_core.ini','emf/known_tools.txt'}}
    effective={n:r['sha256'] for n,r in selected.items()}
    effective.update({r['path']:r['sha256'] for r in entries})
    preserved=[]
    for name in ('first-movement/movement-intent.json','movement-20m-attempt/movement-intent.json','movement-20m-attempt/result.json'):
        p=ROOT/'runtime/stage10_12'/name
        preserved.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=file_hash(p)))
    for p in sorted((ROOT/'runtime/stage10_13').rglob('*')):
        if p.is_file():
            no_links(p);preserved.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=file_hash(p)))
    old_history=json.loads((ROOT/'runtime/stage10_12/movement-20m-installation/history.json').read_text(encoding='utf-8'))
    manifest=dict(schema=1,stage='10.14',version='0.3.0',status='PREPARED_NOT_INSTALLED',token=token,
        baseline_sha256=sha,roaming='native',entries=entries,
        effective_files=[dict(path=n,sha256=h) for n,h in sorted(effective.items())],
        preserved_intents=preserved,spawn_history=old_history,
        backup_plan=dict(local_files=23,replaced_files=5,total=28,fresh_preflight_required=True),
        session=dict(activation_horizontal=20,deactivation_horizontal=50,requires_separate_authorization=True,journal='runtime/stage10_14/test-session.jsonl',lock_name='follow-stage10-14.lock',seconds=180,max_orders=24,max_recoveries=2,heartbeat_seconds=4),spawn_ready=False)
    public=ROOT/'compatibility/experiments/stage10_14';public.mkdir(parents=True,exist_ok=True)
    data=(json.dumps(manifest,indent=2)+'\n').encode()
    for p in (package/'exact-update-manifest.json',public/'exact-update-manifest.json'):
        no_links(p);p.write_bytes(data)
    print(json.dumps(dict(entries=len(entries),replace=5,add=1,effective=len(effective),
                         manifest_sha256=file_hash(public/'exact-update-manifest.json')),indent=2))


if __name__=='__main__':main()
