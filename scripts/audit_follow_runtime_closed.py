"""Read-only audit of Stage10.13 PID471612: stopped Follow, no movement orders."""
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
from scripts.install_follow_registration_fix import RUN, BACKUP, MANIFEST_SHA
import hashlib


def main():
    live()
    out=ROOT/'runtime/stage10_13/session471612/post-close';out.mkdir(exist_ok=False)
    before=read_pinned(RUN/'inventory-after.json','a67f92b091f533c807d43d6b2b984b389dcd67ecdabbb377d1992d2ce6b3a175')
    plan=read_pinned(ROOT/'compatibility/experiments/stage10_13/registration-fix/exact-update-manifest.json',MANIFEST_SHA)
    print('Closed/build PASS; hashing game and LOCAL...',flush=True)
    after=dict(game=snapshot(GAME),saves=snapshot(SAVES))
    write_json_new(out/'inventory.json',after)
    lock_name='emf/mods/aic_companion_movement/follow-session.lock'
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
    if len(added)!=1:raise ValueError('UNEXPECTED_ADDITIONS')
    # Exact authorized latch transition checked above; exclude it from generic log-only attribution.
    attribution=reassess_post_close({k:v for k,v in before['game'].items() if k!=lock_name},
        {k:v for k,v in after['game'].items() if k!=lock_name},archive=next(iter(added)),
        session_start_ns=int(datetime.fromisoformat('2026-11-22T19:38:45+03:00').timestamp()*1e9),
        session_end_ns=int(datetime.now(timezone.utc).timestamp()*1e9))
    if history()!=plan['spawn_history']:raise ValueError('SPAWN_HISTORY_CHANGED')
    for row in plan['preserved_intents']:
        if row['path']=='runtime/stage10_13/test-session.jsonl':continue
        if file_hash(ROOT/row['path'])!=row['sha256']:raise ValueError('PREVIOUS_INTENT_CHANGED')
    journal=ROOT/'runtime/stage10_13/test-session.jsonl'
    raw=journal.read_bytes()
    prefix=b''.join(raw.splitlines(keepends=True)[:4])
    if hashlib.sha256(prefix).hexdigest()!=plan['continuation']['prior_journal_sha256']:raise ValueError('OLD_JOURNAL_PREFIX_CHANGED')
    if file_hash(journal)!='5e9b66266c46d6f7682319890c894aeacde710cd045604dd7591933429283b03':raise ValueError('RUNTIME_JOURNAL_CHANGED')
    records=[json.loads(line) for line in raw.splitlines()][4:]
    if sum(r['kind']=='AUDITED_CONTINUATION' for r in records)!=1:raise ValueError('CONTINUATION_COUNT')
    bm=read_pinned(BACKUP/'manifest.json','ea332f1eec7f88f7bb60d49055607126f8fdca040845bbeefcacfdbeec4aff00')
    verify_backup(BACKUP,bm)
    delta=differences(before['saves'],after['saves'])
    if delta['added'] or delta['removed']:raise ValueError('LOCAL_SET_CHANGED')
    if any(r['size']<=0 or r['links']!=1 for r in after['saves'].values()):raise ValueError('LOCAL_EMPTY_OR_LINKED')
    for rel,name in [('default/character0.ksd','Body Test'),('default/world0.ksd','AI Body Test')]:
        if (SAVES/rel).read_bytes().count(name.encode())!=1:raise ValueError('LOCAL_NAME_CHANGED')
    core=(GAME/'emf/emf_core.log').read_text(encoding='utf-8')
    commands=[line.split('[cmd] > ',1)[1].split()[0] for line in core.splitlines() if '[cmd] > ' in line]
    expected=['aic_companion_movement.discover','aic_companion_movement.f_start']+['aic_companion_movement.f_step']*30
    if commands!=expected:raise ValueError('UNEXPECTED_COMMANDS')
    if core.count('AIC_FOLLOW START ')!=1 or 'AIC_FOLLOW STOPPED {"reason":"GROUND_REFUSED"}' not in core:
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
    result=dict(status='POST_CLOSE_INTEGRITY_PASS_FOLLOW_STOPPED',runtime_verdict='GROUND_REFUSED_NO_MOVEMENT',
        pid=471612,created_utc=datetime.now(timezone.utc).isoformat(),counts=counts,backup_verified=len(bm['files']),
        history_unchanged=len(plan['spawn_history']),old_latch='SPENT',follow_latch='SPENT!' ,old_journal_prefix_preserved=True,
        local_count=len(after['saves']),local_changes=delta,local_semantic_integrity='NOT_ESTABLISHED; game autosaves, no restore',
        world_save_events=core.count('world saved (slot 0x0001)'),game_changes=differences(before['game'],after['game']),
        attribution=attribution,console_commands=commands,command_lengths={n:len('aic_companion_movement.'+n) for n in names},
        follow_started=True,movement_commands_executed=0,retry_performed=False,rollback_executed=False,
        journal_sha256=file_hash(journal),runtime_summary=records[-1]['value'],
        ground_refusal=dict(ground_y=893.5009765625,npc_origin_y=894.98779296875,height_delta=1.48681640625,limit=1),
        summary_warning='stopped_reason is stale; final cause established from core log',log_hashes=logs,
        post_close_baseline_sha256=file_hash(out/'inventory.json'),spawn_ready=False)
    write_json_new(out/'result.json',result)
    write_json_new(ROOT/'compatibility/experiments/stage10_13/post-close-471612.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
