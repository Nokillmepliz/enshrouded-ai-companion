"""Read-only entry point. Movement is a separately gated library prototype."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from companion.movement import MovementClient
from companion.transport import connect

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('command', choices=['discover', 'status'])
    args = parser.parse_args()
    client = MovementClient(connect(pid=args.pid))
    print(json.dumps(getattr(client, args.command)(), ensure_ascii=False, indent=2))
