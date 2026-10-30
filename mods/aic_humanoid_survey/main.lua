-- Read-only Stage 8 survey.  This module intentionally exposes no spawn,
-- write, event-emission, inventory, destroy, save or automatic-tick path.
local json = require('json')

local COMPONENTS = {
  'ActiveNpcState', 'DynamicActiveNpcState', 'ActiveNpcStateSaved',
  'NpcCommon', 'NpcState', 'Faction', 'Actor', 'Health', 'CurrentTransform',
  'PathWalker', 'DynamicPathWalker', 'SteeringAgent', 'Movement',
  'MovementCollider', 'Inventory', 'InventorySetup', 'Equipment',
  'RenderEquipment', 'VisualEquipment', 'ForceSave', 'DoNotSave',
  'NetworkEntity', 'AnimationGraphComponent2',
  'AnimationGraphResourceComponent2', 'ModelResource',
}

local function read_dynamic(world, name, id)
  local ok, value = pcall(world.get, world, name, id)
  if not ok then return nil, true end
  return value, false
end

local function read_template(world, name, id)
  local ok, value = pcall(world.template, world, name, id)
  if not ok then return nil, true end
  return value, false
end

local function position(world, id)
  local ok, x, y, z = pcall(world.position, world, id)
  if not ok or x == nil then return nil end
  return {x=x, y=y, z=z}
end

local function distance(a, b)
  if not a or not b then return nil end
  return math.sqrt((a.x-b.x)^2 + (a.y-b.y)^2 + (a.z-b.z)^2)
end

local function inspect(world, id)
  local present, reflection_error = {}, false
  for _, name in ipairs(COMPONENTS) do
    local dynamic, failed = read_dynamic(world, name, id)
    local template = nil
    if dynamic == nil and not failed then template, failed = read_template(world, name, id) end
    present[name] = dynamic ~= nil or template ~= nil
    reflection_error = reflection_error or failed
  end
  local active, aerr = read_template(world, 'ActiveNpcState', id)
  local faction, ferr = read_dynamic(world, 'Faction', id)
  if not faction and not ferr then faction, ferr = read_template(world, 'Faction', id) end
  local model, merr = read_template(world, 'ModelResource', id)
  local graph, gerr = read_template(world, 'AnimationGraphResourceComponent2', id)
  return {
    entity_id=id,
    session=tostring(emf.session()),
    position=position(world, id),
    npc_id=active and active.npcId or nil,
    npc_type=active and active.npcType or nil,
    faction=faction and faction.faction or nil,
    model_guid=model and model.model or nil,
    animation_graph_guid=graph and graph.animationGraph or nil,
    template_guid='unavailable_public_lua_api',
    template_guid_available=false,
    components=present,
    reflection_error=reflection_error or aerr or ferr or merr or gerr,
    read_only=true,
  }
end

local function reply(value)
  emf.reply('AIC_HUMANOID_SURVEY ' .. json.encode(value))
end

emf.command('inspect', '<entity-id>: read-only humanoid component snapshot', function(world, args)
  if not world:is_server() then return end
  if #args ~= 1 then reply({error='invalid_request', read_only=true}); return end
  local id = tonumber(args[1])
  if not id or id < 1 or id % 1 ~= 0 then reply({error='invalid_entity_id', read_only=true}); return end
  reply(inspect(world, id))
end)

emf.command('scan', '[radius 1..100]: read-only active NPCs near host', function(world, args)
  if not world:is_server() then return end
  if #args > 1 then reply({error='invalid_request', read_only=true}); return end
  local radius = tonumber(args[1]) or 40
  if radius < 1 or radius > 100 then reply({error='invalid_radius', read_only=true}); return end
  local player = emf.local_player()
  local origin = player and position(world, player)
  if not origin then reply({error='local_host_player_missing', read_only=true}); return end
  local out, count = {read_only=true, radius=radius, template_guid_available=false}, 0
  local ok, entities = pcall(world.entities, world)
  if not ok then reply({error='entity_enumeration_failed', read_only=true}); return end
  for _, id in ipairs(entities) do
    local active = read_template(world, 'ActiveNpcState', id)
    local at = active and position(world, id)
    local d = distance(origin, at)
    if active and d and d <= radius then
      count = count + 1
      local value = inspect(world, id)
      value.distance_to_host = d
      out['entity_' .. tostring(id)] = value
    end
  end
  out.count = count
  reply(out)
end)

emf.log('Humanoid survey loaded disabled-by-default; read-only commands: aic_humanoid_survey.scan / inspect')
