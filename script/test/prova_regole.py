"""Prova di levante_regole.lua: eiezione, AIM-54 lanciati, tiri d'artiglieria, traccia TARPS,
pilota recuperato da un elicottero amico atterrato vicino."""
import os
from lupa import lua51

QUI = os.path.dirname(os.path.abspath(__file__))
L = lua51.LuaRuntime()
L.execute(open(os.path.join(QUI, 'mock_dcs.lua'), encoding='utf-8').read())
L.execute('LEVANTE = { missione = "PROVA" }')
L.execute(open(os.path.join(QUI, '..', 'lua', 'levante_core.lua'), encoding='utf-8').read())
L.execute('''
Unit.Category = { AIRPLANE = 0, HELICOPTER = 1, GROUND_UNIT = 2 }
land.SurfaceType = { LAND = 1, SHALLOW_WATER = 2, WATER = 3, ROAD = 4, RUNWAY = 5 }
land.getSurfaceType = function() return 1 end
trigger.action.outTextForCoalition = function() end
LEVANTE_ARTIGLIERIA = { ["Art"] = true }
LEVANTE_TARPS = { ["Recce"] = true }
LEVANTE_PILOTI = { ["Hammer-2"] = { x = 1000, y = 2000, coal = 2 } }
local function oggetto(nome, gruppo, coal, cat, x, z, alt, inaria)
  return { getName = function() return nome end, getTypeName = function() return "T" end, getCoalition = function() return coal end,
           getGroup = function() return { getName = function() return gruppo end } end, getPlayerName = function() return nil end,
           getDesc = function() return { category = cat } end, getPoint = function() return { x = x, y = alt or 0, z = z } end,
           isExist = function() return true end, inAir = function() return inaria end }
end
F14 = oggetto("Cedro-1", "Cedro", 2, 0, 5000, 5000, 3000, true)
ART = oggetto("Art-1", "Art", 1, 2, 9000, 9000)
HELO = oggetto("Mulo-1", "Mulo", 2, 1, 1100, 2100)
RECCE = oggetto("Recce-1", "Recce", 2, 0, 20000, 20000, 3000, true)
Group.getByName = function(n) if n == "Recce" then return { isExist = function() return true end,
  getUnits = function() return { RECCE } end } end return nil end
''')
L.execute(open(os.path.join(QUI, '..', 'lua', 'levante_regole.lua'), encoding='utf-8').read())
L.execute('''
local function ev(id, u, arma) for _, h in ipairs(MOCK.handlers) do h:onEvent({ id = id, initiator = u, weapon = arma }) end end
ev(world.event.S_EVENT_EJECTION, F14)
ev(world.event.S_EVENT_SHOT, F14, { getTypeName = function() return "AIM_54C_Mk47" end })
ev(world.event.S_EVENT_SHOT, F14, { getTypeName = function() return "AIM_54C_Mk47" end })
ev(world.event.S_EVENT_SHOT, ART, { getTypeName = function() return "3OF56" end })
ev(world.event.S_EVENT_LAND, HELO)
''')
for _ in range(30):
    L.execute('MOCK.avanza(1)')
L.execute('ev2 = function() for _, h in ipairs(MOCK.handlers) do h:onEvent({ id = world.event.S_EVENT_LAND, initiator = RECCE }) end end; ev2()')
X = L.eval('LEVANTE.extra')
assert len(X['eiezioni']) == 1 and X['eiezioni'][1]['coal'] == 2
assert X['aim54'][2] == 2
assert X['tiri'][1]['gruppo'] == 'Art'
assert 'Hammer-2' in X['csar']
assert X['tarps']['Recce-1']['atterrato'] and len(X['tarps']['Recce-1']['punti']) >= 2
print('OK')
