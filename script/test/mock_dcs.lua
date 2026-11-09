-- Ambiente DCS simulato, minimo, per provare gli script fuori dal gioco.
MOCK = { testi = {}, file = {}, timers = {}, handlers = {}, statici = {} }
env = { info = function(m) print("ENV: " .. m) end, mission = { date = { Year = 1989, Month = 10, Day = 2 }, theatre = "Syria" } }
world = { event = {}, VolumeType = { SPHERE = 2 } }
local nomi = { "S_EVENT_SHOT","S_EVENT_HIT","S_EVENT_TAKEOFF","S_EVENT_LAND","S_EVENT_CRASH","S_EVENT_EJECTION","S_EVENT_DEAD","S_EVENT_PILOT_DEAD","S_EVENT_BIRTH","S_EVENT_ENGINE_STARTUP","S_EVENT_ENGINE_SHUTDOWN","S_EVENT_PLAYER_ENTER_UNIT","S_EVENT_PLAYER_LEAVE_UNIT","S_EVENT_REFUELING","S_EVENT_REFUELING_STOP","S_EVENT_LANDING_QUALITY_MARK","S_EVENT_UNIT_LOST","S_EVENT_KILL","S_EVENT_RUNWAY_TAKEOFF","S_EVENT_RUNWAY_TOUCH","S_EVENT_MISSION_END" }
for i, n in ipairs(nomi) do world.event[n] = i end
function world.addEventHandler(h) table.insert(MOCK.handlers, h) end
function world.searchObjects(cat, vol, fn) if MOCK.edifici and math.abs(vol.params.point.x - MOCK.edifici.x) < 2000 then fn() end return 0 end
function world.getAirbases() return { { getDesc = function() return { category = 0 } end, getName = function() return "Incirlik" end, getCoalition = function() return 0 end } } end
Airbase = { Category = { AIRDROME = 0 } }
Object = { Category = { SCENERY = 5 } }
Weapon = { Category = { SHELL = 0 } }
land = { SurfaceType = { LAND = 1, SHALLOW_WATER = 2, WATER = 3, ROAD = 4, RUNWAY = 5 } }
function land.getSurfaceType(p) return 1 end
function land.getHeight(p) return 20 end
coord = { LOtoLL = function(p) return 36.88, 35.55, p.y end }
local tempo = 0
timer = { getTime = function() return tempo end, getAbsTime = function() return 27000 + tempo end,
  scheduleFunction = function(f, a, t) table.insert(MOCK.timers, { f = f, a = a, t = t }) end }
function MOCK.avanza(sec)
  tempo = tempo + sec
  local ancora = true
  while ancora do
    ancora = false
    for i, tm in ipairs(MOCK.timers) do
      if tm.t <= tempo then
        table.remove(MOCK.timers, i)
        local r = tm.f(tm.a, tm.t)
        if r then table.insert(MOCK.timers, { f = tm.f, a = tm.a, t = r }) end
        ancora = true
        break
      end
    end
  end
end
trigger = { action = {
  outText = function(t) table.insert(MOCK.testi, t); print("TESTO: " .. t) end,
  smoke = function() end, markToAll = function() end },
  smokeColor = { Green = 0, Red = 1, White = 2, Orange = 3, Blue = 4 } }
missionCommands = { addSubMenu = function(n) return { n } end, addCommand = function(n, m, f) MOCK.comandi = MOCK.comandi or {}; MOCK.comandi[n] = f end }
country = { id = { USA = 2 } }
coalition = { side = { NEUTRAL = 0, RED = 1, BLUE = 2 } }
function coalition.addStaticObject(c, t) table.insert(MOCK.statici, t) end
local function unita(nome, tipo, giocatore)
  return { getName = function() return nome end, getTypeName = function() return tipo end, getLife = function() return 10 end,
    getLife0 = function() return 10 end, isActive = function() return true end, isExist = function() return true end,
    getPoint = function() return { x = 1, y = 2, z = 3 } end, getPlayerName = function() return giocatore end,
    getCoalition = function() return 2 end, getFuel = function() return 0.8 end, getVelocity = function() return { x = 100, y = 0, z = 0 } end,
    getGroup = function() return { getName = function() return "G-" .. nome end } end }
end
MOCK.giocatore = unita("Dodge11", "F-14A-135-GR-Early", "Fabio")
function coalition.getGroups(c, cat)
  if c == 2 and cat == 0 then return { { getName = function() return "Dodge 1" end, isExist = function() return true end, getUnits = function() return { MOCK.giocatore } end } } end
  return {}
end
function coalition.getStaticObjects(c) return {} end
-- MOOSE minimo
COORDINATE = { New = function(self, x, y, z) return { x = x, y = y, z = z } end }
RANGE = { New = function(self, n) local o = {}; setmetatable(o, { __index = RANGE }); MOCK.range = o; return o end,
  AddBombingTargetCoordinate = function(s) return s end, SetScoreBombDistance = function(s) return s end,
  SetRangeRadius = function(s) return s end, SetMessageTimeDuration = function(s) return s end, Start = function(s) return s end }
-- io/lfs simulati
lfs = { writedir = function() return "C:\\SavedGames\\DCS\\" end, mkdir = function() end }
io = { open = function(p, m) local buf = {}; return { write = function(_, s) table.insert(buf, s) end, close = function() MOCK.file[p] = table.concat(buf) end } end }
