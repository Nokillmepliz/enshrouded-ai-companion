"""Explicit Phase C quarantine: 30 reviewed artifacts and one separately held .bak.

Does not change the Phase B protection policy. No restore, recursive removal,
automatic retry/resume, game launch, installation or save mutation.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil

from .compatibility import fingerprint
from .recovery import (RecoveryError, external_destination, match, measure,
                       no_links, target, write_json_new)
from .residual_cleanup import MOD_CATEGORIES, compare_inventory


def selected(proposal):
    if proposal.get('format') != 'aic_residual_proposal_v1':
        raise RecoveryError('INVALID_RESIDUAL_PROPOSAL')
    seen, mods, bak, kept = set(), [], [], []
    for row in proposal.get('entries', []):
        name = row['relative_path']
        if name.casefold() in seen:
            raise RecoveryError('DUPLICATE_RESIDUAL')
        seen.add(name.casefold())
        action = row['proposed_action']
        if action == 'PROPOSE_MOD_QUARANTINE':
            if (row['category'] not in MOD_CATEGORIES or not name.startswith(('emf/', '.cache/', 'export/'))
                    or Path(name).suffix.lower() not in {'.lua', '.ini', '.json', '.txt'}):
                raise RecoveryError('PROTECTED_OR_UNKNOWN_TARGET')
            mods.append(row)
        elif action == 'REQUEST_SEPARATE_BAK_HOLD':
            if name != 'enshrouded.kfc.bak' or row['category'] != 'CONTENT_BASE_BLOCKER':
                raise RecoveryError('ONLY_EXACT_KFC_BAK_HOLD_ALLOWED')
            bak.append(row)
        elif action == 'KEEP_UNCHANGED':
            kept.append(row)
        else:
            raise RecoveryError('UNKNOWN_PROPOSAL_ACTION')
    if (len(mods), len(bak), len(kept)) != (30, 1, 20):
        raise RecoveryError('EXPECTED_30_MODS_1_BAK_20_KEEP')
    return mods + bak  # The separate resource hold is last and never a restore.


def capture(roots):
    result = {'created_utc': datetime.now(timezone.utc).isoformat()}
    for group in ('game', 'saves'):
        root = roots[group]
        no_links(root)
        if not root.is_dir():
            raise RecoveryError('ROOT_MISSING')
        rows = result[group] = {}
        for base, dirs, files in os.walk(root, followlinks=False):
            for name in dirs + files:
                no_links(Path(base) / name)
            for name in files:
                p = Path(base) / name
                a = p.stat()
                data = measure(p)
                b = p.stat()
                if (a.st_ino, a.st_size, a.st_mtime_ns) != (b.st_ino, b.st_size, b.st_mtime_ns):
                    raise RecoveryError('SOURCE_CHANGED_DURING_CAPTURE')
                rows[p.relative_to(root).as_posix()] = {'sha256': data['sha256'], 'bytes': data['size'],
                                                       'mtime_ns': b.st_mtime_ns}
    return result


def check_live(proposal, live):
    state = live()
    if state.get('stopped') is not True:
        raise RecoveryError('GAME_OR_SERVER_NOT_STOPPED')
    if state.get('identity') != proposal['game_identity']:
        raise RecoveryError('BUILD_CHANGED')


def validate_before(proposal, roots, before, backup):
    rows = selected(proposal)
    if fingerprint({g: before[g] for g in ('game', 'saves')}) != proposal['inventory_identity']:
        raise RecoveryError('REVIEWED_INVENTORY_CHANGED')
    for e in proposal['entries']:
        match(target(roots['game'], e['relative_path']), e)
    for e in rows:
        match(target(backup, 'game/' + e['relative_path']), e)
    return rows


def verify_after(proposal, before, after):
    rows = selected(proposal)
    delta = compare_inventory(before, after)
    if (delta['game']['REMOVED'] != sorted(e['relative_path'] for e in rows)
            or delta['game']['ADDED'] or delta['game']['CHANGED']
            or any(delta['saves'][k] for k in ('ADDED', 'REMOVED', 'CHANGED'))):
        raise RecoveryError('POST_CLEANUP_INTEGRITY_MISMATCH')
    if any(e['relative_path'] not in after['game'] for e in proposal['entries']
           if e['proposed_action'] == 'KEEP_UNCHANGED'):
        raise RecoveryError('KEPT_RESIDUAL_MISSING')
    return delta


def quarantine(proposal, roots, backup, previous_quarantine, dest, before, *,
               authorize_mods=False, authorize_bak=False, live):
    if authorize_mods is not True or authorize_bak is not True:
        raise RecoveryError('BOTH_EXPLICIT_AUTHORIZATIONS_REQUIRED')
    check_live(proposal, live)
    # Verify every resolved path and forbid overlap with game, saves and history.
    external_destination(dest, {**roots, 'backup': backup, 'old_quarantine': previous_quarantine})
    rows = validate_before(proposal, roots, before, backup)
    for e in rows:
        target(dest, e['relative_path'])
    if shutil.disk_usage(dest.parent).free < sum(e['size'] for e in rows) + 1024 * 1024:
        raise RecoveryError('INSUFFICIENT_SPACE')
    dest.mkdir()
    write_json_new(dest / 'proposal.json', proposal)
    write_json_new(dest / 'authorization.json', {
        'scope': 'PHASE_C_30_MOD_ARTIFACTS_AND_SEPARATE_KFC_BAK_HOLD',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'proposal_identity': fingerprint(proposal), 'game_identity': proposal['game_identity'],
        'mods': 30, 'separate_bak_hold': 1, 'kept_residuals': 20,
        'restore_authorized': False, 'installation_authorized': False, 'spawn_ready': False})
    with (dest / 'journal.jsonl').open('x', encoding='utf-8', newline='\n') as log:
        def event(e, state):
            log.write(json.dumps({'relative_path': e['relative_path'], 'sha256': e['sha256'],
                                  'size': e['size'], 'state': state,
                                  'proposal_identity': fingerprint(proposal)}) + '\n')
            log.flush()
            os.fsync(log.fileno())

        # Stage ALL verified copies before removing ANY source name.
        for e in rows:
            check_live(proposal, live)
            src = target(roots['game'], e['relative_path'])
            match(src, e)
            out = target(dest, e['relative_path'])
            out.parent.mkdir(parents=True, exist_ok=True)
            with src.open('rb') as inp, out.open('xb') as stream:
                shutil.copyfileobj(inp, stream, 4 * 1024 * 1024)
                stream.flush()
                os.fsync(stream.fileno())
            match(out, e)
            match(src, e)
            event(e, 'COPIED_VERIFIED_SOURCE_PRESENT')
        for e in rows:
            check_live(proposal, live)
            match(target(backup, 'game/' + e['relative_path']), e)
            match(target(dest, e['relative_path']), e)
            src = target(roots['game'], e['relative_path'])
            match(src, e)
            src.unlink()  # Exact reviewed file only; never a directory or wildcard.
            if src.exists():
                raise RecoveryError('SOURCE_STILL_PRESENT')
            event(e, 'QUARANTINED')
    check_live(proposal, live)
    return len(rows)
