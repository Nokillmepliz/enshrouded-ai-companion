"""Approved exact four-file 0.1.1 update. No launch, movement or rollback."""
import argparse
from datetime import datetime,timezone
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from companion.compatibility import file_hash
from companion.integrated_deployment import read_pinned
from companion.patch_update_transaction import snapshot,verified_backup,verify_backup
from companion.recovery import target,no_links,write_json_new
from companion.shadow_integrity import record
from scripts.prepare_phase_d_backup import GAME,SAVES,live
from scripts.install_companion_discovery import history

MANIFEST_SHA='a4c574d4e0678caec35d1a4567ca2cdeed2a5955983a00eae1a3e099b100681d'
PUBLIC=ROOT/'compatibility/experiments/stage10_12/movement-installation'
RUN=ROOT/'runtime/stage10_12/movement-installation'
BACKUP=ROOT/'runtime/backups/stage10_12-movement-0_1_1'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--install-approved',action='store_true');args=ap.parse_args()
    live()
    package=ROOT/'dist/stage10_12_movement_0_1_1'
    plan=read_pinned(package/'exact-update-manifest.json',MANIFEST_SHA)
    before=read_pinned(ROOT/'runtime/stage10_12/session437520/post-close/inventory.json',plan['baseline_sha256'])
    previous=read_pinned(ROOT/'runtime/stage10_12/discovery-install/receipt.json',plan['previous_receipt_sha256'])
    for row in previous['installed_records']:
        if record(target(GAME,row['path']))!=row['record']:raise ValueError('CURRENT_INSTALL_CHANGED')
    paths={'emf/mods/aic_companion_movement/'+n for n in ('main.lua','controller.lua','mod.json','README.md')}
    if len(plan['entries'])!=4 or {r['path'] for r in plan['entries']}!=paths:raise ValueError('EXACT_FOUR_REQUIRED')
    for row in plan['entries']:
        source=target(package,row['source']);dest=target(GAME,row['path'])
        if (file_hash(source),source.stat().st_size)!=(row['sha256'],row['bytes']):raise ValueError('PAYLOAD_CHANGED')
        if (file_hash(dest),dest.stat().st_size)!=(row['before_sha256'],row['before_bytes']):raise ValueError('OLD_PAYLOAD_CHANGED')
        temp=dest.with_name(dest.name+'.aic-movement-update.tmp');no_links(temp)
        if temp.exists():raise ValueError('TEMP_CONFLICT')
    if (ROOT/'runtime/stage10_12/first-movement/movement-intent.json').exists():raise ValueError('MOVEMENT_ALREADY_ATTEMPTED')
    old_history=history()
    print('Closed/build/payload4/current5/SPENT/history PASS; hashing fresh baseline...',flush=True)
    if dict(game=snapshot(GAME),saves=snapshot(SAVES))!=before:raise ValueError('BASELINE_CHANGED')
    live()
    if not args.install_approved:
        print('READ_ONLY_PREFLIGHT_PASS');return
    for p in (RUN,BACKUP,PUBLIC):
        no_links(p)
        if p.exists():raise ValueError('NEW_TRANSACTION_REQUIRED')
    RUN.mkdir(parents=True)
    write_json_new(RUN/'baseline.json',before);write_json_new(RUN/'history.json',old_history)
    bp=dict(files=[dict(group='saves',path=n,sha256=r['sha256'],bytes=r['size']) for n,r in before['saves'].items()]+
        [dict(group='game',path=n,sha256=before['game'][n]['sha256'],bytes=before['game'][n]['size']) for n in sorted(paths)])
    write_json_new(RUN/'backup-plan.json',bp)
    done=[]
    try:
        bm=verified_backup(bp,{'game':GAME,'saves':SAVES},BACKUP,live=live);verify_backup(BACKUP,bm)
        if snapshot(SAVES)!=before['saves'] or history()!=old_history:raise ValueError('SOURCE_CHANGED')
        print('Verified backup27 PASS; replacing exact four files...',flush=True)
        write_json_new(RUN/'install-intent.json',dict(manifest_sha256=MANIFEST_SHA,entries=plan['entries']))
        for row in plan['entries']:
            live();source=target(package,row['source']);dest=target(GAME,row['path'])
            temp=dest.with_name(dest.name+'.aic-movement-update.tmp');no_links(temp)
            if record(dest)!=before['game'][row['path']] or file_hash(source)!=row['sha256']:raise ValueError('PRE_REPLACE_CHANGED')
            with temp.open('xb') as f:
                f.write(source.read_bytes());f.flush();os.fsync(f.fileno())
            if file_hash(temp)!=row['sha256']:raise ValueError('STAGED_HASH')
            live();no_links(dest)
            if record(dest)!=before['game'][row['path']]:raise ValueError('DESTINATION_CHANGED')
            os.replace(temp,dest)
            r=record(dest)
            if (r['sha256'],r['size'])!=(row['sha256'],row['bytes']):raise ValueError('INSTALLED_HASH')
            done.append(dict(path=row['path'],record=r));write_json_new(RUN/f'installed-{len(done)}.json',done[-1])
        print('Four replacements verified; checking unchanged files and saves...',flush=True)
        after=dict(game=snapshot(GAME),saves=snapshot(SAVES));live()
        if after['saves']!=before['saves'] or set(after['game'])!=set(before['game']):raise ValueError('POST_INSTALL_SET_OR_SAVES')
        if any(after['game'][n]!=r for n,r in before['game'].items() if n not in paths):raise ValueError('UNRELATED_FILE_CHANGED')
        if any(after['game'][r['path']]!=r['record'] for r in done):raise ValueError('NEW_FILE_CHANGED')
        if history()!=old_history:raise ValueError('HISTORY_CHANGED')
        verify_backup(BACKUP,bm)
        write_json_new(RUN/'inventory-after.json',after)
        receipt=dict(status='INSTALLED_READY_FOR_MANUAL_START',version='0.1.1',created_utc=datetime.now(timezone.utc).isoformat(),
            manifest_sha256=MANIFEST_SHA,installed_records=done,backup_manifest_sha256=file_hash(BACKUP/'manifest.json'),
            backup_files=len(bm['files']),backup_bytes=bm['payload_bytes'],unchanged_game_files=len(before['game'])-4,
            local_unchanged=len(before['saves']),history_unchanged=len(old_history),latch='SPENT',
            post_install_baseline_sha256=file_hash(RUN/'inventory-after.json'),movement_executed=False,
            game_launched=False,spawn_ready=False,automatic_rollback=False)
        write_json_new(RUN/'receipt.json',receipt)
        PUBLIC.mkdir(parents=True);write_json_new(PUBLIC/'receipt.json',receipt)
        print(receipt,flush=True)
    except Exception as exc:
        write_json_new(RUN/'blocked.json',dict(error=str(exc),completed=done,automatic_rollback=False));raise


if __name__=='__main__':main()
