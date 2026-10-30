-- Engine-independent controller. All effects are supplied by main.lua.
-- This module stores runtime handles only; personality lives in the Python profile.
local M = {}
local profile = require('body_profiles').active()
M.BODY_PROFILE = profile.id
M.BODY = profile.template
M.MARKER = profile.marker
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
  local unfinished = self.lock_owned or self.body or self.marker or self.uncertain_spawn or self.orphaned
  self.session = session
  self.epoch = session .. '-' .. self.env.instance
  self.records, self.count, self.seq = {}, 0, 0
  self.extra_dismiss = nil
  self.body, self.marker, self.pending, self.identity, self.owner = nil, nil, nil, nil, nil
  self.lock_owned, self.uncertain_spawn = false, false
  self.lock_text = 'aic-body-lock-v2\n' .. self.epoch .. '\n'
  self.mode, self.last_error = 'absent', ''
  self.orphaned = true -- retain the barrier if reading the file itself throws
  self.orphaned = not not (unfinished or self.env.locked())
  self.recovery = self.orphaned
  if self.recovery then self.mode, self.last_error = 'recovery_required', 'unresolved_runtime_lock' end
end
function C:finish(status, code)
  if self.pending then
    self.pending.status, self.pending.code = status, code
    self.pending.state_confirmed = status == 'succeeded'
    self.pending.phase = status == 'succeeded' and 'state_confirmed' or status
    self.pending.finished_tick = self.seq
    self.pending = nil
  end
  if status == 'failed' then self.last_error = code end
end
function C:halt(code)
  self.recovery, self.mode = true, 'recovery_required'
  self.last_error = code
  self:finish('failed', code)
end
function C:owned(handle)
  if not handle then return nil, 'absent' end
  if handle.gone then return nil, 'gone' end -- a reused ID can never regain ownership
  local sample = self.env.inspect(handle.id)
  if not sample then
    if not self.env.exists(handle.id) then
      handle.observed_missing = true
      if handle.absent_tick ~= self.seq then
        handle.absent_count = handle.absent_tick == self.seq-1 and (handle.absent_count or 0)+1 or 1
        handle.absent_tick = self.seq
      end
      if handle.absent_count >= 3 then handle.gone = true; return nil, 'gone' end
      return nil, 'absence_pending'
    end
    if handle.observed_missing then handle.invalidated = true end
    handle.absent_count = 0
    return nil, 'entity_unreadable'
  end
  if handle.observed_missing then handle.invalidated = true end
  handle.absent_count = 0
  if handle.invalidated then return nil, 'identity_changed' end
  if not handle.trusted then return nil, 'identity_unconfirmed' end
  if sample.model ~= handle.model or sample.birth ~= handle.birth or sample.kind ~= handle.kind then
    handle.invalidated = true
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
  local ok, b = pcall(self.owned, self, self.body)
  if not ok then b = nil end
  local target = self.mode == 'stay' and self.marker and self.marker.id or self.owner
  local target_ok, target_sample = true, nil
  if target then target_ok, target_sample = pcall(self.env.inspect, target) end
  if not target_ok then target_sample = nil end
  return {
    protocol=1, adapter='0.1.0', safety_revision=2, epoch=self.epoch, session=self.session,
    mode=self.mode, companion_id=self.identity, entity_id=self.body and self.body.id,
    marker_id=self.marker and self.marker.id, owner_id=self.owner,
    body_profile=M.BODY_PROFILE, template_guid=M.BODY, tick=self.seq, last_error=self.last_error,
    position=b and b.position, health=b and b.health, ready=b and b.ready,
    faction=b and b.faction, guard_target=b and b.guard,
    distance_to_target=b and target_sample and distance(b.position, target_sample.position),
    recovery_required=self.recovery,
    recovery_action=self.recovery and ((self.orphaned or self.uncertain_spawn) and 'manual_world_restore' or 'dismiss') or nil,
    uncertain_spawn=self.uncertain_spawn, orphaned=self.orphaned,
    body_trusted=self.body and self.body.trusted, marker_trusted=self.marker and self.marker.trusted,
    body_identity_invalidated=self.body and self.body.invalidated or false,
    marker_identity_invalidated=self.marker and self.marker.invalidated or false,
    body_destroy_requested=self.body and self.body.destroy_requested,
    marker_destroy_requested=self.marker and self.marker.destroy_requested,
    body_destroy_result=self.body and self.body.destroy_result,
    marker_destroy_result=self.marker and self.marker.destroy_result,
    behavior_verified=false,
    observation_error=(not ok or not target_ok) and 'inspect_failed' or nil,
  }
end
function C:reply(request, code)
  return {protocol=1, state=self:state(), request=request, error=code}
end
function C:status(id)
  self:sync()
  return self:reply(id and self.records[id], id and not self.records[id] and 'unknown_request' or nil)
end
function C:new_handle(handle)
  local s = self.env.inspect(handle.id)
  -- ModelResource is available through the confirmed Lua template API.
  -- SpawnTime is optional (plain emf.spawn does not add it). Never assume it exists.
  if not s or not s.model or not s.kind then return false end
  handle.birth, handle.model, handle.kind, handle.trusted = s.birth, s.model, s.kind, true
  return true
end
function C:create(which, guid, position)
  -- Preserve uncertainty even if the native call creates something and then throws/returns 0.
  self.uncertain_spawn = true
  local id = self.env.spawn(guid, position)
  if not id or id == 0 then return false, 'spawn_outcome_unknown' end
  self[which] = {id=id, trusted=false} -- store BEFORE reflection can fail
  self.uncertain_spawn = false
  if not self:new_handle(self[which]) then return false, 'fingerprint_missing' end
  return true
end
function C:emit_guard()
  local target = self.mode == 'stay' and self.marker and self.marker.id or self.owner
  if not self.body or not target then return false end
  local queued = self.env.guard(self.body.id, target, false)
  if self.pending then
    self.pending.event_submission = queued and 'queued' or 'enqueue_failed'
    self.pending.phase = queued and 'event_queued' or 'accepted'
  end
  return queued
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
  if self.recovery and action ~= 'dismiss' then return self:reply(nil, 'recovery_required') end
  if action == 'dismiss' and (self.orphaned or self.uncertain_spawn) then
    return self:reply(nil, 'manual_world_restore_required')
  end
  if self.identity and self.identity ~= identity then return self:reply(nil, 'different_companion') end
  if self.mode == 'lost' and action ~= 'dismiss' then return self:reply(nil, 'cleanup_required') end
  if self.pending and action ~= 'dismiss' then return self:reply(nil, 'busy') end
  if action ~= 'dismiss' and self.marker and self.marker.destroy_requested then
    return self:reply(nil, 'cleanup_required')
  end
  -- Capacity must never prevent cleanup of a live body. Dismiss is idempotent
  -- by effect and has one extra replaceable reply slot after the main cache fills.
  if self.count >= LIMIT and action ~= 'dismiss' then return self:reply(nil, 'request_capacity_restart_world') end
  if action ~= 'spawn' and action ~= 'dismiss' and not self.body then return self:reply(nil, 'no_body') end
  if action ~= 'dismiss' and self.mode == 'dismissing' then return self:reply(nil, 'cleanup_required') end
  if action == 'spawn' and (self.body or self.marker or self.lock_owned or self.mode == 'lost') then
    return self:reply(nil, 'body_exists_or_cleanup_required')
  end
  self:finish('cancelled', 'superseded_by_dismiss')
  local r = {id=id, action=action, companion_id=identity, status='accepted', code='queued', started_tick=self.seq,
    phase='accepted', event_submission='not_requested', state_confirmed=false, behavior_verified=false}
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
    self.orphaned = true -- also covers an exception during file I/O
    if not self.env.lock(self.lock_text) then
      self:halt('runtime_lock_write_failed'); return self:reply(r)
    end
    self.orphaned = false
    self.lock_owned = true
    self.identity, self.owner = identity, owner
    local pos = p.position
    local created, why = self:create('body', M.BODY, {x=pos.x+2, y=pos.y, z=pos.z})
    if not created then self:halt(why); return self:reply(r) end
    if self.body.kind ~= 'enemy' or not self.env.ally(self.body.id) then
      self:halt('body_setup_failed'); return self:reply(r)
    end
    self.mode = 'follow'
    if not self:emit_guard() then self:finish('failed', 'guard_enqueue_failed') end
  elseif action == 'dismiss' then
    self.mode = 'dismissing'
    local sample = self:owned(self.body)
    if sample and not self.body.destroy_requested then
      r.event_submission = self.env.guard(self.body.id, sample.guard or self.owner, true) and 'queued' or 'enqueue_failed'
    end
  else
    local b, why = self:owned(self.body)
    if not b or not b.health or b.health <= 0 then
      self:forget_body(why or 'body_dead'); return self:reply(r)
    end
    if action == 'stay' and not self.marker then
      local created, why = self:create('marker', M.MARKER, b.position)
      if not created then self:halt('marker_' .. why); return self:reply(r) end
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
    if why == 'gone' then return true end
    if why == 'absence_pending' then return false end
    return false, why
  end
  if handle.destroy_requested then return false end -- never resend an accepted/unknown destroy
  handle.destroy_requested = true -- a throw after side effects must not cause replay
  handle.destroy_result = 'outcome_unknown'
  local ok, removed = pcall(self.env.destroy, handle.id)
  if not ok then return false, 'destroy_outcome_unknown' end
  -- Native guarded_destroy also returns false after an SEH fault. It does not
  -- prove that no side effect occurred, so even an explicit retry only observes.
  if not removed then handle.destroy_result = 'refused_or_unknown'; return false, 'destroy_refused' end
  handle.destroy_result = 'accepted'
  return false -- An accepted destroy is not proof of disappearance. Check next tick.
end
function C:step()
  self:sync()
  self.seq = self.seq + 1
  local r = self.pending
  if self.recovery and not (r and r.action == 'dismiss') then
    -- Observe late disappearance after a partial cleanup, but never retry side effects.
    -- Keep each absence observation tied to a distinct callback, not repeated status reads.
    pcall(self.owned, self, self.body)
    pcall(self.owned, self, self.marker)
    return
  end
  if r and self.seq-r.started_tick > DEADLINE then
    if r.action == 'dismiss' then self:halt('cleanup_timeout') else self:finish('failed', 'verification_timeout') end
    return
  end
  if self.mode == 'dismissing' and r then
    if self.seq-r.started_tick < 2 then return end -- allow queued StopGuardingEvent to be consumed
    local body_done, body_err = self:remove(self.body)
    local marker_done, marker_err = self:remove(self.marker)
    if body_err or marker_err then self:halt(body_err or marker_err); return end
    if body_done then self.body = nil end
    if marker_done then self.marker = nil end
    if body_done and marker_done then
      if self.lock_owned and not self.env.unlock(self.lock_text) then self:halt('runtime_lock_remove_failed'); return end
      self.mode, self.recovery, self.lock_owned = 'absent', false, false
      self.identity, self.owner = nil, nil
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
  if self.body and self.body.id == entity and self.mode ~= 'dismissing' and not self.recovery then
    self:forget_body('body_died_event')
  end
end
return M
