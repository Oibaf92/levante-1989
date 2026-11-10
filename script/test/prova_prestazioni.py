"""Prova di levante_prestazioni.lua: un aereo IA atterrato viene rimosso e annotato come rientrato;
il gruppo del giocatore e gli aerei in volo no; esiti.py non conta i rientrati come perdite."""
import os
import sys
from lupa import lua51

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(QUI, '..', 'tools'))
import esiti  # noqa: E402

L = lua51.LuaRuntime()
L.execute(open(os.path.join(QUI, 'mock_dcs.lua'), encoding='utf-8').read())
L.execute('LEVANTE = { missione = "PROVA" }; LEVANTE_GIOCATORE = { ["Hammer"] = true }')
L.execute(open(os.path.join(QUI, '..', 'lua', 'levante_core.lua'), encoding='utf-8').read())
L.execute('''
Unit.Category = { AIRPLANE = 0, HELICOPTER = 1, GROUND_UNIT = 2 }
RIMOSSI = {}
local function aereo(nome, gruppo, inaria, giocatore)
  return { getName = function() return nome end, isExist = function() return RIMOSSI[nome] == nil end,
           getDesc = function() return { category = 0 } end, getPlayerName = function() return giocatore end,
           getGroup = function() return { getName = function() return gruppo end } end,
           inAir = function() return inaria end, destroy = function() RIMOSSI[nome] = true end }
end
AEREI = { ["Viper-1"] = aereo("Viper-1", "Viper", false, nil), ["Hammer-2"] = aereo("Hammer-2", "Hammer", false, nil),
          ["Colt-1"] = aereo("Colt-1", "Colt", true, nil) }
Unit.getByName = function(n) return AEREI[n] end
''')
L.execute(open(os.path.join(QUI, '..', 'lua', 'levante_prestazioni.lua'), encoding='utf-8').read())
L.execute('''
for _, h in ipairs(MOCK.handlers) do
  h:onEvent({ id = world.event.S_EVENT_ENGINE_SHUTDOWN, initiator = AEREI["Viper-1"] })
  h:onEvent({ id = world.event.S_EVENT_ENGINE_SHUTDOWN, initiator = AEREI["Hammer-2"] })
  h:onEvent({ id = world.event.S_EVENT_LAND, initiator = AEREI["Colt-1"] })
end
''')
L.execute('MOCK.avanza(400)')
rimossi = sorted(L.eval('RIMOSSI').keys())
print('rimossi:', rimossi)
assert rimossi == ['Viper-1'], rimossi
assert 'Viper-1' in L.eval('LEVANTE.extra.rientrati')
costr = {'unita': [{'nome': 'Viper-1', 'gruppo': 'Viper', 'tipo': 'FA-18C_hornet', 'lato': 'blue', 'categoria': 'plane'}]}
e = esiti.esiti({'gruppi': {}, 'extra': {'rientrati': {'Viper-1': '10:00:00'}}}, costr, 1)
assert e['distrutti'] == [] and e['perdite_aeree'] == {}, e
print('OK')
