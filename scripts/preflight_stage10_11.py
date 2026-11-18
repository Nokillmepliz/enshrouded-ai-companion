"""Read-only closed-game preflight; does not connect to Bridge or spawn."""
import argparse
from datetime import datetime,timezone
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.compatibility import file_hash
from companion.experimental_install import removal_dry_run
from companion.experimental_install_check import verify
from companion.integrated_deployment import read_pinned
from companion.patch_update_transaction import snapshot
from companion.recovery import write_json_new
from scripts.install_stage10_11 import MANIFEST_SHA,PUBLIC
from scripts.prepare_phase_d_backup import live,GAME,SAVES


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--installation-result-sha256',required=True)
    args=ap.parse_args()
    live()
    result=read_pinned(PUBLIC/'installation/result.json',args.installation_result_sha256)
    if result['status']!='INSTALLED_READY_FOR_MANUAL_START_PREFLIGHT':raise ValueError('INSTALL_NOT_COMPLETE')
    m=read_pinned(PUBLIC/'exact-install-manifest.json',MANIFEST_SHA)
    package=Path(m['package'])
    receipt_path=PUBLIC/'installation/receipt.json'
    receipt=read_pinned(receipt_path,result['receipt_sha256'])
    binding=verify(package,MANIFEST_SHA,receipt_path,result['receipt_sha256'],ROOT)
    if (GAME/m['runtime_mutable_file']['path']).read_bytes()!=('UNUSED:'+binding['key']).encode():raise ValueError('LATCH_CONSUMED')
    if (ROOT/'runtime/stage10_11/experiments'/binding['key']).exists():raise ValueError('EXPERIMENT_JOURNAL_ALREADY_EXISTS')
    prior=Path(result['private_evidence'])/'inventory-after.json'
    baseline=read_pinned(prior,result['post_install_inventory_sha256'])
    print('Receipt/installed23/backup23/unused latch PASS; hashing preflight inventory',flush=True)
    now=dict(game=snapshot(GAME),saves=snapshot(SAVES));live()
    if now!=baseline:raise ValueError('POST_INSTALL_BASELINE_CHANGED')
    for rel,name in [('default/character0.ksd','Body Test'),('default/world0.ksd','AI Body Test')]:
        if (SAVES/rel).read_bytes().count(name.encode())!=1:raise ValueError('LOCAL_NAME_CHANGED')
    dry=removal_dry_run(m,receipt,GAME)
    at=datetime.now(timezone.utc)
    private=ROOT/'runtime/stage10_11/preflight'/at.strftime('%Y%m%dT%H%M%S%fZ')
    private.mkdir(parents=True,exist_ok=False)
    write_json_new(private/'inventory.json',now)
    ready=dict(status='READY_FOR_MANUAL_START',checked_utc=at.isoformat(),game_server_closed=True,
        installed_files=23,backup_files=23,originals_unchanged=67,shadow_unchanged=77,LOCAL_unchanged=23,
        inventory_sha256=file_hash(private/'inventory.json'),private_evidence=str(private),
        receipt_path=str(receipt_path),receipt_sha256=result['receipt_sha256'],manifest_sha256=MANIFEST_SHA,
        removal_dry_run=dry['status'],latch='UNUSED',local_character='Body Test',local_world='AI Body Test',slot=1,
        runtime_context='REQUIRES_BRIDGE_AFTER_MANUAL_LOAD',position='NOT_PROBED',spawn_authorized=False,
        experimental_spawn_executed=False,production_spawn_ready=False,spawn_ready=False,RUNTIME_RENDER_CONFIRMED='UNKNOWN')
    write_json_new(private/'preflight.json',ready)
    output=PUBLIC/'installation/preflight'
    output.mkdir(exist_ok=True)
    write_json_new(output/(at.strftime('%Y%m%dT%H%M%S%fZ')+'.json'),ready)
    print(ready,flush=True)


if __name__=='__main__':main()
