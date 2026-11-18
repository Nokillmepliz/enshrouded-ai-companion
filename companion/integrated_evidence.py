"""Strict v8 build-log frames. A build observation is not a runtime verdict."""
import re

FIELDS = set('schema patch build owner plan_id profile_sha256 baseline_sha256 source_guid clone_guid '
             'resource_type part component_count component_fingerprint source_hashkeys clone_hashkeys '
             'hashkey_provenance gender use_new_proportions animation_graph retarget_data source_unchanged '
             'source_comparison source_fnv32 clone_fields_preserved render_equipment_preserved '
             'dependencies_resolved dependency_set_sha256 visual_basis resource_lookup npc_id '
             'npc_collision_scan faction faction_enum_value writer_status runtime_render spawn_ready errors '
             'hierarchy_guid joint_count visual_reference_count'.split())
KEYS = set('beard beardColorId eyeBrowColor eyeColor hair hairColorId presetId skinColor voicePackId'.split())


def fnv(text):
    value = 2166136261
    for byte in text.encode('utf-8'):
        value = ((value ^ byte) * 16777619) & 0xffffffff
    return f'{value:08x}'


def hashkeys(text):
    result = {}
    for item in text.split(','):
        key, value = item.split('=')
        if key in result or not re.fullmatch(r'0|[1-9][0-9]{0,9}', value) or int(value) > 0xffffffff:
            raise ValueError('INVALID_HASHKEY32')
        result[key] = int(value)
    if set(result) != KEYS:
        raise ValueError('HASHKEY32_FIELDS')
    return result


def parse(text, expected):
    """Require exactly one complete ordered build. Reject mixed/stale reruns."""
    token = expected['run_token']
    if not re.fullmatch('[0-9a-f]{32}', token) or len(text.encode()) > 8 * 1024 * 1024:
        raise ValueError('INVALID_TOKEN_OR_LOG_SIZE')
    rows, state, values = [], 'initial', {}
    for line in text.splitlines():
        marker = 'AIC_EVIDENCE_V8|'
        if marker not in line:
            continue
        raw = line[line.index(marker):]
        parts = raw.split('|')
        if len(parts) != 4 or len(raw.encode()) > 4096:
            raise ValueError('MALFORMED_FRAME')
        _, observed_token, key, value = parts
        if observed_token != token:
            raise ValueError('STALE_RUN')
        if key == 'BEGIN':
            if state != 'initial' or value != str(len(FIELDS)):
                raise ValueError('DUPLICATE_BEGIN_OR_COUNT')
            state = 'body'
        elif key == 'END':
            if state != 'body' or set(values) != FIELDS or value != fnv('\n'.join(rows)):
                raise ValueError('TRUNCATED_OR_DIGEST')
            state = 'done'
        else:
            if state != 'body' or key not in FIELDS or key in values or not value:
                raise ValueError('DUPLICATE_OR_UNEXPECTED_FRAME')
            rows.append(key + '|' + value)
            values[key] = value
    if state != 'done' or list(values) != sorted(FIELDS):
        raise ValueError('INCOMPLETE_OR_UNORDERED')
    constants = dict(schema='8', patch='0.5.0', build='1287369', owner='EMF_INTEGRATED',
                     resource_type='keen::ecs::TemplateResource', part='0',
                     hashkey_provenance='EML_MAPPED_STRUCT_VALUE_UINT32', retarget_data='null',
                     source_unchanged='true', source_comparison='FULL_REFLECTED_VALUE_EQUALITY',
                     clone_fields_preserved='true', render_equipment_preserved='true',
                     visual_basis='PRESERVED_SOURCE_SETUP_AND_COMPONENTS_RESOURCE_EXISTENCE',
                     resource_lookup='EML_APP_STATE_AFTER_CREATE', faction='PlayerAlly', faction_enum_value='11',
                     writer_status='REQUESTED_NOT_FINALIZED', runtime_render='UNKNOWN', spawn_ready='false', errors='NONE')
    for key in ('plan_id', 'profile_sha256', 'baseline_sha256', 'source_guid', 'clone_guid',
                'component_count', 'component_fingerprint', 'animation_graph', 'npc_id',
                'dependency_set_sha256', 'dependencies_resolved', 'npc_collision_scan', 'gender',
                'hierarchy_guid', 'joint_count', 'visual_reference_count'):
        constants[key] = str(expected[key])
    constants['use_new_proportions'] = str(expected['use_new_proportions']).lower()
    for key, value in constants.items():
        if values[key] != value:
            raise ValueError('EVIDENCE_MISMATCH:' + key)
    if not re.fullmatch('[0-9a-f]{8}', values['source_fnv32']):
        raise ValueError('INVALID_SOURCE_FINGERPRINT')
    if hashkeys(values['source_hashkeys']) != expected['hashkeys'] or hashkeys(values['clone_hashkeys']) != expected['hashkeys']:
        raise ValueError('HASHKEY32_MISMATCH')
    return values


RUNTIME_GATES = ('original_integrity', 'single_content_owner', 'shadow_integrity',
                 'writer_finalized', 'content_unloaded', 'fresh_state', 'shadow_readback',
                 'resource_redirection', 'observer_session', 'no_legacy_artifacts')


def verdict(evidence, checks):
    """Checks must be separately recorded with provenance; missing is UNKNOWN."""
    gates = {k: (checks.get(k, {}).get('status', 'UNKNOWN')
                 if checks.get(k, {}).get('source') else 'UNKNOWN') for k in RUNTIME_GATES}
    complete = bool(evidence) and all(v == 'PASS' for v in gates.values())
    return {'verdict': 'LOAD_ONLY_SUCCESS' if complete else 'LOAD_ONLY_UNCONFIRMED',
            'gates': gates, 'A': 'PASS' if evidence else 'UNKNOWN',
            'H': 'PASS' if evidence else 'UNKNOWN', 'R': gates['shadow_readback'],
            'V': 'REFERENCES_ONLY' if evidence else 'UNKNOWN', 'B': gates['observer_session'],
            'C': gates['original_integrity'], 'runtime_render': 'UNKNOWN', 'spawn_ready': False}
