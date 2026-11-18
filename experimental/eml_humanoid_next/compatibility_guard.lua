-- Stage 10.10 offline preparation for patch 0.5.0. NOT a loadable EML mod.
-- Only confirmed EML 0.2.0 APIs; no create_resource/export/writer/entity calls.
local M = {}
local function fail(code) error("aic_compatibility:" .. code, 0) end
local function component(data, name)
 for _, c in ipairs(data.components) do if c.type == name then return c.value end end
end
local function uint32(value)
 local ok, n = pcall(function() return value.value end)
 if not ok or type(n) ~= "number" or n % 1 ~= 0 or n < 0 or n > 4294967295 then
  fail("unsupported_hashkey32")
 end
 return n
end
local function fingerprint(data)
 local names = {}
 for _, c in ipairs(data.components) do names[#names + 1] = c.type end
 table.sort(names)
 local text, h = table.concat(names, ","), 2166136261
 for i = 1, #text do h = ((h ~ text:byte(i)) * 16777619) & 0xffffffff end
 return string.format("%08x", h)
end
function M.inspect(game, profile)
 if type(profile) ~= "table" or profile.clean_baseline_verified ~= true then fail("clean_baseline_required") end
 local required = {"voicePackId","presetId","hair","beard","hairColorId","beardColorId","skinColor","eyeBrowColor","eyeColor"}
 if type(profile.hashkeys) ~= "table" or type(profile.dependencies) ~= "table" or #profile.dependencies == 0 then
  fail("incomplete_profile")
 end
 for _, field in ipairs(required) do if profile.hashkeys[field] == nil then fail("incomplete_profile") end end
 if type(game.version) ~= "string" or tonumber(game.version:match("^(%d+)|")) ~= profile.game_build then
  fail("UNSUPPORTED_GAME_BUILD")
 end
 local kind = "keen::ecs::TemplateResource"
 if game.assets.get_resource(profile.clone_guid, kind) then fail("custom_guid_collision") end
 local source = game.assets.get_resource(profile.source_guid, kind)
 if not source then fail("source_missing") end
 if #source.data.components ~= profile.component_count or fingerprint(source.data) ~= profile.component_fingerprint then
  fail("component_schema_changed")
 end
 local setup = component(source.data, "keen::ecs::CharacterSetup")
 if not setup or setup.gender ~= profile.gender or setup.useNewProportions ~= profile.use_new_proportions then
  fail("character_setup_changed")
 end
 for field, expected in pairs(profile.hashkeys) do
  if uint32(setup[field]) ~= expected then fail("source_hashkey_changed:" .. field) end
 end
 local graph = component(source.data, "keen::ecs::AnimationGraphResourceComponent2")
 if not graph or tostring(graph.animationGraph) ~= profile.animation_graph then fail("animation_graph_changed") end
 for _, ref in ipairs(profile.dependencies) do
  if not game.assets.get_resource(ref.guid, ref.type) then fail("resource_dependency_missing") end
 end
 for _, resource in ipairs(game.assets.get_resources_by_type(kind)) do
  local npc = component(resource.data, "keen::ecs::ActiveNpcState")
  if npc and uint32(npc.npcId) == profile.npc_id then fail("npc_id_collision") end
 end
 return {source=source, installation_ready=false, spawn_ready=false,
         runtime_status="NOT_EXECUTED", writer_status="NOT_EXECUTED"}
end
return M
