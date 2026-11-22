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
    baseline_path=ROOT/'runtime/movement_0_3_4/session536832/post-close/inventory.json'
    sha='02850eb4f979f14874b0bfa5dfb64f4b59ca4426906b962e0a3b3b3bec2f0029'
    baseline=read_pinned(baseline_path,sha)
    assert json.loads((ROOT/'runtime/movement_0_3_4/session536832/post-close/result.json').read_text())['schedule_released'] is True
    package=ROOT/'dist/movement_0_3_5';no_links(package)
    package.mkdir(parents=True,exist_ok=True)
    prefix='emf/mods/aic_companion_movement/'
    token='a1c00350000000000000000000000001'
    names=('main.lua','mod.json','README.md','follow_config.lua','follow.lua','controller.lua','follow-movement-0-3-5.lock','schedule-movement-0-3-5.jsonl')
    entries=[]
    for name in names:
        data=('UNUSED:'+token).encode() if name.endswith('.lock') else b'' if name.endswith('.jsonl') else (ROOT/'mods/aic_companion_movement'/name).read_bytes().replace(b'\r\n',b'\n')
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
    for p in sorted([*(ROOT/'runtime/stage10_13').rglob('*'), *(ROOT/'runtime/stage10_14').rglob('*'), *(ROOT/'runtime/stage10_15').rglob('*'), *(ROOT/'runtime/stage10_16').rglob('*'), *(ROOT/'runtime/movement_0_3_3').rglob('*'), *(ROOT/'runtime/movement_0_3_4').rglob('*')]):
        if p.is_file():
            no_links(p);preserved.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=file_hash(p)))
    old_history=json.loads((ROOT/'runtime/stage10_12/movement-20m-installation/history.json').read_text(encoding='utf-8'))
    manifest=dict(schema=1,stage='10.16-fix',version='0.3.5',status='PREPARED_RESPONSIVENESS_ONLY_HOME_LIMIT_UNRESOLVED',token=token,
        baseline_sha256=sha,roaming='hold',entries=entries,
        exe_sha256='5d9ef2f140b8ed49e30dbee655841b89d08baec20f799a1817e171a18a850c77',
        schedule=dict(component='NpcCommon',sleepTime=25,wakeUpTime=-1,lease_journal='schedule-movement-0-3-5.jsonl',wake_timeout_seconds=15),
        effective_files=[dict(path=n,sha256=h) for n,h in sorted(effective.items())],
        preserved_intents=preserved,spawn_history=old_history,
        backup_plan=dict(local_files=23,replaced_files=6,total=29,fresh_preflight_required=True),
        session=dict(activation_horizontal=20,deactivation_horizontal=50,requires_separate_authorization=True,journal='runtime/movement_0_3_5/test-session.jsonl',lock_name='follow-movement-0-3-5.lock',seconds=210,max_orders=24,max_recoveries=2,heartbeat_seconds=4),spawn_ready=False)
    public=ROOT/'compatibility/experiments/movement_0_3_5';public.mkdir(parents=True,exist_ok=True)
    data=(json.dumps(manifest,indent=2)+'\n').encode()
    for p in (package/'exact-update-manifest.json',public/'exact-update-manifest.json'):
        no_links(p);p.write_bytes(data)
    print(json.dumps(dict(entries=len(entries),replace=6,add=2,effective=len(effective),
                         manifest_sha256=file_hash(public/'exact-update-manifest.json')),indent=2))


if __name__=='__main__':main()
