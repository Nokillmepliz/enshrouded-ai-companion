"""Short read-only audit. Large DAT hashes are inherited ONLY with identical metadata.

This does not cryptographically reverify DAT bytes. A metadata mismatch blocks
the short audit; it requires a separate resource check, not automatic acceptance.
"""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from companion.compatibility import file_hash
from companion.integrated_deployment import read_pinned
from companion.patch_update_transaction import snapshot, verify_backup
from companion.recovery import write_json_new
from companion.shadow_integrity import record, no_reparse, DAT, INDEXES
from companion.runtime_validation import reassess_post_close
from scripts.prepare_phase_d_backup import GAME,SAVES,live
from scripts.install_follow_034 import RUN,BACKUP,MANIFEST_SHA
from scripts.install_companion_discovery import history
from scripts.audit_phase_f_closed import differences


from scripts.audit_follow_stage16_closed import short_snapshot


def main():
    live()
    out=ROOT/'runtime/movement_0_3_4/session536832/post-close'
    out.mkdir(exist_ok=False)
    before=read_pinned(RUN/'inventory-after.json','3785eea111c9ee3b88b1fe2cb85210b71a62c82c7e6729e91b7a81105b062ef9')
    plan=read_pinned(ROOT/'compatibility/experiments/movement_0_3_4/exact-update-manifest.json',MANIFEST_SHA)
    receipt=json.loads((RUN/'receipt.json').read_text())
    assert (RUN/'receipt.json').read_bytes()==(ROOT/'compatibility/experiments/movement_0_3_4/installation/receipt.json').read_bytes()
    after=dict(game=short_snapshot(GAME,before['game']),saves=snapshot(SAVES))
    write_json_new(out/'inventory.json',after)
    prefix='emf/mods/aic_companion_movement/'
    lock=prefix+'follow-movement-0-3-4.lock';journal=prefix+'schedule-movement-0-3-4.jsonl'
    assert (GAME/lock).read_bytes()==('SPENT!:'+plan['token']).encode()
    schedule=[json.loads(x) for x in (GAME/journal).read_bytes().splitlines()]
    prior=json.loads((out.parent/'runtime-result.json').read_text())
    assert schedule==prior['schedule_journal'] and schedule[-1]['state']=='RELEASED'
    for r in plan['effective_files']:
        if r['path'] not in (lock,journal):
            assert after['game'][r['path']]==before['game'][r['path']],r['path']
            assert after['game'][r['path']]['sha256']==r['sha256']
    counts={}
    for label,choose in {
        'originals':lambda n:n in INDEXES|{'enshrouded.exe'} or DAT.fullmatch(n),
        'shadow':lambda n:n.startswith('emf/content/client/')}.items():
        b={n:r for n,r in before['game'].items() if choose(n)}
        a={n:r for n,r in after['game'].items() if choose(n)}
        assert a==b,label+'_CHANGED';counts[label]=len(a)
    attribution=reassess_post_close(
        {n:r for n,r in before['game'].items() if n not in (lock,journal)},
        {n:r for n,r in after['game'].items() if n not in (lock,journal)},
        archive='backup/enshrouded_2026-11-22T22-59-54.log',
        session_start_ns=int(datetime.fromisoformat('2026-11-22T22:59:54+03:00').timestamp()*1e9),
        session_end_ns=int(datetime.now(timezone.utc).timestamp()*1e9))
    bm=read_pinned(BACKUP/'manifest.json',receipt['backup_manifest_sha256']);verify_backup(BACKUP,bm)
    assert history()==plan['spawn_history']
    for row in plan['preserved_intents']:assert file_hash(ROOT/row['path'])==row['sha256']
    delta=differences(before['saves'],after['saves'])
    assert not delta['added'] and not delta['removed']
    assert all(r['size']>0 and r['links']==1 for r in after['saves'].values())
    for rel,name in [('default/character0.ksd','Body Test'),('default/world0.ksd','AI Body Test')]:
        assert (SAVES/rel).read_bytes().count(name.encode())==1
    core=(GAME/'emf/emf_core.log').read_text(encoding='utf-8')
    commands=Counter(line.split('[cmd] > ',1)[1].split()[0] for line in core.splitlines() if '[cmd] > ' in line)
    assert commands.get('aic_companion_movement.f_start')==1
    assert not (set(commands)-{'aic_companion_movement.'+n for n in ('discover','f_start','f_step','f_stop','f_status')})
    assert core.count('AIC_FOLLOW WAKE_TYPE1_INTENT ')==0 and 'WAKE_HANDOFF_CONFIRMED' not in core
    assert core.count('AIC_FOLLOW MOVE_INTENT ')==15
    assert core.count('AIC_FOLLOW ACCEPTED ')==9
    assert commands.get('aic_companion_movement.f_stop')==1
    assert 'SCHEDULE_RESTORED' in core and 'CLEANUP_COMPLETE' in core
    assert 'SCHEDULE_NATIVE_OR_EXTERNAL_VALUE' not in core and 'REQUEST_ERROR' not in core
    assert "Shutdown 'Debug'" in (GAME/'enshrouded.log').read_text(encoding='utf-8')
    for rel in ('enshrouded.log','emf/emf_core.log','emf/emf_loader.log','emf/file_opens.log'):
        (out/Path(rel).name).write_bytes((GAME/rel).read_bytes())
        assert file_hash(out/Path(rel).name)==after['game'][rel]['sha256']
    live()
    result=dict(status='SHORT_POST_CLOSE_PASS_SCHEDULE_RESTORED',pid=536832,
        resource_check='DAT_METADATA_ONLY_WITH_INHERITED_HASHES; other files freshly SHA256 hashed',
        counts=counts,installed_unchanged=40,runtime_changes=2,backup_verified=len(bm['files']),
        preserved_intents=len(plan['preserved_intents']),spawn_history=len(plan['spawn_history']),
        local_count=len(after['saves']),local_changes=delta,local_semantics='NOT_VERIFIED',
        schedule_released=True,restored_hours=schedule[0],commands=dict(commands),attribution=attribution,
        follow_result='MOVEMENT_CONFIRMED_HOME_RADIUS_BLOCKS_FREE_FOLLOW',orders=15,accepted=9,arrived=4,post_close_baseline_sha256=file_hash(out/'inventory.json'),
        spawn_ready=False)
    write_json_new(out/'result.json',result)
    write_json_new(ROOT/'compatibility/experiments/movement_0_3_4/post-close-536832.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
