"""Future authorized recovery. Defaults to dry-run; no install/restore/game launch."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from companion.compatibility import file_hash, load_profile
from companion.recovery import (RecoveryError, validate_manifest, create_backup, verify_backup,
                                quarantine, clean_baseline, steam_identity)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('operation', choices=['dry-run', 'backup', 'verify-backup', 'quarantine', 'evaluate'])
    ap.add_argument('--plan', type=Path, required=True)
    ap.add_argument('--plan-sha256', required=True, help='Reviewed raw plan hash, supplied separately')
    ap.add_argument('--backup', type=Path)
    ap.add_argument('--destination', type=Path)
    ap.add_argument('--execute', action='store_true')
    ap.add_argument('--authorization', choices=['PHASE_B_BACKUP', 'PHASE_B_QUARANTINE'])
    args = ap.parse_args()
    if file_hash(args.plan) != args.plan_sha256:
        raise RecoveryError('PLAN_HASH_MISMATCH')
    plan = json.loads(args.plan.read_text(encoding='utf-8'))
    if args.operation == 'evaluate':
        print(json.dumps(clean_baseline(plan), indent=2))
        return
    roots = {k: Path(v) for k, v in plan['roots'].items()}

    def live():
        # Failure of enumeration is NOT an empty process list.
        result = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command',
            "$ErrorActionPreference='Stop'; @(Get-Process | Where-Object { $_.ProcessName -in @('enshrouded','enshrouded_server') }).Count"],
            capture_output=True, text=True, check=True, timeout=20)
        if result.stdout.strip() != '0':
            raise RecoveryError('GAME_NOT_CONFIRMED_STOPPED')
        profile = load_profile(1287369)
        sha = file_hash(roots['game'] / 'enshrouded.exe')
        if sha != profile['exe_sha256']:
            raise RecoveryError('BUILD_MISMATCH')
        identity={k: profile[k] for k in ('game_build', 'exe_sha256', 'steam_build_id')}
        identity.update(steam_identity(Path(plan['steam_manifest_path'])))
        return dict(identity=identity,
                    stopped=True, receipt_sha256=file_hash(Path(plan['receipt_path'])))

    if args.operation == 'verify-backup':
        if args.backup is None:
            ap.error('--backup is required')
        verify_backup(plan, args.backup)
        print('BACKUP_VERIFIED')
        return
    validate_manifest(plan, roots, **live())
    if not args.execute or args.operation == 'dry-run':
        print(json.dumps({'status': 'DRY_RUN_VALID', 'cleanup_executed': False,
                          'unresolved': sum(e['proposed_action'] in ('UNKNOWN', 'MANUAL_REVIEW') for e in plan['entries'])}))
        return
    if args.destination is None:
        ap.error('--destination is required')
    if args.operation == 'backup' and args.authorization == 'PHASE_B_BACKUP':
        create_backup(plan, roots, args.destination, authorize=True, preflight=live)
        print('BACKUP_VERIFIED')
    elif args.operation == 'quarantine' and args.authorization == 'PHASE_B_QUARANTINE' and args.backup:
        count = quarantine(plan, roots, args.backup, args.destination, authorize=True, preflight=live)
        print(json.dumps({'quarantined': count}))
    else:
        raise RecoveryError('EXPLICIT_OPERATION_AUTHORIZATION_REQUIRED')


if __name__ == '__main__':
    main()
