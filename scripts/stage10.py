"""Read-only Stage 10.1 preflight and collected-artifact evaluator."""

import argparse
import json
from pathlib import Path

from companion.stage10 import (
    Stage10Error, detect_game_process, evaluate_load_only, preflight, verify_backup,
)


DEFAULT_GAME = r"D:\SteamLibrary\steamapps\common\Enshrouded"
DEFAULT_EML = r"runtime\stage10\downloads\dbghelp.dll"


def _text(path: str | None) -> str | None:
    return Path(path).read_text(encoding="utf-8", errors="replace") if path else None


def _json(path: str | None) -> dict | None:
    if not path:
        return None
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Stage10Error(f"json_object_required:{path}")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    prepare = commands.add_parser("preflight", help="read-only installation preflight")
    prepare.add_argument("--game", default=DEFAULT_GAME)
    prepare.add_argument("--eml", default=DEFAULT_EML)
    prepare.add_argument("--backup-manifest")
    prepare.add_argument("--install-receipt", default=r"runtime\stage10\install-receipt.json")

    evaluate = commands.add_parser("evaluate", help="evaluate already collected artifacts")
    evaluate.add_argument("--eml-log")
    evaluate.add_argument("--evidence")
    evaluate.add_argument("--emf-log")
    evaluate.add_argument("--observer-results")
    evaluate.add_argument("--bridge-diagnostics")
    evaluate.add_argument("--game-load-report")
    evaluate.add_argument("--backup-manifest")
    evaluate.add_argument("--integrity-report")
    evaluate.add_argument("--install-receipt")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "preflight":
            result = preflight(
                args.game, args.eml, "experimental/eml_humanoid", "mods/aic_template_observer",
                expected_game_dir=DEFAULT_GAME,
                game_running=detect_game_process(),
                backup_manifest=args.backup_manifest,
                receipt_path=args.install_receipt,
            )
        else:
            result = evaluate_load_only(
                eml_log=_text(args.eml_log),
                evidence_text=_text(args.evidence),
                emf_log=_text(args.emf_log),
                observer_results=_json(args.observer_results),
                bridge_diagnostics=_json(args.bridge_diagnostics),
                game_load_report=_json(args.game_load_report),
                backup_verified=(
                    verify_backup(args.backup_manifest) if args.backup_manifest else None
                ),
                integrity_report=_json(args.integrity_report),
                install_receipt=_json(args.install_receipt),
            )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, Stage10Error, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "mode": args.command, "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
