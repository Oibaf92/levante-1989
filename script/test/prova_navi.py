"""Prova di levante_navi.lua in DCS simulato: rotta contro vento ed evitamento della terra."""
import os, sys, zipfile, glob
from lupa import lua51
qui = os.path.dirname(os.path.abspath(__file__))
miz = sorted(f for f in glob.glob(os.path.join(qui, '..', '..', 'missioni', 'G1[0-9]_*.miz')) if not f.endswith('_TEST.miz'))[0]
z = zipfile.ZipFile(miz)
L = lua51.LuaRuntime()
L.execute(open(os.path.join(qui, 'mock_dcs.lua'), encoding='utf-8').read())
L.execute(z.read('l10n/DEFAULT/init.lua').decode())
L.execute(open(os.path.join(qui, '..', 'lua', 'levante_core.lua'), encoding='utf-8').read())
L.execute('''
land.SurfaceType = land.SurfaceType or { LAND = 1, SHALLOW_WATER = 2, WATER = 3, ROAD = 4, RUNWAY = 5 }
-- terra a nord di x = 30000 sopra la LHA (per la prova di evitamento), mare altrove
TERRA_X = nil
land.getSurfaceType = function(p) if TERRA_X and p.x > TERRA_X then return land.SurfaceType.LAND end return land.SurfaceType.WATER end
-- vento che soffia VERSO est (viene da ovest, 270) a 5 m/s
atmosphere = { getWind = function(p) return { x = 0, y = 0, z = 5 } end }
COMPITI, COMANDI = {}, {}
POS = {}
Group.getByName = function(n)
  return { isExist = function() return true end,
    getUnit = function() return { getPoint = function() return POS[n] end,
                                  getPosition = function() return { x = { x = 1, y = 0, z = 0 } } end } end,
    getController = function() return { setTask = function(_, t) COMPITI[n] = t end,
                                        setCommand = function(_, c) COMANDI[n] = (COMANDI[n] or 0) + 1 end } end }
end
POS["CVN-71 Roosevelt"] = { x = 0, y = 0, z = 0 }
POS["LHA-1 Tarawa"] = { x = 0, y = 0, z = 100000 }
''')
L.execute(open(os.path.join(qui, '..', 'lua', 'levante_navi.lua'), encoding='utf-8').read())
L.execute('MOCK.avanza(2)')
import math
def esito(n):
    r = L.eval('COMPITI["%s"].params.route.points' % n)
    a, b = r[1], r[2]
    prua = math.degrees(math.atan2(b['y'] - a['y'], b['x'] - a['x'])) % 360
    return round(prua), round(b['speed'] / 0.514444), round(math.hypot(b['x'] - a['x'], b['y'] - a['y']) / 1852), L.eval('COMANDI["%s"]' % n)
cvn, lha = esito('CVN-71 Roosevelt'), esito('LHA-1 Tarawa')
print('CVN prua/nodi/nm/comandi:', cvn, ' LHA:', lha)
assert abs(cvn[0] - 279) <= 1 and abs(lha[0] - 270) <= 1, 'prua non contro vento'
assert cvn[3] == 4 and lha[3] == 1
# terra davanti a nord: vento da nord, la nave deve accorciare o deviare
L.execute('atmosphere.getWind = function(p) return { x = -5, y = 0, z = 0 } end; TERRA_X = 30000')
L.execute('MOCK.avanza(1900)')
cvn2 = esito('CVN-71 Roosevelt')
fine_x = L.eval('COMPITI["CVN-71 Roosevelt"].params.route.points[2].x')
print('con terra a 30 km a nord:', cvn2, 'fine tratta x = %.0f m' % fine_x)
assert fine_x < 30000 - 2000, 'la tratta finisce sulla terra'
# distanza minima da una minaccia (regole riviste: CVN ad almeno 150 nm da Tartus)
L.execute('''TERRA_X = nil
LEVANTE_NAVI["CVN-71 Roosevelt"].minacce = { { nome = "Tartus", x = 0, z = 300000, min_m = 280000 } }
atmosphere.getWind = function(p) return { x = 0, y = 0, z = -6 } end   -- vento da est: contro vento = verso la minaccia
POS["CVN-71 Roosevelt"] = { x = 0, y = 0, z = 0 }''')
L.execute('MOCK.avanza(1900)')
cvn3 = esito('CVN-71 Roosevelt')
fz = L.eval('COMPITI["CVN-71 Roosevelt"].params.route.points[2].y')
print('margine 20 km, vento da est:', cvn3, 'distanza finale %.0f m' % (300000 - fz))
assert 59 <= cvn3[0] <= 139 and 300000 - fz >= 280000, 'la tratta entra nella distanza minima'
# gia' dentro la distanza minima: tratta di riposizionamento lontano dalla minaccia
L.execute('POS["CVN-71 Roosevelt"] = { x = 0, y = 0, z = 30000 }')
L.execute('MOCK.avanza(1900)')
cvn4 = esito('CVN-71 Roosevelt')
print('dentro di 10 km:', cvn4)
assert 250 <= cvn4[0] <= 290 and cvn4[1] == 30, 'la nave non si allontana dalla minaccia'
print('OK')
