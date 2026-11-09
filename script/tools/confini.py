"""Confini e fazioni della campagna "Fuoco sul Levante 1989", come disegni del Mission Editor.

Sono informazioni PUBBLICHE (la situazione politica del README): nessuno
schieramento militare. Vanno nello strato "Common", visibile a tutti.

I tracciati sono approssimati (precisione di qualche km): servono a orientarsi,
non a delimitare con esattezza.
"""
from geo import ll_to_xy

# colori DCS: 0xRRGGBBAA
ROSSO = ('0xcc1f1fff', '0xcc1f1f22')
BLU = ('0x1f5fccff', '0x1f5fcc2a')
GIALLO = ('0xe0b000ff', '0xe0b00026')
GRIGIO = ('0x707070ff', '0x7070701c')
VIOLA = ('0x8a3fb0ff', '0x8a3fb022')

# --- territori (lat, lon) ---------------------------------------------------
SIRIA = [
    (35.92, 35.92), (35.52, 35.78), (35.25, 35.93), (34.89, 35.88), (34.64, 35.97),   # costa
    (34.63, 36.40), (34.46, 36.62), (34.18, 36.50), (33.95, 36.30), (33.70, 36.07),   # Libano
    (33.50, 35.95), (33.33, 35.78),
    (33.25, 35.83), (33.00, 35.87), (32.80, 35.88), (32.69, 35.80),                   # Golan (linea 1974)
    (32.56, 36.00), (32.49, 36.20), (32.32, 36.84), (33.37, 38.79),                   # Giordania
    (34.45, 40.95), (35.60, 41.35), (36.40, 41.27), (37.10, 42.35),                   # Iraq
    (37.05, 41.22), (36.85, 40.07), (36.70, 38.95), (36.83, 38.00), (36.65, 37.10),   # Turchia
    (36.65, 36.80), (36.22, 36.67), (36.00, 36.35), (35.90, 36.06),
]

LIBANO_SIRIANO = [   # Libano sotto controllo siriano e alleati (nord, Bekaa, Beirut Ovest, Chouf)
    (34.64, 35.97), (34.44, 35.82), (34.17, 35.63), (34.15, 35.88), (33.95, 35.92),
    (33.84, 35.78), (33.83, 35.55), (33.87, 35.50), (33.56, 35.37), (33.32, 35.24),
    (33.25, 35.35), (33.32, 35.52), (33.42, 35.65), (33.36, 35.80), (33.33, 35.78),
    (33.50, 35.95), (33.70, 36.07), (33.95, 36.30), (34.18, 36.50), (34.46, 36.62),
    (34.63, 36.40),
]

ENCLAVE_AOUN = [     # Beirut Est, Metn, Kesrouan, Jbeil
    (33.87, 35.50), (34.17, 35.63), (34.15, 35.88), (33.95, 35.92), (33.84, 35.78), (33.83, 35.55),
]

ZONA_SICUREZZA_ISRAELE = [   # "zona di sicurezza" israeliana nel sud del Libano (dal 1985)
    (33.09, 35.10), (33.32, 35.24), (33.25, 35.35), (33.32, 35.52), (33.42, 35.65),
    (33.36, 35.80), (33.33, 35.78), (33.28, 35.62), (33.10, 35.50),
]

ISRAELE = [          # Israele e territori sotto il suo controllo nel 1989 (Golan, Cisgiordania)
    (33.09, 35.10), (32.82, 34.95), (32.08, 34.77), (31.60, 34.53), (31.32, 34.27),
    (31.00, 34.30), (31.00, 35.40), (31.75, 35.55), (32.32, 35.57), (32.70, 35.57),
    (32.69, 35.80), (32.80, 35.88), (33.00, 35.87), (33.25, 35.83), (33.33, 35.78),
    (33.28, 35.62), (33.10, 35.50),
]

GIORDANIA = [
    (32.70, 35.57), (32.69, 35.80), (32.56, 36.00), (32.49, 36.20), (32.32, 36.84),
    (33.37, 38.79), (32.24, 39.30), (31.50, 37.00), (31.00, 36.30), (31.00, 35.40),
    (31.75, 35.55), (32.32, 35.57),
]

ZONA_NAVALE_USA = [  # area operativa del gruppo portaerei: tra Cipro e la Turchia
    (35.80, 34.65), (35.75, 33.95), (36.05, 33.75), (36.30, 34.10),
    (36.40, 34.60), (36.30, 35.00), (36.15, 35.15), (35.90, 35.10),
]

TERRITORI = [
    ('SIRIA', SIRIA, ROSSO, 6),
    ('Libano - controllo siriano', LIBANO_SIRIANO, ROSSO, 4),
    ('Enclave di Aoun', ENCLAVE_AOUN, BLU, 5),
    ('Zona di sicurezza israeliana', ZONA_SICUREZZA_ISRAELE, GIALLO, 3),
    ('ISRAELE', ISRAELE, GIALLO, 5),
    ('GIORDANIA', GIORDANIA, GRIGIO, 4),
    ('Zona operativa navale USA', ZONA_NAVALE_USA, BLU, 3),
]

# --- etichette (lat, lon, testo, colori, dimensione) -------------------------
ETICHETTE = [
    (34.90, 37.60, 'SIRIA\nOstile (rosso)', ROSSO, 30),
    (34.35, 36.15, 'LIBANO\ncontrollo siriano', ROSSO, 16),
    (34.02, 35.71, 'ENCLAVE AOUN\nalleata (blu)', BLU, 13),
    (32.15, 35.05, 'ISRAELE\nneutrale - spazio aereo VIETATO\n(intervento IAF)', GIALLO, 16),
    (31.90, 37.20, 'GIORDANIA\nneutrale', GRIGIO, 20),
    (37.15, 35.70, 'TURCHIA (NATO)\nneutrale - attacco VIETATO\nIncirlik a disposizione del blu', VIOLA, 15),
    (35.05, 33.00, 'CIPRO\nneutrale - Akrotiri (UK)\ndirottamento per il blu', GRIGIO, 15),
    (36.05, 34.45, 'ZONA OPERATIVA\nNAVALE USA', BLU, 14),
]


def _area(pts):
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1])) / 2


def _croce(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _dentro(p, a, b, c):
    d1, d2, d3 = _croce(a, b, p), _croce(b, c, p), _croce(c, a, p)
    return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))


def _triangoli(pts):
    """Ear clipping: scompone un poligono semplice in triangoli (indici)."""
    idx = list(range(len(pts)))
    if _area(pts) < 0:
        idx.reverse()
    tri = []
    while len(idx) > 3:
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = pts[i0], pts[i1], pts[i2]
            if _croce(a, b, c) <= 0:
                continue
            if any(_dentro(pts[j], a, b, c) for j in idx if j not in (i0, i1, i2)):
                continue
            tri.append([i0, i1, i2])
            idx.pop(k)
            break
        else:
            raise ValueError('poligono non semplice')
    tri.append(idx)
    return tri


def _convesso(pts, poly):
    n = len(poly)
    return all(_croce(pts[poly[k]], pts[poly[(k + 1) % n]], pts[poly[(k + 2) % n]]) >= 0 for k in range(n))


def _pezzi_convessi(pts):
    """Triangoli fusi a coppie finche' il risultato resta convesso (Hertel-Mehlhorn)."""
    pezzi = _triangoli(pts)
    fuso = True
    while fuso:
        fuso = False
        for i in range(len(pezzi)):
            for j in range(i + 1, len(pezzi)):
                a, b = pezzi[i], pezzi[j]
                for ka in range(len(a)):
                    u, v = a[ka], a[(ka + 1) % len(a)]
                    if v in b and b[(b.index(v) + 1) % len(b)] == u:
                        kb = b.index(v)
                        nuovo = a[:ka + 1] + [b[(kb + t) % len(b)] for t in range(2, len(b))] + a[ka + 1:]
                        if _convesso(pts, nuovo):
                            pezzi[i] = nuovo
                            pezzi.pop(j)
                            fuso = True
                            break
                if fuso:
                    break
            if fuso:
                break
    return pezzi


def _punti_relativi(xy):
    x0, y0 = xy[0]
    pts = {k: {'x': x - x0, 'y': y - y0} for k, (x, y) in enumerate(xy, 1)}
    pts[len(xy) + 1] = {'x': 0.0, 'y': 0.0}      # ripete il primo punto: DCS non chiude da solo
    return x0, y0, pts


def _territorio(nome, punti, colori, spessore):
    """Bordo (linea chiusa) + riempimento in pezzi convessi senza bordo."""
    xy = [ll_to_xy(lat, lon) for lat, lon in punti]
    ogg = []
    for k, pezzo in enumerate(_pezzi_convessi(xy), 1):
        x0, y0, pts = _punti_relativi([xy[i] for i in pezzo])
        ogg.append({
            'visible': True, 'primitiveType': 'Polygon', 'polygonMode': 'free',
            'mapX': x0, 'mapY': y0, 'angle': 0, 'points': pts,
            'colorString': '0x00000000', 'fillColorString': colori[1],
            'thickness': 0, 'style': 'solid',
            'name': '%s - area %d' % (nome, k), 'layerName': 'Common',
        })
    x0, y0, pts = _punti_relativi(xy)
    ogg.append({
        'visible': True, 'primitiveType': 'Line', 'lineMode': 'free', 'closed': True,
        'mapX': x0, 'mapY': y0, 'points': pts,
        'colorString': colori[0], 'thickness': spessore, 'style': 'solid',
        'name': nome, 'layerName': 'Common',
    })
    return ogg


def _testo(i, lat, lon, testo, colori, dim):
    x, y = ll_to_xy(lat, lon)
    return {
        'visible': True, 'primitiveType': 'TextBox', 'mapX': x, 'mapY': y, 'angle': 0,
        'text': testo, 'font': 'DejaVuLGCSansCondensed.ttf', 'fontSize': dim,
        'colorString': colori[0], 'fillColorString': '0x00000000', 'borderThickness': 0,
        'name': 'Etichetta %d' % i, 'layerName': 'Common',
    }


def disegni():
    """Oggetti da mettere in mission['drawings']['layers'][<Common>]['objects']."""
    ogg = []
    for nome, punti, colori, spessore in TERRITORI:
        ogg.extend(_territorio(nome, punti, colori, spessore))
    for i, (lat, lon, testo, colori, dim) in enumerate(ETICHETTE, 1):
        ogg.append(_testo(i, lat, lon, testo, colori, dim))
    return {k: o for k, o in enumerate(ogg, 1)}


def aggiungi(mission):
    for strato in mission['drawings']['layers'].values():
        if strato['name'] == 'Common':
            strato['objects'] = disegni()
            return
    raise KeyError('strato Common non trovato')
