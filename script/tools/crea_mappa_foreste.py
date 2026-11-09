"""Unisce gli screenshot SAT della missione R01 in una griglia di vegetazione da 250 m.

Uso: python3 crea_mappa_foreste.py
Legge campagna/terreno/screenshot_foreste/*.webp (senza perdita), scrive:
  campagna/terreno/vegetazione_250m.npz   (frazione di vegetazione per cella, NaN = non coperta)
  campagna/terreno/vegetazione_80m.npz    (percentuale 0-100 per cella da 80 m, 255 = non coperta)
  campagna/terreno/mappa_vegetazione.png  (controllo visivo, nord in alto)
"""
import glob
import json
import os
import numpy as np
from PIL import Image
import foreste

RADICE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
TER = os.path.join(RADICE, 'campagna', 'terreno')
RITAGLIO = (52, 42, 1920, 1050)


def main():
    dati = json.load(open(os.path.join(TER, 'marcatori_foreste.json')))
    xs = [t['x_sud'] for t in dati['tessere']] + [t['x_nord'] for t in dati['tessere']]
    ys = [t['y_ovest'] for t in dati['tessere']] + [t['y_est'] for t in dati['tessere']]
    mo = foreste.Mosaico(min(xs), max(xs), min(ys), max(ys), 250)
    fine = foreste.Mosaico(min(xs), max(xs), min(ys), max(ys), 80)
    for f in sorted(glob.glob(os.path.join(TER, 'screenshot_foreste', '*.webp'))):
        r = foreste.elabora(f, dati['marcatori'], ritaglio=RITAGLIO)
        mo.aggiungi(r, RITAGLIO)
        fine.aggiungi(r, RITAGLIO)
        print('%-14s scala %.1f m/px, corrispondenze %d/%d, errore %.0f m'
              % (os.path.basename(f), r['s'], r['corrispondenze'], r['crocette'], r['errore_m']))
    fr = mo.frazione()
    np.savez_compressed(os.path.join(TER, 'vegetazione_250m.npz'), frazione=fr.astype(np.float32),
                        x0=mo.x0, y0=mo.y0, passo=mo.passo)
    ff = fine.frazione()
    np.savez_compressed(os.path.join(TER, 'vegetazione_80m.npz'),
                        percento=np.where(np.isnan(ff), 255, np.round(ff * 100)).astype(np.uint8),
                        x0=fine.x0, y0=fine.y0, passo=fine.passo)
    img = np.full(fr.shape + (3,), (200, 200, 205), np.uint8)
    v = ~np.isnan(fr)
    g = np.clip(np.nan_to_num(fr) * 1.5, 0, 1)
    img[v] = np.stack([235 - 200 * g[v], 230 - 120 * g[v], 210 - 190 * g[v]], -1).astype(np.uint8)
    Image.fromarray(img[::-1]).save(os.path.join(TER, 'mappa_vegetazione.png'))
    print('celle coperte: %.0f%%' % (100 * v.mean()))


if __name__ == '__main__':
    main()
