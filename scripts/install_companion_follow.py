"""Authorized exact Stage10.13 installation. No launch, Bridge commands or rollback."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from companion.compatibility import file_hash
from companion.integrated_deployment import read_pinned
from companion.patch_update_transaction import snapshot, verified_backup, verify_backup
from companion.recovery import no_links, target, write_json_new
from companion.shadow_integrity import record
from scripts.prepare_phase_d_backup import GAME, SAVES, live
from scripts.install_companion_discovery import history
from scripts.companion_follow import preflight as runner_preflight

MANIFEST_SHA='5e18844a7999679f1cd0af12fbf49ce00813c023b0bbc3674c90b40dab09b4c8'
RUN=ROOT/'runtime/stage10_13/installation'
BACKUP=ROOT/'runtime/backups/stage10_13-movement_0_2_0'
PUBLIC=ROOT/'compatibility/experiments/stage10_13/installation'
PACKAGE=ROOT/'dist/stage10_13_movement_0_2_0'


def check_entries(plan,package,game,before):
    prefix='emf/mods/aic_companion_movement/'
    replace={'main.lua','mod.json','README.md'}
    add={'follow.lua','follow_config.lua','follow-session.lock'}
    rows=plan['entries']
    if len(rows)!=6 or {r['path'] for r in rows}!={prefix+n for n in replace|add}:
        raise ValueError('EXACT_SIX_REQUIRED')
    for row in rows:
        name=row['path'][len(prefix):]
        if row['source']!=name or row['operation']!=('replace' if name in replace else 'add'):
            raise ValueError('ENTRY_OPERATION')
        source=target(package,row['source']);dest=target(game,row['path'])
        if (file_hash(source),source.stat().st_size)!=(row['sha256'],row['bytes']):raise ValueError('PAYLOAD_CHANGED')
        if name in replace:
            if record(dest)!=before[row['path']] or row['before_sha256']!=before[row['path']]['sha256']:
                raise ValueError('CURRENT_FILE_CHANGED')
        elif dest.exists() or row['path'] in before or row['before_sha256'] is not None:
            raise ValueError('ADDITION_CONFLICT')
        temp=dest.with_name(dest.name+'.aic-follow-update.tmp');no_links(temp)
        if temp.exists():raise ValueError('TEMP_CONFLICT')


def preserved(plan):
    if history()!=plan['spawn_history']:raise ValueError('SPAWN_HISTORY_CHANGED')
    for row in plan['preserved_intents']:
        p=target(ROOT,row['path'])
        if file_hash(p)!=row['sha256']:raise ValueError('PREVIOUS_INTENT_CHANGED')
    journal=ROOT/'runtime/stage10_13/test-session.jsonl';no_links(journal)
    if journal.exists():raise ValueError('FOLLOW_SESSION_ALREADY_CONSUMED')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--install-approved',action='store_true');args=ap.parse_args()
    live()
    plan=read_pinned(PACKAGE/'exact-update-manifest.json',MANIFEST_SHA)
    read_pinned(ROOT/'compatibility/experiments/stage10_13/exact-update-manifest.json',MANIFEST_SHA)
    before=read_pinned(ROOT/'runtime/stage10_12/session456828/post-close/inventory.json',plan['baseline_sha256'])
    check_entries(plan,PACKAGE,GAME,before['game']);preserved(plan)
    for p in (RUN,BACKUP,PUBLIC):
        no_links(p)
        if p.exists():raise ValueError('NEW_INSTALLATION_TRANSACTION_REQUIRED')
    print('Closed/build/exact payload6/old intents/SPENT PASS; hashing baseline...',flush=True)
    if dict(game=snapshot(GAME),saves=snapshot(SAVES))!=before:raise ValueError('BASELINE_CHANGED')
    live()
    if not args.install_approved:
        print('READ_ONLY_PREFLIGHT_PASS');return
    RUN.mkdir(parents=True)
    write_json_new(RUN/'baseline.json',before)
    replace={r['path'] for r in plan['entries'] if r['operation']=='replace'}
    additions={r['path'] for r in plan['entries'] if r['operation']=='add'}
    bp=dict(files=[dict(group='saves',path=n,sha256=r['sha256'],bytes=r['size']) for n,r in before['saves'].items()]+
        [dict(group='game',path=n,sha256=before['game'][n]['sha256'],bytes=before['game'][n]['size']) for n in sorted(replace)])
    if len(bp['files'])!=26:raise ValueError('BACKUP_COUNT')
    write_json_new(RUN/'backup-plan.json',bp)
    done=[]
    try:
        bm=verified_backup(bp,{'game':GAME,'saves':SAVES},BACKUP,live=live);verify_backup(BACKUP,bm)
        if snapshot(SAVES)!=before['saves']:raise ValueError('LOCAL_CHANGED')
        preserved(plan);check_entries(plan,PACKAGE,GAME,before['game'])
        print('Verified backup26 PASS; applying exact three replacements and three additions...',flush=True)
        write_json_new(RUN/'install-intent.json',dict(manifest_sha256=MANIFEST_SHA,entries=plan['entries']))
        for i,row in enumerate(plan['entries'],1):
            live();source=target(PACKAGE,row['source']);dest=target(GAME,row['path'])
            if file_hash(source)!=row['sha256']:raise ValueError('SOURCE_CHANGED')
            if row['operation']=='replace':
                if record(dest)!=before['game'][row['path']]:raise ValueError('DESTINATION_CHANGED')
            elif dest.exists():raise ValueError('NEW_DESTINATION_CONFLICT')
            temp=dest.with_name(dest.name+'.aic-follow-update.tmp');no_links(temp)
            write_json_new(RUN/f'{i:02}-intent.json',dict(path=row['path'],operation=row['operation'],temporary_name=temp.name))
            with temp.open('xb') as f:
                f.write(source.read_bytes());f.flush();os.fsync(f.fileno())
            if file_hash(temp)!=row['sha256']:raise ValueError('STAGED_HASH')
            live();no_links(dest)
            if row['operation']=='replace':
                if record(dest)!=before['game'][row['path']]:raise ValueError('DESTINATION_CHANGED_BEFORE_REPLACE')
                os.replace(temp,dest)
            else:
                if os.name!='nt':raise ValueError('WINDOWS_NO_CLOBBER_RENAME_REQUIRED')
                os.rename(temp,dest)  # Windows rename refuses an existing destination.
            result=record(dest)
            if (result['sha256'],result['size'])!=(row['sha256'],row['bytes']):raise ValueError('INSTALLED_HASH')
            done.append(dict(path=row['path'],operation=row['operation'],record=result))
            write_json_new(RUN/f'{i:02}-verified.json',done[-1])
        print('Installed6 PASS; verifying unrelated files/LOCAL and Runner readiness...',flush=True)
        after=dict(game=snapshot(GAME),saves=snapshot(SAVES));live()
        if set(after['game'])!=set(before['game'])|additions or after['saves']!=before['saves']:
            raise ValueError('FILE_SET_OR_LOCAL_CHANGED')
        for n,r in before['game'].items():
            if n not in replace and after['game'][n]!=r:raise ValueError('UNRELATED_FILE_CHANGED:'+n)
        for r in done:
            if after['game'][r['path']]!=r['record']:raise ValueError('INSTALLED_RECORD_CHANGED')
        preserved(plan);verify_backup(BACKUP,bm);runner_preflight(plan,GAME)
        # Read-only rollback readiness: replacements have verified before-images; additions are exact-owned.
        rollback=[]
        for row in plan['entries']:
            if row['operation']=='replace':
                if file_hash(target(BACKUP/'payload/game',row['path']))!=row['before_sha256']:raise ValueError('RESTORE_SOURCE_CHANGED')
            rollback.append(dict(path=row['path'],action='restore_verified_backup' if row['operation']=='replace' else 'remove_exact_owned_addition',
                                 current_sha256=row['sha256'],before_sha256=row['before_sha256']))
        write_json_new(RUN/'rollback-dry-run.json',dict(status='PASS',executed=False,save_restore=False,entries=rollback))
        write_json_new(RUN/'inventory-after.json',after)
        receipt=dict(status='INSTALLED_READY_FOR_MANUAL_START',version='0.2.0',created_utc=datetime.now(timezone.utc).isoformat(),
            manifest_sha256=MANIFEST_SHA,installed_records=done,effective_hashes_verified=len(plan['effective_files']),
            backup_files=len(bm['files']),backup_bytes=bm['payload_bytes'],backup_manifest_sha256=file_hash(BACKUP/'manifest.json'),
            local_unchanged=len(before['saves']),unchanged_game_files=len(before['game'])-len(replace),
            history_unchanged=len(plan['spawn_history']),old_latch='SPENT',follow_latch='UNUSED',runner_ready=True,
            post_install_baseline_sha256=file_hash(RUN/'inventory-after.json'),rollback_dry_run='PASS',
            game_launched=False,movement_executed=False,roaming='native',spawn_ready=False)
        write_json_new(RUN/'receipt.json',receipt);PUBLIC.mkdir(parents=True);write_json_new(PUBLIC/'receipt.json',receipt)
        print(receipt,flush=True)
    except Exception as exc:
        write_json_new(RUN/'blocked.json',dict(error=str(exc),verified=done,partial_update_possible=True,automatic_rollback=False))
        raise


if __name__=='__main__':main()
