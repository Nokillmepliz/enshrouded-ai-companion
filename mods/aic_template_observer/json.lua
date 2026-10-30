local M = {}
local function esc(s) return s:gsub('\\','\\\\'):gsub('"','\\"'):gsub('\n','\\n'):gsub('\r','\\r'):gsub('\t','\\t') end
local function encode(v)
  local t=type(v)
  if t=='nil' then return 'null' elseif t=='boolean' or t=='number' then return tostring(v)
  elseif t=='string' then return '"'..esc(v)..'"' elseif t=='table' then
    local array,n=true,0; for k in pairs(v) do if type(k)~='number' then array=false; break end; if k>n then n=k end end
    local out={}; if array then for i=1,n do out[#out+1]=encode(v[i]) end; return '['..table.concat(out,',')..']' end
    local keys={}; for k in pairs(v) do keys[#keys+1]=k end; table.sort(keys)
    for _,k in ipairs(keys) do out[#out+1]=encode(tostring(k))..':'..encode(v[k]) end
    return '{'..table.concat(out,',')..'}'
  end
  error('unsupported json type '..t)
end
M.encode=encode
return M
