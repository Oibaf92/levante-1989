"""Esegue R00_rilievo.lua in un DCS simulato e rilegge il file con tools/rilievo.py."""
import os
import sys
from lupa import lua51
qui = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(qui, '..', 'tools'))
L = lua51.LuaRuntime()
L.execute(open(os.path.join(qui, 'mock_dcs.lua'), encoding='utf-8').read())
L.execute('''
land.getHeight = function(p) return 100 + 50 * math.sin(p.x / 3000) + 30 * math.cos(p.y / 2000) end
land.getSurfaceType = function(p) if p.y < -100000 then return 3 end return 1 end
land.getClosestPointOnRoads = function(t, x, z) return x + 500, z end
world.searchObjects = function(cat, vol, fn) if math.floor(vol.params.point.x / 1000) % 7 == 0 then fn(); fn() end end
LEVANTE_RILIEVO = { regioni = {
  { nome = "generale", x0 = 0, y0 = -110000, passo = 2000, nx = 20, ny = 15 },
  { nome = "dettaglio", x0 = 10000, y0 = -100000, passo = 1000, nx = 12, ny = 9 },
}, punti_per_passo = 37 }
''')
L.execute(open(os.path.join(qui, '..', 'lua', 'R00_rilievo.lua'), encoding='utf-8').read())
L.execute('for k = 1, 2000 do MOCK.avanza(0.02) end')
files = L.eval('MOCK.file')
testo = files['C:\\SavedGames\\DCS\\Levante1989\\rilievo_terreno.txt']
print(testo[:400])
p = '/tmp/claude-0/-home-user-levante-1989/594c839f-9b10-599e-aa8a-ed2eb0e4850f/scratchpad/rilievo_prova.txt'
open(p, 'w').write(testo)
import rilievo
t = rilievo.Terreno.carica(p)
print(t.riepilogo())
print(t.punto(12000, -96000), t.punto(2000, -108000), t.punto(30000, -95000))
print('messaggi:', list(L.eval('MOCK.testi').values())[-2:])
