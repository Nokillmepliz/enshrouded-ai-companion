"""Exact, journalled replacements; no game launch, shadow cleanup or rollback."""
from datetime import datetime, timezone
import os
import shutil

from .compatibility import file_hash
from .recovery import no_links, target, write_json_new
from .shadow_integrity import record, no_reparse
from .integrated_update import check_plan


def snapshot(root):
    """Hash each physical file once, allowing audited shadow hardlinks."""
    no_reparse(root)
    files={};cache={}
    for p in root.rglob('*'):
        no_reparse(p)
        if not p.is_file():continue
        s=p.stat();key=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink)
        r=cache[key] if key in cache else record(p)
        cache[key]=r;files[p.relative_to(root).as_posix()]=r
    if {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}!=set(files):
        raise ValueError('INVENTORY_CHANGED_DURING_READ')
    for name,r in files.items():
        p=root/name;no_reparse(p);s=p.stat()
        if (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink)!=(r['volume'],r['file_id'],r['size'],r['mtime_ns'],r['links']):
            raise ValueError('FILE_CHANGED_DURING_READ:'+name)
    return files


def verified_backup(plan, roots, destination, *, live):
    no_links(destination)
    if destination.exists():raise ValueError('NEW_BACKUP_REQUIRED')
    if any(destination.resolve().is_relative_to(r.resolve()) for k,r in roots.items() if k!='project'):
        raise ValueError('BACKUP_INSIDE_GAME_OR_SAVES')
    live();destination.mkdir(parents=True)
    rows=[]
    for row in plan['files']:
        live()
        src=target(roots[row['group']],row['path']);before=record(src)
        if before['sha256']!=row['sha256'] or before['size']!=row['bytes']:
            raise ValueError('BACKUP_SOURCE_MISMATCH:'+row['path'])
        relative=row['group']+'/'+row['path'];dst=target(destination/'payload',relative)
        dst.parent.mkdir(parents=True,exist_ok=True)
        with src.open('rb') as a,dst.open('xb') as b:
            shutil.copyfileobj(a,b,1024*1024);b.flush();os.fsync(b.fileno())
        os.utime(dst,ns=(before['mtime_ns'],before['mtime_ns']))
        if record(src)!=before or file_hash(dst)!=before['sha256']:
            raise ValueError('BACKUP_COPY_OR_SOURCE_CHANGED')
        rows.append(dict(row,relative=relative,source_record=before))
    manifest=dict(format='aic_patch_backup_v1',files=rows,payload_bytes=sum(r['bytes'] for r in rows),
                  created_utc=datetime.now(timezone.utc).isoformat(),save_restore_authorized=False)
    write_json_new(destination/'manifest.json',manifest)
    verify_backup(destination,manifest)
    live();return manifest


def verify_backup(root, manifest):
    expected={r['relative'] for r in manifest['files']}
    if len(expected)!=len(manifest['files']):raise ValueError('DUPLICATE_BACKUP_ENTRY')
    if {p.relative_to(root/'payload').as_posix() for p in (root/'payload').rglob('*') if p.is_file()}!=expected:
        raise ValueError('BACKUP_FILE_SET_MISMATCH')
    for row in manifest['files']:
        path=target(root/'payload',row['relative'])
        if file_hash(path)!=row['sha256'] or path.stat().st_size!=row['bytes'] or path.stat().st_mtime_ns!=row['source_record']['mtime_ns']:
            raise ValueError('BACKUP_INTEGRITY_MISMATCH')


def replace_four(plan, package, game, backup, journal, *, authorized, live):
    if authorized is not True:raise ValueError('UPDATE_NOT_AUTHORIZED')
    check_plan(plan,package);no_links(journal)
    if journal.exists() or journal.resolve().is_relative_to(game.resolve()):raise ValueError('NEW_EXTERNAL_JOURNAL_REQUIRED')
    live();journal.mkdir(parents=True)
    write_json_new(journal/'intent.json',dict(plan_id=plan['plan_id'],authorized=True,entries=plan['entries']))
    done=[]
    try:
        for i,row in enumerate(plan['entries'],1):
            live()
            src=target(package,'game/'+row['destination']);dst=target(game,row['destination'])
            saved=target(backup/'payload/game',row['destination'])
            before=record(dst)
            if (before['sha256'],before['size'],before['mtime_ns'])!=(row['current_sha256'],row['current_bytes'],row['current_mtime_ns']):
                raise ValueError('CURRENT_FILE_CHANGED')
            if file_hash(saved)!=row['current_sha256']:raise ValueError('BACKUP_CHANGED')
            source=record(src)
            if (source['sha256'],source['size'],source['mtime_ns'])!=(row['new_sha256'],row['new_bytes'],row['new_mtime_ns']):
                raise ValueError('PAYLOAD_CHANGED')
            temp=dst.with_name(dst.name+'.aic-update-'+plan['plan_id'][:12]+'.tmp')
            no_links(temp)
            if temp.exists():raise ValueError('TEMP_CONFLICT')
            write_json_new(journal/f'{i:02}-intent.json',dict(destination=row['destination'],before=before,temporary_name=temp.name))
            with src.open('rb') as a,temp.open('xb') as b:
                shutil.copyfileobj(a,b,1024*1024);b.flush();os.fsync(b.fileno())
            os.utime(temp,ns=(row['new_mtime_ns'],row['new_mtime_ns']))
            no_links(temp)
            if record(src)!=source or file_hash(temp)!=row['new_sha256']:
                raise ValueError('STAGED_COPY_CHANGED')
            live();no_links(dst)
            if record(dst)!=before:raise ValueError('DESTINATION_CHANGED_BEFORE_REPLACE')
            os.replace(temp,dst)
            no_links(dst);after=record(dst)
            if (after['sha256'],after['size'],after['mtime_ns'])!=(row['new_sha256'],row['new_bytes'],row['new_mtime_ns']):
                raise ValueError('REPLACEMENT_VERIFY_FAILED')
            done.append(row['destination'])
            write_json_new(journal/f'{i:02}-verified.json',dict(destination=row['destination'],before=before,after=after))
        live();return done
    except Exception as exc:
        write_json_new(journal/'failure.json',dict(error=str(exc),verified=done,partial_update_possible=True,
                                                  automatic_rollback=False,temporary_files_preserved=True))
        raise
