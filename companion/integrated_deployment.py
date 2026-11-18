"""Exact candidate/receipt verification and rollback planning, without writes."""
import json
from pathlib import Path

from .compatibility import file_hash, fingerprint
from .recovery import measure, no_links, target


def read_pinned(path, sha):
    no_links(path)
    if file_hash(path) != sha:
        raise ValueError('PINNED_DOCUMENT_CHANGED')
    return json.loads(path.read_text(encoding='utf-8'))


def validate_plan(plan, package):
    if plan.get('format') != 'aic_integrated_install_v1' or plan.get('build') != 1287369:
        raise ValueError('UNSUPPORTED_PLAN')
    if fingerprint(plan['identity']) != plan['plan_id']:
        raise ValueError('PLAN_IDENTITY_CHANGED')
    allowed = plan['identity']['targets']
    paths = [r['destination'] for r in plan['entries']]
    if len(paths) != len(set(p.casefold() for p in paths)) or sorted(paths) != sorted(allowed):
        raise ValueError('EXACT_TARGET_SET')
    for row in plan['entries']:
        if row['before_sha256'] is not None or row['rollback'] != 'REMOVE_ONLY_IF_INSTALLED_HASH_MATCHES':
            raise ValueError('UNEXPECTED_REPLACE_OR_RESTORE')
        if row['source'] != 'game/' + row['destination']:
            raise ValueError('SOURCE_DESTINATION_BINDING')
        if measure(target(package, row['source'])) != {'sha256': row['sha256'], 'size': row['bytes']}:
            raise ValueError('PACKAGE_HASH_CHANGED')
    actual = {p.relative_to(package / 'game').as_posix() for p in (package / 'game').rglob('*') if p.is_file()}
    if actual != set(paths):
        raise ValueError('UNREVIEWED_PACKAGE_FILE')
    return plan


def preinstall(plan, package, game, baseline):
    validate_plan(plan, package)
    if fingerprint(baseline) != plan['identity']['baseline_sha256']:
        raise ValueError('WRONG_BASELINE')
    for row in plan['entries']:
        if target(game, row['destination']).exists():
            raise ValueError('DESTINATION_CONFLICT:' + row['destination'])
    # Exact original inventory, including preserved residues; no deleting extras.
    actual = {p.relative_to(game).as_posix() for p in game.rglob('*') if p.is_file()}
    if actual != set(baseline['game']):
        raise ValueError('BASELINE_FILE_SET_CHANGED')
    for name, row in baseline['game'].items():
        if measure(target(game, name)) != {'sha256': row['sha256'], 'size': row['bytes']}:
            raise ValueError('ORIGINAL_CHANGED:' + name)
    return {'status': 'PREINSTALL_PASS', 'targets_absent': len(plan['entries']), 'spawn_ready': False}


def installed(plan, plan_sha, receipt, game):
    if (receipt.get('format') != 'aic_integrated_receipt_v1' or receipt.get('status') != 'INSTALLED'
            or receipt.get('plan_sha256') != plan_sha or receipt.get('plan_id') != plan['plan_id']
            or receipt.get('build') != 1287369 or receipt.get('entries') != plan['entries']):
        raise ValueError('RECEIPT_IDENTITY_OR_FILE_SET')
    for row in plan['entries']:
        if measure(target(game, row['destination'])) != {'sha256': row['sha256'], 'size': row['bytes']}:
            raise ValueError('INSTALLED_HASH_MISMATCH:' + row['destination'])
    return True


def rollback_dry_run(plan, plan_sha, receipt, game):
    installed(plan, plan_sha, receipt, game)
    # Runtime shadow cleanup needs a fresh, separately reviewed audit. Do not
    # recursively remove a directory whose contents are generated at runtime.
    shadow = target(game, 'emf/content/client')
    if shadow.exists():
        raise ValueError('SHADOW_REQUIRES_FRESH_ATTRIBUTION_AND_LINK_AUDIT')
    return {'status': 'ROLLBACK_DRY_RUN_PASS', 'executed': False,
            'operations': [{'path': r['destination'], 'action': r['rollback'], 'sha256': r['sha256']}
                           for r in reversed(plan['entries'])],
            'resource_restore': False, 'save_restore': False, 'unknown_files_removed': False,
            'spawn_ready': False}
