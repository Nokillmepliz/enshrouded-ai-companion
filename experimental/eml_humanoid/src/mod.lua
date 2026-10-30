-- Experimental EML 0.2.0 data patch. It creates data only and never spawns an entity.
if not loader.features.patch then
	return
end

local TEMPLATE_GUID = "a1c90001-5e4d-4a91-8a1c-000000000001"
local SOURCE_GUID = "e3736dff-0ad2-47fc-903c-66c1775836e8" -- hunter_assistant
local TEMPLATE_NAME = "AIC_Humanoid_Companion_Experimental"
local NPC_ID = game.guid.hash(TEMPLATE_GUID)

local source = game.assets.get_resource(SOURCE_GUID, "keen::ecs::TemplateResource")
assert(source, "aic_eml_humanoid: source TemplateResource is missing; unsupported game build")

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

-- EMF's pinned model-patch generator registers a cloned template here when
-- its source is registered. Keep the same conditional rule.
local registry = game.assets.get_resources_by_type("keen::GuidRegistryResource")[1]
if registry then
	local registered = {}
	for _, guid in ipairs(registry.data.guids) do
		registered[tostring(guid)] = true
	end
	if registered[tostring(source.guid)] then table.insert(registry.data.guids, TEMPLATE_GUID) end
end

print("aic_eml_humanoid: created disabled experimental template", TEMPLATE_GUID, NPC_ID)
