"""Exclusive, journalled installation of a previously verified exact plan.

No launch, rollback, overwrite, deletion, game resource or save writes.
On failure preserve partial files and the journal; never resume implicitly.
"""
from datetime import datetime, timezone
import os
import shutil

from .integrated_deployment import validate_plan, installed
from .recovery import measure, no_links, target, write_json_new


def copy_approved(plan, plan_sha, package, game, transaction, *, authorized, live):
    if authorized is not True: raise ValueError('INSTALLATION_NOT_AUTHORIZED')
    validate_plan(plan,package)
    no_links(transaction)
    if transaction.exists(): raise ValueError('NEW_TRANSACTION_REQUIRED')
    if transaction.resolve().is_relative_to(game.resolve()): raise ValueError('JOURNAL_MUST_BE_OUTSIDE_GAME')
    live()
    for row in plan['entries']:
        if target(game,row['destination']).exists(): raise ValueError('DESTINATION_CONFLICT')
    transaction.mkdir(parents=True)
    write_json_new(transaction/'intent.json',dict(plan_sha256=plan_sha,plan_id=plan['plan_id'],
        build=plan['build'],entries=plan['entries'],authorized=True,created_utc=datetime.now(timezone.utc).isoformat()))
    completed=[]
    try:
        for i,row in enumerate(plan['entries'],1):
            live()
            src=target(package,row['source']); dst=target(game,row['destination'])
            expected={'sha256':row['sha256'],'size':row['bytes']}
            if measure(src)!=expected: raise ValueError('SOURCE_CHANGED_BEFORE_COPY')
            write_json_new(transaction/f'{i:02}-intent.json',dict(destination=row['destination'],expected=expected))
            dst.parent.mkdir(parents=True,exist_ok=True)
            no_links(dst)
            with src.open('rb') as a,dst.open('xb') as b:
                shutil.copyfileobj(a,b,1024*1024); b.flush();os.fsync(b.fileno())
            if measure(src)!=expected or measure(dst)!=expected: raise ValueError('COPY_OR_SOURCE_HASH_MISMATCH')
            completed.append(row['destination'])
            write_json_new(transaction/f'{i:02}-verified.json',dict(destination=row['destination'],**expected))
        live()
        receipt=dict(format='aic_integrated_receipt_v1',status='INSTALLED',build=plan['build'],
            plan_sha256=plan_sha,plan_id=plan['plan_id'],entries=plan['entries'],
            installed_utc=datetime.now(timezone.utc).isoformat(),game_root=str(game),
            backup_manifest_sha256=plan['identity'].get('backup_manifest_sha256'),
            installation_authorized=True,installation_executed=True,runtime_status='NOT_EXECUTED',spawn_ready=False)
        installed(plan,plan_sha,receipt,game)
        write_json_new(transaction/'install-receipt.json',receipt)
        return receipt
    except Exception as exc:
        write_json_new(transaction/'failure.json',dict(status='STOPPED',error=str(exc),verified_destinations=completed,
            partial_current_file_possible=True,automatic_cleanup=False,spawn_ready=False))
        raise
