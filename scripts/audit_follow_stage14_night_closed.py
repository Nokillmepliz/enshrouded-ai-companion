"""Read-only audit of Stage10.14 PID490800: stopped Follow, no movement orders."""
from datetime import datetime, timezone
import json
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
from scripts.install_follow_stage14 import RUN, BACKUP, MANIFEST_SHA
import hashlib


def main():
    live()
    out=ROOT/'runtime/stage10_14/session490800/post-close-reviewed';out.mkdir(exist_ok=False)
    before=read_pinned(RUN/'inventory-after.json','77f889dadb0261adf0f799e64df0544b99701569a246caeccb483a880280f16e')
    plan=read_pinned(ROOT/'compatibility/experiments/stage10_14/exact-update-manifest.json',MANIFEST_SHA)
    print('Closed/build PASS; hashing game and LOCAL...',flush=True)
    after=dict(game=snapshot(GAME),saves=snapshot(SAVES))
    write_json_new(out/'inventory.json',after)
    lock_name='emf/mods/aic_companion_movement/follow-stage10-14.lock'
    if (GAME/lock_name).read_bytes()!=('SPENT!:'+plan['token']).encode():raise ValueError('FOLLOW_LATCH_NOT_SPENT')
    if after['game'][lock_name]['links']!=1:raise ValueError('FOLLOW_LATCH_LINKED')
    selectors={
        'originals':lambda n:n in INDEXES|{'enshrouded.exe','enshrouded.kfc.bak'} or DAT.fullmatch(n),
        'shadow':lambda n:n.startswith('emf/content/client/'),
        'installed':lambda n:n!=lock_name and n in {r['path'] for r in plan['effective_files']}}
    counts={}
    for label,choose in selectors.items():
        b={n:r for n,r in before['game'].items() if choose(n)}
        a={n:r for n,r in after['game'].items() if choose(n)}
        if b!=a:raise ValueError(label.upper()+'_CHANGED')
        counts[label]=len(a)
    added=set(after['game'])-set(before['game'])
    archive='backup/enshrouded_2026-11-22T20-22-26.log'
    extra='backup/enshrouded_2026-11-22T20-24-02.log'
    if added!={archive,extra}:raise ValueError('UNEXPECTED_ADDITIONS')
    intermediate=(GAME/extra).read_text(encoding='utf-8')
    if (file_hash(GAME/extra)!='cddeea7aeb5f652ba074d95b59f52522d389ee68cde1c664a81ec9bd9f3420fe'
        or after['game'][extra]['links']!=1
        or not intermediate.startswith('[I 00:00:00,000] [GameFramework] Current UTC date: 2026.11.22 17:22:26')
        or "Shutdown 'Debug'" not in intermediate):raise ValueError('INTERMEDIATE_LOG_NOT_REVIEWED')
    if not (GAME/'enshrouded.log').read_text(encoding='utf-8').startswith('[I 00:00:00,000] [GameFramework] Current UTC date: 2026.11.22 17:24:02'):
        raise ValueError('CURRENT_LOG_SESSION')
    # Exact authorized latch transition checked above; exclude it from generic log-only attribution.
    attribution=reassess_post_close({k:v for k,v in before['game'].items() if k!=lock_name},
        {k:v for k,v in after['game'].items() if k not in (lock_name,extra)},archive=archive,
        session_start_ns=int(datetime.fromisoformat('2026-11-22T20:24:02+03:00').timestamp()*1e9),
        session_end_ns=int(datetime.now(timezone.utc).timestamp()*1e9))
    attribution['additional_reviewed_log']={extra:dict(sha256=file_hash(GAME/extra),basis='reviewed startup17:22:26UTC and orderly shutdown; current log starts17:24:02UTC',scope='intermediate launch observed only via log; no runtime diagnostics')}
    if history()!=plan['spawn_history']:raise ValueError('SPAWN_HISTORY_CHANGED')
    for row in plan['preserved_intents']:
        if file_hash(ROOT/row['path'])!=row['sha256']:raise ValueError('PREVIOUS_INTENT_CHANGED')
    journal=ROOT/'runtime/stage10_14/test-session.jsonl'
    if file_hash(journal)!='2eb241e7b6cbf2c2c6f0379dd049d8be6c53e2968056acf1d8ed9d24de2d1717':raise ValueError('RUNTIME_JOURNAL_CHANGED')
    records=[json.loads(line) for line in journal.read_bytes().splitlines()]
    samples=[r['value'] for r in records if r['kind']=='SAMPLE']
    if len(samples)!=66 or any(x['orders'] or x.get('probes',0) for x in samples):raise ValueError('UNEXPECTED_RUNTIME_ORDERS')
    if len({tuple(x['discovery']['position'].values()) for x in samples})!=1:raise ValueError('NPC_MOVED')
    bm=read_pinned(BACKUP/'manifest.json','9520210b034f5ee0c86aa2a7b47359002edce84fa31145d905c4fbc1aed95e5e')
    verify_backup(BACKUP,bm)
    delta=differences(before['saves'],after['saves'])
    if delta['added'] or delta['removed']:raise ValueError('LOCAL_SET_CHANGED')
    if any(r['size']<=0 or r['links']!=1 for r in after['saves'].values()):raise ValueError('LOCAL_EMPTY_OR_LINKED')
    for rel,name in [('default/character0.ksd','Body Test'),('default/world0.ksd','AI Body Test')]:
        if (SAVES/rel).read_bytes().count(name.encode())!=1:raise ValueError('LOCAL_NAME_CHANGED')
    core=(GAME/'emf/emf_core.log').read_text(encoding='utf-8')
    commands=[line.split('[cmd] > ',1)[1].split()[0] for line in core.splitlines() if '[cmd] > ' in line]
    from collections import Counter
    expected={'aic_companion_movement.discover':1,'aic_companion_movement.f_start':1,
              'aic_companion_movement.f_step':65,'aic_companion_movement.f_stop':1}
    if Counter(commands)!=expected:raise ValueError('UNEXPECTED_COMMANDS')
    if core.count('AIC_FOLLOW START ')!=1 or 'AIC_FOLLOW STOPPED {"reason":"RUNNER_STOP"}' not in core:
        raise ValueError('SESSION_EVIDENCE_MISSING')
    if any(s in core for s in ('AIC_FOLLOW MOVE_INTENT','AIC_FOLLOW ACCEPTED','AIC_EXPERIMENT SPAWN_ATTEMPT')):
        raise ValueError('UNEXPECTED_EXECUTION')
    names=('f_start','f_step','f_stop','f_status')
    logs={}
    for rel in ('enshrouded.log','emf/emf_core.log','emf/emf_loader.log','emf/file_opens.log'):
        p=out/Path(rel).name;p.write_bytes((GAME/rel).read_bytes())
        if file_hash(p)!=after['game'][rel]['sha256']:raise ValueError('LOG_CHANGED')
        logs[rel]=file_hash(p)
    live()
    result=dict(status='POST_CLOSE_INTEGRITY_PASS_FOLLOW_STOPPED',runtime_verdict='NIGHT_BUSY_NO_MOVEMENT',
        pid=490800,created_utc=datetime.now(timezone.utc).isoformat(),counts=counts,backup_verified=len(bm['files']),
        history_unchanged=len(plan['spawn_history']),old_latch='SPENT',follow_latch='SPENT!' ,old_journals_unchanged=True,
        local_count=len(after['saves']),local_changes=delta,local_semantic_integrity='NOT_ESTABLISHED; game autosaves, no restore',
        world_save_events=core.count('world saved (slot 0x0001)'),game_changes=differences(before['game'],after['game']),
        attribution=attribution,console_commands=commands,command_lengths={n:len('aic_companion_movement.'+n) for n in names},
        follow_started=True,movement_commands_executed=0,retry_performed=False,rollback_executed=False,
        journal_sha256=file_hash(journal),runtime_summary=records[-1]['value'],
        npc_displacement=0,probes=0,threshold_tests='NOT_TESTED',vertical_tests='NOT_TESTED',
        cause='NPC_ASLEEP_OR_BUSY ai_state8 decision5; user confirmed night',log_hashes=logs,
        post_close_baseline_sha256=file_hash(out/'inventory.json'),spawn_ready=False)
    write_json_new(out/'result.json',result)
    write_json_new(ROOT/'compatibility/experiments/stage10_14/post-close-490800.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
