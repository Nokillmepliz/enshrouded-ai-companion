"""Explicit local console experiment. No game launch, install, cleanup or retry."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.experimental_install_check import verify
from companion.experimental_wait import ContinuationClient,verify_history
from companion.integrated_deployment import read_pinned
from companion.patch_update_transaction import verify_backup
from companion.interactive_spawn import WindowsKeyboard,run_interactive
from companion.transport import connect

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--plan',type=Path,required=True)
    ap.add_argument('--sha256',required=True)
    ap.add_argument('--pid',type=int,required=True)
    args=ap.parse_args()
    if args.pid<=0:ap.error('Positive current game PID required')
    keyboard=WindowsKeyboard()  # Reject pipes before opening a bridge or recording a probe.
    plan=read_pinned(args.plan,args.sha256)
    if plan.get('format')!='aic_probe_continuation_v1' or plan.get('confirmation_mode')!='local_key_after_ready':
        raise ValueError('LOCAL_INTERACTIVE_PLAN_REQUIRED')
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
    game=Path(json.loads((ROOT/'dist/stage10_11_first_spawn_0_1_0/exact-install-manifest.json').read_text())['game'])
    if (game/'emf/mods/aic_first_spawn/attempt.lock').read_bytes()!=('UNUSED:'+binding['key']).encode():
        raise ValueError('LATCH_NOT_UNUSED')
    if (journal/plan['attempt']/'interactive-started.json').exists():raise ValueError('INTERACTIVE_ALREADY_STARTED')
    t=connect(pid=args.pid)
    try:
        client=ContinuationClient(t,binding,journal,plan)
        if client.context()['pid']!=args.pid:raise ValueError('PID_CHANGED')
        result=run_interactive(client,keyboard,output=lambda text:print(text,flush=True))
        # Avoid printing session tokens/private bindings; full reply stays in the journal.
        print('Результат:',result['status'])
        reply=result.get('reply',{})
        if reply:print('Состояние:',reply.get('state'),'entity:',reply.get('entity'),'визуальная проверка ещё не выполнена.')
        print('Повторов нет. Сохраните терминал и сообщите результат. Журнал сохранён локально в runtime.')
    finally:t.close()

if __name__=='__main__':
    try:main()
    except (Exception,KeyboardInterrupt) as exc:
        print('ОСТАНОВЛЕНО:',str(exc) or type(exc).__name__,'— не повторяйте команду.',file=sys.stderr)
        sys.exit(1)
