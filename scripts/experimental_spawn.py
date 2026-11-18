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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=['prepare', 'status', 'spawn', 'observe'])
    ap.add_argument('--package', type=Path, required=True)
    ap.add_argument('--manifest-sha256', required=True)
    ap.add_argument('--receipt', type=Path, required=True)
    ap.add_argument('--receipt-sha256', required=True)
    ap.add_argument('--pid', type=int, required=True)
    ap.add_argument('--live-approved', action='store_true')
    ap.add_argument('--authorization')
    ap.add_argument('--confirm-clear-area', action='store_true')
    ap.add_argument('--accept-disposable-risk', action='store_true')
    args = ap.parse_args()
    if not args.live_approved or args.pid <= 0:
        ap.error('Separate live authorization and current PID required')
    binding = verify(args.package, args.manifest_sha256, args.receipt, args.receipt_sha256, ROOT)
    journal = ROOT/'runtime/stage10_11/experiments'/binding['key']
    transport = connect(pid=args.pid)
    try:
        client = ExperimentalClient(transport, binding, journal)
        if args.command == 'spawn':
            result = client.spawn_once(authorization=args.authorization,
                clear_area=args.confirm_clear_area, disposable_risk=args.accept_disposable_risk)
        else:
            result = getattr(client, args.command)()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        transport.close()


if __name__ == '__main__':
    main()
