"""Read-only audit of Stage10.13 PID471028: rejected command registration."""
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
from scripts.install_companion_follow import RUN, BACKUP, MANIFEST_SHA


def main():
    live()
    out=ROOT/'runtime/stage10_13/session471028/post-close';out.mkdir(exist_ok=False)
    before=read_pinned(RUN/'inventory-after.json','2a55ebc2f3f2851955f7eb85cbef3016c9ed9884d1ecdd091a23cd02e470d463')
    plan=read_pinned(ROOT/'compatibility/experiments/stage10_13/exact-update-manifest.json',MANIFEST_SHA)
    print('Closed/build PASS; hashing game and LOCAL...',flush=True)
    after=dict(game=snapshot(GAME),saves=snapshot(SAVES))
    write_json_new(out/'inventory.json',after)
    selectors={
        'originals':lambda n:n in INDEXES|{'enshrouded.exe','enshrouded.kfc.bak'} or DAT.fullmatch(n),
        'shadow':lambda n:n.startswith('emf/content/client/'),
        'installed':lambda n:n in {r['path'] for r in plan['effective_files']}}
    counts={}
    for label,choose in selectors.items():
        b={n:r for n,r in before['game'].items() if choose(n)}
        a={n:r for n,r in after['game'].items() if choose(n)}
        if b!=a:raise ValueError(label.upper()+'_CHANGED')
        counts[label]=len(a)
    added=set(after['game'])-set(before['game'])
    if len(added)!=1:raise ValueError('UNEXPECTED_ADDITIONS')
    attribution=reassess_post_close(before['game'],after['game'],archive=next(iter(added)),
        session_start_ns=int(datetime.fromisoformat('2026-11-22T19:25:12+03:00').timestamp()*1e9),
        session_end_ns=int(datetime.now(timezone.utc).timestamp()*1e9))
    if history()!=plan['spawn_history']:raise ValueError('SPAWN_HISTORY_CHANGED')
    for row in plan['preserved_intents']:
        if file_hash(ROOT/row['path'])!=row['sha256']:raise ValueError('PREVIOUS_INTENT_CHANGED')
    journal=ROOT/'runtime/stage10_13/test-session.jsonl'
    if file_hash(journal)!='9c394226b46a4698058c549a2310ab17b7a892d5c41e5256488e50a01fcc76d4':raise ValueError('FOLLOW_JOURNAL_CHANGED')
    bm=read_pinned(BACKUP/'manifest.json','4c287e1a4c82b969a542fa9fb90ec49c429a2319d62c635a9d897f6b37e48011')
    verify_backup(BACKUP,bm)
    delta=differences(before['saves'],after['saves'])
    if delta['added'] or delta['removed']:raise ValueError('LOCAL_SET_CHANGED')
    if any(r['size']<=0 or r['links']!=1 for r in after['saves'].values()):raise ValueError('LOCAL_EMPTY_OR_LINKED')
    for rel,name in [('default/character0.ksd','Body Test'),('default/world0.ksd','AI Body Test')]:
        if (SAVES/rel).read_bytes().count(name.encode())!=1:raise ValueError('LOCAL_NAME_CHANGED')
    core=(GAME/'emf/emf_core.log').read_text(encoding='utf-8')
    commands=[line.split('[cmd] > ',1)[1].split()[0] for line in core.splitlines() if '[cmd] > ' in line]
    if commands!=['aic_companion_movement.discover','aic_companion_movement.follow_start']:raise ValueError('UNEXPECTED_COMMANDS')
    names=('follow_start','follow_step','follow_stop','follow_status')
    for name in names:
        qualified='aic_companion_movement.'+name
        if qualified+' ('+str(len(qualified))+' characters) is not added' not in core:raise ValueError('REGISTRATION_EVIDENCE_MISSING')
    if "unknown command 'aic_companion_movement.follow_start'" not in core:raise ValueError('REFUSAL_EVIDENCE_MISSING')
    if any(s in core for s in ('AIC_FOLLOW START ','AIC_FOLLOW MOVE_INTENT','AIC_EXPERIMENT SPAWN_ATTEMPT')):
        raise ValueError('UNEXPECTED_EXECUTION')
    lock=GAME/'emf/mods/aic_companion_movement/follow-session.lock'
    if lock.read_text(encoding='utf-8')!='UNUSED:'+plan['token']:raise ValueError('FOLLOW_LATCH_CHANGED')
    logs={}
    for rel in ('enshrouded.log','emf/emf_core.log','emf/emf_loader.log','emf/file_opens.log'):
        p=out/Path(rel).name;p.write_bytes((GAME/rel).read_bytes())
        if file_hash(p)!=after['game'][rel]['sha256']:raise ValueError('LOG_CHANGED')
        logs[rel]=file_hash(p)
    live()
    result=dict(status='POST_CLOSE_INTEGRITY_PASS_FOLLOW_NOT_STARTED',runtime_verdict='BLOCKED_COMMAND_NAME_LIMIT',
        pid=471028,created_utc=datetime.now(timezone.utc).isoformat(),counts=counts,backup_verified=len(bm['files']),
        history_unchanged=len(plan['spawn_history']),old_latch='SPENT',follow_latch='UNUSED',
        local_count=len(after['saves']),local_changes=delta,local_semantic_integrity='NOT_ESTABLISHED; game autosaves, no restore',
        world_save_events=core.count('world saved (slot 0x0001)'),game_changes=differences(before['game'],after['game']),
        attribution=attribution,console_commands=commands,command_lengths={n:len('aic_companion_movement.'+n) for n in names},
        follow_started=False,movement_commands_executed=0,retry_performed=False,rollback_executed=False,
        journal_preserved_sha256=file_hash(journal),log_hashes=logs,
        post_close_baseline_sha256=file_hash(out/'inventory.json'),spawn_ready=False)
    write_json_new(out/'result.json',result)
    write_json_new(ROOT/'compatibility/experiments/stage10_13/post-close-471028.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
