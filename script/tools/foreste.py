"""Mappa dei boschi di DCS dagli screenshot del Mission Editor (vista SAT, missione R01).

La vista ALT non va bene: in montagna le tinte del rilievo si confondono con i boschi.

1. rileva le crocette magenta nello screenshot;
2. le riconosce confrontandole con le posizioni note (marcatori_foreste.json) e
   ricava la trasformazione pixel -> coordinate DCS (scala + traslazione, nord in alto);
3. classifica i pixel (bosco, centro abitato) e li riporta su una griglia comune.
"""
import json
import math
from collections import deque

import numpy as np
from PIL import Image


# ---------------------------------------------------------------------------
def rileva_crocette(rgb):
    """Centri delle crocette magenta (pixel): lista di (px, py)."""
    r, g, b = (rgb[..., k].astype(int) for k in range(3))
    mask = (r > 190) & (b > 190) & (g < 90)
    h, w = mask.shape
    visto = np.zeros_like(mask)
    centri = []
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
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not visto[yy, xx]:
                        visto[yy, xx] = True
                        coda.append((yy, xx))
        if len(pts) < 8:
            continue
        a = np.array(pts, dtype=float)
        # la crocetta e' simmetrica: il centro e' il punto medio dell'ingombro
        centri.append(((a[:, 0].min() + a[:, 0].max()) / 2, (a[:, 1].min() + a[:, 1].max()) / 2,
                       a[:, 0].max() - a[:, 0].min(), a[:, 1].max() - a[:, 1].min()))
    # scarta i pezzi tagliati dal bordo (ingombro molto diverso dalla mediana)
    if not centri:
        return []
    dim = np.median([max(c[2], c[3]) for c in centri])
    return [(c[0], c[1]) for c in centri if abs(max(c[2], c[3]) - dim) <= 0.35 * dim + 2]


def calibra(punti, marcatori, tolleranza_m=600.0):
    """Trova scala s (m/px) e traslazione: x_nord = X0 - s*py, y_est = Y0 + s*px.

    Restituisce (s, X0, Y0, n_corrispondenze, errore_medio_m)."""
    if len(punti) < 3:
        raise ValueError('troppo poche crocette riconosciute (%d)' % len(punti))
    M = np.array([[m['x'], m['y']] for m in marcatori])
    P = np.array(punti)
    d = np.hypot(P[:, None, 0] - P[None, :, 0], P[:, None, 1] - P[None, :, 1])
    np.fill_diagonal(d, np.inf)
    # piu' coppie di riferimento (crocetta + la sua vicina), sparse sull'immagine:
    # basta che una sia buona; vince l'ipotesi con piu' corrispondenze
    ordine = np.argsort(np.abs(d.min(1) - np.median(d.min(1))))
    riferimenti = list(ordine[:12])
    migliore = None
    for i0 in riferimenti:
        i1 = int(np.argmin(d[i0]))
        p0, p1 = P[i0], P[i1]
        for a in range(len(M)):
            dm = np.hypot(M[:, 0] - M[a, 0], M[:, 1] - M[a, 1])
            for b in np.nonzero((dm > 1) & (dm < 30000))[0]:
                dpx, dpy = p1 - p0
                dy, dxn = M[b, 1] - M[a, 1], M[b, 0] - M[a, 0]
                n_px = math.hypot(dpx, dpy)
                n_m = math.hypot(dy, dxn)
                s = n_m / n_px
                if not 20 < s < 400:
                    continue
                if abs(dy - s * dpx) > 0.15 * n_m or abs(-dxn - s * dpy) > 0.15 * n_m:
                    continue
                X0 = M[a, 0] + s * p0[1]
                Y0 = M[a, 1] - s * p0[0]
                pred = np.stack([X0 - s * P[:, 1], Y0 + s * P[:, 0]], 1)
                dist = np.min(np.hypot(pred[:, None, 0] - M[None, :, 0], pred[:, None, 1] - M[None, :, 1]), 1)
                ok = dist < tolleranza_m
                n = int(ok.sum())
                if migliore is None or n > migliore[0]:
                    migliore = (n, s, X0, Y0, ok)
        if migliore and migliore[0] >= 0.8 * len(P):
            break
    if migliore is None or migliore[0] < 3:
        raise ValueError('calibrazione non riuscita')
    # raffinamento ai minimi quadrati su tutte le corrispondenze
    n, s, X0, Y0, ok = migliore
    pred = np.stack([X0 - s * P[:, 1], Y0 + s * P[:, 0]], 1)
    idx = np.argmin(np.hypot(pred[:, None, 0] - M[None, :, 0], pred[:, None, 1] - M[None, :, 1]), 1)
    Pk, Mk = P[ok], M[idx[ok]]
    # x = X0 - s*py ; y = Y0 + s*px  -> sistema lineare in (s, X0, Y0)
    A = np.vstack([np.column_stack([-Pk[:, 1], np.ones(len(Pk)), np.zeros(len(Pk))]),
                   np.column_stack([Pk[:, 0], np.zeros(len(Pk)), np.ones(len(Pk))])])
    bvec = np.concatenate([Mk[:, 0], Mk[:, 1]])
    (s, X0, Y0), *_ = np.linalg.lstsq(A, bvec, rcond=None)
    res = A @ np.array([s, X0, Y0]) - bvec
    err = float(np.sqrt((res.reshape(2, -1) ** 2).sum(0)).mean())
    return float(s), float(X0), float(Y0), int(ok.sum()), err


# ---------------------------------------------------------------------------
def classifica_sat(rgb):
    """Bosco dalla vista SAT (satellitare): verde scuro. I centri abitati vengono dal rilievo (edifici)."""
    r, g, b = (rgb[..., k].astype(int) for k in range(3))
    lum = (r + g + b) / 3
    bosco = (lum < 95) & (g >= r - 2) & (g > b + 5)
    return bosco, np.zeros_like(bosco)


def classifica(rgb):
    """Maschere di bosco e centro abitato dai colori della vista ALT (inaffidabile in montagna)."""
    r, g, b = (rgb[..., k].astype(int) for k in range(3))
    bosco = (g < 195) & (r < 195) & (np.abs(r - g) < 45) & (b < 130) & (g > 60) & (g >= b + 25)
    abitato = (r - g > 25) & (r > 160) & (b < 155) & (r < 245)
    return bosco, abitato


def pixel_validi(rgb):
    """Esclude i disegni sovrapposti alla mappa: crocette, riquadri, griglia, scritte e icone."""
    r, g, b = (rgb[..., k].astype(int) for k in range(3))
    lum = (r + g + b) / 3
    magenta = (r > 170) & (b > 170) & (g < 120)
    ciano = (g > 140) & (b > 150) & (r < 90)
    nero = lum < 30
    bianco = lum > 200
    testo_blu = (b > r + 50) & (b > g + 25) & (lum > 60)
    escludi = magenta | ciano | nero | bianco | testo_blu
    # allarga di un pixel per togliere anche i bordi sfumati
    e = escludi.copy()
    e[1:] |= escludi[:-1]
    e[:-1] |= escludi[1:]
    e[:, 1:] |= escludi[:, :-1]
    e[:, :-1] |= escludi[:, 1:]
    return ~e


def elabora(percorso_png, marcatori, ritaglio=None, vista='sat'):
    """Restituisce dict con calibrazione e maschere, coordinate DCS per pixel."""
    img = Image.open(percorso_png).convert('RGB')
    rgb = np.array(img)
    if ritaglio:                     # (sinistra, alto, destra, basso) dell'area mappa nello screenshot
        l, t, rr, bb = ritaglio
        sub = np.zeros_like(rgb)
        sub[t:bb, l:rr] = rgb[t:bb, l:rr]
        rgb = sub
    punti = rileva_crocette(rgb)
    s, X0, Y0, n, err = calibra(punti, marcatori)
    bosco, abitato = classifica_sat(rgb) if vista == 'sat' else classifica(rgb)
    valido = pixel_validi(rgb)
    return {'s': s, 'X0': X0, 'Y0': Y0, 'crocette': len(punti), 'corrispondenze': n, 'errore_m': err,
            'bosco': bosco, 'abitato': abitato, 'valido': valido, 'forma': rgb.shape[:2]}


def carica_marcatori(percorso):
    return json.load(open(percorso))['marcatori']


# ---------------------------------------------------------------------------
class Mosaico:
    """Griglia comune (passo in metri) che accumula la frazione di vegetazione da piu' screenshot."""

    def __init__(self, x0, x1, y0, y1, passo=250.0):
        self.x0, self.y0, self.passo = x0, y0, passo
        self.nx = int((x1 - x0) // passo) + 1
        self.ny = int((y1 - y0) // passo) + 1
        self.bosco = np.zeros((self.nx, self.ny), dtype=np.float64)
        self.totale = np.zeros((self.nx, self.ny), dtype=np.float64)

    def aggiungi(self, r, ritaglio):
        l, t, rr, bb = ritaglio
        # margine di sicurezza dai bordi dell'area mappa (crocette tagliate, etichette)
        l, t, rr, bb = l + 4, t + 4, rr - 4, bb - 4
        ys, xs = np.mgrid[t:bb, l:rr]
        x = r['X0'] - r['s'] * ys
        y = r['Y0'] + r['s'] * xs
        i = ((x - self.x0) / self.passo).astype(int)
        j = ((y - self.y0) / self.passo).astype(int)
        ok = (i >= 0) & (i < self.nx) & (j >= 0) & (j < self.ny)
        ok &= r['valido'][t:bb, l:rr]
        np.add.at(self.totale, (i[ok], j[ok]), 1)
        np.add.at(self.bosco, (i[ok], j[ok]), r['bosco'][t:bb, l:rr][ok].astype(float))

    def frazione(self):
        with np.errstate(invalid='ignore', divide='ignore'):
            f = self.bosco / self.totale
        f[self.totale == 0] = np.nan
        return f
