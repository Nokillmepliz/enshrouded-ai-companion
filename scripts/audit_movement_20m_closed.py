"""Read-only post-close audit of the single PID456828 movement experiment."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from companion.compatibility import file_hash
from companion.integrated_deployment import read_pinned
from companion.patch_update_transaction import snapshot, verify_backup
from companion.recovery import write_json_new
from companion.runtime_validation import reassess_post_close
from companion.shadow_integrity import DAT, INDEXES
from scripts.prepare_phase_d_backup import GAME, SAVES, live
from scripts.audit_phase_f_closed import differences
from scripts.install_companion_discovery import history
from scripts.install_companion_movement_20m import RUN, BACKUP


def main():
    live()
    out = ROOT/'runtime/stage10_12/session456828/post-close'
    out.mkdir(exist_ok=False)
    before = read_pinned(RUN/'inventory-after.json', '25eb067ef2f33f2a017f42f26341bc4a5e07bf99bb098a81a96bbfcd26c08fd8')
    print('Closed/build PASS; hashing game and LOCAL...', flush=True)
    after = dict(game=snapshot(GAME), saves=snapshot(SAVES))
    write_json_new(out/'inventory.json', after)
    counts = {}
    selectors = {
        'originals': lambda n: n in INDEXES|{'enshrouded.exe','enshrouded.kfc.bak'} or DAT.fullmatch(n),
        'shadow': lambda n: n.startswith('emf/content/client/'),
        'installed': lambda n: n.startswith(('emf/mods/', 'emf/config/', 'mods/')) or n in {
            'dinput8.dll','emf/emf_core.dll','emf/emf_content.dll','emf/emf_core.ini','emf/known_tools.txt'},
    }
    for label, choose in selectors.items():
        b = {n:r for n,r in before['game'].items() if choose(n)}
        a = {n:r for n,r in after['game'].items() if choose(n)}
        if b != a: raise ValueError(label.upper()+'_CHANGED')
        counts[label] = len(a)
    added = set(after['game'])-set(before['game'])
    if len(added) != 1: raise ValueError('UNEXPECTED_GAME_ADDITIONS')
    attribution = reassess_post_close(before['game'], after['game'], archive=next(iter(added)),
        session_start_ns=int(datetime.fromisoformat('2026-11-22T18:40:38+03:00').timestamp()*1e9),
        session_end_ns=int(datetime.now(timezone.utc).timestamp()*1e9))
    expected = json.loads((RUN/'history.json').read_text(encoding='utf-8'))
    if history() != expected: raise ValueError('SPAWN_HISTORY_CHANGED')
    old_intent = ROOT/'runtime/stage10_12/first-movement/movement-intent.json'
    if file_hash(old_intent) != '3a95622cca0de46bb0edf29b46b18810cb63e490737bd7d1f696918e49309d33':
        raise ValueError('OLD_MOVEMENT_INTENT_CHANGED')
    bm = read_pinned(BACKUP/'manifest.json', 'ce2158275bedad8c6213714aa796b3905c86104b842ffb65fbf1bcc9d9b55499')
    verify_backup(BACKUP, bm)
    delta = differences(before['saves'], after['saves'])
    if delta['added'] or delta['removed']: raise ValueError('LOCAL_SET_CHANGED')
    if any(r['size']<=0 or r['links']!=1 for r in after['saves'].values()): raise ValueError('LOCAL_EMPTY_OR_LINKED')
    for rel, name in [('default/character0.ksd','Body Test'),('default/world0.ksd','AI Body Test')]:
        if (SAVES/rel).read_bytes().count(name.encode())!=1: raise ValueError('LOCAL_NAME_CHANGED')
    core = (GAME/'emf/emf_core.log').read_text(encoding='utf-8')
    commands = [line.split('[cmd] > ',1)[1].split() for line in core.splitlines() if '[cmd] > ' in line]
    allowed = {'aic_companion_movement.'+x for x in ('discover','status','move_to')}
    if any(c[0] not in allowed for c in commands) or 'AIC_EXPERIMENT SPAWN_ATTEMPT' in core:
        raise ValueError('UNEXPECTED_GAME_COMMAND')
    moves = [c for c in commands if c[0].endswith('.move_to')]
    if len(moves)!=1: raise ValueError('SINGLE_MOVE_REQUIRED')
    attempt = ROOT/'runtime/stage10_12/movement-20m-attempt'
    intent = json.loads((attempt/'movement-intent.json').read_text(encoding='utf-8'))
    result = json.loads((attempt/'result.json').read_text(encoding='utf-8'))
    req = moves[0]
    if req[2]!=intent['session'] or int(req[3])!=intent['entity'] or [float(v) for v in req[4:7]]!=intent['target'] or req[7]!=intent['approval']:
        raise ValueError('INTENT_LOG_MISMATCH')
    if result['result']!='STUCK' or result['history'][-1].get('engine_result')!='stuck': raise ValueError('UNEXPECTED_RESULT')
    replies = [json.loads(line.split('[cmd] AIC_MOVEMENT ',1)[1]) for line in core.splitlines() if '[cmd] AIC_MOVEMENT ' in line]
    if not any(r.get('nonce')==req[1] and r.get('ok') is True for r in replies): raise ValueError('MOVE_REPLY_MISSING')
    logs = {}
    for rel in ('enshrouded.log','emf/emf_core.log','emf/emf_loader.log','emf/file_opens.log'):
        dest = out/Path(rel).name
        dest.write_bytes((GAME/rel).read_bytes())
        if file_hash(dest)!=after['game'][rel]['sha256']: raise ValueError('LOG_CHANGED')
        logs[rel] = file_hash(dest)
    live()
    report = dict(status='POST_CLOSE_INTEGRITY_PASS_MOVEMENT_OBSERVED_ORDER_STUCK', pid=456828,
        created_utc=datetime.now(timezone.utc).isoformat(), counts=counts, backup_verified=len(bm['files']),
        history_unchanged=len(expected), latch='SPENT', local_count=len(after['saves']), local_changes=delta,
        local_semantic_integrity='NOT_ESTABLISHED; game autosaves, no restore',
        game_changes=differences(before['game'],after['game']), attribution=attribution,
        console_command_counts={name:sum(c[0]==name for c in commands) for name in sorted(allowed)},
        world_save_events=core.count('world saved (slot 0x0001)'),
        movement=dict(result=result['result'], samples=len(result['history']), initial_distance=result['initial']['distance'],
            minimum_distance=min(r['distance'] for r in result['history']), final_distance=result['history'][-1]['distance'],
            event_sent='UNVERIFIED', user_observed_approach=True, user_suspected_player_collision=True,
            collision_cause='HYPOTHESIS_NOT_PROVEN', identity='PROFILE_ONLY'),
        intent_sha256=file_hash(attempt/'movement-intent.json'), result_sha256=file_hash(attempt/'result.json'),
        log_hashes=logs, post_close_baseline_sha256=file_hash(out/'inventory.json'),
        spawn_ready=False, spawn_executed=False, rollback_executed=False)
    write_json_new(out/'result.json', report)
    write_json_new(ROOT/'compatibility/experiments/stage10_12/movement-20m/post-close-456828.json',report)
    print(json.dumps(report,indent=2))


if __name__ == '__main__': main()
