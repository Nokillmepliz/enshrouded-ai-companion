"""Closed read-only preflight after the pinned 0.1.1 installation."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.integrated_deployment import read_pinned
from companion.smart_deployment import verify
from companion.experimental_wait import verify_history
from companion.patch_update_transaction import snapshot
from scripts.prepare_phase_d_backup import GAME,SAVES,live

def main():
    live()
    plan=read_pinned(ROOT/'runtime/stage10_11_3/smart-position-plan.json',
        'd137680beff2ccc68fedefd87617202075a1d367407ddd34096ae43537d6647c')
    receipt_path=ROOT/'compatibility/experiments/stage10_11_3/installation/receipt.json'
    digest='d973898fbd447f274fbf2365a9146d1b193a01413677d253fbcfbfc0da338485'
    receipt=read_pinned(receipt_path,digest)
    binding,_=verify(plan,receipt_path,digest)
    verify_history(ROOT/'runtime/stage10_11/experiments'/binding['key'],plan['history'],'unused-placeholder')
    baseline=read_pinned(Path(receipt['post_install_baseline_path']),receipt['post_install_baseline_sha256'])
    if dict(game=snapshot(GAME),saves=snapshot(SAVES))!=baseline:raise ValueError('POST_INSTALL_BASELINE_CHANGED')
    live();print('CLOSED_PREFLIGHT_PASS: installed23, backup27, baseline245/23, history75, UNUSED; runtime NOT RUN')

if __name__=='__main__':main()
