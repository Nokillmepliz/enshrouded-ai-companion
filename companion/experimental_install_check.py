"""Read-only gate for the future separately approved additive installation."""
from pathlib import Path

from .compatibility import file_hash
from .integrated_deployment import read_pinned
from .integrated_update import verify_updated, check_plan
from .patch_update_transaction import verify_backup
from .recovery import no_links


def verify(package, manifest_sha, receipt_path, receipt_sha, root):
    manifest = read_pinned(package/'exact-install-manifest.json', manifest_sha)
    if manifest.get('format') != 'aic_stage10_11_additive_install_v1':
        raise ValueError('INSTALL_MANIFEST_FORMAT')
    receipt = read_pinned(receipt_path, receipt_sha)
    if (receipt.get('format') != 'aic_experiment_receipt_v1' or receipt.get('status') != 'INSTALLED'
            or receipt.get('manifest_sha256') != manifest_sha or receipt.get('entries') != manifest['entries']):
        raise ValueError('VERIFIED_INSTALL_RECEIPT_REQUIRED')
    binding = read_pinned(package/'client-binding.json', manifest['client_binding_sha256'])
    game = Path(manifest['game'])
    for row in manifest['entries']:
        path = game/row['path'];no_links(path)
        if row['path'] == manifest['runtime_mutable_file']['path']:
            if path.read_bytes() not in [(s+binding['key']).encode() for s in ('UNUSED:', 'SPENT!:')]:
                raise ValueError('INVALID_LATCH')
        elif file_hash(path) != row['sha256'] or path.stat().st_size != row['bytes']:
            raise ValueError('INSTALLED_FILE_CHANGED')
    bp = root/'compatibility/experiments/stage10_11/backup-plan.json'
    backup_plan = read_pinned(bp, manifest['backup_plan_sha256'])
    backup = Path(receipt['backup_path'])
    bm = read_pinned(backup/'manifest.json', receipt['backup_manifest_sha256'])
    expected = {r['group']+'/'+r['path']: (r['sha256'], r['bytes']) for r in backup_plan['files']}
    actual = {r['relative']: (r['sha256'], r['bytes']) for r in bm['files']}
    if actual != expected:
        raise ValueError('WRONG_SAVE_BACKUP')
    verify_backup(backup, bm)
    old = root/'compatibility/updates/1287369/0.5.1'
    approved = read_pinned(old/'update-manifest.json', 'a6ef7bd5714353b8b6a3da7354baff4581de7effb1f9409fab4b5f983ac4bdf4')
    prior_package = Path(approved['local_package'])
    plan = read_pinned(prior_package/'update-plan.json', approved['update_plan_sha256'])
    check_plan(plan, prior_package)
    prior_receipt = read_pinned(old/'installation/receipt.json', manifest['prior_receipt_sha256'])
    verify_updated(plan, approved['update_plan_sha256'], prior_receipt, game)
    return binding
