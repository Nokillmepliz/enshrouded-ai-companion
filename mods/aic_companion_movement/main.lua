local policy=dofile(emf.dir..'/controller.lua')
local controller=policy.new({allow_move=true,session=emf.session_token,player=emf.local_player,
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
 emf.command(name,'Stage 10.12: explicit one-shot movement; no automatic retry',function(w,args)
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
 end)
end
