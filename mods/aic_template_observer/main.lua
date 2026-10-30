-- Stage 10 read-only observer. Public EMF Lua cannot look up a template GUID
-- without an entity, so this mod validates EML's positive export and reports
-- that direct limitation. It never spawns, emits, writes components or saves.
local json = require('json')

local EXPECTED = {
  format='aic_eml_humanoid_evidence_v1',
  template_guid='a1c90001-5e4d-4a91-8a1c-000000000001',
  source_guid='e3736dff-0ad2-47fc-903c-66c1775836e8',
  npc_id='2939921867',
  faction='PlayerAlly',
}

local function evidence_paths()
  local paths = {'export/aic_eml_humanoid/template_evidence_v1.txt'}
  if type(emf.dir) == 'string' then
    paths[#paths + 1] = emf.dir .. '/../../../export/aic_eml_humanoid/template_evidence_v1.txt'
  end
  return paths
end

local function read_evidence()
  for _, path in ipairs(evidence_paths()) do
    local file = io.open(path, 'r')
    if file then
      local raw = file:read('*a')
      file:close()
      if type(raw) ~= 'string' then return nil, 'evidence_read_failed', path end
      local result = {}
      for line in raw:gmatch('[^\r\n]+') do
        local key, value = line:match('^([a-z_]+)=(.*)$')
        if not key or result[key] ~= nil then return nil, 'evidence_malformed', path end
        result[key] = value
      end
      return result, nil, path
    end
  end
  return nil, 'evidence_missing', nil
end

local function checks(value)
  if not value then return {evidence_present=false} end
  local source_registered = value.source_registered == 'true'
  return {
    evidence_present=true,
    format=value.format == EXPECTED.format,
    template_guid=value.template_guid == EXPECTED.template_guid,
    source_guid=value.source_guid == EXPECTED.source_guid,
    npc_id=value.npc_id == EXPECTED.npc_id,
    faction=value.faction == EXPECTED.faction,
    model_available=value.model_guid ~= nil and value.model_guid ~= '' and value.model_guid ~= 'UNAVAILABLE',
    model_matches_source=value.model_guid ~= nil and value.model_guid == value.source_model_guid,
    animation_graph_available=value.animation_graph_guid ~= nil and value.animation_graph_guid ~= '' and value.animation_graph_guid ~= 'UNAVAILABLE',
    animation_graph_matches_source=value.animation_graph_guid ~= nil and value.animation_graph_guid == value.source_animation_graph_guid,
    component_clone=value.component_clone == 'true' and value.components == value.source_components,
    source_unchanged=value.source_unchanged == 'true',
    resource_lookup_after_create=value.resource_lookup_after_create == 'true',
    registry_consistent=(not source_registered) or value.registry_added == 'true',
    writer_finalization_confirmed=false,
  }
end

local function component_groups(raw)
  local groups = {navigation={}, inventory={}, equipment={}, save={}, network={}}
  if type(raw) ~= 'string' then return groups end
  for name in raw:gmatch('[^,]+') do
    local lower = name:lower()
    if lower:find('nav', 1, true) or lower:find('path', 1, true) or lower:find('movement', 1, true) then
      groups.navigation[#groups.navigation + 1] = name
    end
    if lower:find('inventory', 1, true) then groups.inventory[#groups.inventory + 1] = name end
    if lower:find('equipment', 1, true) then groups.equipment[#groups.equipment + 1] = name end
    if lower:find('save', 1, true) then groups.save[#groups.save + 1] = name end
    if lower:find('network', 1, true) or lower:find('replic', 1, true) then
      groups.network[#groups.network + 1] = name
    end
  end
  return groups
end

local function all_required(value)
  for key, ok in pairs(value) do
    if key ~= 'writer_finalization_confirmed' and ok ~= true then return false end
  end
  return value.writer_finalization_confirmed == true
end

local function reply(kind, extra)
  extra = extra or {}
  extra.command = kind
  extra.loaded = true
  extra.read_only = true
  extra.spawn_forbidden = true
  extra.direct_emf_template_lookup = 'UNAVAILABLE_WITHOUT_ENTITY'
  emf.reply('AIC_TEMPLATE_OBSERVER ' .. json.encode(extra))
end

emf.command('status', 'read-only EML evidence status', function()
  local value, err, path = read_evidence()
  reply('status', {evidence_available=value ~= nil, evidence_error=err, evidence_path=path,
    new_template_eml_evidence=value ~= nil and value.template_guid == EXPECTED.template_guid,
    original_template_eml_evidence=value ~= nil and value.source_guid == EXPECTED.source_guid,
    reflection_error=err, direct_new_template='UNAVAILABLE', direct_original_template='UNAVAILABLE',
    limitation='public EMF Lua requires an entity for world:template'})
end)

emf.command('inspect', 'read-only exported template fingerprint', function()
  local value, err, path = read_evidence()
  reply('inspect', {evidence=value, evidence_error=err, evidence_path=path, checks=checks(value),
    component_groups=component_groups(value and value.components),
    field_source=value and 'EML_EXPORT' or 'UNAVAILABLE'})
end)

emf.command('compare', 'read-only clone/source comparison', function()
  local value, err, path = read_evidence()
  local result = checks(value)
  reply('compare', {ok=all_required(result), checks=result, evidence_error=err, evidence_path=path,
    status='INCOMPLETE_UNTIL_EML_LOG_CONFIRMS_WRITER_FINALIZE'})
end)

emf.log('Template observer loaded; read-only commands: aic_template_observer.status / inspect / compare')
