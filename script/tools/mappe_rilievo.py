"""Mappe di controllo del rilievo del terreno: rilievo, pendenza, edifici, strade."""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import rilievo
import confini
from geo import ll_to_xy

F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'


def _img_regione(reg, campo):
    d = reg.dati
    acqua = (d['sup'] == 3) | (d['sup'] == 2)
    v = d[campo].astype(float)
    rgb = np.zeros(v.shape + (3,), dtype=np.uint8)
    if campo == 'quota':
        q = np.clip(v / 2000.0, 0, 1)
        # ombreggiatura da nord-ovest per leggere il rilievo
        gx, gy = np.gradient(np.where(acqua, 0, v))
        luce = np.clip(0.75 + (gx - gy) / (reg.passo * 0.6), 0.35, 1.15)
        base = np.stack([150 + 80 * q, 170 + 40 * q - 60 * q * q, 110 + 60 * q], -1)
        rgb = np.clip(base * luce[..., None], 0, 255).astype(np.uint8)
    elif campo == 'pendenza':
        p = np.clip(v / 40.0, 0, 1)
        rgb = np.stack([235 * np.ones_like(p), 235 - 200 * p, 220 - 200 * p], -1).astype(np.uint8)
        rgb[(v >= 15) & ~acqua] = (200, 40, 30)
    elif campo == 'edifici':
        e = np.clip(v / 40.0, 0, 1)
        rgb = np.stack([235 - 60 * e, 230 - 160 * e, 215 - 200 * e], -1).astype(np.uint8)
        rgb[(v > 0) & (v < 3)] = (215, 190, 150)
    elif campo == 'strada':
        s = np.clip(v / 5000.0, 0, 1)
        rgb = np.stack([60 + 180 * s, 60 + 175 * s, 60 + 160 * s], -1).astype(np.uint8)
    rgb[acqua] = (170, 200, 225)
    return rgb


def mappa(terreno, campo, titolo, uscita, scala_px=1.0):
    gen = next(r for r in terreno.regioni if r.nome == 'generale')
    det = next(r for r in terreno.regioni if r.nome == 'dettaglio')
    # griglia di uscita alla risoluzione di 1 km (dettaglio), nord in alto
    passo = det.passo
    nx = int(gen.nx * gen.passo / passo)
    ny = int(gen.ny * gen.passo / passo)
    g = _img_regione(gen, campo)
    out = np.repeat(np.repeat(g, gen.passo // passo, 0), gen.passo // passo, 1)[:nx, :ny]
    i0 = int(round((det.x0 - gen.x0) / passo))
    j0 = int(round((det.y0 - gen.y0) / passo))
    out[i0:i0 + det.nx, j0:j0 + det.ny] = _img_regione(det, campo)
    img = Image.fromarray(out[::-1])          # x cresce verso nord: capovolgi per avere il nord in alto
    d = ImageDraw.Draw(img)

    def p(x, y):
        return ((y - gen.y0) / passo, nx - 1 - (x - gen.x0) / passo)
    for nome, punti, colori, _ in confini.TERRITORI:
        if nome.startswith('Zona operativa'):
            continue
        xy = [ll_to_xy(*q) for q in punti] + [ll_to_xy(*punti[0])]
        d.line([p(*q) for q in xy], fill=(30, 30, 30), width=1)
    d.rectangle([(j0, nx - i0 - det.nx), (j0 + det.ny, nx - i0)], outline=(0, 0, 160), width=1)
    d.rectangle([0, 0, img.width, 34], fill=(25, 25, 30))
    d.text((10, 6), titolo, font=ImageFont.truetype(F % '-Bold', 18), fill=(240, 235, 220))
    img.save(uscita)


if __name__ == '__main__':
    t = rilievo.Terreno.carica(sys.argv[1])
    pref = sys.argv[2]
    mappa(t, 'quota', 'Rilievo (quota)', pref + '_quota.png')
    mappa(t, 'pendenza', 'Pendenza (rosso = oltre 15%)', pref + '_pendenza.png')
    mappa(t, 'edifici', 'Edifici entro 400 m (scuro = centri abitati)', pref + '_edifici.png')
    mappa(t, 'strada', 'Distanza dalla strada (scuro = vicino)', pref + '_strade.png')
