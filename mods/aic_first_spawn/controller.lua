-- Experimental policy, not production ownership or a general purpose spawn API.
local M={GUID='a1c90001-5e4d-4a91-8a1c-000000000001', NPC=2939921867}
function M.new(api, binding)
 assert(binding.guid==M.GUID and binding.build==1287369, 'binding')
 local c={state='NEW', reason='', attempted=false, entity=nil}
 local session,player,origin,target,ready_at,started,probe_id
 local function fail(reason)
  c.state='STOPPED'; c.reason=reason; api.log('STOPPED '..reason)
 end
 local function finite(n) return type(n)=='number' and n==n and math.abs(n)<100000 end
 local function position(p) return type(p)=='table' and finite(p.x) and finite(p.y) and finite(p.z) end
 local function distance(a,b) return math.sqrt((a.x-b.x)^2+(a.y-b.y)^2+(a.z-b.z)^2) end
 local function context(w)
  return api.context(w,session,player) and position(api.position(w,player))
 end
 local function still(w, expected)
  if c.state~=expected then return false end
  if not context(w) or api.now()-started>20 or api.now()<started then fail('context_or_timeout');return false end
  if distance(api.position(w,player),origin)>0.25 then fail('player_moved');return false end
  return true
 end
 function c.status(w)
  if session and (not context(w) or (c.state=='READY' and (api.now()-ready_at>20 or api.now()<ready_at))) then fail('stale_session_or_position') end
  if (c.state=='GROUND' or c.state=='PATH') and (api.now()-started>20 or api.now()<started) then fail('query_timeout') end
  return {state=c.state,reason=c.reason,session=api.session(),player=api.player(),
   probe=probe_id,position=target,entity=c.entity,attempted=c.attempted,
   experimental_spawn_executed=c.attempted,production_spawn_ready=false,spawn_ready=false,
   render='UNKNOWN',identity='NO_INSTANCE_GENERATION',cleanup='MANUAL_CLOSE_NO_DESTROY'}
 end
 function c.probe(w, s, p, nonce)
  if c.state~='NEW' or not api.unused() then fail('spent_or_reload_lock');return end
  session,player,probe_id=s,p,nonce; started=api.now()
  if not context(w) then fail('context');return end
  origin=api.position(w,player)
  if api.has_candidate(w,M.NPC) then fail('existing_or_ambiguous_candidate');return end
  c.state='GROUND';api.log('GROUND_REQUESTED '..nonce)
  local accepted=api.ground(w,origin.x+4,origin.z,function(world,ok,x,y,z,why,hop,fog,water)
   if not still(world,'GROUND') then return end
   local at={x=x,y=y,z=z}
   if not ok or not position(at) or math.abs(x-(origin.x+4))>0.1 or math.abs(z-origin.z)>0.1
      or math.abs(y-origin.y)>0.75 or (fog~='none' and fog~='removed') or water~=nil then fail('ground_unconfirmed');return end
   target=at
   local d=distance(origin,target)
   if d<3 or d>5 then fail('distance');return end
   if api.wall(world,origin,target) then fail('building_obstruction');return end
   c.state='PATH'
   local query=api.path(world,origin,target,{width=0.6,height=2.2,jumps=false,doors=false,swim=false,closest=false,nodes=2000,owner=player},function(w2,r,points)
    if not still(w2,'PATH') then return end
    if type(r)~='table' or r.status~='found' or r.reaches~=true or type(points)~='table'
       or #points<1 or r.count~=#points or not finite(r.length) or r.length>8 then fail('path_unconfirmed');return end
    for _,pt in ipairs(points) do
     if not position(pt) or pt.move~=0 or pt.door~=nil then fail('non_walk_path');return end
    end
    if distance(points[#points],target)>0.5 then fail('path_endpoint');return end
    c.state='READY';ready_at=api.now();api.log('READY_VISUAL_APPROVAL_REQUIRED '..nonce)
   end)
   if not query then fail('path_refused') end
  end)
  if not accepted then fail('ground_refused') end
 end
 function c.spawn(w,s,p,nonce,authorization)
  if authorization~='I_APPROVE_ONE_DISPOSABLE_SPAWN' then fail('authorization');return end
  if c.state~='READY' or s~=session or p~=player or nonce~=probe_id or not api.unused() then fail('not_ready_or_spent');return end
  if not context(w) or api.now()-ready_at>20 or api.now()<ready_at or distance(api.position(w,player),origin)>0.25 then fail('stale_position');return end
  if api.has_candidate(w,M.NPC) then fail('candidate_appeared');return end
  if api.wall(w,origin,target) then fail('building_appeared');return end
  -- Persist and verify before the only mutation. Never reset on error or reload.
  if not api.consume() then fail('latch_write_failed');return end
  c.state='ATTEMPTED';c.attempted=true;api.log('SPAWN_ATTEMPT '..nonce)
  local ok,id=pcall(api.spawn,w,M.GUID,target.x,target.y+0.1,target.z)
  if not ok or type(id)~='number' or id<=0 or id%1~=0 or id>4294967295 then fail('spawn_outcome_unknown');return end
  c.entity=id;c.state='RETURNED_UNVERIFIED';api.log('ENTITY_ID_RETURNED '..tostring(id))
 end
 function c.observe(w)
  if not c.entity or not context(w) then fail('no_current_handle');return nil end
  local data=api.inspect(w,c.entity)
  -- Matching fields do not prove generation or ownership. Read only, always.
  if not data or data.npc~=M.NPC or data.faction~=11 or data.player then fail('entity_missing_or_mismatch');return nil end
  return data
 end
 function c.stop(reason) fail(reason or 'operator_stop') end
 if not api.unused() then fail('persisted_attempt_or_invalid_latch') end
 return c
end
return M
