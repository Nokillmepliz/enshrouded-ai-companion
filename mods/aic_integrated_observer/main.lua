-- No game.assets: integrated EML has unloaded before this runtime Lua host.
local binding=dofile(emf.dir..'/binding.lua')
assert(binding.schema==8 and #binding.run_token==32,'missing deployment binding')
local function dispatch(command,world,args)
 local nonce=args[1]
 if #args~=1 or type(nonce)~='string' or #nonce~=32 or not nonce:match('^[0-9a-f]+$') then
  emf.reply('AIC_OBSERVER_ERROR invalid_nonce'); return
 end
 local session=emf.session_token()
 local player=emf.local_player()
 local ok=world~=nil and world:is_server() and type(session)=='string' and #session>0
 local name=ok and world:character_name(player) or ''
 local reply={schema=8,command=command,nonce=nonce,ok=ok and name=='Body Test',
  run_token=binding.run_token,plan_id=binding.plan_id,profile_sha256=binding.profile_sha256,
  session_token=session,session=emf.session(),character=name,
  read_only=true,spawn_ready=false,eml_runtime_lookup='UNAVAILABLE_CONTENT_UNLOADED',
  context_provenance='WORLD_LOCAL_AND_API_REQUIRE_BRIDGE_STATE',
  evidence_operation=command=='status' and 'SESSION_ONLY' or 'PYTHON_LOCAL_VALIDATION_REQUIRED'}
 -- Keep one reply under the host's bounded console line size.
 local raw=assert(emf.json.encode(reply))
 if #raw>950 then emf.reply('AIC_OBSERVER_ERROR response_too_large'); return end
 emf.reply('AIC_OBSERVER_V8 '..raw)
end
for _,command in ipairs({'status','inspect','compare'}) do
 emf.command(command,'<nonce>: read-only session observation',function(world,args) dispatch(command,world,args) end)
end
