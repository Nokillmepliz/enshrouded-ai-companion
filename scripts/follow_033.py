"""Launch only after separate installation/runtime approval and manual game start."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.follow import FollowClient, run
from companion.transport import connect
from companion.compatibility import file_hash
from companion.integrated_deployment import read_pinned
from companion.recovery import no_links


def preflight(plan, game):
    for row in plan['effective_files']:
        p=game/row['path'];no_links(p)
        if file_hash(p)!=row['sha256']: raise ValueError('INSTALLED_FILE_MISMATCH:'+row['path'])
    for row in plan['preserved_intents']:
        p=ROOT/row['path'];no_links(p)
        if file_hash(p)!=row['sha256']: raise ValueError('PREVIOUS_INTENT_CHANGED')
    # Reads only; verifies SPENT and historical spawn intent exists.
    from scripts.install_companion_discovery import history
    if history()!=plan['spawn_history']: raise ValueError('SPAWN_HISTORY_CHANGED')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--pid',type=int,required=True)
    ap.add_argument('--manifest-sha256',required=True)
    ap.add_argument('--authorized-session',action='store_true')
    args=ap.parse_args()
    if not args.authorized_session: ap.error('Separate runtime authorization required')
    plan=read_pinned(ROOT/'compatibility/experiments/movement_0_3_3/exact-update-manifest.json',args.manifest_sha256)
    from scripts.prepare_phase_d_backup import GAME
    if file_hash(GAME/'enshrouded.exe')!=plan['exe_sha256']:raise ValueError('SLEEP_BUILD_MISMATCH')
    preflight(plan,GAME)
    from scripts.install_follow_stage16 import MANIFEST_SHA, RUN
    if args.manifest_sha256!=MANIFEST_SHA:raise ValueError('UNREVIEWED_MANIFEST')
    import json
    receipt=json.loads((RUN/'receipt.json').read_text(encoding='utf-8'))
    if receipt.get('status')!='INSTALLED_READY_FOR_MANUAL_START' or receipt.get('manifest_sha256')!=MANIFEST_SHA:
        raise ValueError('INSTALL_RECEIPT_REQUIRED')
    result=run(FollowClient(connect(pid=args.pid),version='0.3.3'),ROOT/'runtime/movement_0_3_3/test-session.jsonl',plan['token'])
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
