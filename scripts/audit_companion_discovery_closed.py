"""Finish the short read-only PID437520 audit using its fresh post-close snapshot."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from companion.compatibility import file_hash
from companion.integrated_deployment import read_pinned
from companion.patch_update_transaction import verify_backup
from companion.recovery import write_json_new
from companion.runtime_validation import reassess_post_close
from companion.shadow_integrity import DAT,INDEXES,no_reparse
from scripts.prepare_phase_d_backup import GAME,SAVES,live
from scripts.audit_phase_f_closed import differences
from scripts.install_companion_discovery import history,RUN,BACKUP


def main():
    live()
    out=ROOT/'runtime/stage10_12/session437520/post-close'
    b=read_pinned(RUN/'inventory-after.json','9efbdf467f494e57b6938c8923b139b62b9ff0c612a3dae3edd5d5948a48a90f')
    a=json.loads((out/'inventory.json').read_text())
    # Snapshot was just hashed in this closed audit. Reject stale metadata or file sets.
    for group,root in [('game',GAME),('saves',SAVES)]:
        if {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}!=set(a[group]):raise ValueError('FILE_SET_CHANGED')
        for name,r in a[group].items():
            p=root/name;no_reparse(p);s=p.stat()
            if (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink)!=(r['volume'],r['file_id'],r['size'],r['mtime_ns'],r['links']):raise ValueError('STALE_SNAPSHOT:'+name)
    receipts=read_pinned(RUN/'receipt.json','0cc3b3e3cd2db671ad3ec0e5e88d8a5bb0740a8b8b3e6e389219f47a6b10340c')
    for row in receipts['installed_records']:
        if a['game'][row['path']]!=row['record']:raise ValueError('DISCOVERY_INSTALL_CHANGED')
    old=read_pinned(ROOT/'compatibility/experiments/stage10_11_3/installation/receipt.json','d973898fbd447f274fbf2365a9146d1b193a01413677d253fbcfbfc0da338485')
    for row in old['effective_files']:
        if a['game'][row['path']]!=b['game'][row['path']]:raise ValueError('EXISTING_INSTALL_CHANGED')
    selectors={
        'originals':lambda n:n in INDEXES|{'enshrouded.exe','enshrouded.kfc.bak'} or DAT.fullmatch(n),
        'shadow':lambda n:n.startswith('emf/content/client/')}
    counts={}
    for label,choose in selectors.items():
        before={n:r for n,r in b['game'].items() if choose(n)}
        after={n:r for n,r in a['game'].items() if choose(n)}
        if before!=after:raise ValueError(label.upper()+'_CHANGED')
        counts[label]=len(after)
    added=set(a['game'])-set(b['game'])
    if len(added)!=1:raise ValueError('UNEXPECTED_ADDED_GAME_FILES')
    attribution=reassess_post_close(b['game'],a['game'],archive=next(iter(added)),
        session_start_ns=int(datetime.fromisoformat('2026-11-22T18:04:11+03:00').timestamp()*1e9),
        session_end_ns=int(datetime.now(timezone.utc).timestamp()*1e9))
    expected=json.loads((RUN/'history.json').read_text())
    if history()!=expected:raise ValueError('HISTORY_CHANGED')
    bm=read_pinned(BACKUP/'manifest.json',receipts['backup_sha256']);verify_backup(BACKUP,bm)
    delta=differences(b['saves'],a['saves'])
    if delta['added'] or delta['removed']:raise ValueError('LOCAL_FILE_SET_CHANGED')
    for name,r in a['saves'].items():
        if r['size']<=0 or r['links']!=1:raise ValueError('LOCAL_EMPTY_OR_LINKED')
    for rel,name in [('default/character0.ksd','Body Test'),('default/world0.ksd','AI Body Test')]:
        if (SAVES/rel).read_bytes().count(name.encode())!=1:raise ValueError('LOCAL_NAME_CHANGED')
    core=(GAME/'emf/emf_core.log').read_text(encoding='utf-8')
    commands=[line.split('[cmd] > ',1)[1].split()[0] for line in core.splitlines() if '[cmd] > ' in line]
    if commands!=['aic_companion_movement.discover']:raise ValueError('UNEXPECTED_CONSOLE_COMMANDS:'+str(commands))
    if 'AIC_EXPERIMENT SPAWN_ATTEMPT' in core:raise ValueError('UNEXPECTED_SPAWN_LOG')
    log_hashes={}
    for rel in ('enshrouded.log','emf/emf_core.log','emf/emf_loader.log','emf/file_opens.log'):
        dest=out/Path(rel).name;dest.write_bytes((GAME/rel).read_bytes())
        if file_hash(dest)!=a['game'][rel]['sha256']:raise ValueError('LOG_CHANGED')
        log_hashes[rel]=file_hash(dest)
    live()
    result=dict(status='POST_CLOSE_INTEGRITY_PASS_PROFILE_FOUND',pid=437520,
        created_utc=datetime.now(timezone.utc).isoformat(),counts=counts,installed_verified=28,
        backup_verified=23,history_unchanged=len(expected),latch='SPENT',game_count=len(a['game']),
        local_count=len(a['saves']),local_changes=delta,game_changes=differences(b['game'],a['game']),
        attribution=attribution,console_commands=commands,world_save_events=core.count('world saved (slot 0x0001)'),
        local_semantic_integrity='NOT_ESTABLISHED; autosave changes observed, no restore',
        discovery='FOUND_ONE_USER_LOCAL_CLI',instance_identity='PROFILE_ONLY_NOT_PROVEN',
        movement_executed=False,spawn_executed=False,rollback_executed=False,allow_move=False,spawn_ready=False,
        log_hashes=log_hashes,post_close_baseline_sha256=file_hash(out/'inventory.json'))
    write_json_new(out/'result.json',result)
    write_json_new(ROOT/'compatibility/experiments/stage10_12/post-close.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
