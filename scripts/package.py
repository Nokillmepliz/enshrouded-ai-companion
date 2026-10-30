"""Package ONLY reviewed adapter sources into dist; never install into a game."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
FILES = ("mod.json", "main.lua", "body.lua", "json.lua")


def build(output=None):
    folder = ROOT / "mods/aic_body"
    manifest = json.loads((folder / "mod.json").read_text(encoding="utf-8"))
    if manifest["enabled"] is not False:
        raise ValueError("Distribution must be disabled by default")
    target = Path(output) if output else ROOT / "dist/aic_body-0.1.0.zip"
    target.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for filename in FILES:
            info = ZipInfo("aic_body/" + filename, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (folder / filename).read_bytes())
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix(".zip.sha256").write_text(f"{digest}  {target.name}\n", encoding="ascii")
    return target


if __name__ == "__main__":
    print(build())
