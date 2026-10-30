import argparse
import json
import sys

from .client import BodyClient, ClientError
from . import profile


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description="EMF Body Adapter: explicit commands, no automatic spawn")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("profile-init", help="offline: create a stable personality outside the game")
    init.add_argument("--profile", default="runtime/personality.json")
    init.add_argument("--name", default="Спутник")
    for name in ("diagnose", "status", "spawn", "follow", "stay", "dismiss"):
        cmd = commands.add_parser(name)
        target = cmd.add_mutually_exclusive_group(required=True)
        target.add_argument("--game", help="Explicit folder containing enshrouded.exe")
        target.add_argument("--pid", type=int)
        if name == "status":
            cmd.add_argument("--request-id")
        if name in {"spawn", "follow", "stay", "dismiss"}:
            cmd.add_argument("--profile", default="runtime/personality.json")
            cmd.add_argument("--allow-game-mutations", action="store_true")
            cmd.add_argument("--world-slot", type=int, required=True)
            cmd.add_argument("--character-slot", type=int, required=True)
            cmd.add_argument("--character-name", required=True)
            cmd.add_argument("--request-id")
            cmd.add_argument("--timeout", type=float, default=40)
    args = parser.parse_args(argv)
    journal = None
    try:
        from .journal import Journal
        journal = Journal()
        print('Log: ' + str(journal.path), file=sys.stderr)
        journal.emit('invocation', vars(args))
        if args.command == "profile-init":
            result = profile.create(args.profile, args.name)
        else:
            identity = None
            if args.command not in {"diagnose", "status"}:
                # Refuse before even importing/connecting the live transport.
                if not args.allow_game_mutations:
                    raise ClientError("game_mutations_not_authorized")
                identity = profile.load(args.profile)["companion_id"]
            from .transport import connect
            journal.emit('connect_started', {'game': args.game, 'pid': args.pid})
            with connect(game=args.game, pid=args.pid) as bridge:
                journal.emit('connect_succeeded')
                client = BodyClient(bridge, trace=journal.emit)
                if args.command == "diagnose":
                    result = client.diagnose()
                elif args.command == "status":
                    result = client.status(args.request_id)
                else:
                    result = client.execute(args.command, identity, allow_mutations=True,
                                            request_id=args.request_id, world_slot=args.world_slot,
                                            character_slot=args.character_slot, character_name=args.character_name,
                                            timeout=args.timeout)
        journal.emit('completed', result)
        print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, indent=2))
        return 0
    except (ClientError, OSError, ValueError, RuntimeError) as exc:
        if journal:
            journal.emit('failed', {'error': getattr(exc, 'code', type(exc).__name__),
                                    'detail': getattr(exc, 'detail', str(exc))})
        print(json.dumps({"ok": False, "error": getattr(exc, "code", type(exc).__name__),
                          "detail": getattr(exc, "detail", str(exc))}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    finally:
        if journal:
            journal.close()


if __name__ == "__main__":
    raise SystemExit(main())
