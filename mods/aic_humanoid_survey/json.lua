-- Minimal deterministic JSON encoder for diagnostic output only.
local M = {}
local function quote(s)
  return '"' .. s:gsub('[%z\1-\31\\"]', function(c)
    if c == '"' then return '\\"' end
    if c == '\\' then return '\\\\' end
    return string.format('\\u%04x', c:byte())
  end) .. '"'
end
function M.encode(v)
  if v == nil then return 'null' end
  if type(v) == 'string' then return quote(v) end
  if type(v) == 'boolean' then return tostring(v) end
  if type(v) == 'number' then return string.format('%.17g', v) end
  assert(type(v) == 'table', 'unsupported JSON value')
  local keys, fields = {}, {}
  for k in pairs(v) do assert(type(k) == 'string'); keys[#keys+1] = k end
  table.sort(keys)
  for _, k in ipairs(keys) do fields[#fields+1] = quote(k) .. ':' .. M.encode(v[k]) end
  return '{' .. table.concat(fields, ',') .. '}'
end
return M
