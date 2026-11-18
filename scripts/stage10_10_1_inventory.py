"""Read-only Stage 10.10.1 attribution. Does not create a backup or clean files."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from companion.compatibility import file_hash, load_profile
from companion.recovery import write_json_new, steam_identity, no_links
from scripts.stage10_10_snapshot import snapshot, GAME, SAVES, ROOT


def prepare(before):
    receipt_path = ROOT / 'runtime/stage10_7/install-receipt.json'
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    known = {e['path']: (e['sha256'], 'AIC' if 'aic_' in e['path'] else 'EML',
                         'Stage10.7 receipt applied[] SHA-256') for e in receipt['applied']}
    archive = ROOT / 'artifacts/emf-0.3.2-audit/EMF-0.3.2-manual.zip'
    archive_sha = file_hash(archive)
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            name = info.filename.replace('\\', '/')
            if '/game/' in name and not info.is_dir():
                rel = name.split('/game/', 1)[1]
                known.setdefault(rel, (hashlib.sha256(z.read(info)).hexdigest(), 'EMF',
                                      'EMF0.3.2 manual archive SHA256=' + archive_sha + '; entry=' + name))
    # Repository source equality is explicit attribution, not directory guessing.
    for p in (ROOT / 'mods/aic_body').glob('*'):
        if p.is_file() and p.suffix in ('.lua', '.json'):
            known.setdefault('emf/mods/aic_body/' + p.name,
                             (file_hash(p), 'AIC', 'repository mods/aic_body/' + p.name))
    profile = load_profile(1287369)
    identity = {k: profile[k] for k in ('game_build', 'exe_sha256', 'steam_build_id')}
    steam_path = GAME.parents[1] / 'appmanifest_1203620.acf'
    steam = steam_identity(steam_path)
    if steam != {'steam_build_id': '26430625', 'depot_manifest': '7226436020230696061'}:
        raise RuntimeError('STEAM_BUILD_CHANGED')
    identity.update(steam)
    if before['game']['enshrouded.exe']['sha256'] != identity['exe_sha256']:
        raise RuntimeError('BUILD_CHANGED')
    entries = []
    for rootkey, folder, values in (('game', GAME, before['game']), ('saves', SAVES, before['saves'])):
        for rel, measured in values.items():
            owner, confidence, attribution, action = 'UNKNOWN', 'UNKNOWN', 'fresh inventory only', 'MANUAL_REVIEW'
            isdat = rel.startswith('enshrouded_') and rel.endswith('.dat')
            if rootkey == 'saves':
                owner, action, attribution = 'LOCAL_SAVES', 'KEEP', 'configured LOCAL save root; preserve all files'
            elif rel in known and known[rel][0] == measured['sha256']:
                _, owner, attribution = known[rel]
                confidence, action = 'HASH_CONFIRMED', 'QUARANTINE'
            elif isdat:
                owner, action = 'GAME_OR_PREVIOUS_EML', 'STEAM_REPAIR' if int(rel[-7:-4]) < 55 else 'MANUAL_REVIEW'
                attribution = 'historical inventory comparison; no current official per-file depot hash'
            elif rel in ('enshrouded.kfc', 'enshrouded.kfc_resources'):
                owner, action, attribution = 'MIXED_GAME_DATA', 'STEAM_REPAIR', 'Stage10.10 KFC resource audit: clone present'
            elif rel == 'enshrouded.exe':
                owner, action, confidence, attribution = 'GAME', 'KEEP', 'HASH_CONFIRMED', '1287369 pinned EXE profile'
            elif rel.startswith('backup/') or rel == 'enshrouded.log':
                action = 'KEEP'  # Unknown historic diagnostics are harmless to keep; not declared official.
            elif rel == 'enshrouded.kfc.bak':
                action = 'MANUAL_REVIEW'
            purpose = 'Unknown: keep until attribution; filename is not ownership evidence'
            if rootkey == 'saves':
                purpose = 'LOCAL character/world save state; contents not published'
            elif action == 'QUARANTINE':
                purpose = ('loader proxy' if rel in ('dinput8.dll', 'dbghelp.dll') else
                           'EMF core runtime' if rel == 'emf/emf_core.dll' else
                           'mod manifest' if rel.endswith('mod.json') else
                           'documentation' if rel.endswith('README.md') else
                           'configuration' if rel.endswith(('.ini', '.json')) else
                           'mod/runtime code or support tool; exact archive/receipt entry identifies package')
            elif action == 'STEAM_REPAIR':
                purpose = 'game resource container/index; mixed state, repair through Steam only'
            elif rel == 'enshrouded.exe':
                purpose = 'game executable build1287369'
            entries.append(dict(root=rootkey, absolute_path=str(folder / rel), relative_path=rel,
                sha256=measured['sha256'], size=measured['bytes'], artifact_owner=owner,
                original_purpose=purpose,
                source_of_attribution=attribution, proposed_action=action,
                backup_required=not isdat, confidence=confidence,
                restore_procedure='No automatic restore; exact build/path/hash review; saves need separate consent',
                reason='Never delete by filename. DAT numbers and empty SHA do not prove ownership.'))
    # Receipt is backed up without publishing its token/content.
    roots = {'game': str(GAME), 'saves': str(SAVES), 'receipt': str(receipt_path.parent)}
    # A whole receipt directory is not an input root: use a private single-file
    # metadata copy in Phase B, bound to receipt_sha256. See backup strategy.
    roots.pop('receipt')
    result = dict(format='aic_recovery_plan_v1', game_identity=identity, roots=roots,
                  receipt_sha256=file_hash(receipt_path), receipt_path=str(receipt_path),
                  receipt_size=receipt_path.stat().st_size, entries=entries,
                  steam_manifest_path=str(steam_path),
                  cleanup_executed=False, clean_baseline_confirmed=False, installation_ready=False,
                  runtime_status='NOT_EXECUTED', RUNTIME_RENDER_CONFIRMED='UNKNOWN', spawn_ready=False)
    return result


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=['before', 'after', 'plan'])
    ap.add_argument('--run-dir', type=Path, default=ROOT / 'runtime/stage10_10_1',
                    help='New evidence folder under project runtime; existing files never overwritten')
    args = ap.parse_args()
    run = args.run_dir.absolute()
    no_links(run)
    if not run.resolve().is_relative_to((ROOT / 'runtime').resolve()):
        raise RuntimeError('OUTPUT_MUST_BE_IN_PROJECT_RUNTIME')
    run.mkdir(parents=True, exist_ok=True)
    if args.action in ('before', 'after'):
        data = snapshot()
        write_json_new(run / (args.action + '.json'), data)
        print(json.dumps({'game_files': len(data['game']), 'save_files': len(data['saves'])}))
    else:
        plan = prepare(json.loads((run / 'before.json').read_text(encoding='utf-8')))
        out = ROOT / 'compatibility/recovery/1287369'
        out.mkdir(parents=True, exist_ok=True)
        write_json_new(out / 'cleanup_manifest.json', plan)
        print(json.dumps({a: sum(e['proposed_action'] == a for e in plan['entries'])
                          for a in sorted({e['proposed_action'] for e in plan['entries']})}))
