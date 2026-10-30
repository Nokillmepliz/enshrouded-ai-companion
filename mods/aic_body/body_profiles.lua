-- Runtime profiles are deliberately separate from the generic lifecycle controller.
-- Only the historical Vukah profile is wired to a live adapter. Human candidates
-- remain research-only until their spawn, identity and cleanup are verified in game.
local profiles = {
  legacy_vukah = {
    id = 'legacy_vukah',
    template = 'd5d05217-52dc-467a-9192-26b4f661d8d9',
    marker = '0ce28db1-522f-4455-b358-3888fb5e089b',
  },
}

local M = {}
function M.get(id) return profiles[id] end
function M.active() return profiles.legacy_vukah end
return M
