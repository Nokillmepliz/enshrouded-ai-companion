-- Build 1287369: sleep = tod >= sleepTime OR tod <= wakeUpTime.
-- 25/-1 hours excludes the entire 0..24h domain (including endpoints).
-- Only NpcCommon's two transient floats are written. AI performs its own exit.
local M={sleep=25,wake=-1}
local function normal(v) return type(v)=='number' and v==v and v>=0 and v<=24 end
function M.new(api)
 local s={lease=api.load(),state='INACTIVE',rerolls=0}
 local function check(d,l)
  assert(d.result=='FOUND_ONE' and d.session==l.session and d.entity==l.entity,'SCHEDULE_IDENTITY_CHANGED')
 end
 local function common(w,d)
  local c=assert(w:get('NpcCommon',d.entity),'SCHEDULE_COMPONENT_MISSING')
  return c
 end
 function s.release(w,d)
  local l=s.lease;if not l then return end
  check(d,l)
  local c=common(w,d)
  -- Restore only fields we still own; do not overwrite third-party edits.
  for _,p in ipairs({{'sleepTime',M.sleep,l.sleep},{'wakeUpTime',M.wake,l.wake}}) do
   if c[p[1]]==p[2] then c[p[1]]=p[3];assert(c[p[1]]==p[3],'SCHEDULE_RESTORE_READBACK')
   elseif c[p[1]]~=p[3] then api.log('SCHEDULE_NATIVE_OR_EXTERNAL_VALUE',{field=p[1],value=c[p[1]]}) end
  end
  api.save({state='RELEASED',session=l.session,entity=l.entity})
  s.lease=nil;s.state='RESTORED';api.log('SCHEDULE_RESTORED',{})
 end
 function s.acquire(w,d)
  assert(not s.lease,'SCHEDULE_RECOVERY_REQUIRED')
  assert(d.result=='FOUND_ONE','SCHEDULE_IDENTITY_CHANGED')
  local c=common(w,d)
  assert(normal(c.sleepTime) and normal(c.wakeUpTime),'SCHEDULE_UNEXPECTED_HOURS')
  local h=api.time(w);assert(normal(h),'SCHEDULE_CLOCK_UNAVAILABLE')
  local l={state='ACQUIRED',session=d.session,entity=d.entity,sleep=c.sleepTime,wake=c.wakeUpTime}
  -- Durable before either write: a partial setter failure can still be restored.
  api.save(l);s.lease=l;s.started=api.now();s.previous=d.ai_state;s.rerolls=0
  c.sleepTime=M.sleep;c.wakeUpTime=M.wake
  assert(c.sleepTime==M.sleep and c.wakeUpTime==M.wake,'SCHEDULE_WRITE_READBACK')
  s.state='WAKING';api.log('SCHEDULE_ACQUIRED',{sleep=l.sleep,wake=l.wake,ai_state=d.ai_state,hour=h})
 end
 function s.update(w,d)
  local l=assert(s.lease,'SCHEDULE_NOT_ACQUIRED');check(d,l)
  local h=api.time(w);assert(normal(h),'SCHEDULE_CLOCK_UNAVAILABLE')
  local c=common(w,d)
  if c.sleepTime~=M.sleep or c.wakeUpTime~=M.wake then
   -- Sleep exit rolls both times again. Permit precisely this observed transition,
   -- once per acquisition, not a continuous fight with another writer.
   assert(s.previous==8 and d.ai_state~=8 and s.rerolls==0
    and normal(c.sleepTime) and normal(c.wakeUpTime),'SCHEDULE_CONFLICT')
   s.rerolls=1;c.sleepTime=M.sleep;c.wakeUpTime=M.wake
   assert(c.sleepTime==M.sleep and c.wakeUpTime==M.wake,'SCHEDULE_WRITE_READBACK')
   api.log('SCHEDULE_SLEEP_EXIT_REAPPLIED',{})
  end
  s.previous=d.ai_state
  local waiting=d.ai_state==8 or d.ai_state==2 or d.decision==5
  if waiting then
   assert(api.now()-s.started<15,'SCHEDULE_WAKE_TIMEOUT')
   s.state='WAKING';return false
  end
  if s.state~='AWAKE' then api.log('SCHEDULE_AWAKE_OBSERVED',{ai_state=d.ai_state,decision=d.decision}) end
  s.state='AWAKE';return true
 end
 return s
end
return M
