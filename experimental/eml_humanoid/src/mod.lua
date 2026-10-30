-- Experimental EML 0.2.0 data patch. It creates data only and never spawns an entity.
if not loader.features.patch then
	return
end

local TEMPLATE_GUID = "a1c90001-5e4d-4a91-8a1c-000000000001"
local SOURCE_GUID = "e3736dff-0ad2-47fc-903c-66c1775836e8" -- hunter_assistant
local TEMPLATE_NAME = "AIC_Humanoid_Companion_Experimental"
local NPC_ID = game.guid.hash(TEMPLATE_GUID)
-- Replaced with a cryptographically random value by the Stage 10 installer.
-- Repository source containing the placeholder is never runtime evidence.
local RUN_TOKEN = "__AIC_STAGE10_RUN_TOKEN__"
assert(RUN_TOKEN:match("^[0-9a-f]+$") and #RUN_TOKEN == 32,
	"aic_eml_humanoid: missing Stage 10 run token")

local function text(value)
	local ok, result = pcall(tostring, value)
	return ok and result or "UNAVAILABLE"
end

local function component(data, kind)
	for _, value in ipairs(data.components) do
		if value.type == kind then return value.value end
	end
	return nil
end

local function component_names(data)
	local result = {}
	for _, value in ipairs(data.components) do result[#result + 1] = value.type end
	table.sort(result)
	return table.concat(result, ",")
end

local function is_guid(value)
	if type(value) ~= "string" or #value ~= 36 then return false end
	if value:sub(9, 9) ~= "-" or value:sub(14, 14) ~= "-"
		or value:sub(19, 19) ~= "-" or value:sub(24, 24) ~= "-" then return false end
	if not value:sub(15, 15):match("^[1-5]$") or not value:sub(20, 20):match("^[89aAbB]$") then
		return false
	end
	return value:gsub("%-", ""):match("^[0-9a-fA-F]+$") ~= nil
end

-- Pinned EML converts a mapped Guid to a Lua string. A missing mapped field is
-- nil; userdata/table values are therefore reported, but never stringified into
-- a false positive fingerprint.
local function model_fingerprint(data)
	local value = component(data, "keen::ecs::ModelResource")
	if value == nil then
		return { status = "MISSING", value_type = "NONE", value = "", reason = "component_missing" }
	end
	if value.model == nil then
		return { status = "MISSING", value_type = "NONE", value = "", reason = "field_absent_or_unmapped" }
	end
	if type(value.model) ~= "string" then
		return { status = "UNSUPPORTED", value_type = type(value.model), value = "",
			reason = "unexpected_lua_type" }
	end
	if not is_guid(value.model) then
		return { status = "UNSUPPORTED", value_type = "string", value = "", reason = "invalid_guid" }
	end
	return { status = "CONFIRMED", value_type = "GUID", value = value.model, reason = "" }
end

local source = game.assets.get_resource(SOURCE_GUID, "keen::ecs::TemplateResource")
assert(source, "aic_eml_humanoid: source TemplateResource is missing; unsupported game build")
local source_faction = component(source.data, "keen::ecs::Faction")
local source_npc = component(source.data, "keen::ecs::ActiveNpcState")
local source_model = component(source.data, "keen::ecs::ModelResource")
local source_model_fingerprint = model_fingerprint(source.data)
local source_graph = component(source.data, "keen::ecs::AnimationGraphResourceComponent2")
local source_components = component_names(source.data)
local source_before = table.concat({
	text(source_faction and source_faction.faction),
	text(source_npc and source_npc.npcId and source_npc.npcId.value),
	text(source_model and source_model.model),
	text(source_graph and source_graph.animationGraph),
	source_components,
}, "|")

local template = game.assets.create_resource(
	source.data, "keen::ecs::TemplateResource", TEMPLATE_GUID, 0
).data
template.name = TEMPLATE_NAME

local faction_set = false
local npc_id_set = false
for _, comp in ipairs(template.components) do
	if comp.type == "keen::ecs::Faction" then
		comp.value.faction = "PlayerAlly"
		faction_set = true
	elseif comp.type == "keen::ecs::ActiveNpcState" then
		comp.value.npcId = { value = NPC_ID }
		npc_id_set = true
	end
end
assert(faction_set, "aic_eml_humanoid: source has no Faction component")
assert(npc_id_set, "aic_eml_humanoid: source has no ActiveNpcState component")

local created = game.assets.get_resource(TEMPLATE_GUID, "keen::ecs::TemplateResource")
assert(created, "aic_eml_humanoid: new TemplateResource lookup failed")

-- EMF's pinned model-patch generator registers a cloned template here when
-- its source is registered. Keep the same conditional rule.
local registry = game.assets.get_resources_by_type("keen::GuidRegistryResource")[1]
local source_registered = false
local registry_added = false
if registry then
	local registered = {}
	for _, guid in ipairs(registry.data.guids) do
		registered[tostring(guid)] = true
	end
	source_registered = registered[tostring(source.guid)] == true
	if source_registered then
		table.insert(registry.data.guids, TEMPLATE_GUID)
		registry_added = true
	end
end

local new_model = component(created.data, "keen::ecs::ModelResource")
local new_model_fingerprint = model_fingerprint(created.data)
local new_graph = component(created.data, "keen::ecs::AnimationGraphResourceComponent2")
local source_after = table.concat({
	text(source_faction and source_faction.faction),
	text(source_npc and source_npc.npcId and source_npc.npcId.value),
	text(source_model and source_model.model),
	text(source_graph and source_graph.animationGraph),
	component_names(source.data),
}, "|")

if loader.features.export then
	local evidence = {
		"format=aic_eml_humanoid_evidence_v2",
		"patch_version=0.2.0",
		"run_token=" .. RUN_TOKEN,
		"template_guid=" .. TEMPLATE_GUID,
		"source_guid=" .. SOURCE_GUID,
		"template_name=" .. TEMPLATE_NAME,
		"npc_id=" .. tostring(NPC_ID),
		"faction=" .. text(component(created.data, "keen::ecs::Faction").faction),
		"source_faction=" .. text(source_faction and source_faction.faction),
		"model_status=" .. new_model_fingerprint.status,
		"model_component=keen::ecs::ModelResource",
		"model_field_path=value.model",
		"model_value_type=" .. new_model_fingerprint.value_type,
		"model_value=" .. new_model_fingerprint.value,
		"model_reason=" .. new_model_fingerprint.reason,
		"source_model_status=" .. source_model_fingerprint.status,
		"source_model_component=keen::ecs::ModelResource",
		"source_model_field_path=value.model",
		"source_model_value_type=" .. source_model_fingerprint.value_type,
		"source_model_value=" .. source_model_fingerprint.value,
		"source_model_reason=" .. source_model_fingerprint.reason,
		"model_match=" .. tostring(new_model_fingerprint.status == "CONFIRMED"
			and source_model_fingerprint.status == "CONFIRMED"
			and new_model_fingerprint.value:lower() == source_model_fingerprint.value:lower()),
		"animation_graph_guid=" .. text(new_graph and new_graph.animationGraph),
		"source_animation_graph_guid=" .. text(source_graph and source_graph.animationGraph),
		"components=" .. component_names(created.data),
		"source_components=" .. source_components,
		"component_clone=" .. tostring(component_names(created.data) == source_components),
		"source_unchanged=" .. tostring(source_before == source_after),
		"resource_lookup_after_create=true",
		"source_registered=" .. tostring(source_registered),
		"registry_added=" .. tostring(registry_added),
		"serialization_status=pending_writer_finalize",
	}
	io.export("aic_eml_humanoid/template_evidence_v2.txt", table.concat(evidence, "\n") .. "\n")
end

print("AIC_EML_TEMPLATE_READY", RUN_TOKEN, TEMPLATE_GUID, NPC_ID, new_model_fingerprint.status,
	text(new_graph and new_graph.animationGraph), registry_added)
