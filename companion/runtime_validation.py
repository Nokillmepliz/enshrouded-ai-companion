"""Stage10.10.3 pure validators: no game access, writes or bridge requests."""
import copy
import hashlib
import json
from pathlib import PureWindowsPath
import re


def bridge_error(error):
    """Classify OS error, never infer a client count from a library hint."""
    code = getattr(error, 'winerror', None)
    if code is None:
        match = re.search(r'\berror\s+(\d+)\b', str(error), re.I)
        if match: code = int(match[1])
        elif str(error).startswith('no pipe '): code = 2
    kind = {5:'ACCESS_DENIED',2:'PIPE_NOT_FOUND',3:'PIPE_NOT_FOUND',231:'PIPE_BUSY',
            121:'WAIT_TIMEOUT',109:'PIPE_BROKEN',233:'PIPE_DISCONNECTED'}.get(code,'UNKNOWN')
    return dict(windows_error=code,category=kind,client_limit_reached='UNPROVEN',
                retry_requires_review=kind=='ACCESS_DENIED')


def attribute_post_close(before, after, *, archive, session_start_ns, session_end_ns):
    """Only the exact renamed pre-run log and same-object chain timestamp change."""
    if not re.fullmatch(r'backup/enshrouded_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.log',archive):
        raise ValueError('ARCHIVE_PATH')
    if archive in before or archive not in after: raise ValueError('ARCHIVE_NOT_NEW')
    archived,oldlog=after[archive],before['enshrouded.log']
    if any(archived[k]!=oldlog[k] for k in ('sha256','size','mtime_ns')) or archived['links']!=1:
        raise ValueError('ARCHIVE_NOT_EXACT_PREVIOUS_LOG')
    if archived!=oldlog:raise ValueError('ARCHIVE_NOT_RENAMED_PREVIOUS_LOG')
    current=after['enshrouded.log']
    if current['links']!=1 or (current['volume'],current['file_id'])==(archived['volume'],archived['file_id']):
        raise ValueError('CURRENT_LOG_ALIASES_ARCHIVE')
    name='emf/chain_status.txt';a,b=before[name],after[name]
    if any(a[k]!=b[k] for k in ('sha256','size','volume','file_id','links')) or b['links']!=1:
        raise ValueError('CHAIN_CONTENT_OR_IDENTITY_CHANGED')
    if not session_start_ns <= b['mtime_ns'] <= session_end_ns: raise ValueError('CHAIN_OUTSIDE_SESSION')
    # This reviewed installation has no chained tools: only the empty status is valid.
    if b['size']!=0 or b['sha256']!=hashlib.sha256(b'').hexdigest(): raise ValueError('UNREVIEWED_CHAIN_STATUS')
    return {archive:'EXACT_PREVIOUS_GAME_LOG_RENAME',name:'SAME_IDENTITY_EMPTY_STATUS_MTIME_ONLY'}


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))


def reassess_post_close(before, after, **session):
    attributed=attribute_post_close(before,after,**session)
    logs={'enshrouded.log','emf/content.log','emf/emf_loader.log','emf/emf_core.log','emf/file_opens.log'}
    for name in before.keys()|after.keys():
        if before.get(name)==after.get(name):continue
        if name not in after:raise ValueError('UNEXPECTED_REMOVAL:'+name)
        if name.startswith('emf/content/client/'):continue  # separately audited exact shadow77 contract
        if name in attributed:continue
        if name in logs and name in before and after[name]['links']==1:continue
        raise ValueError('UNATTRIBUTED_CHANGE:'+name)
    return dict(validator='post_close_v2',status='ATTRIBUTION_PASS',attributed=attributed,
                scope='REQUIRES_SEPARATE_ORIGINAL_INSTALLED_AND_SHADOW_CHECKS')


def components(resource):
    rows=resource['components'];result={r['$type']:r['$value'] for r in rows}
    if len(result)!=len(rows):raise ValueError('DUPLICATE_COMPONENT')
    return result


def semantic_readback(source, shadow_source, clone, hierarchy, presets, lookups, profile):
    """Compare independent KFCReader decodes, not evidence or Lua stdout."""
    meta=profile['expected_resource_metadata'];kind='keen::ecs::TemplateResource'
    for dump,guid in [(source,profile['source_guid']),(shadow_source,profile['source_guid']),(clone,profile['clone_guid'])]:
        if dump.get('mode')!='READ_ONLY' or dump.get('guid')!=guid or dump.get('part')!=0 or dump.get('type')!=kind:
            raise ValueError('DECODE_IDENTITY')
    if source['resource']!=shadow_source['resource']:raise ValueError('SOURCE_CHANGED_IN_SHADOW')
    if hashlib.sha256(canonical(source['resource']).encode()).hexdigest()!=meta['canonical_resource_sha256']:
        raise ValueError('SOURCE_BASELINE_CHANGED')
    expected=copy.deepcopy(source['resource']);ec=components(expected)
    expected['name']='AIC_Humanoid_Companion_Experimental'
    ec['keen::ecs::Faction']['faction']='PlayerAlly'
    ec['keen::ecs::ActiveNpcState']['npcId']={'value':profile['npc_id']}
    if clone['resource']!=expected:raise ValueError('UNEXPECTED_CLONE_CHANGE')
    cc=components(clone['resource'])
    if len(cc)!=meta['component_count']:raise ValueError('COMPONENT_COUNT')
    if cc['keen::ecs::CharacterSetup']!=meta['character_setup']:raise ValueError('CHARACTER_SETUP')
    if cc['keen::ecs::AnimationGraphResourceComponent2']!=meta['animation']:raise ValueError('ANIMATION')
    if hierarchy.get('mode')!='READ_ONLY' or hierarchy['guid']!=meta['hierarchy_guid'] or hierarchy['type']!='keen::ModelHierarchyResource' or hierarchy['part']!=0 or hierarchy['resource']['jointCount']!=meta['joints']:
        raise ValueError('SKELETON')
    if presets.get('mode')!='READ_ONLY' or presets['guid']!='a1bea7fc-2122-4dd3-a471-2b815a65134b':raise ValueError('PRESET_IDENTITY')
    selected=[p for p in presets['resource']['presets'] if p['presetId']==meta['character_setup']['presetId']]
    if len(selected)!=1:raise ValueError('PRESET_SELECTION')
    for ref in meta['decoded_preset_references']:
        if selected[0]['references'][ref['slot']]!=ref['guid']:raise ValueError('VISUAL_REFERENCE')
    if len(lookups)!=len(profile['dependencies']):raise ValueError('DEPENDENCY_COUNT')
    for dep,lookup in zip(profile['dependencies'],lookups):
        if lookup.get('mode')!='READ_ONLY_GUID_LOOKUP' or lookup['guid']!=dep['guid'] or lookup['count']!=len(lookup['resources']):
            raise ValueError('DEPENDENCY_LOOKUP')
        identities=[(r['guid'],r['type'],r['part']) for r in lookup['resources']]
        if len(set(identities))!=len(identities) or any(r[0]!=dep['guid'] for r in identities):raise ValueError('DEPENDENCY_DUPLICATE_OR_GUID')
        if identities.count((dep['guid'],dep['type'],0))!=1:raise ValueError('DEPENDENCY_TYPE')
    return dict(status='PASS',scope='INDEPENDENT_KFC_DECODE_FULL_SOURCE_AND_CLONE_EQUALITY',
        source_unchanged=True,only_changes=['name','Faction.faction','ActiveNpcState.npcId'],
        guid=clone['guid'],npc_id=profile['npc_id'],faction='PlayerAlly',components=len(cc),
        character_setup='PASS',hashkeys=9,animation='PASS',render_equipment='FULL_VALUE_EQUAL',
        skeleton_joints=meta['joints'],dependencies=len(lookups),visual_references=len(meta['decoded_preset_references']),
        runtime_render='UNKNOWN',spawn_ready=False)


def redirection(log, game, expected_names, *, started_local):
    """Successful redirected CreateFile reads are opens, not ReadFile byte proofs."""
    if f'# started {started_local} local time;' not in log:raise ValueError('LOG_SESSION_MISMATCH')
    if 'redirect_test=1' not in log:raise ValueError('REDIRECT_NOT_ENABLED')
    root=PureWindowsPath(game);opened=set();lines=[]
    pattern=re.compile(r'^\+\d+ms t\d+ CreateFile[AW] "([^"]+)" => "([^"]+)" (.+) -> handle (0x[0-9a-fA-F]+)$')
    for number,line in enumerate(log.splitlines(),1):
        m=pattern.fullmatch(line)
        if not m:continue
        src,dst,args,handle=m.groups();s=PureWindowsPath(src);d=PureWindowsPath(dst)
        access=re.search(r'access=0x([0-9a-fA-F]+)',args)
        if not access or not int(access[1],16)&0x80000000 or int(access[1],16)&0x40000000 or 'disp=OPEN_EXISTING' not in args:continue
        if int(handle,16) in (0,0xffffffff,0xffffffffffffffff):continue
        if s.parent!=root or s.name not in expected_names:continue
        if d!=root/'emf/content/client'/s.name:raise ValueError('WRONG_REDIRECT_TARGET')
        opened.add(s.name);lines.append(number)
    missing=sorted(set(expected_names)-opened)
    return dict(status='PASS' if not missing else 'INCOMPLETE',successful_read_opens=sorted(opened),missing=missing,
        log_lines=lines,scope='GAME_EXE_CREATEFILE_READ_OPEN_SUCCESS; READFILE_BYTES_NOT_TRACED',spawn_ready=False)
