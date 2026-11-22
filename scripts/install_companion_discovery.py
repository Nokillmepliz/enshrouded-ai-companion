"""Stage 10.12 additive discovery installation; no overwrite, rollback or launch."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.compatibility import file_hash
from companion.integrated_deployment import read_pinned
from companion.patch_update_transaction import snapshot, verified_backup, verify_backup
from companion.recovery import no_links, target, write_json_new
from companion.shadow_integrity import record
from scripts.prepare_phase_d_backup import GAME,SAVES,live

RUN=ROOT/'runtime/stage10_12/discovery-install'
BACKUP=ROOT/'runtime/backups/stage10_12-discovery-local'
PREFIX='emf/mods/aic_companion_movement/'
NAMES=('mod.json','main.lua','controller.lua','README.md')
PATHS={PREFIX+n for n in NAMES}|{'emf/config/aic_companion_movement.ini'}


def history():
    binding=json.loads((ROOT/'dist/stage10_11_first_spawn_0_1_0/client-binding.json').read_text())
    root=ROOT/'runtime/stage10_11/experiments'/binding['key']
    if (GAME/'emf/mods/aic_first_spawn/attempt.lock').read_bytes()!=('SPENT!:'+binding['key']).encode():
        raise ValueError('SPENT_LATCH_REQUIRED')
    if not (root/'spawn-intent.json').is_file():raise ValueError('SPAWN_INTENT_MISSING')
    return {p.relative_to(root).as_posix():file_hash(p) for p in root.rglob('*') if p.is_file()}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--install-approved',action='store_true');args=ap.parse_args()
    live()
    baseline=read_pinned(ROOT/'runtime/stage10_11_3/live/20261118T165734028417Z/session257936/post-close/inventory-after.json',
        '120850afac7ff4242f5e07b32f8fa071607c2af411a06681cadf61e7bc56fe80')
    if json.loads((RUN/'baseline.json').read_text())!=baseline:raise ValueError('PREFLIGHT_BASELINE_CHANGED')
    package=RUN/'package'
    if not args.install_approved:
        if target(GAME,'emf/mods/aic_companion_movement').exists():raise ValueError('MOD_DIRECTORY_CONFLICT')
        package.mkdir(exist_ok=False)
        rows=[]
        for name in NAMES:
            source=ROOT/'mods/aic_companion_movement'/name
            dest=package/name;dest.write_bytes(source.read_bytes())
            rows.append(dict(path=PREFIX+name,source=name,sha256=file_hash(dest),bytes=dest.stat().st_size))
        (package/'config.ini').write_bytes(b'[aic_companion_movement]\nenabled=1\n')
        rows.append(dict(path='emf/config/aic_companion_movement.ini',source='config.ini',
            sha256=file_hash(package/'config.ini'),bytes=(package/'config.ini').stat().st_size))
        assert 'allow_move=false' in (package/'main.lua').read_text()
        assert json.loads((package/'mod.json').read_text())['enabled'] is False
        for row in rows:
            if target(GAME,row['path']).exists():raise ValueError('DESTINATION_CONFLICT')
        bp=dict(files=[dict(group='saves',path=n,sha256=r['sha256'],bytes=r['size']) for n,r in baseline['saves'].items()],
                payload_bytes=sum(r['size'] for r in baseline['saves'].values()))
        before=history()
        bm=verified_backup(bp,{'saves':SAVES},BACKUP,live=live);verify_backup(BACKUP,bm)
        if snapshot(SAVES)!=baseline['saves'] or history()!=before:raise ValueError('SOURCE_CHANGED')
        write_json_new(RUN/'history.json',before)
        write_json_new(RUN/'manifest.json',dict(entries=rows,backup_sha256=file_hash(BACKUP/'manifest.json'),
            history_sha256=file_hash(RUN/'history.json'),baseline_sha256=file_hash(RUN/'baseline.json'),
            allow_move=False,spawn_ready=False))
        print(json.dumps(dict(status='BACKUP_VERIFIED_READY_TO_INSTALL',files=len(bm['files']),bytes=bm['payload_bytes'],
            manifest_sha256=file_hash(RUN/'manifest.json'))));return
    manifest=read_pinned(RUN/'manifest.json','5e0c7b2e60a627c6976a7098b726894a267632a4dea7839a50a5df13fd349003');rows=manifest['entries']
    if len(rows)!=5 or {r['path'] for r in rows}!=PATHS or manifest['allow_move'] is not False:raise ValueError('EXACT_FIVE_REQUIRED')
    read_pinned(RUN/'baseline.json',manifest['baseline_sha256'])
    expected_history=read_pinned(RUN/'history.json',manifest['history_sha256'])
    bm=read_pinned(BACKUP/'manifest.json',manifest['backup_sha256']);verify_backup(BACKUP,bm)
    for row in rows:
        src=target(package,row['source'])
        if (file_hash(src),src.stat().st_size)!=(row['sha256'],row['bytes']):raise ValueError('PAYLOAD_CHANGED')
        if target(GAME,row['path']).exists():raise ValueError('DESTINATION_CONFLICT')
    if target(GAME,'emf/mods/aic_companion_movement').exists():raise ValueError('MOD_DIRECTORY_CONFLICT')
    if 'allow_move=false' not in (package/'main.lua').read_text():raise ValueError('MOVEMENT_GATE')
    if history()!=expected_history:raise ValueError('HISTORY_CHANGED')
    # Fresh whole-tree comparison immediately before the five new writes.
    if dict(game=snapshot(GAME),saves=snapshot(SAVES))!=baseline:raise ValueError('BASELINE_CHANGED')
    live();write_json_new(RUN/'install-intent.json',manifest)
    done=[]
    try:
        for row in rows:
            live();src=target(package,row['source']);dst=target(GAME,row['path'])
            if file_hash(src)!=row['sha256']:raise ValueError('SOURCE_CHANGED')
            dst.parent.mkdir(parents=True,exist_ok=True);no_links(dst)
            with dst.open('xb') as f:
                f.write(src.read_bytes());f.flush();os.fsync(f.fileno())
            actual=record(dst)
            if (actual['sha256'],actual['size'])!=(row['sha256'],row['bytes']):raise ValueError('INSTALLED_HASH')
            done.append(dict(path=row['path'],record=actual))
            write_json_new(RUN/f'installed-{len(done)}.json',done[-1])
        after=dict(game=snapshot(GAME),saves=snapshot(SAVES));live()
        if after['saves']!=baseline['saves'] or set(after['game'])!=set(baseline['game'])|PATHS:raise ValueError('POST_INSTALL_SET_OR_SAVES')
        if any(after['game'][n]!=r for n,r in baseline['game'].items()):raise ValueError('EXISTING_FILE_CHANGED')
        if history()!=expected_history:raise ValueError('HISTORY_CHANGED')
        verify_backup(BACKUP,bm)
        write_json_new(RUN/'inventory-after.json',after)
        receipt=dict(status='INSTALLED_READ_ONLY_DISCOVERY',created_utc=datetime.now(timezone.utc).isoformat(),
            manifest_sha256=file_hash(RUN/'manifest.json'),installed_records=done,backup_files=len(bm['files']),
            backup_bytes=bm['payload_bytes'],backup_sha256=manifest['backup_sha256'],existing_game_unchanged=len(baseline['game']),
            local_unchanged=len(baseline['saves']),history_unchanged=len(expected_history),allow_move=False,
            baseline_after_sha256=file_hash(RUN/'inventory-after.json'),spawn_ready=False,game_launched=False)
        write_json_new(RUN/'receipt.json',receipt)
        print(json.dumps(receipt,indent=2))
    except Exception as exc:
        write_json_new(RUN/'blocked.json',dict(error=str(exc),completed=done,automatic_rollback=False));raise


if __name__=='__main__':main()
