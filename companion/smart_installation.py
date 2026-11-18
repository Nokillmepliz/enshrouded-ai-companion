"""Exact four-file replacement with exclusive journals; never automatic rollback."""
import os
import shutil
from .compatibility import file_hash
from .recovery import target,no_links,write_json_new
from .shadow_integrity import record
from .smart_deployment import check_manifest


def replace(manifest,baseline,package,game,backup,journal,*,authorized,live):
    if authorized is not True:raise ValueError('INSTALL_NOT_AUTHORIZED')
    check_manifest(manifest,baseline)
    no_links(journal)
    if journal.exists() or journal.resolve().is_relative_to(game.resolve()):raise ValueError('NEW_EXTERNAL_JOURNAL_REQUIRED')
    checked=[]
    for row in manifest['entries']:
        src=target(package,row['source']);dst=target(game,row['path'])
        saved=target(backup/'payload/game',row['path'])
        live();before=record(dst);payload=record(src)
        if before!=baseline['game'][row['path']]:raise ValueError('BEFORE_RECORD_CHANGED')
        if (payload['sha256'],payload['size'])!=(row['sha256'],row['bytes']):raise ValueError('PAYLOAD_CHANGED')
        if file_hash(saved)!=row['before_sha256']:raise ValueError('BACKUP_CHANGED')
        temp=dst.with_name(dst.name+'.aic-smart-update.tmp');no_links(temp)
        if temp.exists():raise ValueError('TEMP_CONFLICT')
        checked.append((row,src,dst,temp,before,payload))
    live();journal.mkdir(parents=True)
    write_json_new(journal/'intent.json',dict(entries=manifest['entries'],authorized=True,automatic_rollback=False))
    done=[]
    try:
        for i,(row,src,dst,temp,before,payload) in enumerate(checked,1):
            live();no_links(dst);no_links(src);no_links(temp)
            if record(dst)!=before or record(src)!=payload:raise ValueError('SOURCE_OR_DESTINATION_CHANGED')
            if file_hash(target(backup/'payload/game',row['path']))!=row['before_sha256']:raise ValueError('BACKUP_CHANGED')
            write_json_new(journal/f'{i:02}-intent.json',dict(path=row['path'],before=before,payload=payload))
            with src.open('rb') as a,temp.open('xb') as b:
                shutil.copyfileobj(a,b);b.flush();os.fsync(b.fileno())
            os.utime(temp,ns=(payload['mtime_ns'],payload['mtime_ns']))
            if file_hash(temp)!=row['sha256'] or record(src)!=payload:raise ValueError('COPY_CHANGED')
            live();no_links(dst);no_links(temp)
            if record(dst)!=before:raise ValueError('DESTINATION_CHANGED')
            os.replace(temp,dst)
            after=record(dst)
            if (after['sha256'],after['size'])!=(row['sha256'],row['bytes']):raise ValueError('INSTALL_VERIFY_FAILED')
            result=dict(path=row['path'],before=before,after=after);done.append(result)
            write_json_new(journal/f'{i:02}-verified.json',result)
        live();return done
    except Exception as exc:
        write_json_new(journal/'failure.json',dict(error=str(exc),verified=done,automatic_rollback=False))
        raise


def rollback_dry_run(manifest,game,backup):
    rows=[]
    for row in manifest['entries']:
        current=target(game,row['path']);saved=target(backup/'payload/game',row['path'])
        if file_hash(current)!=row['sha256'] or file_hash(saved)!=row['before_sha256']:
            raise ValueError('ROLLBACK_CONFLICT')
        rows.append(dict(path=row['path'],current_sha256=row['sha256'],restore_sha256=row['before_sha256']))
    return dict(status='ROLLBACK_DRY_RUN_PASS',entries=rows,executed=False,save_restore=False,latch_restore=False)
