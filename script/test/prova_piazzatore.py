"""Prova di levante_piazzatore.lua in DCS simulato: verifica all'avvio e SPOSTA."""
import os, sys, zipfile
from lupa import lua51
qui = os.path.dirname(os.path.abspath(__file__))
z = zipfile.ZipFile(os.path.join(qui, '..', '..', 'missioni', 'P00_prova_piazzatore.miz'))
init = z.read('l10n/DEFAULT/p00_init.lua').decode()
L = lua51.LuaRuntime()
L.execute(open(os.path.join(qui, 'mock_dcs.lua'), encoding='utf-8').read())
# terreno simulato: edificio vicino alle x multiple di 1000, pendenza ripida in una fascia
L.execute('''
land.getSurfaceType = function(p) return 1 end
land.getHeight = function(p) if p.x % 5000 < 40 then return p.x * 0.5 end return 100 end
world.searchObjects = function(cat, vol, fn) if vol.params.radius < 100 and vol.params.point.z % 200 < 40 then fn() end end
''')
L.execute(init)
L.execute(open(os.path.join(qui, '..', 'lua', 'levante_core.lua'), encoding='utf-8').read())
# crea i gruppi come se fossero nel .miz
L.execute('''
for nome, d in pairs(LEVANTE_PIAZZAMENTI) do
  local pos = d.posizioni[1]
  local r = math.rad(pos.rotta)
  local g = { name = nome, units = {} }
  for k, u in ipairs(d.unita) do
    g.units[k] = { type = u.tipo, x = pos.x + u.avanti * math.cos(r) - u.destra * math.sin(r),
                   y = pos.y + u.avanti * math.sin(r) + u.destra * math.cos(r) }
  end
  MOCK.gruppi[nome] = g
end
''')
L.execute(open(os.path.join(qui, '..', 'lua', 'levante_piazzatore.lua'), encoding='utf-8').read())
L.execute('MOCK.ricreati = 0'); [L.execute('MOCK.avanza(1)') for _ in range(6)]
print('gruppi ricreati dopo la verifica:', L.eval('MOCK.ricreati'))
ver = L.eval('LEVANTE.extra.piazzatore.verifiche')
tot = sum(v['spostate'] for v in ver.values())
print('gruppi verificati: %d, veicoli spostati: %d' % (len(list(ver.items())), tot))
# SPOSTA vicino al SA-6 Bekaa
L.execute('''
local g = MOCK.gruppi["SA-6 Bekaa"].units[1]
for _, h in ipairs(MOCK.handlers) do h:onEvent({ id = world.event.S_EVENT_MARK_CHANGE, idx = 77, text = "sposta qui", pos = { x = g.x + 500, y = 0, z = g.y } }) end
''')
print('spostamenti:', [(s['gruppo'], s['alternativa']) for s in L.eval('LEVANTE.extra.piazzatore.spostamenti').values()])
print('ultimo messaggio:', list(L.eval('MOCK.testi').values())[-1])
