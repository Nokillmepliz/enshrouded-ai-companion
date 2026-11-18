"""Explicit search or local interactive spawn; requires separately installed 0.1.1."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.integrated_deployment import read_pinned
from companion.smart_deployment import verify, PREFIX
from companion.smart_position import SmartPositionClient
from companion.experimental_wait import wait_ready
from companion.interactive_spawn import WindowsKeyboard,run_interactive
from companion.transport import connect
from companion.recovery import target


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--plan',required=True,type=Path)
    ap.add_argument('--sha256',required=True)
    ap.add_argument('--receipt',required=True,type=Path)
    ap.add_argument('--receipt-sha256',required=True)
    ap.add_argument('--pid',required=True,type=int)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--search-only',action='store_true')
    mode.add_argument('--interactive',action='store_true')
    mode.add_argument('--settle-only',action='store_true')
    args=ap.parse_args()
    if args.pid<=0:ap.error('Positive current PID required')
    keyboard=WindowsKeyboard() if args.interactive else None
    plan=read_pinned(args.plan,args.sha256)
    if (plan.get('format')!='aic_smart_position_plan_v1'
            or plan.get('confirmation_mode')!='local_key_after_ready'):
        raise ValueError('SMART_LOCAL_PLAN_REQUIRED')
    binding,game=verify(plan,args.receipt,args.receipt_sha256)
    journal=ROOT/'runtime/stage10_11/experiments'/binding['key']
    def unused():return target(game,PREFIX+'attempt.lock').read_bytes()==('UNUSED:'+binding['key']).encode()
    transport=connect(pid=args.pid)
    try:
        client=SmartPositionClient(transport,binding,journal,plan['history'],unused)
        if client.context()['pid']!=args.pid:raise ValueError('PID_CHANGED')
        if args.settle_only:
            client.settle_search()
            print('История закрыта: очередь завершена, spawn intent отсутствует. Новый поиск только отдельной командой.')
            return
        client.open_search()
        try:
            if args.interactive:
                result=run_interactive(client,keyboard,output=lambda s:print(s,flush=True))
            else:
                client.prepare();result=wait_ready(client)
            print('Результат:',result['status'])
            if args.search_only:print('Позиция:',result.get('position'),'— spawn не разрешён этим режимом.')
            if client.intent_file.exists():
                print('Spawn intent сохранён. Повтор запрещён, результат требует визуальной проверки.')
        finally:
            if not client.intent_file.exists():
                # Read-only status only: no stop/reset/new probe and no background retry.
                try:
                    client.settle_search()
                    print('История поиска сохранена. Следующий поиск возможен только явно, без автоматического повтора.')
                except Exception as exc:
                    print('Поиск НЕ закрыт:',str(exc),'Новый поиск заблокирован; требуется --settle-only после завершения очереди.')
    finally:transport.close()

if __name__=='__main__':
    try:main()
    except (Exception,KeyboardInterrupt) as exc:
        print('ОСТАНОВЛЕНО:',str(exc) or type(exc).__name__,file=sys.stderr)
        sys.exit(1)
