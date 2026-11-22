-- Offline prototype. No component writes, persistence changes or spawn APIs.
local M={}
M.guid='a1c90001-5e4d-4a91-8a1c-000000000001'
M.npc=2939921867
local function finite(n) return type(n)=='number' and n==n and math.abs(n)<1000000 end
local function point(p) return p and finite(p.x) and finite(p.y) and finite(p.z) end
local function distance(a,b) return math.sqrt((a.x-b.x)^2+(a.y-b.y)^2+(a.z-b.z)^2) end
function M.new(api)
 local self={attempted=false}
 function self.discover(w)
  assert(api.context(w),'LOCAL_CONTEXT')
  local matches={}
  -- Count ALL matching npcIds, even wrong faction/incomplete components: GoToPosition addresses npcId.
  for _,id in ipairs(w:entities()) do
   local t=w:template('ActiveNpcState',id)
   if t and t.npcId==M.npc then matches[#matches+1]=id end
  end
  local r={result=#matches==0 and 'NOT_FOUND' or 'AMBIGUOUS',count=#matches,
   expected_guid=M.guid,guid_verified=false,identity='PROFILE_ONLY',session=api.session(),player=api.player()}
  if #matches~=1 then return r end
  local id=matches[1]
  local f=w:get('Faction',id)
  local a=w:get('DynamicActiveNpcState',id)
  local saved=w:get('ActiveNpcStateSaved',id)
  local common=w:get('NpcCommon',id)
  local walker=w:get('DynamicPathWalker',id)
  local x,y,z=w:position(id)
  r.entity=id;r.npc=M.npc;r.faction=f and f.faction or -1;r.position={x=x,y=y,z=z}
  r.components={ai=a~=nil,saved=saved~=nil,common=common~=nil,walker=walker~=nil}
  if f and f.faction==11 and a and saved and common and walker and point(r.position)
   and not w:get('PlayerState',id) then r.result='FOUND_ONE' end
  -- Copy scalar data; never expose writable component proxies.
  if a then r.ai_state=a.state;r.decision=a.decision end
  if saved then r.home={x=saved.spawnPosition.x,y=saved.spawnPosition.y,z=saved.spawnPosition.z} end
  return r
 end
 function self.navigation(w)
  local d=self.discover(w)
  assert(d.result=='FOUND_ONE','NO_UNIQUE_NPC')
  local t=assert(w:template('ActiveNpcState',d.entity),'NAV_TEMPLATE_MISSING')
  local s=assert(w:get('ActiveNpcStateSaved',d.entity),'NAV_SAVED_MISSING')
  local radius=t.roamingSetup.maxRadiusFromSpawn
  local target=t.searchTargetSetup.targetRadius;local bed=t.searchTargetSetup.bedRadius
  assert(type(s.overrideRoamingRange)=='boolean' and finite(s.roamingRange)
   and finite(radius) and finite(target) and finite(bed),'NAV_FIELDS_UNCONFIRMED')
  return {discovery={session=d.session,player=d.player,entity=d.entity,result=d.result},
   navigation={home=d.home,override=s.overrideRoamingRange,saved_radius=s.roamingRange,
    template_radius=radius,effective_radius=s.overrideRoamingRange and s.roamingRange or radius,
    leash=math.max(target,bed),target_radius=target,bed_radius=bed,read_only=true}}
 end
 function self.move_to(w,session,entity,target,approval)
  assert(api.allow_move==true,'MOVEMENT_DISABLED_PENDING_REVIEW')
  assert(approval=='APPROVE_PROFILE_ONLY_MOVE','IDENTITY_APPROVAL_REQUIRED')
  assert(not self.attempted,'ATTEMPT_CONSUMED_NO_RETRY')
  assert(point(target),'INVALID_TARGET')
  local d=self.discover(w)
  assert(d.session==session and d.result=='FOUND_ONE' and d.entity==entity,'IDENTITY_OR_SESSION_CHANGED')
  assert(not api.moving(w,entity),'EXISTING_MOVE')
  assert(distance(d.position,target)<=20,'TARGET_DISTANCE_MAX_20')
  assert(math.abs(d.position.y-target.y)<=1,'TARGET_HEIGHT_DELTA')
  assert(d.ai_state~=1 and d.ai_state~=2 and d.ai_state~=8 and d.ai_state~=16 and d.decision~=5,'NPC_NOT_AWAKE')
  assert(not api.wall(w,d.position,target),'TARGET_WALL_BLOCKED')
  self.attempted=true -- consumed BEFORE API; exceptions have an uncertain outcome
  self.order={session=session,entity=entity,start=d.position,target=target,state='OUTCOME_UNKNOWN',started=false,progress=false}
  local order=self.order
  local id,why=api.move(w,entity,target,{arrive=0.5,seconds=30,stuck=10},function(_,mid,status)
   if order.id and order.id~=mid then return end
   order.engine_result=status
  end)
  if not id then order.state='REFUSED';order.reason=why;return self.status(w) end
  order.id=id;order.state='ACCEPTED';return self.status(w)
 end
 function self.status(w)
  local d=self.discover(w)
  local o=self.order
  if not o then return {discovery=d,state='IDLE'} end
  if d.session~=o.session or d.result~='FOUND_ONE' or d.entity~=o.entity then
   return {discovery=d,state='IDENTITY_LOST_NO_RETRY'}
  end
  local remaining=distance(d.position,o.target)
  o.started=o.started or distance(d.position,o.start)>=0.25
  o.progress=o.progress or distance(o.start,o.target)-remaining>=0.5
  local state=o.state
  if o.engine_result then
   state=o.engine_result=='arrived' and (remaining<=0.75 and 'ARRIVAL_OBSERVED' or 'ENGINE_ARRIVED_NOT_AT_TARGET') or o.engine_result:upper()
  end
  return {discovery=d,state=state,order=o.id,reason=o.reason,engine_result=o.engine_result,
   displacement_observed=o.started,progress_observed=o.progress,distance=remaining,event_sent='UNVERIFIED'}
 end
 return self
end
return M
