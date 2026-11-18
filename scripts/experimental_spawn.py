"""Future authorized experiment commands. Never launches or installs anything."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from companion.experimental_spawn import ExperimentalClient
from companion.experimental_install_check import verify
from companion.transport import connect
from companion.experimental_wait import ContinuationClient, wait_ready
from companion.integrated_deployment import read_pinned
from companion.patch_update_transaction import verify_backup


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=['prepare', 'prepare-wait', 'wait-ready', 'status', 'spawn', 'observe'])
    ap.add_argument('--package', type=Path, required=True)
    ap.add_argument('--manifest-sha256', required=True)
    ap.add_argument('--receipt', type=Path, required=True)
    ap.add_argument('--receipt-sha256', required=True)
    ap.add_argument('--pid', type=int, required=True)
    ap.add_argument('--live-approved', action='store_true')
    ap.add_argument('--authorization')
    ap.add_argument('--confirm-clear-area', action='store_true')
    ap.add_argument('--accept-disposable-risk', action='store_true')
    ap.add_argument('--continuation-plan', type=Path)
    ap.add_argument('--continuation-sha256')
    args = ap.parse_args()
    if not args.live_approved or args.pid <= 0:
        ap.error('Separate live authorization and current PID required')
    binding = verify(args.package, args.manifest_sha256, args.receipt, args.receipt_sha256, ROOT)
    journal = ROOT/'runtime/stage10_11/experiments'/binding['key']
    plan=None
    if bool(args.continuation_plan)!=bool(args.continuation_sha256):
        ap.error('Both pinned continuation arguments required')
    if args.continuation_plan:
        plan=read_pinned(args.continuation_plan,args.continuation_sha256)
        if (plan.get('format')!='aic_probe_continuation_v1'
                or plan['installation_receipt_sha256']!=args.receipt_sha256):
            raise ValueError('CONTINUATION_BINDING')
        baseline=read_pinned(Path(plan['baseline_path']),plan['baseline_sha256'])
        backup=Path(plan['backup_path'])
        bm=read_pinned(backup/'manifest.json',plan['backup_manifest_sha256'])
        expected={'saves/'+n:(r['sha256'],r['size']) for n,r in baseline['saves'].items()}
        if {r['relative']:(r['sha256'],r['bytes']) for r in bm['files']}!=expected:
            raise ValueError('CONTINUATION_BACKUP_BASELINE')
        verify_backup(backup,bm)
    transport = connect(pid=args.pid)
    try:
        client = (ContinuationClient(transport,binding,journal,plan) if plan else
                  ExperimentalClient(transport, binding, journal))
        if client.context()['pid']!=args.pid:raise ValueError('PID_CHANGED')
        if args.command == 'spawn':
            result = client.spawn_once(authorization=args.authorization,
                clear_area=args.confirm_clear_area, disposable_risk=args.accept_disposable_risk)
        elif args.command=='prepare-wait':
            client.prepare()
            result=wait_ready(client)
        elif args.command=='wait-ready':
            result=wait_ready(client)
        else:
            result = getattr(client, args.command)()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        transport.close()


if __name__ == '__main__':
    main()
