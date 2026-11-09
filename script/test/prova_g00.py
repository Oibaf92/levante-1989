"""Esegue levante_core.lua + G00_ambientamento.lua in un DCS simulato (Lua 5.1 via lupa)."""
import os, sys
from lupa import lua51
qui = os.path.dirname(os.path.abspath(__file__))
L = lua51.LuaRuntime()
def run(path):
    L.execute(open(path, encoding='utf-8').read())
run(os.path.join(qui, 'mock_dcs.lua'))
L.execute('LEVANTE = { missione = "G00_ambientamento", poligono = { x = 207254, y = -24700 } }')
run(os.path.join(qui, '..', 'lua', 'levante_core.lua'))
run(os.path.join(qui, '..', 'lua', 'G00_ambientamento.lua'))
L.execute('''
MOCK.avanza(10)
local g = MOCK.giocatore
for _, h in ipairs(MOCK.handlers) do
  h:onEvent({ id = world.event.S_EVENT_TAKEOFF, initiator = g, place = { getName = function() return "CVN-71" end } })
  h:onEvent({ id = world.event.S_EVENT_SHOT, initiator = g, weapon = { getTypeName = function() return "BDU-33" end, getDesc = function() return { category = 3 } end } })
  h:onEvent({ id = world.event.S_EVENT_LANDING_QUALITY_MARK, initiator = g, comment = "LSO: GRADE:OK  _OK_ 3 WIRE" })
end
MOCK.range:OnAfterImpact("a", "Impact", "b", { player = "Fabio", name = "Bersaglio B", weapon = "BDU-33", distance = 12.3, radial = 45, quality = "GOOD", attackHdg = 40, attackAlt = 9000, attackVel = 420, clock = "08:01:00" }, {})
MOCK.avanza(301)
MOCK.comandi["Informazioni poligono"]()
for _, h in ipairs(MOCK.handlers) do h:onEvent({ id = world.event.S_EVENT_MARK_CHANGE, idx = 55, text = "Poligono qui", pos = { x = 210000, y = 0, z = -20000 } }) end
print("distrutti:", MOCK.distrutti, "target A:", MOCK.range.bombingTargets[1].coordinate.x)
for _, h in ipairs(MOCK.handlers) do h:onEvent({ id = world.event.S_EVENT_MISSION_END }) end
''')
files = L.eval('MOCK.file')
for k in files:
    print('FILE', k, len(files[k]))
stato = files['C:\\SavedGames\\DCS\\Levante1989\\stato_G00_ambientamento.lua']
registro = files['C:\\SavedGames\\DCS\\Levante1989\\registro_G00_ambientamento.lua']
print(stato[:1200]); print('...'); print(registro[-900:])
sys.path.insert(0, os.path.join(qui, '..', 'tools'))
import luatable
n, v = luatable.parse(stato); print('parse stato ok:', n, list(v.keys()))
n, v = luatable.parse(registro); print('parse registro ok:', n, len(v['eventi']), 'eventi')
print('gruppi rimossi:', L.eval('MOCK.gruppiRimossi'))
print('statici creati:', L.eval('#MOCK.statici'))

pos = files['C:\\SavedGames\\DCS\\Levante1989\\poligono_G00_v2.lua']
print('FILE POSIZIONE:', pos)
# secondo avvio: deve usare la posizione salvata
L.execute('MOCK.statici = {}; MOCK.testi = {}')
run(os.path.join(qui, '..', 'lua', 'G00_ambientamento.lua'))
L.execute('MOCK.avanza(30)')
print('secondo avvio, ultimo messaggio:', list(L.eval('MOCK.testi').values())[-1])
