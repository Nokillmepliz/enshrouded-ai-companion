"""Read-only post-close audit of PID507224 and its approved schedule recovery."""
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from companion.compatibility import file_hash
from companion.integrated_deployment import read_pinned
from companion.patch_update_transaction import snapshot, verify_backup
from companion.recovery import write_json_new
from companion.runtime_validation import reassess_post_close
from companion.shadow_integrity import DAT, INDEXES
from scripts.prepare_phase_d_backup import GAME, SAVES, live
from scripts.audit_phase_f_closed import differences
from scripts.install_companion_discovery import history
from scripts.install_follow_stage15 import RUN, BACKUP, MANIFEST_SHA


def main():
    live()
    session=ROOT/'runtime/stage10_15/session507224'
    out=session/'post-close';out.mkdir(exist_ok=False)
    before=read_pinned(RUN/'inventory-after.json','db3f1e81c73c70d0c679756f527fab9dc2ae56d2e7aebab7899a400be96b0b71')
    plan=read_pinned(ROOT/'compatibility/experiments/stage10_15/exact-update-manifest.json',MANIFEST_SHA)
    receipt=json.loads((RUN/'receipt.json').read_text())
    assert (RUN/'receipt.json').read_bytes()==(ROOT/'compatibility/experiments/stage10_15/installation/receipt.json').read_bytes()
    print('Closed/build PASS; hashing original, shadow, installed files and LOCAL...',flush=True)
    after=dict(game=snapshot(GAME),saves=snapshot(SAVES))
    write_json_new(out/'inventory.json',after)
    prefix='emf/mods/aic_companion_movement/'
    main_name=prefix+'main.lua';lock=prefix+'follow-stage10-15.lock';journal_name=prefix+'schedule-stage10-15.jsonl'
    recovery=json.loads((session/'recovery-result.json').read_text())
    assert recovery['status']=='SCHEDULE_RESTORED_SAME_SESSION'
    expected=dict(before['game'][main_name],mtime_ns=recovery['mtime_ns_after'])
    assert after['game'][main_name]==expected,'UNEXPECTED_MAIN_METADATA_CHANGE'
    assert (GAME/lock).read_bytes()==('SPENT!:'+plan['token']).encode()
    assert after['game'][lock]['links']==after['game'][journal_name]['links']==1
    assert file_hash(GAME/journal_name)==recovery['hashes_after']['schedule-stage10-15.jsonl']
    schedule=[json.loads(x) for x in (GAME/journal_name).read_bytes().splitlines()]
    assert schedule==recovery['journal'] and len(schedule)==2 and schedule[-1]['state']=='RELEASED'
    counts={}
    for label,choose in {
        'originals':lambda n:n in INDEXES|{'enshrouded.exe','enshrouded.kfc.bak'} or DAT.fullmatch(n),
        'shadow':lambda n:n.startswith('emf/content/client/'),
        'installed_records_unchanged':lambda n:n in {r['path'] for r in plan['effective_files']} and n not in (main_name,lock,journal_name)
    }.items():
        b={n:r for n,r in before['game'].items() if choose(n)}
        a={n:r for n,r in after['game'].items() if choose(n)}
        assert a==b,label+'_CHANGED';counts[label]=len(a)
    for row in plan['effective_files']:
        if row['path'] not in (lock,journal_name):assert after['game'][row['path']]['sha256']==row['sha256']
    counts['installed_content_unchanged']=len(plan['effective_files'])-2
    counts['authorized_runtime_files']=2
    excluded={main_name,lock,journal_name}
    attribution=reassess_post_close(
        {n:r for n,r in before['game'].items() if n not in excluded},
        {n:r for n,r in after['game'].items() if n not in excluded},
        archive='backup/enshrouded_2026-11-22T21-13-43.log',
        session_start_ns=int(datetime.fromisoformat('2026-11-22T21:13:43+03:00').timestamp()*1e9),
        session_end_ns=int(datetime.now(timezone.utc).timestamp()*1e9))
    assert history()==plan['spawn_history'],'SPAWN_HISTORY_CHANGED'
    for row in plan['preserved_intents']:assert file_hash(ROOT/row['path'])==row['sha256'],'OLD_INTENT_CHANGED'
    bm=read_pinned(BACKUP/'manifest.json','48336b13c32f3a2e2d1f184368e85bf23207d3948ff4ea47c7d8ab80a53d51ef');verify_backup(BACKUP,bm)
    delta=differences(before['saves'],after['saves'])
    assert not delta['added'] and not delta['removed'],'LOCAL_SET_CHANGED'
    assert all(r['size']>0 and r['links']==1 for r in after['saves'].values())
    for rel,name in [('default/character0.ksd','Body Test'),('default/world0.ksd','AI Body Test')]:
        assert (SAVES/rel).read_bytes().count(name.encode())==1,'LOCAL_NAME_CHANGED'
    core=(GAME/'emf/emf_core.log').read_text(encoding='utf-8')
    commands=Counter(line.split('[cmd] > ',1)[1].split()[0] for line in core.splitlines() if '[cmd] > ' in line)
    assert commands=={'aic_companion_movement.discover':4,'aic_companion_movement.f_start':1,
                      'aic_companion_movement.f_step':11,'aic_companion_movement.f_status':2},'UNEXPECTED_COMMANDS'
    events={}
    for line in core.splitlines():
        if 'AIC_FOLLOW ' not in line:continue
        name,payload=line.split('AIC_FOLLOW ',1)[1].split(' ',1)
        events.setdefault(name,[]).append(json.loads(payload))
    assert len(events['START'])==len(events['MOVE_INTENT'])==len(events['ACCEPTED'])==1
    assert len(events['SCHEDULE_RESTORED'])==1 and not events.get('SCHEDULE_NATIVE_OR_EXTERNAL_VALUE')
    assert events['SCHEDULE_ACQUIRED'][0]['ai_state']==8
    assert events['SCHEDULE_ACQUIRED'][0]['hour']<schedule[0]['wake']
    assert events['STOPPED']==[{'reason':'REQUEST_ERROR'}]
    assert 'AIC_EXPERIMENT SPAWN_ATTEMPT' not in core
    records=[json.loads(x) for x in (ROOT/'runtime/stage10_15/test-session.jsonl').read_bytes().splitlines()]
    samples=[r['value'] for r in records if r['kind']=='SAMPLE']
    assert len(samples)==11 and len([r for r in records if r['kind']=='START_GRANT'])==1
    assert any(r['kind']=='STOPPED_UNKNOWN_NO_RETRY' for r in records)
    initial=next(s for s in samples if s['orders']==1)
    initial_target=math.dist([initial['discovery']['position'][k] for k in 'xyz'],[initial['target'][k] for k in 'xyz'])
    logs={}
    for rel in ('enshrouded.log','emf/emf_core.log','emf/emf_loader.log','emf/file_opens.log'):
        data=(GAME/rel).read_bytes();(out/Path(rel).name).write_bytes(data)
        assert file_hash(out/Path(rel).name)==after['game'][rel]['sha256'],'LOG_CHANGED'
        logs[rel]=file_hash(out/Path(rel).name)
    assert "Shutdown 'Debug'" in (GAME/'enshrouded.log').read_text(encoding='utf-8')
    live()
    result=dict(status='POST_CLOSE_INTEGRITY_PASS_SCHEDULE_RESTORED',runtime_verdict='NATIVE_WAKE_CONFIRMED_FOLLOW_ABORTED',
        pid=507224,created_utc=datetime.now(timezone.utc).isoformat(),counts=counts,backup_verified=len(bm['files']),
        history_unchanged=len(plan['spawn_history']),preserved_intents=len(plan['preserved_intents']),follow_latch='SPENT!',
        local_count=len(after['saves']),local_changes=delta,local_semantic_integrity='NOT_ESTABLISHED; game autosaves; no direct save writes or restore',
        world_save_events=core.count('world saved (slot 0x0001)'),game_changes=differences(before['game'],after['game']),
        attribution=attribution,authorized_main_mtime_change=dict(before=before['game'][main_name]['mtime_ns'],after=after['game'][main_name]['mtime_ns']),
        console_command_counts=dict(commands),runtime_summary=records[-1]['value'],
        movement_intents=1,movement_accepted=1,completed_arrivals=len([r for r in events.get('ORDER_RESULT',[]) if r['result']=='arrived']),
        initial_target_distance=initial_target,last_progress=events['PROGRESS'][-1],
        schedule_acquired=events['SCHEDULE_ACQUIRED'][0],awake_observed=events['SCHEDULE_AWAKE_OBSERVED'],
        restored_hours=schedule[0],schedule_released=True,recovery_method='separately approved same-session mtime-only Lua reload',
        automatic_cleanup_failed=True,thresholds_20_50='NOT_COVERED',sustained_follow='NOT_CONFIRMED',
        other_npcs='No other NPC targeted by controller; no independent all-NPC schedule comparison',
        journal_sha256=file_hash(ROOT/'runtime/stage10_15/test-session.jsonl'),schedule_journal_sha256=file_hash(GAME/journal_name),
        recovery_result_sha256=file_hash(session/'recovery-result.json'),log_hashes=logs,
        post_close_baseline_sha256=file_hash(out/'inventory.json'),retry_performed=False,rollback_executed=False,spawn_ready=False)
    write_json_new(out/'result.json',result)
    write_json_new(ROOT/'compatibility/experiments/stage10_15/post-close-507224.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
