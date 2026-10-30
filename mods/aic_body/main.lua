-- EMF Lua API, pinned sources and semantics: docs/PROTOCOL.md.
local body = require('body')
local json = require('json')
emf.emits({'StartGuardingEvent', 'StopGuardingEvent'})
local current_world
local lock_path = emf.dir .. '/runtime.lock'
local function read_lock()
  local f = io.open(lock_path, 'r')
  if not f then return nil end
  local text = f:read('*l'); f:close(); return text
end
local env = {
  instance=(tostring({}) .. string.format('%.9f', os.clock())):gsub('[^%w]', ''),
  session=function() return emf.session_token() end,
  owner=function() return emf.local_player() end,
  locked=function(session) return read_lock() == session end,
  lock=function(session)
    local f = io.open(lock_path, 'w')
    if not f then return false end
    local ok = f:write(session .. '\n'); local closed = f:close()
    return ok ~= nil and closed ~= nil and read_lock() == session
  end,
  unlock=function()
    if read_lock() == nil then return true end
    return os.remove(lock_path) ~= nil
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
  current_world = world
  local ok, result = pcall(fn)
  pcall(log_transition) -- diagnostics must not change command execution
  current_world = nil -- no game/component pointers escape the callback
  if not ok then
    controller.recovery, controller.mode = true, 'recovery_required'
    controller.last_error = 'callback_error'
    controller:finish('failed', 'callback_error')
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
