-- Test double only. No game files, native API, pipe, or real entities.
fake = {session='testrun-1', entities={}, commands={}, handlers={}, events={}, removed={}, files={},
        next_id=100, tick=0, spawns=0, destroys=0, log={}, owner=1, server=true}
local F = fake
local function position(x) return {x=x or 0,y=0,z=0} end
F.entities[1] = {position=position(),model='player-model',kind='actor',health=100,faction=7,ready=true}
world = {}
function world:is_server() return F.server end
function world:position(id)
  local e = F.entities[id]; if not e then return nil end
  return e.position.x, e.position.y, e.position.z
end
function world:get(name, id)
  local e = F.entities[id]; if not e then return nil end
  if name == 'SpawnTime' then return e.birth and {spawnTime=e.birth} end
  if name == 'Faction' then
    if F.no_faction and id ~= 1 then return nil end
    return setmetatable({}, {__index=function(_,key) assert(key=='faction'); return e.faction end,
                            __newindex=function(_,key,value) assert(key=='faction'); e.faction=value end})
  end
  if name == 'DynamicEnemy01BehaviorState' and e.kind == 'enemy' then return {guardEntityId=e.guard or 0} end
  if name == 'Actor' and e.kind ~= 'static' then return {currentState=e.ready and 2^50 or 0} end
  return nil
end
function world:template(name, id)
  assert(name == 'ModelResource')
  local e = F.entities[id]
  if not e or F.no_model then return nil end
  return {model=e.model}
end
emf = {dir='FAKE', id='aic_body'}
function emf.session_token() return F.session end
function emf.local_player() return F.owner end
function emf.sender() return {chat=F.chat or false} end
function emf.emits(names) F.declared=names end
function emf.command(name, _, fn) F.commands[name]=fn; return true end
function emf.on_tick(fn) F.on_tick=fn end
function emf.on_event(name, fn, kind) assert(kind=='server'); F.handlers[name]=fn end
function emf.log(text) table.insert(F.log,text) end
function emf.reply(text) F.reply=text end
function emf.health(_,id) local e=F.entities[id]; return e and e.health end
function emf.spawn(_,guid,x,y,z)
  F.spawns=F.spawns+1
  if F.spawn_refused then return 0 end
  local id=F.next_id; F.next_id=id+1
  local enemy=guid=='d5d05217-52dc-467a-9192-26b4f661d8d9'
  F.entities[id]={position={x=x,y=y,z=z},model=enemy and 'vukah-model' or 'barrel-model',
                 kind=enemy and 'enemy' or 'static', health=enemy and 119 or nil,
                 faction=enemy and 3 or 0,ready=enemy and not F.not_ready,guard=enemy and 0 or nil}
  return id
end
function emf.destroy(_,id)
  F.destroys=F.destroys+1
  if F.destroy_refused then return false end
  F.removed[id]=true; return true
end
function emf.emit(kind,name,fields)
  assert(kind=='server')
  if F.emit_error then error('queue full') end
  table.insert(F.events,{name=name,fields=fields})
  -- Actual emf.emit returns no values. A truthiness check would be wrong.
end
io = {}
function io.open(path, mode)
  if F.io_error then return nil end
  if mode == 'r' and not F.files[path] then return nil end
  local buffer=F.files[path]
  return {read=function() return buffer and buffer:match('([^\n]+)') end,
          write=function(_,text) buffer=text; return true end,
          close=function() if mode=='w' then F.files[path]=buffer end; return true end}
end
os.remove=function(path) if F.io_error then return nil end; F.files[path]=nil; return true end
function F.command(name, args)
  F.reply=nil; F.commands[name](world,args); return F.reply
end
function F.step(count)
  for _=1,count do
    F.tick=F.tick+1
    if not F.destroy_delayed then
      for id in pairs(F.removed) do F.entities[id]=nil end
      F.removed={}
    end
    if not F.drop_events then
      for _,ev in ipairs(F.events) do
        local e=F.entities[ev.fields.guardingEntityId]
        if e then e.guard=ev.name=='StartGuardingEvent' and ev.fields.guardedEntityId or 0 end
      end
    end
    F.events={}
    F.on_tick(world)
  end
end
