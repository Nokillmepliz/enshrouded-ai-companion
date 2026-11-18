"""Read-only post-close audit for the single authorized spawn in PID257936."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from companion.compatibility import file_hash
from companion.integrated_deployment import read_pinned
from companion.patch_update_transaction import snapshot,verify_backup
from companion.recovery import no_links,write_json_new
from companion.smart_deployment import check_manifest,CHANGED,PREFIX
from companion.runtime_validation import reassess_post_close
from companion.shadow_integrity import DAT,INDEXES
from scripts.prepare_phase_d_backup import GAME,SAVES,live
from scripts.audit_phase_f_closed import differences


def main():
    live()
    session=ROOT/'runtime/stage10_11_3/live/20261118T165734028417Z/session257936'
    out=session/'post-close';out.mkdir(exist_ok=False)
    try:
        plan=read_pinned(ROOT/'runtime/stage10_11_3/smart-position-plan.json','d137680beff2ccc68fedefd87617202075a1d367407ddd34096ae43537d6647c')
        receipt=read_pinned(ROOT/'compatibility/experiments/stage10_11_3/installation/receipt.json','d973898fbd447f274fbf2365a9146d1b193a01413677d253fbcfbfc0da338485')
        manifest=read_pinned(Path(plan['manifest_path']),plan['manifest_sha256'])
        original=read_pinned(Path(plan['baseline_path']),plan['baseline_sha256']);check_manifest(manifest,original)
        before=read_pinned(Path(receipt['post_install_baseline_path']),receipt['post_install_baseline_sha256'])
        binding=read_pinned(Path(plan['binding_path']),plan['binding_sha256'])
        backup=Path(receipt['backup_path']);bm=read_pinned(backup/'manifest.json',receipt['backup_manifest_sha256'])
        expected={'saves/'+n:(r['sha256'],r['size']) for n,r in before['saves'].items()}
        expected.update({'game/'+n:(original['game'][n]['sha256'],original['game'][n]['size']) for n in CHANGED})
        if {r['relative']:(r['sha256'],r['bytes']) for r in bm['files']}!=expected:raise ValueError('BACKUP_BASELINE_MISMATCH')
        verify_backup(backup,bm)
        journal=ROOT/'runtime/stage10_11/experiments'/binding['key']
        history={}
        for p in journal.rglob('*'):
            no_links(p)
            if p.is_file():history[p.relative_to(journal).as_posix()]=file_hash(p)
        previous={n:h for n,h in history.items() if n!='spawn-intent.json' and n.split('/')[0] not in ('smart-control','smart-searches')}
        if previous!=plan['history']:raise ValueError('PREVIOUS_HISTORY_CHANGED')
        searches=list((journal/'smart-searches').iterdir())
        if len(searches)!=1 or searches[0].name!='000001':raise ValueError('UNEXPECTED_SEARCHES')
        search=searches[0]
        read=lambda p:json.loads(p.read_text(encoding='utf-8'))
        probe=read(search/'probe.json');confirm=read(search/'local-confirmation.json')
        intent=read(journal/'spawn-intent.json');result=read(search/'interactive-result.json')['reply']
        requests=[read(p) for p in journal.rglob('*-request.json')]
        if any(r['command'] not in ('status','probe','spawn') for r in requests):raise ValueError('UNEXPECTED_COMMAND')
        spawns=[r for r in requests if r['command']=='spawn']
        if len(spawns)!=1:raise ValueError('SPAWN_COUNT')
        request=spawns[0]
        if (confirm.get('key')!='Y' or confirm.get('after_ready') is not True
                or confirm['probe']!=probe['nonce'] or confirm['session']!=probe['session']
                or not 0<=confirm['time']-probe['prepared_at']<=18
                or not probe['prepared_at']<=confirm['time']<=intent['time']<=request['time']<=probe['prepared_at']+18
                or intent['probe']!=probe['nonce'] or intent['session']!=probe['session']
                or intent['authorization']!='I_APPROVE_ONE_DISPOSABLE_SPAWN'
                or intent['manual_area_clear'] is not True or intent['disposable_risk_accepted'] is not True
                or request['args']!=[probe['session'],str(probe['context']['player']),probe['nonce'],intent['authorization']]
                or result['nonce']!=request['nonce'] or result['probe']!=probe['nonce']
                or result['session']!=probe['session'] or result['entity']!=6959 or result['attempted'] is not True):
            raise ValueError('SPAWN_AUTHORIZATION_PROVENANCE')
        print('Closed/backup27/prior history75/single authorized request PASS; hashing inventory...',flush=True)
        after=dict(game=snapshot(GAME),saves=snapshot(SAVES));live()
        write_json_new(out/'inventory-after.json',after)
        originals=lambda d:{n:r for n,r in d.items() if n in INDEXES|{'enshrouded.exe','enshrouded.kfc.bak'} or DAT.fullmatch(n)}
        shadow=lambda d:{n:r for n,r in d.items() if n.startswith('emf/content/client/')}
        if originals(before['game'])!=originals(after['game']):raise ValueError('ORIGINAL_CHANGED')
        if shadow(before['game'])!=shadow(after['game']):raise ValueError('SHADOW_CHANGED')
        latch=PREFIX+'attempt.lock';old=before['game'][latch];new=after['game'][latch]
        start_ns=int(datetime.fromisoformat('2026-11-18T16:58:22+00:00').timestamp()*1e9)
        end_ns=int(datetime.now(timezone.utc).timestamp()*1e9)
        if (old['sha256']!=hashlib.sha256(('UNUSED:'+binding['key']).encode()).hexdigest()
                or new['sha256']!=hashlib.sha256(('SPENT!:'+binding['key']).encode()).hexdigest()
                or new['size']!=39 or new['links']!=1 or old['size']!=39
                or any(new[k]!=old[k] for k in ('volume','file_id','links'))
                or not start_ns<=new['mtime_ns']<=end_ns):raise ValueError('UNATTRIBUTED_LATCH_CHANGE')
        for row in manifest['effective_files']:
            if row['path']==latch:continue
            if after['game'][row['path']]!=before['game'][row['path']]:raise ValueError('INSTALLED_FILE_CHANGED:'+row['path'])
            if (after['game'][row['path']]['sha256'],after['game'][row['path']]['size'])!=(row['sha256'],row['bytes']):raise ValueError('INSTALL_HASH')
        added=set(after['game'])-set(before['game'])
        if len(added)!=1:raise ValueError('ADDED_FILE_SET')
        # Account for the separately proved latch transition in memory only;
        # the immutable raw inventory above retains its actual SPENT bytes/hash.
        without_latch_change=dict(after['game']);without_latch_change[latch]=old
        attribution=reassess_post_close(before['game'],without_latch_change,archive=next(iter(added)),session_start_ns=start_ns,session_end_ns=end_ns)
        attribution['separately_attributed_latch']='UNUSED_TO_SPENT_SAME_FILE_SINGLE_AUTHORIZED_SPAWN'
        delta=differences(before['saves'],after['saves'])
        if delta['added'] or delta['removed']:raise ValueError('LOCAL_FILE_SET')
        if any(r['links']!=1 or r['size']<=0 for r in after['saves'].values()):raise ValueError('LOCAL_EMPTY_OR_LINKED')
        for rel,name in [('default/character0.ksd','Body Test'),('default/world0.ksd','AI Body Test')]:
            if (SAVES/rel).read_bytes().count(name.encode())!=1:raise ValueError('LOCAL_NAME')
        captured={}
        for rel in ['enshrouded.log','emf/emf_core.log','emf/emf_loader.log','emf/file_opens.log','emf/content.log']:
            dest=out/Path(rel).name;dest.write_bytes((GAME/rel).read_bytes());captured[rel]=file_hash(dest)
            if captured[rel]!=after['game'][rel]['sha256']:raise ValueError('LOG_CHANGED')
        core=(out/'emf_core.log').read_text(encoding='utf-8');events=[];timeline=[]
        for line in core.splitlines():
            if 'AIC_POSITION ' in line:
                event,raw=line.split('AIC_POSITION ',1)[1].split(' ',1);data=json.loads(raw)
                if data.pop('probe')!=probe['nonce']:raise ValueError('LOG_PROBE_CHANGED')
                events.append(dict(time=line[1:13],event=event,data=data))
            for marker in ('GROUND_REQUESTED','READY_VISUAL_APPROVAL_REQUIRED','SPAWN_ATTEMPT','ENTITY_ID_RETURNED'):
                if 'AIC_EXPERIMENT '+marker+' ' in line:timeline.append(dict(time=line[1:13],event=marker))
        for marker in ('GROUND_REQUESTED','READY_VISUAL_APPROVAL_REQUIRED','SPAWN_ATTEMPT','ENTITY_ID_RETURNED'):
            if sum(e['event']==marker for e in timeline)!=1:raise ValueError('LOG_EVENT_COUNT:'+marker)
        if 'AIC_EXPERIMENT SPAWN_ATTEMPT '+probe['nonce'] not in core or 'AIC_EXPERIMENT ENTITY_ID_RETURNED 6959' not in core:raise ValueError('SPAWN_LOG_IDENTITY')
        for event in ('GROUND_ACCEPTED','GROUND'):
            rows=[e for e in events if e['event']==event]
            if len(rows)!=8 or {e['data']['candidate'] for e in rows}!=set(range(1,9)):raise ValueError('GROUND_LOG_COUNT')
        write_json_new(out/'history-hashes.json',history)
        result=dict(status='POST_CLOSE_INTEGRITY_PASS_SINGLE_SPAWN_VISUALLY_CONFIRMED',pid=257936,
            original_records_unchanged=len(originals(after['game'])),shadow_records_unchanged=len(shadow(after['game'])),
            installed_immutable_verified=22,latch='SPENT',latch_transition_attributed=True,backup_verified=27,
            game_count=len(after['game']),game_changes=differences(before['game'],after['game']),attribution=attribution,
            local_count=len(after['saves']),local_changes=delta,local_semantic_integrity='NOT_ESTABLISHED',
            npc_persistence_after_reload='NOT_TESTED; do not reset latch or reload without review',
            world_save_events=core.count('world saved (slot 0x0001)'),
            inventory_sha256=file_hash(out/'inventory-after.json'),captured_log_hashes=captured,
            preserved_prior_history_files=75,total_journal_files=len(history),spawn_request_count=1,entity=6959,
            timeline=timeline,position_events=events,render='CONFIRMED_BY_USER_SCREENSHOTS',
            animation_observation='USER_REPORTED_STOOD_UP; THREE_READ_ONLY_SAMPLES',
            dialogue='PROMPT_VISIBLE_NOT_TESTED',follow='NOT_TESTED',peaceful_behavior='NOT_ESTABLISHED',
            spawn_ready=False,production_spawn_ready=False,rollback_executed=False,save_restore_executed=False)
        write_json_new(out/'result.json',result)
        write_json_new(ROOT/'compatibility/experiments/stage10_11_3/post-close-257936.json',result)
        print(json.dumps({k:v for k,v in result.items() if k not in ('position_events','captured_log_hashes','game_changes','attribution','local_changes')},indent=2))
    except Exception as exc:
        write_json_new(out/'blocked.json',dict(error=str(exc),spawn_ready=False));raise

if __name__=='__main__':main()
