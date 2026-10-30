-- EMF Lua API, pinned sources and semantics: docs/PROTOCOL.md.
local body = require('body')
local json = require('json')
emf.emits({'StartGuardingEvent', 'StopGuardingEvent'})
local current_world
local entity_ids
local lock_path = emf.dir .. '/runtime.lock'
local function read_lock()
  local f, _, errno = io.open(lock_path, 'r')
  if not f then return nil, errno == 2 and 'missing' or 'error' end
  local text = f:read('*a')
  local closed = f:close()
  if text == nil or not closed then return nil, 'error' end
  return text, 'present' -- empty, truncated and legacy locks still block spawn
end
local env = {
  instance=(tostring({}) .. string.format('%.9f', os.clock())):gsub('[^%w]', ''),
  session=function() return emf.session_token() end,
  owner=function() return emf.local_player() end,
  locked=function() local _, state = read_lock(); return state ~= 'missing' end,
  lock=function(expected)
    local _, state = read_lock()
    if state ~= 'missing' then return false end -- never overwrite another/old lock
    local f = io.open(lock_path, 'w')
    if not f then return false end
    local ok = f:write(expected)
    local flushed = f:flush()
    local closed = f:close()
    local text, after = read_lock()
    return ok ~= nil and flushed ~= nil and closed ~= nil and after == 'present' and text == expected
  end,
  unlock=function(expected)
    local text, state = read_lock()
    if state ~= 'present' or text ~= expected then return false end
    if not os.remove(lock_path) then return false end
    local _, after = read_lock()
    return after == 'missing'
  end,
  exists=function(entity)
    -- position=nil is NOT evidence that an entity was destroyed.
    -- Build at most one snapshot per callback, only when absence needs checking.
    if not entity_ids then
      entity_ids = {}
      for _, id in ipairs(current_world:entities()) do entity_ids[id] = true end
      local owner = emf.local_player()
      if not owner or owner == 0 or not entity_ids[owner] then error('entity_snapshot_unavailable') end
    end
    return entity_ids[entity] == true
  end,
  spawn=function(guid, position)
    return emf.spawn(current_world, guid, position.x, position.y, position.z)
  end,
  destroy=function(entity) return emf.destroy(current_world, entity) end,
  ally=function(entity)
    local f = current_world:get('Faction', entity)
    if not f then return false end
    f.faction = 11
    return f.faction == 11
  end,
  guard=function(entity, target, stop)
    return pcall(emf.emit, 'server', stop and 'StopGuardingEvent' or 'StartGuardingEvent',
      {guardingEntityId=entity, guardedEntityId=target})
  end,
  inspect=function(entity)
    local x, y, z = current_world:position(entity)
    if x == nil then return nil end
    local birth = current_world:get('SpawnTime', entity)
    local faction = current_world:get('Faction', entity)
    local ai = current_world:get('DynamicEnemy01BehaviorState', entity)
    local actor = current_world:get('Actor', entity)
    local model = current_world:template('ModelResource', entity)
    local health = emf.health(current_world, entity)
    return {position={x=x,y=y,z=z}, birth=birth and birth.spawnTime,
      model=model and model.model, kind=ai and 'enemy' or (actor and 'actor' or 'static'),
      faction=faction and faction.faction, guard=ai and ai.guardEntityId,
      health=health, ready=actor and math.floor(actor.currentState / 2^50) % 2 == 1 or false}
  end,
}
local controller = body.new(env)
local last_state
local function log_transition()
  -- No component reads or position samples here; log changes only, not every tick.
  local snapshot = json.encode({epoch=controller.epoch, mode=controller.mode,
    entity_id=controller.body and controller.body.id,
    marker_id=controller.marker and controller.marker.id,
    pending_id=controller.pending and controller.pending.id,
    last_error=controller.last_error, recovery_required=controller.recovery})
  if snapshot ~= last_state then
    emf.log('AIC_STATE ' .. snapshot)
    last_state = snapshot
  end
end
local function run(world, fn)
  if not world:is_server() then return end
  current_world, entity_ids = world, nil
  local ok, result = pcall(fn)
  if not ok then
    controller:halt('callback_error')
  end
  pcall(log_transition) -- diagnostics must not change command execution
  current_world, entity_ids = nil, nil -- no game/component pointers escape the callback
  if not ok then
    emf.log('Body adapter halted: ' .. tostring(result))
    return {protocol=1, error='callback_error'}
  end
  return result
end
local function reply(result)
  emf.reply('AIC_BODY ' .. json.encode(result or {protocol=1,error='host_required'}))
end
emf.command('request', '<request-id> <epoch> <companion-id> <spawn|follow|stay|dismiss>', function(world, args)
  local sender = emf.sender()
  if sender and sender.chat then reply({protocol=1,error='local_console_only'}); return end
  if #args ~= 4 then reply({protocol=1,error='invalid_request'}); return end
  local result = run(world, function() return controller:request(args[1], args[2], args[3], args[4]) end)
  emf.log('AIC_REQUEST ' .. json.encode(result or {protocol=1,error='host_required'}))
  reply(result)
end)
emf.command('status', '[request-id]: structured observation; no spawn', function(world, args)
  if #args > 1 then reply({protocol=1,error='invalid_request'}); return end
  reply(run(world, function() return controller:status(args[1]) end))
end)
emf.on_tick(function(world) run(world, function() controller:step() end) end)
emf.on_event('EntityDiedEvent', function(world, event)
  run(world, function() controller:died(event.deadEntityId) end)
end, 'server')
emf.log('Body adapter loaded; no automatic spawn. Commands: aic_body.status / aic_body.request')
