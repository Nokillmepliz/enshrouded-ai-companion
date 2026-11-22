"""Explicit local movement confirmation; discovery/status remain read-only."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from companion.movement import MovementClient, manual_move
from companion.transport import connect
from companion.recovery import write_json_new

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--mod-version',choices=['0.1.0','0.1.1'])
    parser.add_argument('command', choices=['discover', 'status', 'move_to'])
    args = parser.parse_args()
    version=args.mod_version or ('0.1.1' if args.command=='move_to' else '0.1.0')
    if args.command=='move_to' and version!='0.1.1':
        parser.error('move_to requires reviewed mod 0.1.1')
    try:
        if args.command=='move_to' and not sys.stdin.isatty():
            raise ValueError('INTERACTIVE_CONSOLE_REQUIRED')
        client = MovementClient(connect(pid=args.pid),version=version)
        if args.command=='move_to':
            run=Path(__file__).resolve().parents[1]/'runtime/stage10_12/first-movement'
            result=manual_move(client,run/'movement-intent.json')
            if (run/'movement-intent.json').exists():write_json_new(run/'result.json',result)
        else:
            result=getattr(client,args.command)()
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (Exception,KeyboardInterrupt) as exc:
        print('STOPPED; no automatic retry/cancel: '+str(exc),file=sys.stderr)
        sys.exit(1)
