"""Screenshot simulato della missione R01 e verifica della calibrazione."""
import os
import sys
import json
import random
import numpy as np
from PIL import Image, ImageDraw
qui = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(qui, '..', 'tools'))
import foreste
dati = json.load(open(os.path.join(qui, '..', '..', 'campagna', 'terreno', 'marcatori_foreste.json')))
M = dati['marcatori']
# vista simulata: 1870x1000 px, 105 m/px, angolo nord-ovest scelto a caso dentro l'area
s_vero, W, H = 105.0, 1870, 1000
t = dati['tessere'][6]
X0, Y0 = t['x_nord'] + 4000, t['y_ovest'] - 5000
img = Image.new('RGB', (W, H), (231, 214, 151))
d = ImageDraw.Draw(img)
rnd = random.Random(3)
for _ in range(200):                                   # macchie di "bosco"
    cx, cy, r = rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(3, 25)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(115, 115, 58))
for m in M:                                            # crocette
    px, py = (m['y'] - Y0) / s_vero, (X0 - m['x']) / s_vero
    a = dati['braccio'] / s_vero
    d.line([px - a, py, px + a, py], fill=(255, 0, 255), width=3)
    d.line([px, py - a, px, py + a], fill=(255, 0, 255), width=3)
p = '/tmp/claude-0/-home-user-levante-1989/594c839f-9b10-599e-aa8a-ed2eb0e4850f/scratchpad/T_sim.png'
img.save(p)
r = foreste.elabora(p, M)
print('scala %.2f m/px (vera %.2f), X0 errore %.0f m, Y0 errore %.0f m, crocette %d, corrispondenze %d, errore medio %.0f m'
      % (r['s'], s_vero, r['X0'] - X0, r['Y0'] - Y0, r['crocette'], r['corrispondenze'], r['errore_m']))
print('pixel di bosco: %d' % r['bosco'].sum())
