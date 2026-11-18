-- Offline read-only controller for EMF0.6.18/API46/Lua-host1.39/protocol1.
-- No mod.json or auto-load: actual context provenance is a Phase D gate.
-- emf.command/emf.reply are the established transport; no entity API is used.
local M={}
local checks={
 {'build','UNSUPPORTED_BUILD'}, {'api','WRONG_API'}, {'emf','WRONG_EMF'},
 {'lua_host','WRONG_LUA_HOST'}, {'protocol','WRONG_PROTOCOL'},
 {'session','WRONG_SESSION'}, {'world','WRONG_WORLD'},
 {'content_owner','CONTENT_OWNER_MISMATCH'}, {'patch','PATCH_MISMATCH'},
 {'receipt_sha256','STALE_RECEIPT'}, {'run_token','WRONG_RUN'}
}
function M.inspect(command,context,expected,evidence)
 local r={command=command,read_only=true,spawn_forbidden=true,spawn_ready=false,
  installation_ready=false,runtime_status='NOT_EXECUTED',runtime_render='UNKNOWN',ok=false}
 if command~='status' and command~='inspect' and command~='compare' then
  r.error='COMMAND_FORBIDDEN'; return r
 end
 for _,v in ipairs(checks) do
  if expected[v[1]]==nil or context[v[1]]~=expected[v[1]] then r.error=v[2];return r end
 end
 if not evidence then r.error='MISSING_EVIDENCE'; return r end
 if context.writer_finalized~=true or context.shadow_readback_verified~=true then
  r.error='WRITER_OR_READBACK_UNCONFIRMED';return r
 end
 local fields={'patch','build','source_guid','clone_guid','character_setup','hashkeys',
  'component_fingerprint','animation_graph','visual_references','resource_lookup','source_integrity','count'}
 if type(expected.evidence)~='table' then r.error='EVIDENCE_BASELINE_UNAVAILABLE';return r end
 for _,key in ipairs(fields) do
  if expected.evidence[key]==nil then r.error='EVIDENCE_BASELINE_UNAVAILABLE';return r end
  if evidence[key]~=expected.evidence[key] then r.error='EVIDENCE_MISMATCH';return r end
 end
 for key,_ in pairs(evidence) do
  if expected.evidence[key]==nil then r.error='EVIDENCE_MISMATCH';return r end
 end
 r.ok=true;r.evidence_validated_offline=true;return r
end
function M.register(emf,json,capture,expected)
 for _,name in ipairs({'status','inspect','compare'}) do
  local command=name
  emf.command(command,'Read-only migration evidence (preparation only)',function()
   local ok,ctx,ev=pcall(capture)
   local r=ok and M.inspect(command,ctx or {},expected,ev) or
    {command=command,ok=false,error='CAPTURE_FAILED',read_only=true,spawn_forbidden=true,spawn_ready=false}
   local raw=json.encode(r)
   if #raw>1023 then raw='{"ok":false,"error":"RESPONSE_TOO_LARGE","spawn_ready":false}' end
   emf.reply('AIC_TEMPLATE_OBSERVER '..raw)
  end)
 end
end
return M
