-- Stage 10.6 read-only observer. Reads EML evidence; never touches an entity.
local json=require('json')
local TOKEN='__AIC_STAGE10_RUN_TOKEN__'
local TEMPLATE='a1c90001-5e4d-4a91-8a1c-000000000001'
local SOURCE='e3736dff-0ad2-47fc-903c-66c1775836e8'
assert(TOKEN:match('^[0-9a-f]+$') and #TOKEN==32,'aic_template_observer: missing run token')
local function paths()
 local p={'export/aic_eml_humanoid/template_evidence_v3.txt'}
 if type(emf.dir)=='string' then p[#p+1]=emf.dir..'/../../../export/aic_eml_humanoid/template_evidence_v3.txt' end
 return p
end
local function read()
 for _,path in ipairs(paths()) do
  local f=io.open(path,'r')
  if f then
   local raw=f:read('*a'); f:close(); local r={}
   for line in raw:gmatch('[^\r\n]+') do
    local k,v=line:match('^([a-z0-9_]+)=(.*)$')
    if not k or r[k]~=nil then return nil,'evidence_malformed',path end
    r[k]=v
   end
   return r,nil,path
  end
 end
 return nil,'evidence_missing',nil
end
local function base(command)
 return {command=command,loaded=true,read_only=true,spawn_forbidden=true,run_token=TOKEN,
  direct_emf_template_lookup='UNAVAILABLE_WITHOUT_ENTITY'}
end
local function send(command,extra)
 local r=base(command); for k,v in pairs(extra or {}) do r[k]=v end
 local encoded=json.encode(r)
 if #encoded>1023 then r={command=command,loaded=true,read_only=true,spawn_forbidden=true,
   run_token=TOKEN,error='observer_response_too_large'}; encoded=json.encode(r) end
 emf.reply('AIC_TEMPLATE_OBSERVER '..encoded)
end
local function valid(e)
 return e and e.format=='aic_eml_humanoid_evidence_v3' and e.run_token==TOKEN
  and e.template_guid==TEMPLATE and e.source_guid==SOURCE
end
emf.command('status','Stage 10.6 evidence status',function()
 local e,err,path=read()
 send('status',{evidence_available=e~=nil,evidence_error=err,evidence_path=path,
  new_template_eml_evidence=e~=nil and e.template_guid==TEMPLATE,
  original_template_eml_evidence=e~=nil and e.source_guid==SOURCE,
  evidence_run_token=e and e.run_token or 'UNAVAILABLE',writer_finalized=e~=nil})
end)
emf.command('inspect','Stage 10.6 compact visual fingerprint',function()
 local e,err=read()
 send('inspect',{ok=valid(e),error=err,template_guid=e and e.template_guid,
  evidence={model_status=e and e.model_status or 'MISSING',
   model_reason=e and e.model_reason or 'component_missing'},
  component_group_counts={},
  source_guid=e and e.source_guid,fingerprint_hash=e and e.fingerprint_hash,
  component_fingerprint=e and e.component_fingerprint,
  component_count=e and select(2,(e.components or ''):gsub(',',','))+1 or 0,
  character_setup_match=e and e.character_setup_match,
  references_match=e and e.visual_references_match,
  dependencies_resolved=e and e.visual_dependencies_resolved,
  field_source=e and 'EML_EXPORT' or 'UNAVAILABLE'})
end)
emf.command('compare','Stage 10.6 clone/source comparison',function()
 local e,err=read(); local ok=valid(e) and e.source_unchanged=='true'
  and e.character_setup_match=='true' and e.visual_references_match=='true'
 send('compare',{ok=ok,error=err,writer_finalized=e~=nil,
  fingerprint_hash=e and e.fingerprint_hash,source_unchanged=e and e.source_unchanged,
  character_setup_match=e and e.character_setup_match,
  runtime_render='UNKNOWN',spawn_ready=false})
end)
emf.log('AIC_TEMPLATE_OBSERVER_READY '..TOKEN..'; Stage10.6 read-only; spawn forbidden')
