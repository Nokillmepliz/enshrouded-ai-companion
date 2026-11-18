"""Offline parser/validator for the proposed integrated-content evidence channel.

This is not an EMF API or a live connection. Frames come from EML print ->
content.log; writer completion and runtime/session identity need separate reads.
"""
import json

from .recovery import FLAGS

FIELDS = ('patch', 'build', 'source_guid', 'clone_guid', 'character_setup', 'hashkeys',
          'component_fingerprint', 'animation_graph', 'visual_references',
          'resource_lookup', 'source_integrity', 'count')
HASHKEYS = {'beard', 'beardColorId', 'eyeBrowColor', 'eyeColor', 'hair',
            'hairColorId', 'presetId', 'skinColor', 'voicePackId'}


def parse_frames(text, run_token):
    values = {}
    if not isinstance(run_token, str) or len(run_token) != 32 or any(c not in '0123456789abcdef' for c in run_token):
        raise ValueError('INVALID_RUN_TOKEN')
    for line in text.splitlines():
        marker = 'AIC_EVIDENCE_V8|'
        if marker not in line:
            continue
        raw = line[line.index(marker):]
        if len(raw.encode('utf-8')) > 4096:
            raise ValueError('EVIDENCE_TOO_LARGE')
        parts = raw.split('|', 3)
        if len(parts) != 4:
            raise ValueError('MALFORMED_EVIDENCE')
        _, token, key, value = parts
        if token != run_token:
            raise ValueError('STALE_BUILD_EVIDENCE')
        if key not in FIELDS or key in values or not value:
            raise ValueError('DUPLICATE_OR_INVALID_FIELD')
        values[key] = value
    if set(values) != set(FIELDS) or values['count'] != str(len(FIELDS) - 1):
        raise ValueError('INCOMPLETE_EVIDENCE')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('DUPLICATE_HASHKEY32')
            result[key] = value
        return result
    hashkeys = json.loads(values['hashkeys'], object_pairs_hook=unique)
    if not isinstance(hashkeys, dict) or set(hashkeys) != HASHKEYS:
        raise ValueError('HASHKEY32_COUNT')
    for v in hashkeys.values():
        if type(v) is not int or not 0 <= v <= 0xffffffff:
            raise ValueError('HASHKEY32_TYPE')
    return values


def inspect(command, context, expected, evidence=None):
    result = {'command': command, 'read_only': True, 'spawn_forbidden': True, **FLAGS}
    if command not in ('status', 'inspect', 'compare'):
        return {**result, 'ok': False, 'error': 'COMMAND_FORBIDDEN'}
    fields = (('build', 'UNSUPPORTED_BUILD'), ('api', 'WRONG_API'), ('emf', 'WRONG_EMF'),
              ('lua_host', 'WRONG_LUA_HOST'), ('protocol', 'WRONG_PROTOCOL'),
              ('session', 'WRONG_SESSION'), ('world', 'WRONG_WORLD'),
              ('content_owner', 'CONTENT_OWNER_MISMATCH'), ('patch', 'PATCH_MISMATCH'),
              ('receipt_sha256', 'STALE_RECEIPT'), ('run_token', 'WRONG_RUN'))
    for key, error in fields:
        if expected.get(key) is None or context.get(key) != expected[key]:
            return {**result, 'ok': False, 'error': error}
    if not evidence:
        return {**result, 'ok': False, 'error': 'MISSING_EVIDENCE'}
    # print() executes before final writer close. Never infer completion from it.
    if context.get('writer_finalized') is not True or context.get('shadow_readback_verified') is not True:
        return {**result, 'ok': False, 'error': 'WRITER_OR_READBACK_UNCONFIRMED'}
    baseline = expected.get('evidence')
    if not isinstance(baseline, dict) or set(baseline) != set(FIELDS):
        return {**result, 'ok': False, 'error': 'EVIDENCE_BASELINE_UNAVAILABLE'}
    if evidence != baseline:
        return {**result, 'ok': False, 'error': 'EVIDENCE_MISMATCH'}
    return {**result, 'ok': True, 'error': None,
            'evidence_validated_offline': True, 'runtime_render': 'UNKNOWN'}
