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
assert(config.lock_name=='follow-stage10-14.lock','SESSION_LOCK_NAME')
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
follow=dofile(emf.dir..'/follow.lua').new(api,controller.discover,config)
for _,name in ipairs({'f_start','f_step','f_stop','f_status'}) do
 assert(#('aic_companion_movement.'..name)<=32,'COMMAND_NAME_LIMIT')
 assert(emf.command(name,'Bounded Stage10.13 runner',function(w,args)
  local nonce=args[1]
  local ok,value=pcall(function()
   assert(type(nonce)=='string' and #nonce==32 and nonce:match('^[0-9a-f]+$'),'NONCE')
   if name=='f_start' then
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
 if not w:is_server() or os.time()==checked then return end
 checked=os.time();follow.watch(w)
end)
