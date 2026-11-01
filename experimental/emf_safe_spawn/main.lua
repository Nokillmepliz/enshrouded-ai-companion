-- Stage 10.8 Phase A scaffold. It contains no game mutation path.
local json=require('json')
local TEMPLATE='a1c90001-5e4d-4a91-8a1c-000000000001'
local state='DISABLED'
local last_error='phase_a_mutation_prohibited'

local function reply(command, extra)
 local result={format='aic_humanoid_spawn_evidence_v5',controller='0.1.0-phase-a',
  command=command,state=state,last_error=last_error,read_only=true,
  phase_a=true,spawn_ready=false,runtime_render_confirmed='UNKNOWN',
  template_guid=TEMPLATE,automatic_retry=false}
 for k,v in pairs(extra or {}) do result[k]=v end
 emf.reply('AIC_SAFE_SPAWN '..json.encode(result))
end

emf.command('status','Stage 10.8 Phase A read-only status',function()
 reply('status',{installed_for_runtime=false})
end)

emf.command('preflight','Stage 10.8 Phase A offline-only gate',function()
 state='LOCKED'; last_error='offline_blockers_present'
 reply('preflight',{blockers={'exact_instance_identity','ownership','safe_position','persistence'}})
end)

emf.command('inspect','Stage 10.8 Phase A read-only scaffold inspection',function()
 reply('inspect',{entity_handle='UNAVAILABLE',entity_identity='UNAVAILABLE',
  render={ENTITY_CREATED='UNKNOWN',ENTITY_IDENTITY_CONFIRMED='UNKNOWN',MODEL_LOADED='UNKNOWN',
   SKELETON_CONFIRMED='UNKNOWN',ANIMATION_CONFIRMED='UNKNOWN',RUNTIME_RENDER_CONFIRMED='UNKNOWN'}})
end)

local function deny(command)
 state='LOCKED'; last_error='phase_a_mutation_prohibited'
 reply(command,{accepted=false,effect='NONE'})
end
emf.command('spawn_once','DISABLED in Stage 10.8 Phase A',function() deny('spawn_once') end)
emf.command('despawn','DISABLED in Stage 10.8 Phase A',function() deny('despawn') end)
emf.command('emergency_stop','Mock-only in Stage 10.8 Phase A',function() deny('emergency_stop') end)

emf.log('AIC_SAFE_SPAWN_PHASE_A_DISABLED; no automatic spawn; no runtime mutation path')
