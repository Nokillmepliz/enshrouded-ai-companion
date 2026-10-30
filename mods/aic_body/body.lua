-- Engine-independent controller. All effects are supplied by main.lua.
-- This module stores runtime handles only; personality lives in the Python profile.
local M = {}
M.BODY = 'd5d05217-52dc-467a-9192-26b4f661d8d9'
M.MARKER = '0ce28db1-522f-4455-b358-3888fb5e089b'
local LIMIT, DEADLINE, ARRIVE = 128, 1800, 8
local actions = {spawn=true, follow=true, stay=true, dismiss=true}
local C = {}; C.__index = C
local function token(s)
  return type(s) == 'string' and #s >= 1 and #s <= 96 and s:match('^[%w_-]+$') ~= nil
end
local function distance(a, b)
  if not a or not b then return nil end
  return math.sqrt((a.x-b.x)^2 + (a.y-b.y)^2 + (a.z-b.z)^2)
end
function M.new(env)
  return setmetatable({env=env, session='', records={}, count=0, seq=0}, C)
end
function C:sync()
  local session = self.env.session()
  if session == self.session then return end
  self.session = session
  self.epoch = session .. '-' .. self.env.instance
  self.records, self.count, self.seq = {}, 0, 0
  self.extra_dismiss = nil
  self.body, self.marker, self.pending, self.identity, self.owner = nil, nil, nil, nil, nil
  self.mode, self.last_error = 'absent', ''
  self.recovery = self.env.locked(session)
  if self.recovery then self.mode, self.last_error = 'recovery_required', 'reload_with_live_body' end
end
function C:finish(status, code)
  if self.pending then
    self.pending.status, self.pending.code = status, code
    self.pending.finished_tick = self.seq
    self.pending = nil
  end
  if status == 'failed' then self.last_error = code end
end
function C:owned(handle)
  if not handle then return nil, 'absent' end
  local sample = self.env.inspect(handle.id)
  if not sample then return nil, 'gone' end
  if sample.model ~= handle.model or sample.birth ~= handle.birth or sample.kind ~= handle.kind then
    return nil, 'identity_changed'
  end
  return sample
end
function C:forget_body(reason)
  self.mode, self.last_error = 'lost', reason
  self:finish('failed', reason)
  -- Keep the lock and marker until explicit dismiss; never auto-respawn.
end
function C:state()
  local b = self:owned(self.body)
  local target = self.mode == 'stay' and self.marker and self.marker.id or self.owner
  local target_sample = target and self.env.inspect(target)
  return {
    protocol=1, adapter='0.1.0', epoch=self.epoch, session=self.session,
    mode=self.mode, companion_id=self.identity, entity_id=self.body and self.body.id,
    marker_id=self.marker and self.marker.id, owner_id=self.owner,
    template_guid=M.BODY, tick=self.seq, last_error=self.last_error,
    position=b and b.position, health=b and b.health, ready=b and b.ready,
    faction=b and b.faction, guard_target=b and b.guard,
    distance_to_target=b and target_sample and distance(b.position, target_sample.position),
    recovery_required=self.recovery,
  }
end
function C:reply(request, code)
  return {protocol=1, state=self:state(), request=request, error=code}
end
function C:status(id)
  self:sync()
  return self:reply(id and self.records[id], id and not self.records[id] and 'unknown_request' or nil)
end
function C:new_handle(id)
  local s = self.env.inspect(id)
  -- ModelResource is available through the confirmed Lua template API.
  -- SpawnTime is optional (plain emf.spawn does not add it). Never assume it exists.
  if not s or not s.model then return nil end
  return {id=id, birth=s.birth, model=s.model, kind=s.kind}
end
function C:emit_guard()
  local target = self.mode == 'stay' and self.marker and self.marker.id or self.owner
  if not self.body or not target then return false end
  return self.env.guard(self.body.id, target, false)
end
function C:request(id, epoch, identity, action)
  self:sync()
  if not token(id) or not token(identity) or not token(epoch) or not actions[action] then
    return self:reply(nil, 'invalid_request')
  end
  if epoch ~= self.epoch then return self:reply(nil, 'stale_epoch') end
  local old = self.records[id]
  if old then
    if old.action ~= action or old.companion_id ~= identity then return self:reply(nil, 'request_id_conflict') end
    return self:reply(old)
  end
  if self.recovery then return self:reply(nil, 'recovery_required') end
  if self.identity and self.identity ~= identity then return self:reply(nil, 'different_companion') end
  if self.mode == 'lost' and action ~= 'dismiss' then return self:reply(nil, 'cleanup_required') end
  if self.pending and action ~= 'dismiss' then return self:reply(nil, 'busy') end
  -- Capacity must never prevent cleanup of a live body. Dismiss is idempotent
  -- by effect and has one extra replaceable reply slot after the main cache fills.
  if self.count >= LIMIT and action ~= 'dismiss' then return self:reply(nil, 'request_capacity_restart_world') end
  if action ~= 'spawn' and action ~= 'dismiss' and not self.body then return self:reply(nil, 'no_body') end
  if action == 'spawn' and (self.body or self.marker or self.mode == 'lost') then
    return self:reply(nil, 'body_exists_or_cleanup_required')
  end
  self:finish('cancelled', 'superseded_by_dismiss')
  local r = {id=id, action=action, companion_id=identity, status='accepted', code='queued', started_tick=self.seq}
  if self.count >= LIMIT and self.extra_dismiss then self.records[self.extra_dismiss] = nil end
  if self.count >= LIMIT then self.extra_dismiss = id else self.count = self.count+1 end
  self.records[id], self.pending = r, r
  self.last_error = ''
  if action == 'spawn' then
    local owner = self.env.owner()
    local p = owner and self.env.inspect(owner)
    if not owner or owner == 0 or not p or not p.position then
      self:finish('failed', 'local_host_player_missing'); return self:reply(r)
    end
    -- Persist a sentinel BEFORE spawning. Reloading this script cannot cause a duplicate.
    if not self.env.lock(self.session) then
      self:finish('failed', 'runtime_lock_write_failed'); return self:reply(r)
    end
    self.identity, self.owner = identity, owner
    local pos = p.position
    local entity = self.env.spawn(M.BODY, {x=pos.x+2, y=pos.y, z=pos.z})
    if not entity or entity == 0 then
      self.env.unlock(); self:finish('failed', 'spawn_refused'); return self:reply(r)
    end
    -- Only this just-created ID may be rolled back without a captured fingerprint.
    self.body = self:new_handle(entity)
    if not self.body or self.body.kind ~= 'enemy' or not self.env.ally(entity) then
      local removed = self.env.destroy(entity)
      self.recovery, self.mode = true, 'recovery_required'
      self:finish('failed', removed and 'unsupported_body_rollback_requested' or 'unsupported_body_cleanup_failed')
      return self:reply(r)
    end
    self.mode = 'follow'
    if not self:emit_guard() then self:finish('failed', 'guard_enqueue_failed') end
  elseif action == 'dismiss' then
    self.mode = 'dismissing'
    local sample = self:owned(self.body)
    if sample then self.env.guard(self.body.id, sample.guard or self.owner, true) end
  else
    local b, why = self:owned(self.body)
    if not b or not b.health or b.health <= 0 then
      self:forget_body(why or 'body_dead'); return self:reply(r)
    end
    if action == 'stay' and not self.marker then
      local marker = self.env.spawn(M.MARKER, b.position)
      if not marker or marker == 0 then self:finish('failed', 'marker_spawn_refused'); return self:reply(r) end
      self.marker = self:new_handle(marker)
      if not self.marker then
        self.env.destroy(marker)
        self.recovery, self.mode = true, 'recovery_required'
        self:finish('failed', 'marker_fingerprint_missing'); return self:reply(r)
      end
    end
    if action == 'stay' then
      local marker, marker_error = self:owned(self.marker)
      if not marker then self:finish('failed', 'marker_' .. marker_error); return self:reply(r) end
    end
    self.mode = action
    if not self:emit_guard() then self:finish('failed', 'guard_enqueue_failed') end
  end
  return self:reply(r)
end
function C:remove(handle)
  if not handle then return true end
  local sample, why = self:owned(handle)
  if not sample then
    if why == 'identity_changed' then return false, why end
    return true
  end
  if not self.env.destroy(handle.id) then return false, 'destroy_refused' end
  return false -- An accepted destroy is not proof of disappearance. Check next tick.
end
function C:step()
  self:sync()
  self.seq = self.seq + 1
  if self.recovery then return end
  local r = self.pending
  if r and self.seq-r.started_tick > DEADLINE then self:finish('failed', 'verification_timeout'); return end
  if self.mode == 'dismissing' and r then
    if self.seq-r.started_tick < 2 then return end -- allow queued StopGuardingEvent to be consumed
    local body_done, body_err = self:remove(self.body)
    local marker_done, marker_err = self:remove(self.marker)
    if body_err or marker_err then self:finish('failed', body_err or marker_err); return end
    if body_done then self.body = nil end
    if marker_done then self.marker = nil end
    if body_done and marker_done then
      if not self.env.unlock() then self:finish('failed', 'runtime_lock_remove_failed'); return end
      self.mode = 'absent'
      self:finish('succeeded', 'body_and_marker_absent')
    end
    return
  end
  if not self.body then return end
  local b, why = self:owned(self.body)
  if not b then self:forget_body(why); return end
  if b.health and b.health <= 0 then self:forget_body('body_dead'); return end
  if not r then return end -- no automatic guard retries or respawn when the client leaves
  local target = self.mode == 'stay' and self.marker and self.marker.id or self.owner
  local t = target and self.env.inspect(target)
  if self.mode == 'stay' then
    local marker, marker_error = self:owned(self.marker)
    if not marker then self:finish('failed', 'marker_' .. marker_error); return end
  end
  if not t or not t.position then self:finish('failed', 'target_missing'); return end
  if not b.health or b.health <= 0 or not b.ready or b.faction ~= 11 or b.guard ~= target then
    r.stable_ticks = 0; return
  end
  local d = distance(b.position, t.position)
  if not d or d > ARRIVE then r.stable_ticks = 0; return end
  -- Delete an old stay marker only once the guard has switched back to its owner.
  if self.mode == 'follow' and self.marker then
    local done, err = self:remove(self.marker)
    if err then self:finish('failed', 'marker_' .. err); return end
    if not done then return end
    self.marker = nil
  end
  r.stable_ticks = (r.stable_ticks or 0)+1
  if r.stable_ticks >= 3 then self:finish('succeeded', 'guard_and_proximity_observed') end
end
function C:died(entity)
  self:sync()
  if self.body and self.body.id == entity then self:forget_body('body_died_event') end
end
return M
