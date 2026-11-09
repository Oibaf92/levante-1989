"""Quadro di intelligence di partenza (2 ottobre 1989, prima delle ostilita').

Situazione di PACE: basi permanenti e siti antiaerei fissi noti, come li stima
ciascuna parte. Ogni parte vede solo il proprio strato sulla mappa F10:
  - strato "Blue": forze USA proprie + stima USA delle forze siro-sovietiche
  - strato "Red":  forze siro-sovietiche proprie + stima delle forze USA

E' il punto di partenza fissato dall'arbitro. I comandanti possono spostare i
sistemi mobili (SA-6, SA-8, ...): in guerra questa mappa puo' essere superata.
Posizioni approssimate.
"""
import math

from geo import ll_to_xy

R_LINEA = '0xcc1f1fff'
R_TENUE = '0xcc1f1f90'
B_LINEA = '0x1f5fccff'
B_TENUE = '0x1f5fcc90'
NERO = '0x202020ff'

# --- forze siro-sovietiche: (lat, lon, nome, dettaglio) ----------------------
BASI_ROSSE = [
    (35.404, 35.950, 'Latakia', 'MiG-21, eli'),
    (35.118, 36.712, 'Hama', 'MiG-21'),
    (34.490, 36.908, 'Shayrat', 'MiG-23, Su-22'),
    (34.523, 37.630, 'Tiyas (T4)', 'MiG-23, MiG-25'),
    (33.610, 36.749, 'Al-Dumayr', 'MiG-23, MiG-29'),
    (33.680, 37.217, 'Sayqal', 'MiG-23'),
    (34.557, 38.317, 'Palmyra', 'MiG-25'),
    (33.478, 36.224, 'Mezzeh', 'eli, ricogn.'),
    (33.289, 36.455, 'Marj Ruhayyil', 'MiG-21, MiG-23'),
    (33.078, 36.541, 'Khalkhalah', 'MiG-21'),
    (34.569, 36.571, 'Al Qusayr', 'MiG-21'),
    (33.426, 36.519, 'Damasco', 'trasporti'),
    (33.851, 35.987, 'Rayak', 'Mi-24, Mi-8'),
    (35.732, 37.104, 'Abu al-Duhur', 'MiG-21'),
    (36.187, 37.581, 'Kuweires', 'scuola volo'),
]
BASE_NAVALE_ROSSA = (34.905, 35.865, 'Tartus', 'flotta sovietica')

# siti SAM fissi e zone dei sistemi mobili: (lat, lon, raggio km, nome, tenue)
SAM_ROSSI = [
    (33.660, 36.820, 150, 'SA-5 Dumayr', True),
    (34.600, 36.740, 150, 'SA-5 Homs', True),
    (33.510, 36.290, 35, 'SA-2/3 Damasco', False),
    (34.730, 36.710, 30, 'SA-2/3 Homs', False),
    (35.130, 36.750, 25, 'SA-2/3 Hama', False),
    (36.200, 37.160, 30, 'SA-2/3 Aleppo', False),
    (35.520, 35.850, 25, 'SA-2/3 Latakia', False),
    (34.890, 35.920, 25, 'SA-2/3 Tartus', False),
    (33.850, 35.980, 30, 'SA-6 mobili Bekaa', False),
    (33.150, 36.050, 30, 'SA-6/SA-8 mobili Golan', False),
]

# --- forze USA: (lat, lon, nome, dettaglio) ----------------------------------
BASI_BLU = [
    (37.002, 35.426, 'Incirlik', 'F-4E, KC-135, E-3A'),
    (34.590, 32.988, 'Akrotiri (UK)', 'dirottamento'),
    (34.050, 35.450, 'LHA-1 Tarawa', 'AH-64, CH-47, AV-8B'),
    (33.980, 35.630, 'Jounieh', 'Marines'),
]
SAM_BLU = [
    (33.980, 35.630, 35, 'I-Hawk Jounieh', False),
]
# cio' che il rosso sa delle forze USA
BASI_BLU_VISTE_DAL_ROSSO = [
    (37.002, 35.426, 'Incirlik', 'F-4 USA'),
    (34.590, 32.988, 'Akrotiri (UK)', 'dirottamento USA?'),
    (34.050, 35.450, 'Nave anfibia USA', 'al largo'),
    (33.980, 35.630, 'Jounieh', 'Marines'),
    (35.900, 33.900, 'Portaerei USA', 'posizione stimata'),
]
SAM_BLU_VISTI_DAL_ROSSO = [
    (33.980, 35.630, 35, 'Hawk Jounieh (stima)', False),
]


# ---------------------------------------------------------------------------
def _linea(nome, strato, punti_xy, colore, spessore, chiusa=True):
    x0, y0 = punti_xy[0]
    pts = {k: {'x': x - x0, 'y': y - y0} for k, (x, y) in enumerate(punti_xy, 1)}
    if chiusa:
        pts[len(punti_xy) + 1] = {'x': 0.0, 'y': 0.0}
    return {'visible': True, 'primitiveType': 'Line', 'lineMode': 'free', 'closed': chiusa,
            'mapX': x0, 'mapY': y0, 'points': pts, 'colorString': colore,
            'thickness': spessore, 'style': 'solid', 'name': nome, 'layerName': strato}


def _cerchio(nome, strato, cx, cy, raggio_m, colore, spessore, n=48):
    pts = [(cx + raggio_m * math.cos(2 * math.pi * i / n), cy + raggio_m * math.sin(2 * math.pi * i / n)) for i in range(n)]
    return _linea(nome, strato, pts, colore, spessore)


def _quadrato(nome, strato, cx, cy, lato_m, colore):
    h = lato_m / 2
    return _linea(nome, strato, [(cx - h, cy - h), (cx - h, cy + h), (cx + h, cy + h), (cx + h, cy - h)], colore, 3)


def _testo_xy(nome, strato, x, y, testo, colore, dim):
    return {'visible': True, 'primitiveType': 'TextBox', 'mapX': x, 'mapY': y,
            'angle': 0, 'text': testo, 'font': 'DejaVuLGCSansCondensed.ttf', 'fontSize': dim,
            'colorString': colore, 'fillColorString': '0x00000000', 'borderThickness': 0,
            'name': nome, 'layerName': strato}


# ---------------------------------------------------------------------------
# Disposizione automatica delle etichette
#
# Ingombro stimato del testo allo zoom di riferimento (circa 150 m per pixel, la
# scala con cui si guarda Libano e Siria occidentale). Si assume che mapX/mapY sia
# l'angolo in alto a sinistra del riquadro (x = nord, y = est).
# ---------------------------------------------------------------------------
M_PER_PX = 150.0
MARGINE = 1500.0


def ingombro(testo, dim):
    righe = testo.split('\n')
    larg = max(len(r) for r in righe) * 0.58 * dim * M_PER_PX
    alt = len(righe) * 1.25 * dim * M_PER_PX
    return larg, alt


def rettangolo(x_alto, y_sinistra, testo, dim):
    larg, alt = ingombro(testo, dim)
    return (x_alto - alt, x_alto, y_sinistra, y_sinistra + larg)   # (x_min, x_max, y_min, y_max)


def _sovrapposizione(a, b):
    dx = min(a[1], b[1]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[2], b[2])
    return dx * dy if dx > 0 and dy > 0 else 0.0


DIREZIONI = [(0, 1), (-1, 1), (1, 1), (-1, 0), (1, 0), (0, -1), (-1, -1), (1, -1)]   # (nord, est)
DISTANZE = [0, 8000, 16000, 28000, 45000]


class Impaginatore:
    """Colloca le etichette evitando sovrapposizioni, con linee di richiamo se serve."""

    def __init__(self, strato):
        self.strato = strato
        self.ostacoli = []
        self.oggetti = []

    def ostacolo(self, rett):
        self.ostacoli.append(rett)

    def ostacolo_punto(self, x, y, lato=3000):
        self.ostacoli.append((x - lato / 2, x + lato / 2, y - lato / 2, y + lato / 2))

    def fisso(self, nome, x_alto, y_sin, testo, colore, dim):
        self.ostacoli.append(rettangolo(x_alto, y_sin, testo, dim))
        self.oggetti.append(_testo_xy(nome, self.strato, x_alto, y_sin, testo, colore, dim))

    def colloca(self, nome, ancore, testo, colore, dim, distanze=DISTANZE):
        """ancore: lista di punti (x, y) da cui l'etichetta puo' partire, in ordine di preferenza."""
        larg, alt = ingombro(testo, dim)
        migliore = None
        for d in distanze:
            for ax, ay in ancore:
                for dn, de in DIREZIONI:
                    norma = math.hypot(dn, de)
                    cx = ax + dn / norma * d + dn * (alt / 2 + MARGINE)
                    cy = ay + de / norma * d + de * (larg / 2 + MARGINE)
                    rett = (cx - alt / 2, cx + alt / 2, cy - larg / 2, cy + larg / 2)
                    costo = sum(_sovrapposizione(rett, o) for o in self.ostacoli)
                    if migliore is None or costo < migliore[0]:
                        migliore = (costo, rett, d, ax, ay)
                    if costo == 0:
                        break
                if migliore[0] == 0:
                    break
            if migliore[0] == 0:
                break
        _, rett, d, ax, ay = migliore
        self.ostacoli.append(rett)
        self.oggetti.append(_testo_xy(nome, self.strato, rett[1], rett[2], testo, colore, dim))
        if d > 0:
            # linea di richiamo dall'ancora al punto piu' vicino del riquadro
            px = min(max(ax, rett[0]), rett[1])
            py = min(max(ay, rett[2]), rett[3])
            self.oggetti.append(_linea(nome + ' (richiamo)', self.strato, [(ax, ay), (px, py)], colore, 1, chiusa=False))


# ---------------------------------------------------------------------------
def _segni_basi(imp, basi, colore, prefisso):
    for lat, lon, nome, _ in basi:
        x, y = ll_to_xy(lat, lon)
        imp.oggetti.append(_quadrato('%s %s' % (prefisso, nome), imp.strato, x, y, 3000, colore))
        imp.ostacolo_punto(x, y)


def _segni_sam(imp, siti, linea, tenue, prefisso):
    for lat, lon, r_km, nome, e_tenue in siti:
        x, y = ll_to_xy(lat, lon)
        col = tenue if e_tenue else linea
        imp.oggetti.append(_cerchio('%s %s' % (prefisso, nome), imp.strato, x, y, r_km * 1000, col, 2 if e_tenue else 3))
        imp.oggetti.append(_quadrato('%s %s (centro)' % (prefisso, nome), imp.strato, x, y, 1200, col))
        imp.ostacolo_punto(x, y, 1500)


def _etichette_sam(imp, siti, linea, tenue, prefisso):
    # prima i cerchi grandi, poi gli altri; etichetta sul bordo del cerchio (preferibilmente a sud)
    for lat, lon, r_km, nome, e_tenue in sorted(siti, key=lambda s: -s[2]):
        x, y = ll_to_xy(lat, lon)
        col = tenue if e_tenue else linea
        r = r_km * 1000
        angoli = [180, 225, 135, 270, 90, 0, 315, 45]
        ancore = [(x + r * math.cos(math.radians(a)), y + r * math.sin(math.radians(a))) for a in angoli]
        imp.colloca('%s %s (testo)' % (prefisso, nome), ancore, '%s (~%d km)' % (nome, r_km), col, 10)


def _etichette_basi(imp, basi, colore, prefisso):
    for lat, lon, nome, det in basi:
        x, y = ll_to_xy(lat, lon)
        imp.colloca('%s %s (testo)' % (prefisso, nome), [(x, y)], '%s · %s' % (nome, det), colore, 10)


def _impaginatore_con_common(strato):
    """Le etichette dello strato Common (confini) sono ostacoli fissi."""
    import confini
    imp = Impaginatore(strato)
    for lat, lon, testo, _, dim in confini.ETICHETTE:
        x, y = ll_to_xy(lat, lon)
        imp.ostacolo(rettangolo(x, y, testo, dim))
    return imp


INTESTAZIONE = (36.95, 38.90)


def disegni_blu():
    imp = _impaginatore_con_common('Blue')
    x, y = ll_to_xy(*INTESTAZIONE)
    imp.fisso('Intestazione intel', x, y,
              'STIMA INTELLIGENCE USA - 2 ottobre 1989\nSituazione di pace: i sistemi mobili\npossono essersi spostati', NERO, 13)
    _segni_basi(imp, BASI_BLU, B_LINEA, 'Propria')
    _segni_sam(imp, SAM_BLU, B_LINEA, B_TENUE, 'Propria')
    _segni_basi(imp, BASI_ROSSE + [BASE_NAVALE_ROSSA], R_LINEA, 'Intel')
    _segni_sam(imp, SAM_ROSSI, R_LINEA, R_TENUE, 'Intel')
    _etichette_sam(imp, SAM_ROSSI, R_LINEA, R_TENUE, 'Intel')
    _etichette_sam(imp, SAM_BLU, B_LINEA, B_TENUE, 'Propria')
    _etichette_basi(imp, BASI_BLU, B_LINEA, 'Propria')
    _etichette_basi(imp, BASI_ROSSE + [BASE_NAVALE_ROSSA], R_LINEA, 'Intel')
    x, y = ll_to_xy(35.30, 38.60)
    imp.colloca('Intel contingente sovietico', [(x, y)], 'Contingente aereo sovietico:\nbasi non confermate', R_LINEA, 11)
    return imp.oggetti


def disegni_rossi():
    imp = _impaginatore_con_common('Red')
    x, y = ll_to_xy(*INTESTAZIONE)
    imp.fisso('Intestazione intel', x, y, 'QUADRO INFORMATIVO SIRO-SOVIETICO\n2 ottobre 1989 - situazione di pace', NERO, 13)
    _segni_basi(imp, BASI_ROSSE + [BASE_NAVALE_ROSSA], R_LINEA, 'Propria')
    _segni_sam(imp, SAM_ROSSI, R_LINEA, R_TENUE, 'Propria')
    _segni_basi(imp, BASI_BLU_VISTE_DAL_ROSSO, B_LINEA, 'Intel')
    _segni_sam(imp, SAM_BLU_VISTI_DAL_ROSSO, B_LINEA, B_TENUE, 'Intel')
    _etichette_sam(imp, SAM_ROSSI, R_LINEA, R_TENUE, 'Propria')
    _etichette_sam(imp, SAM_BLU_VISTI_DAL_ROSSO, B_LINEA, B_TENUE, 'Intel')
    _etichette_basi(imp, BASI_BLU_VISTE_DAL_ROSSO, B_LINEA, 'Intel')
    _etichette_basi(imp, BASI_ROSSE + [BASE_NAVALE_ROSSA], R_LINEA, 'Propria')
    return imp.oggetti


def aggiungi(mission):
    for strato in mission['drawings']['layers'].values():
        if strato['name'] == 'Blue':
            strato['objects'] = {k: o for k, o in enumerate(disegni_blu(), 1)}
        elif strato['name'] == 'Red':
            strato['objects'] = {k: o for k, o in enumerate(disegni_rossi(), 1)}
