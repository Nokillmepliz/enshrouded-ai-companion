-- Bounded, explicitly armed follow session; optional per-NPC schedule lease.
local M={}
local function point(p)
 return type(p)=='table' and type(p.x)=='number' and type(p.y)=='number' and type(p.z)=='number'
  and p.x==p.x and p.y==p.y and p.z==p.z and math.abs(p.x)<1e6 and math.abs(p.y)<1e6 and math.abs(p.z)<1e6
end
local function dist(a,b) return math.sqrt((a.x-b.x)^2+(a.y-b.y)^2+(a.z-b.z)^2) end
local function across(a,b) return math.sqrt((a.x-b.x)^2+(a.z-b.z)^2) end
function M.new(api,discover,config)
 -- The new profile shortens retarget latency; native orders remain serialized.
 local responsive=config.responsive==true
 local retarget_distance=responsive and 3 or 8
 local retarget_seconds=responsive and 2 or 8
 local dispatch_seconds=responsive and 1 or 4
 local c={state='STOPPED',reason='NOT_STARTED',orders=0,recoveries=0,probes=0,seq=0,used=false}
 local started,heartbeat,last,session,entity,order,pending,ready,epoch=0,0,-100,nil,nil,nil,nil,nil,0
 local following=false
 local candidate=0
 local retry_at=-100
 local function reject(why)
  pending=nil;ready=nil;epoch=epoch+1;last=api.now()
  retry_at=last+4 -- Faster dispatch must not burn the bounded budget on refusals.
  candidate=(candidate+1)%8;c.state="RECOVERING";c.reason=why
  api.log("CANDIDATE_REJECTED",{reason=why,next_candidate=candidate})
 end
 local inflight,requested=0,0
 local function log(event,data) api.log(event,data or {}) end
 local function inspect(w)
  local d=discover(w)
  assert(d.result=='FOUND_ONE','NO_UNIQUE_NPC')
  if session then assert(d.session==session and d.entity==entity,'IDENTITY_CHANGED') end
  return d
 end
 -- Cancellation is queued by commands; only watch() calls the native API.
 -- That call may synchronously invalidate w. It is the LAST world operation.
 local cancellation=nil
 local cleanup_at=-100
 c.cleanup='NONE'
 local function cancel(w,d)
  if order and order.id then
   cancellation=cancellation or {id=order.id,requested=false}
  else order=nil end
 end
 function c.stop(w,why)
  -- Pure Lua state change: w may already be invalid after an engine callback.
  if c.state~='STOPPED' or not c.used then
   c.state='STOPPED';c.reason=why;epoch=epoch+1;pending=nil;ready=nil
   log('STOPPED',{reason=c.reason})
  end
  if order and order.id then cancel() end
  if cancellation or (api.schedule and api.schedule.lease) then c.cleanup='PENDING' end
 end
 local function cancellation_tick(w,d)
  if not cancellation then return false end
  local q=cancellation
  local active=api.moving(w,d.entity)
  if active~=q.id then
   if active then
    -- Never cancel a foreign order, but still release our schedule lease.
    c.stop(nil,'FOREIGN_ORDER');log('FOREIGN_ORDER_LEFT_UNCHANGED',{id=active})
   end
   log('CANCEL_CONFIRMED',{id=q.id});cancellation=nil;order=nil;return false
  end
  if q.requested then
   if api.now()-q.at>=5 then
    c.stop(nil,'CANCEL_TIMEOUT');cancellation=nil;order=nil
    -- Do not retry an uncertain cancellation. Original order has a finite deadline.
    log('CANCEL_UNRESOLVED',{id=q.id});return true
   end
   return true
  end
  q.requested=true;q.at=api.now()
  log('CANCEL_REQUEST',{id=q.id})
  local ok,accepted=pcall(api.cancel,q.id)
  if not ok or accepted~=true then
   c.stop(nil,'CANCEL_UNCONFIRMED')
   log('CANCEL_ERROR',{id=q.id,error=tostring(accepted)})
  end
  return true -- NEVER read w, discover, status or release here, even after failure.
 end
 local function fresh(w)
  assert(c.state~='STOPPED','SESSION_STOPPED')
  local now=api.now()
  assert(now>=started and now-started<(config.seconds or 180) and now-heartbeat<=4,'SESSION_OR_HEARTBEAT_EXPIRED')
  return inspect(w)
 end
 local function probe(w,d,p)
  assert(inflight==0,'QUERY_ALREADY_PENDING')
  if c.probes>=30 then c.stop(w,'PROBE_LIMIT');return end
  c.probes=c.probes+1
  epoch=epoch+1;local e=epoch;local origin=d.position;local player_origin=p
  local dx,dz=origin.x-p.x,origin.z-p.z;local length=math.sqrt(dx*dx+dz*dz)
  if length<0.01 then dx,dz,length=1,0,1 end
  -- Eight bounded destination candidates around the player; engine chooses the route.
  local angle=candidate*math.pi/4
  dx,dz=(dx*math.cos(angle)-dz*math.sin(angle))/length,(dx*math.sin(angle)+dz*math.cos(angle))/length
  local target={x=p.x+1.8*dx,y=p.y,z=p.z+1.8*dz}
  pending={at=api.now(),stage='GROUND'};c.state='FOLLOWING'
  local function valid(world)
   if e~=epoch or c.state=='STOPPED' then return false end
   local ok,dd=pcall(fresh,world)
   if not ok then c.stop(world,'PROBE_CONTEXT');return false end
   local pp=api.position(world,dd.player)
   if not point(pp) then c.stop(world,'PLAYER_POSITION_MISSING');return false end
   -- Target is a destination snapshot, not a copy of the player's trajectory.
   -- Native villager_move will plan again from the actual NPC position.
   -- Roaming during this read-only query must not starve destination selection.
   return true
  end
  local ground_done=false;inflight=1;requested=api.now()
  local accepted=api.ground(w,target.x,target.z,function(world,ok,x,y,z,why,hop,fog,water)
   if ground_done then return end;ground_done=true;inflight=0
   if not valid(world) then return end
   log('GROUND',{ok=ok,x=x,y=y,z=z,fog=fog,water=water,why=why,origin=origin,player=player_origin})
   local at={x=x,y=y,z=z}
   if not ok or not point(at) or math.abs(x-target.x)>0.1 or math.abs(z-target.z)>0.1
    or (fog~='none' and fog~='removed') or water~=nil then
    reject('GROUND_REFUSED');return
   end
   log('DIRECT_WALL',{blocked=api.wall(world,origin,at)}) -- An obstruction may have a navigable detour.
   origin=inspect(world).position
   pending.stage='PATH'
   local path_done=false;inflight=1;requested=api.now()
   local query=api.path(world,origin,at,{width=0.6,height=2.2,jumps=true,max_jump_down=0,max_jump_up=0,doors=false,swim=false,closest=false,nodes=5000,owner=d.player},function(ww,r,points)
    if path_done then return end;path_done=true;inflight=0
    if not valid(ww) then return end
    log('PATH',{result=r})
    local good=type(r)=='table' and r.status=='found' and r.reaches==true and type(points)=='table'
      and #points>0 and r.count==#points and type(r.length)=='number' and r.length>=0 and r.length<=200
    if good then
     for _,pt in ipairs(points) do if not point(pt) or (pt.move~=0 and pt.move~=2 and pt.move~=3 and pt.move~=4) or pt.door~=nil then good=false end end
     good=good and dist(points[#points],at)<=0.5
    end
    if not good then reject('PATH_REFUSED');return end
    ready={target=at,origin=origin,player=player_origin,at=api.now()};pending=nil
   end)
   if not query and not path_done then path_done=true;inflight=0;reject('PATH_API_REFUSED') end
  end)
  if not accepted and not ground_done then ground_done=true;inflight=0;reject('GROUND_API_REFUSED') end
 end
 function c.start(w,token,expected_session,expected_entity)
  assert(not c.used and token==config.token,'SESSION_ALREADY_USED_OR_TOKEN')
  local d=inspect(w)
  assert(d.session==expected_session and d.entity==expected_entity,'START_IDENTITY')
  assert(not api.moving(w,d.entity),'FOREIGN_ORDER')
  assert(api.consume(),'DURABLE_SESSION_LATCH')
  c.used=true;session=d.session;entity=d.entity;started=api.now();heartbeat=started
  c.state='WAITING_FOR_PLAYER';c.reason='';log('START',{roaming=config.roaming,identity='PROFILE_ONLY'})
  if api.schedule then api.schedule.acquire(w,d) end
 end
 function c.step(w,token,seq)
  assert(token==config.token and seq==c.seq+1,'TOKEN_OR_SEQUENCE');c.seq=seq
  if c.used and c.state=='STOPPED' then return end
  local d=fresh(w);heartbeat=api.now()
  if cancellation then return end
  if api.wake and api.wake.pending then return end -- exclusively owned by native wake command
  local p=api.position(w,d.player)
  assert(point(p),'PLAYER_POSITION_MISSING')
  local distance=dist(p,d.position);local active=api.moving(w,d.entity)
  assert(not active or (order and active==order.id),'FOREIGN_ORDER')
  local awake=not api.schedule or api.schedule.update(w,d)
  if awake and c.reason=='NATIVE_WAKE_PENDING' then c.reason='' end
  if across(p,d.position)>50 then following=false elseif across(p,d.position)<=20 then following=true end
  if order and order.result then
   log('ORDER_RESULT',{id=order.id,result=order.result,seconds=api.now()-order.at,
    displacement=dist(order.origin,d.position),target_distance=dist(order.target,d.position),
    initial_player_distance=order.initial_distance,current_player_distance=distance})
   local result=order.result;order.result=nil
   if result=='stuck' or result=='timeout' then
    cancel(w,d);last=api.now()
    if c.recoveries>=2 then c.stop(w,'RECOVERY_LIMIT');return end
    c.recoveries=c.recoveries+1;candidate=(candidate+1)%8
    c.state=result=='stuck' and 'STUCK' or 'RECOVERING';c.reason=result;return
   elseif result=='arrived' then
    c.reason=dist(order.target,d.position)<=0.75 and 'ARRIVAL_OBSERVED' or 'ENGINE_ARRIVED_SHORT'
    if config.roaming=='native' or not active then order=nil end
   else c.stop(w,'ORDER_'..tostring(result));return end
  end
  if not following or distance<=2 then
   if not following or config.roaming=='native' then cancel(w,d) end
   -- hold is only an already accepted arrival hold, never a new far-away command.
   if order and active and not order.holding then cancel(w,d) end
   epoch=epoch+1;pending=nil;ready=nil
   c.state=not following and 'WAITING_FOR_PLAYER' or 'IDLE_NEAR_PLAYER';return
  end
  if not awake then c.state='WAITING_FOR_NPC';c.reason='NATIVE_WAKE_PENDING';return end
  if distance<2.8 and c.state=='IDLE_NEAR_PLAYER' then return end
  if order and active then
   log('PROGRESS',{id=order.id,player_distance=distance,target_distance=dist(order.target,d.position),
    displacement=dist(order.origin,d.position),initial_player_distance=order.initial_distance})
   if (dist(p,order.player)>retarget_distance or (responsive and order.holding and distance>2.8))
    and api.now()-last>=retarget_seconds then
    log('RETARGET_REQUEST',{id=order.id,player_displacement=dist(p,order.player)})
    cancel(w,d);last=api.now();c.state='FOLLOWING';return
   end
   if order then c.state='MOVING';return end
  elseif order then
   if order.holding then order=nil else c.stop(w,'ORDER_DISAPPEARED');return end
  end
  if pending then
   if api.now()-pending.at>12 then c.stop(w,'PROBE_TIMEOUT') end
   return
  end
  if inflight>0 then
   if api.now()-requested>12 then c.stop(w,'ABANDONED_QUERY_TIMEOUT') end
   return
  end
  if api.now()-last<dispatch_seconds or api.now()<retry_at then c.state='RECOVERING';return end
  if d.ai_state==1 or d.ai_state==2 or d.ai_state==8 or d.ai_state==16 or d.decision==5 then
   c.state='WAITING_FOR_NPC';c.reason='NPC_ASLEEP_OR_BUSY';return
  end
  if not ready then probe(w,d,p);return end
  local r=ready;ready=nil
  if api.now()-r.at>4 then reject('STALE_PATH');return end
  -- Only approach useful destinations; proximity is 3D, so another floor is not arrival.
  if dist(p,r.target)>=distance or (across(p,r.target)<1.5 and math.abs(p.y-r.target.y)<2) then
   reject('TARGET_NO_LONGER_USEFUL');return
  end
  if c.orders>=24 then c.stop(w,'ORDER_LIMIT');return end
  c.orders=c.orders+1;last=api.now()
  -- Measure later retargeting against the player used for this destination,
  -- not a newer sample taken after the asynchronous query finished.
  local o={at=last,origin=d.position,target=r.target,player=responsive and r.player or p,initial_distance=distance};order=o
  log('MOVE_INTENT',{number=c.orders,target=r.target})
  local id,why=api.move(w,entity,r.target,{arrive=0.5,seconds=30,stuck=8,hold=config.roaming=='hold' and 5 or 0},function(_,mid,result)
   if order==o then o.result=result;o.holding=result=='arrived' end
  end)
  if not id then order=nil;reject('MOVE_REFUSED');log('MOVE_REFUSED',{reason=why});return end
  o.id=id;c.state='MOVING';log('ACCEPTED',{id=id,target=r.target})
 end
 function c.watch(w)
  if not c.used then return end
  if c.state~='STOPPED' then
   local ok,d=pcall(fresh,w)
   if not ok then c.stop(nil,'WATCHDOG_CONTEXT_OR_DEADLINE')
   elseif api.schedule then
    local maintained,why=pcall(api.schedule.update,w,d)
    if not maintained then log('SCHEDULE_ERROR',{error=tostring(why)});c.stop(nil,'SCHEDULE_ERROR') end
   end
  end
  if c.state=='STOPPED' and c.cleanup=='DONE' then return end
  if c.state~='STOPPED' and api.wake and api.schedule and api.schedule.lease
   and following and not order and not cancellation and not pending and not ready then
   local ok,blocked=pcall(function() return api.wake.tick(w,inspect(w)) end)
   if not ok then
    log('WAKE_ERROR',{error=tostring(blocked)});c.stop(nil,'WAKE_ERROR');return
   end
   if blocked then return end -- emit may invalidate w; cleanup waits for a fresh tick.
  end
  if c.state=='STOPPED' and api.now()<cleanup_at then return end
  local ok,err=pcall(function()
   local d=inspect(w) -- Fresh identity also required after STOPPED; never cancel a foreign order.
   if cancellation_tick(w,d) then return end
   if c.state=='STOPPED' then
    if api.schedule and api.schedule.lease then api.schedule.release(w,d) end
    c.cleanup='DONE';log('CLEANUP_COMPLETE',{})
   end
  end)
  if not ok then
   c.stop(nil,'CLEANUP_ERROR');c.cleanup='PENDING';cleanup_at=api.now()+1
   log('CLEANUP_PENDING',{error=tostring(err)})
  end
 end
 function c.status(w)
  local d=inspect(w);local p=api.position(w,d.player)
  return {discovery={session=d.session,player=d.player,entity=d.entity,result=d.result,position=d.position,
   home=d.home,ai_state=d.ai_state,decision=d.decision},player_position=p,
   distance=point(p) and dist(p,d.position) or nil,state=c.state,reason=c.reason,orders=c.orders,
   recoveries=c.recoveries,probes=c.probes,roaming=config.roaming,cleanup=c.cleanup,order=order and order.id or nil,
   target=order and order.target or nil,probe=pending and pending.stage or nil,
   wake=api.wake and api.wake.state or nil}
 end
 return c
end
return M
