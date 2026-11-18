"""Read-only Phase C review. A proposal is not an executable cleanup receipt."""
from .compatibility import fingerprint


MOD_CATEGORIES = frozenset({
    'LEGACY_CODE_REUSE_BLOCKER', 'CONFIG_REUSE_BLOCKER',
    'STALE_CACHE_REUSE_BLOCKER', 'STALE_EVIDENCE_BLOCKER',
    'INSTALLER_CATALOG_BLOCKER',
})


def compare_inventory(before, after):
    """Keep mtime changes visible even when bytes are unchanged."""
    return {group: {
        'ADDED': sorted(set(after[group]) - set(before[group])),
        'REMOVED': sorted(set(before[group]) - set(after[group])),
        'CHANGED': sorted(p for p in before[group].keys() & after[group].keys()
                          if before[group][p] != after[group][p]),
        'UNCHANGED': sorted(p for p in before[group].keys() & after[group].keys()
                            if before[group][p] == after[group][p]),
    } for group in ('game', 'saves')}


def propose(review, previous, current, identity, expected_identity):
    if not identity or identity != expected_identity:
        raise ValueError('BUILD_CHANGED_REVIEW_REQUIRED')
    delta = compare_inventory(previous, current)
    if any(delta[g][k] for g in delta for k in ('ADDED', 'REMOVED', 'CHANGED')):
        raise ValueError('INVENTORY_CHANGED_REVIEW_REQUIRED')
    rows, seen = [], set()
    for item in review['files']:
        rel = item['relative_path']
        if rel.casefold() in seen:
            raise ValueError('DUPLICATE_RESIDUAL')
        seen.add(rel.casefold())
        actual = current['game'].get(rel)
        if not actual or (actual['sha256'], actual['bytes']) != (item['sha256'], item['size']):
            raise ValueError('REVIEWED_HASH_CHANGED')
        category = item['category']
        if category in MOD_CATEGORIES:
            # These are attributed scripts/configuration/output, never game data.
            if not rel.startswith(('emf/', '.cache/', 'export/')) or rel.endswith(('.dat', '.kfc', '.kfc_resources', '.exe', '.bak')):
                raise ValueError('PROTECTED_FILE_IN_MOD_PROPOSAL')
            action = 'PROPOSE_MOD_QUARANTINE'
        elif category == 'CONTENT_BASE_BLOCKER' and rel == 'enshrouded.kfc.bak':
            action = 'REQUEST_SEPARATE_BAK_HOLD'
        else:
            action = 'KEEP_UNCHANGED'
        rows.append({
            'relative_path': rel, 'sha256': item['sha256'], 'size': item['size'],
            'category': category, 'proposed_action': action,
            'provenance': item['observation'], 'reason': item['reason'],
            'restore_policy': 'Preserve verified copy; restore this exact path/hash only after separate review; never auto-restore resources or saves.',
        })
    return {'format': 'aic_residual_proposal_v1', 'game_identity': identity,
            'inventory_identity': fingerprint({'game': current['game'], 'saves': current['saves']}),
            'entries': rows, 'authorization': False, 'execution_supported': False,
            'cleanup_executed': False, 'installation_authorized': False,
            'installation_executed': False, 'spawn_ready': False}


def validate_proposal(proposal, review, previous, current, identity):
    expected = propose(review, previous, current, identity, proposal['game_identity'])
    if proposal != expected:
        raise ValueError('RESIDUAL_PROPOSAL_MISMATCH')
    return expected
