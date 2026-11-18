"""Read-only load-only checkpoint using existing update and inventory validators."""
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from companion.compatibility import file_hash
from companion.integrated_deployment import read_pinned
from companion.integrated_update import check_plan, verify_updated, rollback_plan, input_fingerprint
from companion.patch_update_transaction import snapshot, verify_backup
from companion.clean_backup import verify as verify_clean
from companion.recovery import write_json_new
from scripts.prepare_phase_d_backup import GAME, SAVES, live


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage10-10-3',action='store_true',help='Use the verified latest post-close baseline and preserve historical checkpoints')
    args=ap.parse_args()
    live()
    public = ROOT/'compatibility/updates/1287369/0.5.1'
    approved = read_pinned(public/'update-manifest.json', 'a6ef7bd5714353b8b6a3da7354baff4581de7effb1f9409fab4b5f983ac4bdf4')
    package = Path(approved['local_package'])
    plan = read_pinned(package/'update-plan.json', approved['update_plan_sha256'])
    check_plan(plan, package)
    binding = read_pinned(package/'bridge-binding.json', approved['bridge_binding_sha256'])
    read_pinned(public/'profile.json', plan['identity']['profile_sha256'])
    if binding['plan_id'] != plan['plan_id'] or binding['profile_sha256'] != plan['identity']['profile_sha256']:
        raise ValueError('BINDING_CHANGED')
    receipt_sha = '8fa2fa02ef0ad12b5c3c00864c0e81f21803fc2851872a708dea4e4d8efd2053'
    receipt = read_pinned(public/'installation/receipt.json', receipt_sha)
    verify_updated(plan, approved['update_plan_sha256'], receipt, GAME)
    read_pinned(ROOT/'compatibility/migration/1287369/phase_e/install-receipt.json', receipt['parent_receipt_sha256'])
    backup = Path(receipt['backup_path'])
    manifest = read_pinned(backup/'manifest.json', receipt['verified_backup_manifest_sha256'])
    verify_backup(backup, manifest)
    if len(manifest['files']) != 38: raise ValueError('BACKUP_COUNT_CHANGED')
    verify_clean(ROOT/'runtime/backups/stage10-10-1-clean-20261118', 'd671fd038634433b3400682e0b0f7e513a854111b3ca96e123e76b1d1e59250a')
    rollback = rollback_plan(plan, GAME, backup/'payload/game')
    print('CLOSED/BUILD/PACKAGE/RECEIPT16/BACKUP38/CLEAN27/DRY_RUN4 PASS; hashing baseline', flush=True)
    prior = Path(receipt['per_file_before_after_journal']).parent/'after.json'
    baseline=None
    if args.stage10_10_3:
        reviewed=read_pinned(public/'stage10_10_3/result.json','24c962649a56e891d6b9b4bc93ea3e3b89552fc9ae2805095ed9db10c5a71cb9')
        if reviewed['shadow_readback']['status']!='PASS' or reviewed['shadow_filesystem']!='PASS':
            raise ValueError('REVIEWED_SHADOW_NOT_VALIDATED')
        prior=ROOT/'runtime/stage10_10_3/after.json'
        baseline=read_pinned(prior,'9bb5ef6895915469d1e35a302b2071f2037348049f4f07e0178c39a3237ae904')
    before = dict(game=snapshot(GAME), saves=snapshot(SAVES))
    if before != (baseline if baseline is not None else json.loads(prior.read_text())):
        raise ValueError('REVIEWED_BASELINE_CHANGED')
    fp = input_fingerprint(before['game'], '0.5.1')
    if fp != plan['projected_fingerprint'] or fp != receipt['actual_content_fingerprint']:
        raise ValueError('FINGERPRINT_CHANGED')
    selection = []
    for relative, name in [('default/character0.ksd', 'Body Test'), ('default/world0.ksd', 'AI Body Test')]:
        if (SAVES/relative).read_bytes().count(name.encode()) != 1:
            raise ValueError('LOCAL_NAME_NOT_CONFIRMED')
        selection.append(dict(path=relative, name=name, slot=1, storage='LOCAL',
            sha256=before['saves'][relative]['sha256'], runtime_identity='REQUIRES_BRIDGE_AFTER_LOAD'))
    live()
    now = datetime.now(timezone.utc)
    run = ROOT/('runtime/stage10_10_3/load_only' if args.stage10_10_3 else 'runtime/stage10_10_2/load_only')/now.strftime('%Y%m%dT%H%M%S%fZ')
    run.mkdir(parents=True, exist_ok=False)
    write_json_new(run/'inventory-before.json', before)
    write_json_new(run/'rollback-before.json', rollback)
    result = dict(status='READY_FOR_MANUAL_START', checked_utc=now.isoformat(), run_path=str(run),
        installed_files_verified=16, backup_verified=38, clean_backup_verified=27,
        game_inventory=len(before['game']), original_resources=67,
        shadow_inventory=sum(n.startswith('emf/content/client/') for n in before['game']), LOCAL_files=len(before['saves']),
        inventory_before_sha256=file_hash(run/'inventory-before.json'), receipt_sha256=receipt_sha,
        content_fingerprint=fp, local_selection=selection, rollback_dry_run='PASS4_NOT_EXECUTED',
        shadow_state=('VERIFIED_0.5.1_SUCCESS_CACHE_PRESERVED' if args.stage10_10_3 else 'PRESERVED_FAILED_0.5.0; NATIVE_REBUILD_PENDING'),
        reviewed_baseline_sha256=file_hash(prior),
        runtime_validation='WAITING_FOR_MANUAL_START', game_start_by='USER_ONLY', spawn_ready=False)
    write_json_new(run/'preflight.json', result)
    out = public/('stage10_10_3/load-only' if args.stage10_10_3 else 'load-only');out.mkdir(exist_ok=False)
    write_json_new(out/'preflight.json', result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__': main()
