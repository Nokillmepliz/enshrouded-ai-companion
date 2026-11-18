-- 0.1.1 bounded read-only search; spawn is a separate authorized mutation.
local M={GUID='a1c90001-5e4d-4a91-8a1c-000000000001',NPC=2939921867}
local function finite(n) return type(n)=='number' and n==n and math.abs(n)<100000 end
local function position(p) return type(p)=='table' and finite(p.x) and finite(p.y) and finite(p.z) end
local function distance(a,b) return math.sqrt((a.x-b.x)^2+(a.y-b.y)^2+(a.z-b.z)^2) end
function M.new(api,binding)
 assert(binding.guid==M.GUID and binding.build==1287369,'binding')
 local c={state='NEW',reason='',attempted=false,entity=nil}
 local session,player,origin,target,started,probe_id,selected
 local epoch,pending,history=0,0,{}
 local used={}
 local function fail(reason) c.state='STOPPED';c.reason=reason;api.log('STOPPED '..reason) end
 local function context(w) return api.context(w,session,player) and position(api.position(w,player)) end
 local function valid(w)
  if not context(w) then fail('context_changed');return false end
  if api.now()<started or api.now()-started>20 then fail('search_timeout');return false end
  if distance(api.position(w,player),origin)>0.25 then fail('player_moved');return false end
  return true
 end
 local function diagnostic(event,data)
  data.probe=probe_id;data.search=epoch
  if api.diagnostic then api.diagnostic(event,data) end
 end
 local function reject(row,reason)
  row.reason=reason;diagnostic('REJECT',{candidate=row.index,reason=reason})
 end
 local function ground_reason(row,ok,x,y,z,fog,water)
  if ok~=true then return 'ground_api_not_ok' end
  if not position({x=x,y=y,z=z}) then return 'ground_invalid_coordinates' end
  if math.abs(x-row.x)>0.1 or math.abs(z-row.z)>0.1 then return 'ground_xz_mismatch' end
  if math.abs(y-origin.y)>0.75 then return 'ground_height_delta' end
  if fog=='unknown' or fog==nil then return 'ground_fog_unknown' end
  if fog~='none' and fog~='removed' then return 'ground_fog_unsafe' end
  if water~=nil then return 'ground_water_present' end
  local at={x=x,y=y,z=z};local d=distance(origin,at)
  if d<3 or d>5 then return 'ground_distance' end
  return nil,at
 end
 local function path_reason(r,points,at)
  if type(r)~='table' or type(points)~='table' then return 'path_invalid_result' end
  if r.status~='found' then return 'path_not_found' end
  if r.reaches~=true then return 'path_not_reaching' end
  if #points<1 or r.count~=#points then return 'path_count' end
  if not finite(r.length) or r.length<0 or r.length>8 then return 'path_length' end
  for _,pt in ipairs(points) do
   if not position(pt) or pt.move~=0 or pt.door~=nil then return 'path_non_walk' end
  end
  if distance(points[#points],at)>0.5 then return 'path_endpoint' end
 end
 local next_path
 next_path=function(w,token,index)
  if token~=epoch or c.state=='STOPPED' or not valid(w) then return end
  for i=index,8 do
   local row=history[i]
   if row.at and not row.reason then
    local wall_ok,wall=pcall(api.wall,w,origin,row.at)
    if not wall_ok then fail('wall_api_error');return end
    diagnostic('WALL',{candidate=i,blocked=wall})
    if wall then reject(row,'building_obstruction')
    else
     c.state='PATH';pending=pending+1;local done=false
     local called,query=pcall(api.path,w,origin,row.at,
      {width=0.6,height=2.2,jumps=false,doors=false,swim=false,closest=false,nodes=2000,owner=player},
      function(w2,r,points)
       if done then return end;done=true;pending=pending-1
       if token~=epoch or c.state~='PATH' or not valid(w2) then return end
       diagnostic('PATH',{candidate=i,result=r})
       local reason=path_reason(r,points,row.at)
       if reason then reject(row,reason);next_path(w2,token,i+1);return end
       target=row.at;selected=i;c.state='READY';c.reason=''
       diagnostic('SELECTED',{candidate=i,position=target,age=api.now()-started})
       api.log('READY_VISUAL_APPROVAL_REQUIRED '..probe_id)
      end)
     if not called then fail('path_api_error_pending_unknown');return end
     if not query and not done then
      done=true;pending=pending-1;reject(row,'path_refused');next_path(w,token,i+1)
     end
     return
    end
   end
  end
  fail('no_safe_candidate')
 end
 function c.status(w)
  if started and c.state~='STOPPED' and not c.attempted then valid(w) end
  return {state=c.state,reason=c.reason,session=api.session(),player=api.player(),probe=probe_id,
   position=target,entity=c.entity,attempted=c.attempted,pending=pending,candidate=selected,
   search=epoch,recoverable=not c.attempted and api.unused() and pending==0,
   experimental_spawn_executed=c.attempted,production_spawn_ready=false,spawn_ready=false,
   render='UNKNOWN',identity='NO_INSTANCE_GENERATION',cleanup='MANUAL_CLOSE_NO_DESTROY'}
 end
 function c.probe(w,s,p,nonce)
  if c.attempted or not api.unused() then fail('spent_or_invalid_latch');return end
  if pending~=0 then fail('queries_pending');return end
  if used[nonce] then fail('probe_nonce_reused');return end
  used[nonce]=true;epoch=epoch+1;session,player,probe_id=s,p,nonce
  origin=nil;target=nil;selected=nil;history={};started=api.now();c.reason='';c.state='GROUND'
  if not context(w) then fail('context');return end
  origin=api.position(w,player)
  if api.has_candidate(w,M.NPC) then fail('existing_or_ambiguous_candidate');return end
  local token=epoch;local launching=true
  api.log('GROUND_REQUESTED '..nonce)
  for i=1,8 do
   local angle=(i-1)*math.pi/4
   history[i]={index=i,x=origin.x+4*math.cos(angle),z=origin.z+4*math.sin(angle)}
  end
  for i=1,8 do
   if c.state=='STOPPED' then break end
   local row=history[i];pending=pending+1;local done=false
   local called,accepted=pcall(api.ground,w,row.x,row.z,function(world,ok,x,y,z,why,hop,fog,water)
    if done then return end;done=true;pending=pending-1
    diagnostic('GROUND',{candidate=i,requested_x=row.x,requested_z=row.z,player_y=origin.y,
     api_ok=ok,ground_y_measured=ok==true,x=x,y=y,z=z,delta_y=finite(y) and y-origin.y or 'invalid',
     why=why,hop_y=hop or 'absent',fog=fog or 'absent',water_y=water or 'absent',
     stale=token~=epoch or c.state=='STOPPED'})
    if token~=epoch or c.state=='STOPPED' or not valid(world) then return end
    local reason,at=ground_reason(row,ok,x,y,z,fog,water)
    if reason then reject(row,reason) else row.at=at end
    if pending==0 and not launching then next_path(world,token,1) end
   end)
   diagnostic('GROUND_ACCEPTED',{candidate=i,accepted=called and accepted==true})
   if not called then fail('ground_api_error_pending_unknown');break end
   if not accepted and not done then done=true;pending=pending-1;reject(row,'ground_request_refused') end
  end
  launching=false
  if pending==0 and c.state~='STOPPED' then next_path(w,token,1) end
 end
 function c.spawn(w,s,p,nonce,authorization)
  if authorization~='I_APPROVE_ONE_DISPOSABLE_SPAWN' then fail('authorization');return end
  if c.attempted or c.state~='READY' or pending~=0 or s~=session or p~=player or nonce~=probe_id
      or not api.unused() then fail('not_ready_or_spent');return end
  if not valid(w) then return end
  if api.has_candidate(w,M.NPC) then fail('candidate_appeared');return end
  if api.wall(w,origin,target) then fail('building_appeared');return end
  if not api.consume() then fail('latch_write_failed');return end
  c.state='ATTEMPTED';c.attempted=true;api.log('SPAWN_ATTEMPT '..nonce)
  local ok,id=pcall(api.spawn,w,M.GUID,target.x,target.y+0.1,target.z)
  if not ok or type(id)~='number' or id<=0 or id%1~=0 or id>4294967295 then fail('spawn_outcome_unknown');return end
  c.entity=id;c.state='RETURNED_UNVERIFIED';api.log('ENTITY_ID_RETURNED '..tostring(id))
 end
 function c.observe(w)
  if not c.entity or not context(w) then fail('no_current_handle');return nil end
  local data=api.inspect(w,c.entity)
  if not data or data.npc~=M.NPC or data.faction~=11 or data.player then fail('entity_missing_or_mismatch');return nil end
  return data
 end
 function c.stop(reason) fail(reason or 'operator_stop') end
 if not api.unused() then fail('persisted_attempt_or_invalid_latch') end
 return c
end
return M
