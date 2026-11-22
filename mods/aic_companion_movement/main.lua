local policy=dofile(emf.dir..'/controller.lua')
local controller=policy.new({allow_move=false,session=emf.session_token,player=emf.local_player,
 moving=emf.villager_moving,move=emf.villager_move,
 context=function(w)
  if not (w and w:is_server() and emf.local_player()>0 and w:character_name(emf.local_player())=='Body Test') then return false end
  local n=0;for _,id in ipairs(w:entities()) do if w:get('PlayerState',id) then n=n+1 end end
  return n==1
 end})
-- Movement is deliberately locked pending a separate installation/runtime review.
for _,name in ipairs({'discover','status','move_to'}) do
 emf.command(name,'Stage 10.12 prototype; movement disabled pending review',function(w,args)
  local nonce=args[1]
  local ok,value=pcall(function()
   assert(type(nonce)=='string' and #nonce==32 and nonce:match('^[0-9a-f]+$'),'NONCE')
   if name=='move_to' then
    assert(#args==7,'ARITY')
    return controller.move_to(w,args[2],tonumber(args[3]),{x=tonumber(args[4]),y=tonumber(args[5]),z=tonumber(args[6])},args[7])
   end
   assert(#args==1,'ARITY')
   return name=='discover' and {discovery=controller.discover(w)} or controller.status(w)
  end)
  local reply={schema=1,nonce=nonce,ok=ok,value=ok and value or nil,error=not ok and tostring(value):sub(1,120) or nil}
  local raw=assert(emf.json.encode(reply))
  if #raw>950 then emf.reply('AIC_MOVEMENT_ERROR reply_size');return end
  emf.reply('AIC_MOVEMENT '..raw)
 end)
end
