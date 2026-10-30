"""Stage 10 preflight. Read-only and dry-run by default."""

import argparse
import json
from pathlib import Path

from companion.stage10 import Stage10Error, detect_game_process, preflight


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", default=r"D:\SteamLibrary\steamapps\common\Enshrouded")
    parser.add_argument("--eml", default=r"runtime\stage10\downloads\dbghelp.dll")
    args = parser.parse_args()
    try:
        result = preflight(
            args.game, args.eml, "experimental/eml_humanoid", "mods/aic_template_observer",
            expected_game_dir=r"D:\SteamLibrary\steamapps\common\Enshrouded",
            game_running=detect_game_process(),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, Stage10Error, ValueError) as exc:
        print(json.dumps({"ok": False, "mode": "dry_run", "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
