-- One queued native GoToPosition at the NPC's current position, never Reset.
-- EMF emit queues an event; acceptance is NOT evidence of an engine transition.
local M={}
local allowed={[3]=true,[4]=true,[5]=true,[6]=true,[7]=true,[13]=true,[17]=true}
local function distance(a,b)
 return math.sqrt((a.x-b.x)^2+(a.y-b.y)^2+(a.z-b.z)^2)
end
function M.new(api)
 local s={used=false,pending=false,state='UNUSED'}
 function s.tick(w,d)
  assert(d.result=='FOUND_ONE','WAKE_IDENTITY_AMBIGUOUS')
  local now=api.now()
  if s.pending then
   assert(d.session==s.session and d.entity==s.entity,'WAKE_IDENTITY_CHANGED')
   assert(not api.moving(w,d.entity),'WAKE_FOREIGN_ORDER')
   local a=w:get('DynamicActiveNpcState',d.entity)
   local walker=w:get('DynamicPathWalker',d.entity)
   local common=w:get('NpcCommon',d.entity)
   assert(a and walker and common,'WAKE_COMPONENT_MISSING')
   local same_target=distance(common.currentTargetPosition,s.target)<=0.1
   local near=distance(d.position,s.target)<=0.75
   local signature=tostring(a.state)..':'..tostring(a.previousState)..':'..tostring(a.decision)..':'..tostring(walker.state)..':'..tostring(same_target)
   if signature~=s.observed then
    s.observed=signature
    api.log('WAKE_OBSERVATION',{ai_state=a.state,previous_state=a.previousState,decision=a.decision,walker=walker.state,
     target_matches=same_target,target_distance=distance(d.position,s.target)})
   end
   -- PID532656: Roam/TargetReached -> Idle/Idle on consecutive ticks.
   -- SetState resets the walker. Preserve only the immediately preceding arrival
   -- observation, for this identity/target, for at most one second. No idle-only gate.
   local just_reached=s.reached_at and now-s.reached_at<=1
   s.reached_at=nil
   if a.state==3 and a.previousState==7 and a.decision==1 and same_target and near
    and (walker.state==8 or (walker.state==0 and just_reached)) then
    s.pending=false;s.state='CONFIRMED'
    api.log('WAKE_HANDOFF_CONFIRMED',{entity=d.entity,target=s.target})
    return false
   end
   if a.state==7 and a.decision==1 and walker.state==8 and same_target and near then s.reached_at=now end
   assert(now-s.at<8,'WAKE_HANDOFF_TIMEOUT')
   return true
  end
  if s.used then return false end
  if d.decision~=5 or not allowed[d.ai_state] then s.since=nil;return false end
  -- Require multiple fresh ticks and two seconds with override already checked.
  if not s.since then s.since=now;return false end
  if now-s.since<2 then return false end
  assert(not api.moving(w,d.entity),'WAKE_FOREIGN_ORDER')
  local common=assert(w:get('NpcCommon',d.entity),'WAKE_COMPONENT_MISSING')
  assert(common.sleepTime==25 and common.wakeUpTime==-1,'WAKE_OVERRIDE_MISSING')
  assert(type(common.interactionStates)=='number','WAKE_INTERACTION_UNKNOWN')
  if (common.interactionStates & 0x0b)~=0 then return false end
  local p=d.position
  for _,axis in ipairs({'x','y','z'}) do
   assert(type(p[axis])=='number' and p[axis]==p[axis] and math.abs(p[axis])<1e6,'WAKE_POSITION')
  end
  assert(d.npc==2939921867,'WAKE_NPC_ID') -- discovery counts ALL matches of this npcId.
  s.used=true;s.pending=true;s.at=now;s.session=d.session;s.entity=d.entity
  s.target={x=p.x,y=p.y,z=p.z};s.state='QUEUED_UNCONFIRMED'
  api.log('WAKE_TYPE1_INTENT',{entity=d.entity,npc=d.npc,target=s.target,ai_state=d.ai_state,decision=d.decision})
  -- Latch and intent precede emit. On exception/ambiguous delivery NEVER retry.
  api.emit(d.npc,s.target)
  return true -- Last API call: do not read w or a component proxy after emit.
 end
 return s
end
return M
