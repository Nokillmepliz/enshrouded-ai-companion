local binding=dofile(emf.dir..'/binding.lua')
local policy=dofile(emf.dir..'/controller.lua')
assert(type(binding.key)=='string' and #binding.key==32, 'deployment key missing')
local latch=emf.dir..'/attempt.lock'
local function read_latch()
 local f=io.open(latch,'rb');if not f then return nil end
 local value=f:read('*a');local ok=f:close();if not ok then return nil end;return value
end
local function consume()
 if read_latch()~='UNUSED:'..binding.key then return false end
 local f=io.open(latch,'r+b');if not f then return false end
 local ok=f:write('SPENT!:'..binding.key);local flushed=f:flush();local closed=f:close()
 return ok~=nil and flushed~=nil and closed~=nil and read_latch()=='SPENT!:'..binding.key
end
local function context(w,session,player)
 if not (w~=nil and w:is_server() and emf.session_token()==session
  and player==emf.local_player() and player>0 and w:character_name(player)=='Body Test') then return false end
 local count=0
 for _,id in ipairs(w:entities()) do if w:get('PlayerState',id) then count=count+1 end end
 return count==1
end
local function position(w,id)
 local x,y,z=w:position(id);if not x then return nil end;return {x=x,y=y,z=z}
end
local function inspect(w,id)
 local npc=w:template('ActiveNpcState',id)
 local f=w:get('Faction',id)
 return {npc=npc and npc.npcId or -1,faction=f and f.faction or -1,
  player=w:get('PlayerState',id)~=nil,position=position(w,id),
  force_save=w:template('ForceSave',id)~=nil,
  saved_state=w:get('ActiveNpcStateSaved',id)~=nil,
  character_setup=w:template('CharacterSetup',id)~=nil,
  render_equipment=w:template('RenderEquipment',id)~=nil,
  animation=w:template('AnimationGraphResourceComponent2',id)~=nil}
end
local api={now=os.time,session=emf.session_token,player=emf.local_player,context=context,
 position=position,ground=emf.ground_at,path=emf.path_find,spawn=emf.spawn,
 unused=function() return read_latch()=='UNUSED:'..binding.key end,consume=consume,
 log=function(s) emf.log('AIC_EXPERIMENT '..s) end,inspect=inspect,
 wall=function(w,a,b) return emf.find_wall(w,{x=a.x,y=a.y+1,z=a.z},{x=b.x,y=b.y+1,z=b.z})~=nil end,
 has_candidate=function(w,npc)
  for _,id in ipairs(w:entities()) do
   local v=w:template('ActiveNpcState',id);if v and v.npcId==npc then return true end
  end
  return false
 end}
local controller
local function guarded(fn)
 return function(...)
  local ok,err=pcall(fn,...)
  if not ok then controller.stop('async_api_error');emf.log('AIC_EXPERIMENT async '..tostring(err)) end
 end
end
api.ground=function(w,x,z,fn) return emf.ground_at(w,x,z,guarded(fn)) end
api.path=function(w,a,b,opts,fn) return emf.path_find(w,a,b,opts,guarded(fn)) end
controller=policy.new(api,binding)
for _,command in ipairs({'status','probe','spawn','observe','stop'}) do
 assert(emf.command(command,'Explicit experimental controller; Python client only',function(w,args)
  local nonce=args[1]
  local ok,err=pcall(function()
   assert(type(nonce)=='string' and #nonce==32 and nonce:match('^[0-9a-f]+$'),'nonce')
   assert(args[2]==binding.key,'key')
   if command=='probe' then assert(#args==4,'arity');controller.probe(w,args[3],tonumber(args[4]),nonce)
   elseif command=='spawn' then assert(#args==6,'arity');controller.spawn(w,args[3],tonumber(args[4]),args[5],args[6])
   elseif command=='stop' then assert(#args==2,'arity');controller.stop('operator_stop')
   else assert(#args==2,'arity') end
  end)
  if not ok then controller.stop('api_or_request_error');emf.log('AIC_EXPERIMENT error '..tostring(err)) end
  local safe,reply=pcall(function()
   local r=controller.status(w)
   if command=='observe' then r.observation=controller.observe(w);r.state=controller.state;r.reason=controller.reason end
   r.schema=1;r.nonce=nonce;r.ok=ok and controller.state~='STOPPED';return r
  end)
  if not safe then controller.stop('diagnostic_error');reply={schema=1,nonce=nonce,ok=false,state='STOPPED',reason='diagnostic_error'} end
  local raw=emf.json.encode(reply)
  if not raw or #raw>930 then emf.reply('AIC_EXPERIMENT_ERROR reply_size');return end
  emf.reply('AIC_EXPERIMENT '..raw)
 end))
end
-- No tick mutation, auto-spawn, respawn, destroy, component writes or save API.
