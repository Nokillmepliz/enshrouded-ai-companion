"""Read-only audit of PID216444; no transport, mutation or journal reset."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.compatibility import file_hash
from companion.experimental_install_check import verify
from companion.integrated_deployment import read_pinned
from companion.patch_update_transaction import snapshot
from companion.runtime_validation import reassess_post_close
from companion.shadow_integrity import DAT, INDEXES
from companion.recovery import write_json_new
from scripts.prepare_phase_d_backup import GAME,SAVES,live
from scripts.audit_phase_f_closed import differences

def main():
    live()
    out=ROOT/'runtime/stage10_11/live/20261118-session216444/post-close'
    out.mkdir(exist_ok=False)
    try:
        before=read_pinned(ROOT/'runtime/stage10_11/install/20261118T145106436795Z/inventory-after.json',
            '5f200502df076c1d2c81d126b4f6db5d10e9010f8f32cd682eb09b8117c1175a')
        binding=verify(ROOT/'dist/stage10_11_first_spawn_0_1_0',
            '6ecc792b6c320dc19f0fa201259c573efd142c4c37a579eab07376dc40b9e1e3',
            ROOT/'compatibility/experiments/stage10_11/installation/receipt.json',
            '3b9d80c0ade318c378584e38809eda54d6c4bc689ef16f1a5af28e5a993fd950',ROOT)
        print('Closed / installed23 / backup23 PASS; hashing full inventory',flush=True)
        after=dict(game=snapshot(GAME),saves=snapshot(SAVES));live()
        write_json_new(out/'inventory-after.json',after)
        originals=lambda d:{n:r for n,r in d.items() if n in INDEXES|{'enshrouded.exe','enshrouded.kfc.bak'} or DAT.fullmatch(n)}
        shadow=lambda d:{n:r for n,r in d.items() if n.startswith('emf/content/client/')}
        if originals(before['game'])!=originals(after['game']):raise ValueError('ORIGINAL_CHANGED')
        if shadow(before['game'])!=shadow(after['game']):raise ValueError('SHADOW_CHANGED')
        added=set(after['game'])-set(before['game'])
        if len(added)!=1:raise ValueError('UNEXPECTED_ADDED_FILES')
        attribution=reassess_post_close(before['game'],after['game'],archive=next(iter(added)),
            session_start_ns=int(datetime.fromisoformat('2026-11-18T14:55:06+00:00').timestamp()*1e9),
            session_end_ns=int(datetime.now(timezone.utc).timestamp()*1e9))
        delta=differences(before['saves'],after['saves'])
        if delta['added'] or delta['removed']:raise ValueError('LOCAL_FILE_SET_CHANGED')
        if any(r['links']!=1 or r['size']<=0 for r in after['saves'].values()):raise ValueError('LOCAL_EMPTY_OR_LINKED')
        for rel,name in [('default/character0.ksd','Body Test'),('default/world0.ksd','AI Body Test')]:
            if (SAVES/rel).read_bytes().count(name.encode())!=1:raise ValueError('LOCAL_NAME_CHANGED')
        latch=GAME/'emf/mods/aic_first_spawn/attempt.lock'
        if latch.read_bytes()!=('UNUSED:'+binding['key']).encode():raise ValueError('LATCH_CHANGED')
        journal=ROOT/'runtime/stage10_11/experiments'/binding['key']
        if (journal/'spawn-intent.json').exists():raise ValueError('UNEXPECTED_SPAWN_INTENT')
        captured={}
        for rel in ['enshrouded.log','emf/emf_core.log','emf/emf_loader.log','emf/file_opens.log','emf/content.log']:
            dest=out/Path(rel).name
            dest.write_bytes((GAME/rel).read_bytes())
            captured[rel]=file_hash(dest)
            if captured[rel]!=after['game'][rel]['sha256']:raise ValueError('LOG_CHANGED')
        core=(out/'emf_core.log').read_text(encoding='utf-8')
        if 'SPAWN_ATTEMPT' in core or 'ENTITY_ID_RETURNED' in core or '> aic_first_spawn.spawn ' in core:
            raise ValueError('UNEXPECTED_SPAWN_LOG')
        result=dict(status='POST_CLOSE_INTEGRITY_PASS_SPAWN_NOT_EXECUTED',
            checked_utc=datetime.now(timezone.utc).isoformat(),pid=216444,
            original_records_unchanged=len(originals(after['game'])),
            shadow_records_unchanged=len(shadow(after['game'])),installed_verified=23,backup_verified=23,
            game_count=len(after['game']),game_changes=differences(before['game'],after['game']),
            attribution=attribution,local_count=len(after['saves']),local_changes=delta,
            local_semantic_integrity='NOT_ESTABLISHED; game autosaves observed; no restore',
            captured_log_hashes=captured,inventory_sha256=file_hash(out/'inventory-after.json'),
            ready_logged_after_client_stopped='READY_VISUAL_APPROVAL_REQUIRED' in core,
            latch='UNUSED',spawn_intent_exists=False,experimental_spawn_executed=False,
            spawn_ready=False,production_spawn_ready=False,render='UNKNOWN',rollback_executed=False)
        write_json_new(out/'result.json',result)
        write_json_new(ROOT/'compatibility/experiments/stage10_11/installation/post-close-216444.json',result)
        print(json.dumps(result,indent=2))
    except Exception as exc:
        write_json_new(out/'blocked.json',dict(error=str(exc),spawn_ready=False))
        raise

if __name__=='__main__':main()
