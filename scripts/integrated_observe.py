"""Future authorized load-only diagnostics. Explicit live flag, no launch/install."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.integrated_client import IntegratedClient
from companion.integrated_deployment import read_pinned, installed, validate_plan
from companion.integrated_update import check_plan, verify_updated
from companion.integrated_evidence import verdict
from companion.transport import connect
from companion.recovery import no_links


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command',choices=['status','inspect','compare'])
    ap.add_argument('--package',type=Path,required=True)
    ap.add_argument('--game',type=Path,required=True)
    ap.add_argument('--receipt',type=Path,required=True)
    ap.add_argument('--receipt-sha256',required=True)
    ap.add_argument('--live-read-only',action='store_true')
    ap.add_argument('--patch-0-5-1',action='store_true',help='Use separately approved update manifest/receipt')
    args=ap.parse_args()
    if not args.live_read_only: ap.error('Explicit future load-only authorization required: --live-read-only')
    if args.patch_0_5_1:
        public=json.loads((ROOT/'compatibility/updates/1287369/0.5.1/update-manifest.json').read_text())
        plan=read_pinned(args.package/'update-plan.json',public['update_plan_sha256'])
        check_plan(plan,args.package)
        binding=read_pinned(args.package/'bridge-binding.json',public['bridge_binding_sha256'])
        receipt=read_pinned(args.receipt,args.receipt_sha256)
        verify_updated(plan,public['update_plan_sha256'],receipt,args.game)
    else:
        public=json.loads((ROOT/'compatibility/migration/1287369/exact-install-manifest.json').read_text())
        plan=read_pinned(args.package/'install-plan.json',public['plan_sha256'])
        validate_plan(plan,args.package)
        binding=read_pinned(args.package/'bridge-binding.json',public['bridge_binding_sha256'])
        receipt=read_pinned(args.receipt,args.receipt_sha256)
        installed(plan,public['plan_sha256'],receipt,args.game)
    transport=connect(game=str(args.game))
    try:
        text=None
        if args.command!='status':
            path=args.game/'emf/content.log'; no_links(path)
            with path.open('rb') as stream: raw=stream.read(8*1024*1024+1)
            if len(raw)>8*1024*1024: raise ValueError('LOG_SIZE_LIMIT')
            text=raw.decode('utf-8')
        result=IntegratedClient(transport,binding).observe(args.command,evidence_text=text)
        result['verdict']=verdict(result['evidence'],{})
        print(json.dumps(result,ensure_ascii=False,indent=2))
    finally:
        transport.close()


if __name__=='__main__': main()
