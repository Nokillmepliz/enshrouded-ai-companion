"""Read-only post-quarantine audit. Writes sanitized evidence in the repository.

Never moves/deletes/restores a game file. The Phase A plan stays immutable.
"""
from __future__ import annotations

import argparse
from collections import Counter
import configparser
from datetime import datetime, timezone
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from companion.compatibility import file_hash, fingerprint
from companion.recovery import measure, no_links, target, verify_backup, write_json_new


def verify_delta(plan, before, after):
    expected = {e['relative_path'] for e in plan['entries'] if e['proposed_action'] == 'QUARANTINE'}
    old, new = before['game'], after['game']
    removed = set(old) - set(new)
    added = set(new) - set(old)
    changed = [p for p in set(old) & set(new) if old[p] != new[p]]
    if removed != expected or added or changed or before['saves'] != after['saves']:
        raise ValueError('POST_QUARANTINE_INTEGRITY_MISMATCH')
    manual = [e for e in plan['entries'] if e['proposed_action'] == 'MANUAL_REVIEW']
    if any(e['relative_path'] not in new for e in manual):
        raise ValueError('MANUAL_REVIEW_FILE_MISSING')
    for e in plan['entries']:
        label = 'game' if e['root'] == 'game' else 'saves'
        v = before[label].get(e['relative_path'])
        if v is None or v['sha256'] != e['sha256'] or v['bytes'] != e['size']:
            raise ValueError('BEFORE_DOES_NOT_MATCH_REVIEWED_PLAN')
    return {'game_before': len(old), 'game_after': len(new), 'quarantined': len(removed),
            'unchanged_game_files': len(new), 'added': [], 'changed': [],
            'manual_review_unchanged': len(manual), 'local_files_unchanged': len(after['saves'])}


def kfc_header(path):
    with path.open('rb') as f:
        head = f.read(65536)
    if len(head) < 32 or head[:4] != b'KFC4':
        raise ValueError('KFC_HEADER_INVALID')
    offset, length = struct.unpack_from('<II', head, 16)
    if length > 4096 or 16 + offset + length > len(head):
        raise ValueError('KFC_HEADER_BOUNDS')
    return {'version': head[16+offset:16+offset+length].decode('utf-8'),
            'containers': struct.unpack_from('<I', head, 28)[0], 'size': path.stat().st_size}


def residue_review(plan, game, signature_file):
    signatures = {e['file']: e for e in json.loads(signature_file.read_text(encoding='utf-8-sig'))}
    body = (game/'emf/mods/aic_body/body.lua').read_bytes()
    historical = '026cd8a25fac49ce1dbcb1703fa332369c501e9c'
    old_body = subprocess.check_output(['git','show',historical+':mods/aic_body/body.lua'], cwd=ROOT)
    if body != old_body:
        raise ValueError('HISTORICAL_BODY_ATTRIBUTION_CHANGED')
    headers = {name: kfc_header(game/name) for name in ('enshrouded.kfc','enshrouded.kfc.bak')}
    rows = []
    for e in plan['entries']:
        if e['proposed_action'] != 'MANUAL_REVIEW':
            continue
        rel = e['relative_path']
        p = target(game, rel)
        if measure(p) != {'size': e['size'], 'sha256': e['sha256']}:
            raise ValueError('RESIDUE_CHANGED')
        observation = {}
        if rel == 'enshrouded.kfc.bak':
            category = 'CONTENT_BASE_BLOCKER'
            observation = headers[rel]
            reason = 'Same version but different container count: EMF choose_base selects .bak; clean origin not verified.'
            future = 'Validate both indexes against clean Steam resources; never accept .bak by name/version alone.'
        elif rel.startswith('enshrouded_') and rel.endswith('.dat'):
            category = 'RESOURCE_PROVENANCE_BLOCKER'
            observation = {'empty': p.stat().st_size == 0, 'current_kfc_containers': headers['enshrouded.kfc']['containers']}
            reason = 'Index claims 64 containers; zero bytes and historical numbering do not establish mod ownership.'
            future = 'After authorized Steam Verify compare official container set and full KFC references; no automatic removal.'
        elif rel == 'emf/mods/aic_body/body.lua':
            category = 'LEGACY_CODE_REUSE_BLOCKER'
            observation = {'exact_git_commit': historical, 'main_missing': not (p.parent/'main.lua').exists(),
                           'mod_manifest_missing': not (p.parent/'mod.json').exists()}
            reason = 'Exact historical AIC source. Dormant without loader/manifest/main, but unsafe to merge into a new install.'
            future = 'Separate reviewed migration action; not included in this 81-file authorization.'
        elif rel.startswith('emf/config/') or rel == 'emf/emf_core.ini':
            c = configparser.ConfigParser(interpolation=None)
            c.read(p, encoding='utf-8')
            observation = {s: dict(c[s]) for s in c.sections()}
            category = 'CONFIG_REUSE_BLOCKER'
            reason = 'No loader remains to read this config; future installation must not silently inherit it.'
            future = 'New explicit config plan. aic_body enabled=1 and bridge=1/bridge_verbose=1 require particular review.'
        elif rel.startswith('.cache/'):
            category = 'STALE_CACHE_REUSE_BLOCKER'
            if p.suffix == '.json':
                data = json.loads(p.read_text(encoding='utf-8-sig'))
                observation = {'top_keys': list(data)}
                if rel.endswith('types.json'):
                    observation.update(version=data.get('version'), type_count=len(data.get('types',{})))
                else:
                    observation.update(cache_build_id=data.get('build_id'), tracked_files=len(data.get('files',{})))
            else:
                observation = {'static_text': True, 'not_executed': True}
            reason = 'Generated reflection/cache from mixed installation; not authoritative clean data.'
            future = 'Integrated build uses separate shadow cache; do not copy root cache into shadow or trust it as evidence.'
        elif rel.startswith('export/'):
            category = 'STALE_EVIDENCE_BLOCKER'
            text = p.read_text(encoding='utf-8')
            fields = dict(line.split('=',1) for line in text.splitlines() if '=' in line)
            observation = {k: fields[k] for k in ('format','template_guid','source_guid') if k in fields}
            reason = 'Historical evidence v4 with private run identity; no binding to new load/session or finalized shadow.'
            future = 'Preserve as history only; use reviewed new evidence channel.'
        elif rel == 'emf/installed.txt':
            category = 'INSTALLER_CATALOG_BLOCKER'
            names = p.read_text(encoding='utf-8-sig').splitlines()
            observation = {'catalog_lines': len(names)}
            reason = 'Old installer ownership catalog survives removal; manager reads this to classify shipped files.'
            future = 'Do not use it to authorize repair/removal or declare current installation complete.'
        elif rel in signatures:
            category = 'VENDOR_COMPONENT_KEEP_PENDING_DEPOT'
            observation = signatures[rel]
            reason = 'Valid NVIDIA/Valve Authenticode signature and matching vendor metadata; not an EMF loader attribution.'
            future = 'Keep; Steam per-file/depot comparison remains necessary. Signature does not prove depot identity.'
        elif rel == 'enshrouded_local.json':
            category = 'LOCAL_SETTINGS_KEEP'
            data = json.loads(p.read_text(encoding='utf-8-sig'))
            observation = {'top_keys': list(data), 'version': data.get('version')}
            reason = 'Graphics/sound/version JSON; not a mod loader or character/world save payload.'
            future = 'Keep user settings; no clean-resource failure established by these keys.'
        else:
            assert rel.endswith('.log') or rel == 'emf/chain_status.txt', rel
            category = 'HISTORICAL_DIAGNOSTICS_KEEP'
            observation = {'empty': e['size'] == 0, 'contents_not_published': True}
            reason = 'Historical diagnostic output, not executable startup configuration; cannot prove current runtime status.'
            future = 'Keep, do not ingest as fresh acceptance evidence or active chain configuration.'
        rows.append({'relative_path':rel,'sha256':e['sha256'],'size':e['size'],
                     'reviewed_action':'MANUAL_REVIEW','actual_action':'KEEP_UNCHANGED',
                     'category':category,'observation':observation,'reason':reason,'future_review':future})
    return {'files':rows,'counts':dict(Counter(e['category'] for e in rows)),
            'headers':headers,'resource_baseline_confirmed':False,
            'integrated_content_selected':True,'integrated_content_installed':False}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-dir', type=Path, required=True)
    ap.add_argument('--backup', type=Path, required=True)
    ap.add_argument('--quarantine', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    for path in (args.run_dir,args.backup,args.quarantine,args.output):
        no_links(path)
        if not path.resolve().is_relative_to(ROOT.resolve()):
            raise ValueError('AUDIT_PATH_OUTSIDE_PROJECT')
    plan_path = ROOT/'compatibility/recovery/1287369/cleanup_manifest.json'
    reviewed = subprocess.check_output(['git','show',
        '21d7860ac8b399d570fe37df0f2478bad6102547:compatibility/recovery/1287369/cleanup_manifest.json'], cwd=ROOT)
    if plan_path.read_bytes() != reviewed:
        raise ValueError('REVIEWED_MANIFEST_CHANGED')
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    before = json.loads((args.run_dir/'before.json').read_text(encoding='utf-8'))
    after = json.loads((args.run_dir/'after.json').read_text(encoding='utf-8'))
    delta = verify_delta(plan,before,after)
    backup = verify_backup(plan,args.backup)
    selected = [e for e in plan['entries'] if e['proposed_action']=='QUARANTINE']
    journal = [json.loads(line) for line in (args.quarantine/'journal.jsonl').read_text().splitlines()]
    expected_journal = [{'relative_path':e['relative_path'],'sha256':e['sha256'],'state':state,
                         'plan_sha256':fingerprint(plan)} for e in selected
                        for state in ('COPIED_VERIFIED_SOURCE_PRESENT','QUARANTINED')]
    if journal != expected_journal:
        raise ValueError('QUARANTINE_JOURNAL_MISMATCH')
    from companion.recovery import inventory
    expected_files = {e['relative_path']:{'size':e['size'],'sha256':e['sha256']} for e in selected}
    expected_files['journal.jsonl'] = measure(args.quarantine/'journal.jsonl')
    if inventory(args.quarantine) != expected_files:
        raise ValueError('QUARANTINE_CONTENT_MISMATCH')
    if file_hash(Path(plan['receipt_path'])) != plan['receipt_sha256']:
        raise ValueError('HISTORICAL_RECEIPT_CHANGED')
    game = Path(plan['roots']['game'])
    review = residue_review(plan,game,args.run_dir/'vendor-signatures.json')
    result = {'format':'aic_phase_b_limited_cleanup_v1','created_utc':datetime.now(timezone.utc).isoformat(),
              'reviewed_commit':'21d7860ac8b399d570fe37df0f2478bad6102547',
              'plan_sha256':file_hash(plan_path),'game_identity':plan['game_identity'],
              'backup_path':str(args.backup.resolve()),'backup_payload_files':len(backup['entries'])+1,
              'backup_payload_bytes':sum(e['size'] for e in backup['entries'])+plan['receipt_size'],
              'backup_manifest_sha256':file_hash(args.backup/'manifest.json'),
              'backup_plan_file_sha256':file_hash(args.backup/'plan.json'),
              'backup_complete_tree_files':sum(p.is_file() for p in args.backup.rglob('*')),
              'backup_complete_tree_bytes':sum(p.stat().st_size for p in args.backup.rglob('*') if p.is_file()),
              'full_mixed_state_restore':False,'quarantine_path':str(args.quarantine.resolve()),
              'quarantine_files':len(selected),'quarantine_payload_bytes':sum(e['size'] for e in selected),
              'quarantine_journal_sha256':file_hash(args.quarantine/'journal.jsonl'),
              'quarantine_journal_records':len(journal),'quarantine_preserved':True,
              'integrity':delta,'receipt_unchanged':True,'protected_dat_unchanged':sum(n.endswith('.dat') for n in after['game']),
              'known_loaders_absent':all(not (game/p).exists() for p in ('dinput8.dll','dbghelp.dll','emf/emf_core.dll')),
              'cleanup_executed':True,'cleanup_scope':'ONLY_REVIEWED_81_FILES',
              'clean_baseline_confirmed':False,'installation_ready':False,'phase_c_executed':False,
              'runtime_status':'NOT_EXECUTED','RUNTIME_RENDER_CONFIRMED':'UNKNOWN','spawn_ready':False}
    args.output.mkdir(parents=True,exist_ok=True)
    write_json_new(args.output/'operation.json',result)
    write_json_new(args.output/'residual-review.json',review)
    print(json.dumps({'integrity':delta,'backup_verified_files':len(backup['entries'])+1,
                      'quarantine_verified_files':len(selected),'review_counts':review['counts']},indent=2))


if __name__ == '__main__':
    main()
