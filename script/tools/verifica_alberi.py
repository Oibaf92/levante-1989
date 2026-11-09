"""Controllo degli alberi attorno alle unita' piazzate, da screenshot ravvicinati del Mission Editor.

A zoom massimo (vista SAT, scala ~200 ft) gli alberi di DCS si vedono uno per uno.
Lo screenshot si calibra sulle icone delle unita' stesse, che sono in posizioni note:

  1. rileva le icone delle unita' (riquadri rossi o blu);
  2. le associa alle posizioni note delle unita' del gruppo -> scala e traslazione
     (mappa del Mission Editor: nord in alto, nessuna rotazione);
  3. rileva gli alberi (puntini verdi piu' scuri del campo attorno);
  4. per ogni unita' conta gli alberi entro RAGGIO_LIBERO e, se ce ne sono, propone
     lo spostamento piu' corto verso un punto libero (entro SPOSTAMENTO_MAX).

Uso:
    r = verifica('T.png', [(tipo, x, y), ...])
    r['unita'] -> [{'tipo','x','y','alberi','nuova_x','nuova_y','spostamento_m'}, ...]
"""
import itertools
import math
from collections import deque

import numpy as np
from PIL import Image

RAGGIO_LIBERO = 14.0         # m senza alberi attorno al centro del veicolo
SPOSTAMENTO_MAX = 150.0      # m
AREA_MAPPA = (52, 42, 1920, 1050)


def _componenti(mask, min_px=40):
    h, w = mask.shape
    visto = np.zeros_like(mask)
    out = []
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys, xs):
        if visto[y0, x0]:
            continue
        coda = deque([(y0, x0)])
        visto[y0, x0] = True
        pts = []
        while coda:
            y, x = coda.popleft()
            pts.append((x, y))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not visto[yy, xx]:
                    visto[yy, xx] = True
                    coda.append((yy, xx))
        if len(pts) >= min_px:
            a = np.array(pts)
            out.append((a[:, 0].min(), a[:, 1].min(), a[:, 0].max(), a[:, 1].max(), len(pts)))
    return out


def rileva_icone(rgb):
    """Centri delle icone delle unita' (riquadri pieni rossi o blu del Mission Editor)."""
    r, g, b = (rgb[..., k].astype(int) for k in range(3))
    rosso = (r > 190) & (g < 70) & (b < 70)
    blu = (b > 190) & (r < 70) & (g < 120)
    centri = []
    for mask in (rosso, blu):
        for x0, y0, x1, y1, n in _componenti(mask):
            w, h = x1 - x0 + 1, y1 - y0 + 1
            # i riquadri delle icone: ~25-35 x 18-26 px, pieni; le linee disegnate sono sottili
            if 14 <= w <= 50 and 10 <= h <= 36 and n > 0.4 * w * h:
                centri.append(((x0 + x1) / 2, (y0 + y1) / 2))
    return centri


def calibra_su_unita(icone, unita, tolleranza_px=6):
    """Scala s (m/px) e traslazione: x_nord = X0 - s*py, y_est = Y0 + s*px."""
    U = np.array([(x, y) for _, x, y in unita])
    P = np.array(icone)
    migliore = None
    for (i0, i1) in itertools.permutations(range(len(P)), 2):
        dpx, dpy = P[i1] - P[i0]
        n_px = math.hypot(dpx, dpy)
        if n_px < 30:
            continue
        for (a, b) in itertools.permutations(range(len(U)), 2):
            dxn, dy = U[b] - U[a]
            n_m = math.hypot(dxn, dy)
            s = n_m / n_px
            if not 0.05 < s < 5:
                continue
            if abs(dy - s * dpx) > 0.08 * n_m or abs(-dxn - s * dpy) > 0.08 * n_m:
                continue
            X0 = U[a, 0] + s * P[i0, 1]
            Y0 = U[a, 1] - s * P[i0, 0]
            pred = np.stack([(U[:, 1] - Y0) / s, (X0 - U[:, 0]) / s], 1)     # unita' -> pixel
            d = np.min(np.hypot(pred[:, None, 0] - P[None, :, 0], pred[:, None, 1] - P[None, :, 1]), 1)
            n = int((d < tolleranza_px).sum())
            if migliore is None or n > migliore[0]:
                migliore = (n, s, X0, Y0)
    if migliore is None or migliore[0] < 2:
        raise ValueError('calibrazione sulle unita\' non riuscita')
    return migliore[1], migliore[2], migliore[3], migliore[0]


def rileva_alberi(rgb):
    """Alberi: puntini piu' verdi e piu' scuri del campo attorno."""
    r, g, b = (rgb[..., k].astype(float) for k in range(3))
    lum = (r + g + b) / 3

    def media(a, k=9):
        c = np.pad(a, ((k + 1, k), (k + 1, k)), mode='edge').cumsum(0).cumsum(1)
        s = c[2 * k + 1:, 2 * k + 1:] - c[:-2 * k - 1, 2 * k + 1:] - c[2 * k + 1:, :-2 * k - 1] + c[:-2 * k - 1, :-2 * k - 1]
        return s / (2 * k + 1) ** 2
    scuro = lum < media(lum) - 7
    verde = (g >= r - 6) & (g - b > 8)
    icone = ((r > 190) & (g < 70) & (b < 70)) | ((b > 190) & (r < 70))
    return scuro & verde & ~icone


def verifica(percorso_png, unita, area=AREA_MAPPA):
    img = np.array(Image.open(percorso_png).convert('RGB'))
    l, t, rr, bb = area
    rgb = np.zeros_like(img)
    rgb[t:bb, l:rr] = img[t:bb, l:rr]
    icone = rileva_icone(rgb)
    s, X0, Y0, n = calibra_su_unita(icone, unita)
    alberi = rileva_alberi(rgb)
    alberi[:t] = False
    alberi[bb:] = False
    alberi[:, :l] = False
    alberi[:, rr:] = False
    ay, ax = np.nonzero(alberi)
    # coordinate mappa degli alberi
    tx = X0 - s * ay
    ty = Y0 + s * ax

    def conta(x, y, raggio=RAGGIO_LIBERO):
        return int((np.hypot(tx - x, ty - y) < raggio).sum())

    def dentro(x, y):
        px, py = (y - Y0) / s, (X0 - x) / s
        return l + 10 <= px < rr - 10 and t + 10 <= py < bb - 10
    soglia = max(3, int(0.02 * math.pi * (RAGGIO_LIBERO / s) ** 2))   # pochi pixel isolati non contano
    risultati = []
    for tipo, x, y in unita:
        n_alb = conta(x, y)
        voce = {'tipo': tipo, 'x': x, 'y': y, 'alberi_px': n_alb, 'nel_bosco': n_alb > soglia,
                'nuova_x': x, 'nuova_y': y, 'spostamento_m': 0.0, 'visibile': dentro(x, y)}
        if voce['nel_bosco']:
            trovato = False
            for d in np.arange(5, SPOSTAMENTO_MAX + 1, 5):
                for k in range(int(max(8, 2 * math.pi * d / 5))):
                    a = 2 * math.pi * k / max(8, 2 * math.pi * d / 5)
                    px, py = x + d * math.cos(a), y + d * math.sin(a)
                    if dentro(px, py) and conta(px, py) <= soglia:
                        voce.update(nuova_x=px, nuova_y=py, spostamento_m=float(d))
                        trovato = True
                        break
                if trovato:
                    break
            voce['risolto'] = trovato
        risultati.append(voce)
    return {'scala_m_px': s, 'icone': len(icone), 'corrispondenze': n, 'unita': risultati,
            'alberi': alberi, 'trasf': (s, X0, Y0)}


def identifica_e_verifica(percorso_png, gruppi, area=AREA_MAPPA):
    """Prova la calibrazione con ogni gruppo ({nome: [(tipo, x, y), ...]}) e tiene quello che combacia meglio."""
    img = np.array(Image.open(percorso_png).convert('RGB'))
    l, t, rr, bb = area
    rgb = np.zeros_like(img)
    rgb[t:bb, l:rr] = img[t:bb, l:rr]
    icone = rileva_icone(rgb)
    migliore = None
    for nome, unita in gruppi.items():
        try:
            s, X0, Y0, n = calibra_su_unita(icone, unita)
        except ValueError:
            continue
        if migliore is None or n > migliore[1]:
            migliore = (nome, n)
    if migliore is None:
        raise ValueError('nessun gruppo riconosciuto nello screenshot')
    r = verifica(percorso_png, gruppi[migliore[0]], area)
    r['gruppo'] = migliore[0]
    return r
