"""Read-only four-file update/rollback planning. No install or cleanup entrypoint."""
import hashlib
import json
from pathlib import Path

from .compatibility import file_hash, fingerprint
from .recovery import no_links, target

TARGETS = {'mods/aic_eml_humanoid/mod.json', 'mods/aic_eml_humanoid/src/mod.lua',
           'mods/aic_eml_humanoid/README.md', 'emf/mods/aic_integrated_observer/binding.lua'}


def input_fingerprint(facts, version):
    """Pinned upstream metadata algorithm over audited facts, including links.

    Callers must verify SHA/identities separately. This cannot establish safety.
    """
    if version not in ('0.5.0', '0.5.1'):
        raise ValueError('UNSUPPORTED_PATCH_VERSION')
    text = 'emf content fingerprint 2\nemf\t0.6.18\n'
    def line(label, path, name):
        row = facts[path]
        return f"{label}\t{name}\t{row['size']}\t{row['mtime_ns']//100+116444736000000000}\n"
    for label, name in [('base','enshrouded.kfc'),('kfc','enshrouded.kfc'),
                        ('resources','enshrouded.kfc_resources'),('exe','enshrouded.exe')]:
        text += line(label, name, name)
    text += line('dll', 'emf/emf_content.dll', 'emf_content.dll')
    text += f'dats\t55\t64\nmod\taic_eml_humanoid\t{version}\t3\n'
    for name in ('mod.json','README.md','src/mod.lua'):
        text += line('file', 'mods/aic_eml_humanoid/'+name, name.replace('/','\\'))
    return 'sha256:' + hashlib.sha256(text.encode()).hexdigest()


def check_plan(plan, package):
    if plan.get('format') != 'aic_patch_update_v1' or plan.get('patch_version') != '0.5.1':
        raise ValueError('UPDATE_FORMAT')
    if plan.get('plan_id') != fingerprint(plan['identity']):
        raise ValueError('UPDATE_IDENTITY')
    entries = plan['entries']
    if len(entries) != 4 or {r['destination'] for r in entries} != TARGETS:
        raise ValueError('EXACT_FOUR_TARGETS_REQUIRED')
    if set(plan['identity']['targets']) != TARGETS:
        raise ValueError('UPDATE_TARGET_IDENTITY')
    actual = {p.relative_to(package/'game').as_posix() for p in (package/'game').rglob('*') if p.is_file()}
    if actual != TARGETS:
        raise ValueError('PACKAGE_EXTRA_OR_MISSING')
    for r in entries:
        path = target(package, 'game/'+r['destination'])
        if file_hash(path) != r['new_sha256'] or path.stat().st_size != r['new_bytes']:
            raise ValueError('NEW_PAYLOAD_CHANGED')
        if path.stat().st_mtime_ns != r['new_mtime_ns']:
            raise ValueError('FINGERPRINT_METADATA_CHANGED')
        if r['current_sha256'] == r['new_sha256']:
            raise ValueError('UNCHANGED_TARGET')


def preflight(plan, package, game, parent_receipt, parent_sha):
    check_plan(plan, package)
    if file_hash(parent_receipt) != parent_sha or parent_sha != plan['identity']['parent_receipt_sha256']:
        raise ValueError('PARENT_RECEIPT_CHANGED')
    if json.loads(parent_receipt.read_text())['entries'] != plan['current_install_entries']:
        raise ValueError('PARENT_ENTRY_SET_CHANGED')
    for r in plan['current_install_entries']:
        path = target(game, r['destination'])  # rejects any hardlink/reparse
        if file_hash(path) != r['sha256'] or path.stat().st_size != r['bytes']:
            raise ValueError('CURRENT_INSTALL_CHANGED')
    old = {r['destination']:r for r in plan['current_install_entries']}
    for r in plan['entries']:
        if r['current_sha256'] != old[r['destination']]['sha256']:
            raise ValueError('CURRENT_HASH_BINDING')
    return {'status':'UPDATE_FILES_PREFLIGHT_PASS', 'files':4,
            'requires_external_checks':['game_server_closed','post_close_originals_LOCAL_shadow', 'verified_new_backup'],
            'executed':False}


def verify_updated(plan, plan_sha, receipt, game):
    if (receipt.get('format')!='aic_patch_update_receipt_v1' or receipt.get('status')!='UPDATED'
            or receipt.get('executed') is not True or receipt.get('plan_id')!=plan['plan_id']
            or receipt.get('update_plan_sha256')!=plan_sha
            or receipt.get('parent_receipt_sha256')!=plan['identity']['parent_receipt_sha256']):
        raise ValueError('UPDATE_RECEIPT_NOT_EXECUTED_OR_MISMATCH')
    changes={r['destination']:r for r in plan['entries']}
    for row in plan['current_install_entries']:
        name=row['destination'];new=changes.get(name)
        path=target(game,name)
        if file_hash(path)!=(new['new_sha256'] if new else row['sha256']):
            raise ValueError('UPDATED_INSTALL_HASH_MISMATCH')
        if path.stat().st_size!=(new['new_bytes'] if new else row['bytes']):
            raise ValueError('UPDATED_INSTALL_SIZE_MISMATCH')
    return True


def rollback_plan(plan, game, backup):
    """File-only dry-run. Never authorizes deleting or reusing a runtime shadow."""
    operations=[]
    for r in plan['entries']:
        dest=target(game,r['destination']); saved=target(backup,r['destination'])
        if file_hash(dest)!=r['new_sha256'] or file_hash(saved)!=r['current_sha256']:
            raise ValueError('ROLLBACK_HASH_MISMATCH')
        operations.append({'path':r['destination'],'action':'RESTORE_VERIFIED_PRE_UPDATE_BYTES_AND_MTIME',
                           'only_if_sha256':r['new_sha256'],'restore_sha256':r['current_sha256']})
    return {'status':'FILE_RESTORE_DRY_RUN_PASS','operations':operations,'executed':False,
            'shadow_policy':'PRESERVE; REQUIRE_FRESH_ATTRIBUTION_BEFORE_ANY_CLEANUP_OR_NEXT_START',
            'full_live_rollback_ready':False,'spawn_ready':False}
