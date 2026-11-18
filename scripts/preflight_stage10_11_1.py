"""Pinned closed-game preflight for a planned continuation; never connects."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.integrated_deployment import read_pinned
from companion.experimental_install_check import verify
from companion.experimental_wait import verify_history
from companion.patch_update_transaction import snapshot,verify_backup
from scripts.prepare_phase_d_backup import GAME,SAVES,live

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--plan',type=Path,required=True)
    ap.add_argument('--sha256',required=True)
    args=ap.parse_args();live()
    plan=read_pinned(args.plan,args.sha256)
    if plan['format']!='aic_probe_continuation_v1':raise ValueError('PLAN_FORMAT')
    binding=verify(ROOT/'dist/stage10_11_first_spawn_0_1_0',
        '6ecc792b6c320dc19f0fa201259c573efd142c4c37a579eab07376dc40b9e1e3',
        ROOT/'compatibility/experiments/stage10_11/installation/receipt.json',
        plan['installation_receipt_sha256'],ROOT)
    baseline=read_pinned(Path(plan['baseline_path']),plan['baseline_sha256'])
    backup=Path(plan['backup_path']);bm=read_pinned(backup/'manifest.json',plan['backup_manifest_sha256'])
    expected={'saves/'+n:(r['sha256'],r['size']) for n,r in baseline['saves'].items()}
    if {r['relative']:(r['sha256'],r['bytes']) for r in bm['files']}!=expected:
        raise ValueError('BACKUP_BASELINE_MISMATCH')
    verify_backup(backup,bm)
    journal=ROOT/'runtime/stage10_11/experiments'/binding['key']
    verify_history(journal,plan['history'],plan['attempt'])
    if (journal/plan['attempt']/'probe.json').exists():raise ValueError('NEW_PROBE_ALREADY_STARTED')
    if (GAME/'emf/mods/aic_first_spawn/attempt.lock').read_bytes()!=('UNUSED:'+binding['key']).encode():
        raise ValueError('LATCH_NOT_UNUSED')
    print('Pinned plan/installed23/backup23/history PASS; checking current baseline',flush=True)
    if dict(game=snapshot(GAME),saves=snapshot(SAVES))!=baseline:raise ValueError('BASELINE_CHANGED')
    live()
    print('OFFLINE_PREFLIGHT_PASS; manual game start and new experiment require separate authorization; spawn_ready=false')

if __name__=='__main__':main()
