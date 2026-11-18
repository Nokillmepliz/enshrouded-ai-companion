-- Proposed EML print channel, not a registration patch. No io/export required.
-- Each value must be a bounded single-line serialization produced from typed reads.
local M={}
local fields={'patch','build','source_guid','clone_guid','character_setup','hashkeys',
 'component_fingerprint','animation_graph','visual_references','resource_lookup','source_integrity'}
function M.emit(print_fn,token,values)
 assert(type(token)=='string' and #token==32 and token:match('^[0-9a-f]+$'),'invalid run token')
 local lines={}
 for _,key in ipairs(fields) do
  local v=values[key]
  assert(type(v)=='string' and #v>0 and not v:find('[\r\n|]'),'invalid evidence field: '..key)
  local line='AIC_EVIDENCE_V8|'..token..'|'..key..'|'..v
  assert(#line<=4096,'evidence field too large')
  lines[#lines+1]=line
 end
 lines[#lines+1]='AIC_EVIDENCE_V8|'..token..'|count|'..#fields
 for _,line in ipairs(lines) do print_fn(line) end
end
return M
