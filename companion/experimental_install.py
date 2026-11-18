"""Additive seven-file transaction. No deletion, overwrite or rollback API."""
from datetime import datetime, timezone
import os
import shutil

from .compatibility import file_hash
from .recovery import no_links, target, write_json_new
from .shadow_integrity import record

PREFIX = 'emf/mods/aic_first_spawn/'
PATHS = {PREFIX+n for n in ('mod.json','main.lua','controller.lua','README.md','binding.lua','attempt.lock')} | {'emf/config/aic_first_spawn.ini'}


def validate(manifest, package, game, *, absent):
    rows = manifest['entries']
    if manifest.get('format') != 'aic_stage10_11_additive_install_v1' or manifest.get('build') != 1287369:
        raise ValueError('MANIFEST_FORMAT_OR_BUILD')
    if len(rows) != 7 or {r['path'] for r in rows} != PATHS:
        raise ValueError('EXACT_SEVEN_PATHS_REQUIRED')
    for row in rows:
        if row['source'] != 'payload/'+row['path'] or row['before_sha256'] is not None:
            raise ValueError('ADDITIVE_ONLY')
        source = target(package, row['source']); dest = target(game, row['path'])
        if file_hash(source) != row['sha256'] or source.stat().st_size != row['bytes']:
            raise ValueError('SOURCE_CHANGED:'+row['path'])
        if absent and dest.exists():
            raise ValueError('DESTINATION_CONFLICT:'+row['path'])
    if absent and target(game, 'emf/mods/aic_first_spawn').exists():
        raise ValueError('MOD_DIRECTORY_CONFLICT')


def copy_seven(manifest, package, game, journal, *, authorized, live):
    if authorized is not True:
        raise ValueError('INSTALLATION_NOT_AUTHORIZED')
    live();validate(manifest, package, game, absent=True)
    no_links(journal)
    if journal.exists() or journal.resolve().is_relative_to(game.resolve()):
        raise ValueError('NEW_EXTERNAL_JOURNAL_REQUIRED')
    journal.mkdir(parents=True)
    write_json_new(journal/'intent.json', dict(entries=manifest['entries'], authorized=True,
        spawn_authorized=False, rollback_authorized=False))
    done=[]
    try:
        for index,row in enumerate(manifest['entries'],1):
            live()
            source=target(package,row['source']);dest=target(game,row['path'])
            source_record=record(source)
            if source_record['sha256']!=row['sha256'] or source_record['size']!=row['bytes']:
                raise ValueError('SOURCE_CHANGED_BEFORE_COPY')
            if dest.exists():raise ValueError('DESTINATION_APPEARED')
            write_json_new(journal/f'{index:02}-intent.json',dict(path=row['path'],before=None,source=source_record))
            dest.parent.mkdir(parents=True,exist_ok=True)
            no_links(dest)
            with source.open('rb') as inp,dest.open('xb') as out:
                shutil.copyfileobj(inp,out,1024*1024);out.flush();os.fsync(out.fileno())
            actual=record(dest)
            if (actual['sha256'],actual['size'])!=(row['sha256'],row['bytes']) or record(source)!=source_record:
                raise ValueError('COPY_OR_SOURCE_CHANGED')
            done.append(dict(path=row['path'],record=actual))
            write_json_new(journal/f'{index:02}-complete.json',done[-1])
        live()
        return done
    except Exception as exc:
        write_json_new(journal/'failed.json',dict(error=str(exc),completed=done,
            rollback_executed=False,note='Partial current file may exist; inspect intent, never auto-remove'))
        raise


def removal_dry_run(manifest, receipt, game):
    if receipt.get('status')!='INSTALLED' or receipt.get('entries')!=manifest['entries']:
        raise ValueError('RECEIPT_MISMATCH')
    if len(receipt.get('installed_records',[]))!=7:
        raise ValueError('RECEIPT_RECORDS_REQUIRED')
    records={r['path']:r['record'] for r in receipt['installed_records']}
    if set(records)!=PATHS:raise ValueError('RECEIPT_PATHS')
    for row in manifest['entries']:
        actual=record(target(game,row['path']))
        if actual!=records[row['path']] or actual['sha256']!=row['sha256'] or actual['size']!=row['bytes']:
            raise ValueError('CHANGED_FILE_NOT_REMOVABLE:'+row['path'])
    return dict(status='REMOVAL_DRY_RUN_PASS',files=sorted(PATHS),count=7,
        checked_utc=datetime.now(timezone.utc).isoformat(),executed=False,
        scope='UNUSED_LATCH_INSTALL_STATE_ONLY; re-review after runtime changes',
        excludes=['originals','existing16','shadow','cache','LOCAL','unknown files'],
        deletion_requires_separate_authorization=True)
