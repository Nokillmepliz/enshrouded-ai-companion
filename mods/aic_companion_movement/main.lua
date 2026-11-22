local policy=dofile(emf.dir..'/controller.lua')
local controller=policy.new({allow_move=false,session=emf.session_token,player=emf.local_player,
 moving=emf.villager_moving,move=emf.villager_move,
 wall=function(w,a,b)
  return emf.find_wall(w,{x=a.x,y=a.y+1,z=a.z},{x=b.x,y=b.y+1,z=b.z})~=nil
 end,
 context=function(w)
  if not (w and w:is_server() and emf.local_player()>0 and w:character_name(emf.local_player())=='Body Test') then return false end
  local n=0;for _,id in ipairs(w:entities()) do if w:get('PlayerState',id) then n=n+1 end end
  return n==1
 end})
-- One explicit request only. No automatic move or retry on load/tick.
for _,name in ipairs({'discover','status','move_to'}) do
 assert(#('aic_companion_movement.'..name)<=32,'COMMAND_NAME_LIMIT')
 assert(emf.command(name,'Stage 10.12: explicit one-shot movement; no automatic retry',function(w,args)
  local nonce=args[1]
  local ok,value=pcall(function()
   assert(type(nonce)=='string' and #nonce==32 and nonce:match('^[0-9a-f]+$'),'NONCE')
   if name=='move_to' then
    assert(#args==7,'ARITY')
    return controller.move_to(w,args[2],tonumber(args[3]),{x=tonumber(args[4]),y=tonumber(args[5]),z=tonumber(args[6])},args[7])
   end
   assert(#args==1,'ARITY')
   if name=='discover' then
    local d=controller.discover(w)
    local x,y,z=w:position(emf.local_player())
    d.player_position={x=x,y=y,z=z}
    d.active_order=d.entity and emf.villager_moving(w,d.entity) or nil
    return {discovery=d}
   end
   return controller.status(w)
  end)
  local reply={schema=1,nonce=nonce,ok=ok,value=ok and value or nil,error=not ok and tostring(value):sub(1,120) or nil}
  local raw=assert(emf.json.encode(reply))
  if #raw>950 then emf.reply('AIC_MOVEMENT_ERROR reply_size');return end
  emf.reply('AIC_MOVEMENT '..raw)
 end),'COMMAND_REGISTRATION_FAILED:'..name)
end
-- Stage10.13 commands require a consumed fixed session latch and a Python heartbeat.
local config=dofile(emf.dir..'/follow_config.lua')
assert(config.roaming=='native' or config.roaming=='hold','ROAMING_MODE')
assert(config.lock_name==(config.schedule and 'follow-stage10-15.lock' or 'follow-stage10-14.lock'),'SESSION_LOCK_NAME')
local follow
local function guarded(fn)
 return function(w,...)
  local ok,err=pcall(fn,w,...)
  if not ok then follow.stop(w,'ASYNC_ERROR');emf.log('AIC_FOLLOW ERROR '..tostring(err)) end
 end
end
local api={now=os.time,move=emf.villager_move,moving=emf.villager_moving,cancel=emf.villager_move_cancel,
 position=function(w,id) local x,y,z=w:position(id);return x and {x=x,y=y,z=z} or nil end,
 wall=function(w,a,b) return emf.find_wall(w,{x=a.x,y=a.y+1,z=a.z},{x=b.x,y=b.y+1,z=b.z})~=nil end,
 ground=function(w,x,z,fn) return emf.ground_at(w,x,z,guarded(fn)) end,
 path=function(w,a,b,opts,fn) return emf.path_find(w,a,b,opts,guarded(fn)) end,
 log=function(event,data) emf.log('AIC_FOLLOW '..event..' '..assert(emf.json.encode(data))) end,
 consume=function()
  local f=io.open(emf.dir..'/'..config.lock_name,'r+b');if not f then return false end
  if f:read('*a')~='UNUSED:'..config.token then f:close();return false end
  if not f:seek('set',0) then f:close();return false end
  local wrote=f:write('SPENT!:'..config.token);local flushed=f:flush();local closed=f:close()
  local check=io.open(emf.dir..'/'..config.lock_name,'rb');if not check then return false end
  local bytes=check:read('*a');check:close()
  return wrote~=nil and flushed~=nil and closed~=nil and bytes=='SPENT!:'..config.token
 end}
local recovering=false
if config.schedule then
 local journal=emf.dir..'/schedule-stage10-15.jsonl'
 local function load_lease()
  local f=assert(io.open(journal,'rb'),'SCHEDULE_JOURNAL_MISSING')
  local raw=f:read('*a');assert(f:close());assert(#raw<65536,'SCHEDULE_JOURNAL_SIZE')
  assert(raw=='' or raw:sub(-1)=='\n','SCHEDULE_JOURNAL_INCOMPLETE')
  local last
  for line in raw:gmatch('[^\n]+') do
   last=assert(emf.json.decode(line),'SCHEDULE_JOURNAL_INVALID')
   assert(last.state=='ACQUIRED' or last.state=='RELEASED','SCHEDULE_JOURNAL_STATE')
  end
  if last and last.state=='ACQUIRED' then
   assert(type(last.session)=='string' and type(last.entity)=='number'
    and type(last.sleep)=='number' and last.sleep>=0 and last.sleep<=24
    and type(last.wake)=='number' and last.wake>=0 and last.wake<=24,'SCHEDULE_JOURNAL_VALUES')
   return last
  end
 end
 api.schedule=dofile(emf.dir..'/schedule.lua').new({now=os.time,time=emf.time_of_day,log=api.log,load=load_lease,
  save=function(row)
   local raw=assert(emf.json.encode(row))..'\n'
   local f=assert(io.open(journal,'ab'),'SCHEDULE_JOURNAL_OPEN')
   local wrote=f:write(raw);local flushed=f:flush();local closed=f:close()
   assert(wrote and flushed and closed,'SCHEDULE_JOURNAL_WRITE')
   local check=assert(io.open(journal,'rb'));local bytes=check:read('*a');assert(check:close())
   assert(bytes:sub(-#raw)==raw,'SCHEDULE_JOURNAL_READBACK')
  end})
 recovering=api.schedule.lease~=nil
end
follow=dofile(emf.dir..'/follow.lua').new(api,controller.discover,config)
for _,name in ipairs({'f_start','f_step','f_stop','f_status'}) do
 assert(#('aic_companion_movement.'..name)<=32,'COMMAND_NAME_LIMIT')
 assert(emf.command(name,'Bounded Stage10.13 runner',function(w,args)
  local nonce=args[1]
  local ok,value=pcall(function()
   assert(type(nonce)=='string' and #nonce==32 and nonce:match('^[0-9a-f]+$'),'NONCE')
   if name=='f_start' then
    assert(not recovering,'SCHEDULE_RECOVERY_REQUIRED')
    assert(#args==4,'ARITY');follow.start(w,args[2],args[3],tonumber(args[4]))
   elseif name=='f_step' then
    assert(#args==3,'ARITY');follow.step(w,args[2],tonumber(args[3]))
   elseif name=='f_stop' then
    assert(#args==2 and args[2]==config.token,'TOKEN');follow.stop(w,'RUNNER_STOP')
   else assert(#args==1,'ARITY') end
   return follow.status(w)
  end)
  if not ok then follow.stop(w,'REQUEST_ERROR') end
  local reply={schema=1,nonce=nonce,ok=ok,value=ok and value or nil,error=not ok and tostring(value):sub(1,120) or nil}
  local raw=assert(emf.json.encode(reply))
  if #raw>950 then follow.stop(w,'REPLY_SIZE');emf.reply('AIC_MOVEMENT_ERROR reply_size');return end
  emf.reply('AIC_MOVEMENT '..raw)
 end),'COMMAND_REGISTRATION_FAILED:'..name)
end
local checked=0
emf.on_tick(function(w)
 if not w:is_server() then return end
 if recovering then
  -- A reload restores, never resumes a consumed Follow session.
  local ok,err=pcall(function() api.schedule.release(w,controller.discover(w)) end)
  if ok then recovering=false
  elseif os.time()~=checked then emf.log('AIC_FOLLOW SCHEDULE_RECOVERY_PENDING '..tostring(err)) end
  checked=os.time();return
 end
 if not config.schedule and os.time()==checked then return end
 checked=os.time();follow.watch(w)
end)
