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
    (35.404, 35.950, 'Latakia (Bassel Al-Assad)', 'MiG-21, elicotteri'),
    (35.118, 36.712, 'Hama', 'MiG-21'),
    (34.490, 36.908, 'Shayrat', 'MiG-23, Su-22'),
    (34.523, 37.630, 'Tiyas (T4)', 'MiG-23, MiG-25'),
    (33.610, 36.749, 'Al-Dumayr', 'MiG-23, MiG-29'),
    (33.680, 37.217, 'Sayqal', 'MiG-23'),
    (34.557, 38.317, 'Palmyra', 'MiG-25'),
    (33.478, 36.224, 'Mezzeh', 'elicotteri, ricognizione'),
    (33.289, 36.455, 'Marj Ruhayyil', 'MiG-21, MiG-23'),
    (33.078, 36.541, 'Khalkhalah', 'MiG-21'),
    (34.569, 36.571, 'Al Qusayr', 'MiG-21'),
    (33.426, 36.519, 'Damasco', 'trasporti'),
    (33.851, 35.987, 'Rayak (Bekaa)', 'elicotteri Mi-24, Mi-8'),
    (35.732, 37.104, 'Abu al-Duhur', 'MiG-21'),
    (36.187, 37.581, 'Kuweires', 'scuola di volo'),
]
BASE_NAVALE_ROSSA = (34.905, 35.865, 'Tartus', 'punto d\'appoggio della flotta sovietica')

# siti SAM fissi e zone dei sistemi mobili: (lat, lon, raggio km, nome, tenue)
SAM_ROSSI = [
    (33.660, 36.820, 150, 'SA-5 Dumayr', True),
    (34.600, 36.740, 150, 'SA-5 Homs', True),
    (33.510, 36.290, 35, 'Cintura SA-2/SA-3 di Damasco', False),
    (34.730, 36.710, 30, 'SA-2/SA-3 Homs', False),
    (35.130, 36.750, 25, 'SA-2/SA-3 Hama', False),
    (36.200, 37.160, 30, 'SA-2/SA-3 Aleppo', False),
    (35.520, 35.850, 25, 'SA-2/SA-3 Latakia', False),
    (34.890, 35.920, 25, 'SA-2/SA-3 Tartus', False),
    (33.850, 35.980, 30, 'Zona SA-6 mobili - Bekaa', False),
    (33.150, 36.050, 30, 'Zona SA-6/SA-8 mobili - fronte del Golan', False),
]

# --- forze USA: (lat, lon, nome, dettaglio) ----------------------------------
BASI_BLU = [
    (37.002, 35.426, 'Incirlik', 'USAF: F-4E x12, KC-135 x2, E-3A'),
    (34.590, 32.988, 'Akrotiri (UK)', 'base di dirottamento'),
    (34.050, 35.450, 'LHA-1 Tarawa', 'AH-64, CH-47, AV-8B'),
    (33.980, 35.630, 'Jounieh', 'testa di ponte dei Marines'),
]
SAM_BLU = [
    (33.980, 35.630, 35, 'Batteria I-Hawk Jounieh', False),
]
# cio' che il rosso sa delle forze USA
BASI_BLU_VISTE_DAL_ROSSO = [
    (37.002, 35.426, 'Incirlik', 'aerei USA rilevati (F-4)'),
    (34.590, 32.988, 'Akrotiri (UK)', 'possibile dirottamento USA'),
    (34.050, 35.450, 'Nave d\'assalto USA', 'al largo di Jounieh'),
    (33.980, 35.630, 'Jounieh', 'sbarco dei Marines'),
    (35.900, 33.900, 'Gruppo portaerei USA', 'posizione stimata, in movimento'),
]
SAM_BLU_VISTI_DAL_ROSSO = [
    (33.980, 35.630, 35, 'Hawk (stimato) Jounieh', False),
]


# ---------------------------------------------------------------------------
def _linea_chiusa(nome, strato, punti_xy, colore, spessore):
    x0, y0 = punti_xy[0]
    pts = {k: {'x': x - x0, 'y': y - y0} for k, (x, y) in enumerate(punti_xy, 1)}
    pts[len(punti_xy) + 1] = {'x': 0.0, 'y': 0.0}
    return {'visible': True, 'primitiveType': 'Line', 'lineMode': 'free', 'closed': True,
            'mapX': x0, 'mapY': y0, 'points': pts, 'colorString': colore,
            'thickness': spessore, 'style': 'solid', 'name': nome, 'layerName': strato}


def _cerchio(nome, strato, lat, lon, raggio_m, colore, spessore, n=48):
    cx, cy = ll_to_xy(lat, lon)
    pts = [(cx + raggio_m * math.cos(2 * math.pi * i / n), cy + raggio_m * math.sin(2 * math.pi * i / n)) for i in range(n)]
    return _linea_chiusa(nome, strato, pts, colore, spessore)


def _quadrato(nome, strato, lat, lon, lato_m, colore):
    cx, cy = ll_to_xy(lat, lon)
    h = lato_m / 2
    return _linea_chiusa(nome, strato, [(cx - h, cy - h), (cx - h, cy + h), (cx + h, cy + h), (cx + h, cy - h)], colore, 3)


def _testo(nome, strato, lat, lon, testo, colore, dim, dx_km=0.0, dy_km=0.0):
    x, y = ll_to_xy(lat, lon)
    return {'visible': True, 'primitiveType': 'TextBox', 'mapX': x + dx_km * 1000, 'mapY': y + dy_km * 1000,
            'angle': 0, 'text': testo, 'font': 'DejaVuLGCSansCondensed.ttf', 'fontSize': dim,
            'colorString': colore, 'fillColorString': '0x00000000', 'borderThickness': 0,
            'name': nome, 'layerName': strato}


def _basi(strato, basi, colore, prefisso):
    ogg = []
    for lat, lon, nome, det in basi:
        ogg.append(_quadrato('%s %s' % (prefisso, nome), strato, lat, lon, 3000, colore))
        ogg.append(_testo('%s %s (testo)' % (prefisso, nome), strato, lat, lon, '%s\n%s' % (nome, det), colore, 11, dx_km=2.5, dy_km=2.5))
    return ogg


def _sam(strato, siti, linea, tenue, prefisso):
    ogg = []
    for lat, lon, r_km, nome, e_tenue in siti:
        col = tenue if e_tenue else linea
        ogg.append(_cerchio('%s %s' % (prefisso, nome), strato, lat, lon, r_km * 1000, col, 2 if e_tenue else 3))
        ogg.append(_quadrato('%s %s (centro)' % (prefisso, nome), strato, lat, lon, 1200, col))
        etichetta = '%s\n~%d km' % (nome, r_km)
        # le etichette dei grandi cerchi SA-5 vanno sul bordo nord, le altre accanto al centro
        if r_km > 100:
            ogg.append(_testo('%s %s (testo)' % (prefisso, nome), strato, lat, lon, etichetta, col, 12, dx_km=r_km - 8))
        else:
            ogg.append(_testo('%s %s (testo)' % (prefisso, nome), strato, lat, lon, etichetta, col, 11, dx_km=-1.5, dy_km=2))
    return ogg


def _intestazione(strato, testo, colore):
    return _testo('Intestazione intel', strato, 36.90, 39.30, testo, colore, 18)


def disegni_blu():
    ogg = [_intestazione('Blue', 'STIMA INTELLIGENCE USA\n2 ottobre 1989 - situazione di pace\nI sistemi mobili possono essersi spostati', NERO)]
    ogg += _basi('Blue', BASI_BLU, B_LINEA, 'Propria')
    ogg += _sam('Blue', SAM_BLU, B_LINEA, B_TENUE, 'Propria')
    ogg += _basi('Blue', BASI_ROSSE, R_LINEA, 'Intel')
    ogg += _basi('Blue', [BASE_NAVALE_ROSSA], R_LINEA, 'Intel')
    ogg += _sam('Blue', SAM_ROSSI, R_LINEA, R_TENUE, 'Intel')
    ogg.append(_testo('Intel contingente sovietico', 'Blue', 35.30, 38.60,
                      'Contingente aereo sovietico:\nbasi non confermate', R_LINEA, 13))
    return ogg


def disegni_rossi():
    ogg = [_intestazione('Red', 'QUADRO INFORMATIVO SIRO-SOVIETICO\n2 ottobre 1989 - situazione di pace', NERO)]
    ogg += _basi('Red', BASI_ROSSE, R_LINEA, 'Propria')
    ogg += _basi('Red', [BASE_NAVALE_ROSSA], R_LINEA, 'Propria')
    ogg += _sam('Red', SAM_ROSSI, R_LINEA, R_TENUE, 'Propria')
    ogg += _basi('Red', BASI_BLU_VISTE_DAL_ROSSO, B_LINEA, 'Intel')
    ogg += _sam('Red', SAM_BLU_VISTI_DAL_ROSSO, B_LINEA, B_TENUE, 'Intel')
    return ogg


def aggiungi(mission):
    for strato in mission['drawings']['layers'].values():
        if strato['name'] == 'Blue':
            strato['objects'] = {k: o for k, o in enumerate(disegni_blu(), 1)}
        elif strato['name'] == 'Red':
            strato['objects'] = {k: o for k, o in enumerate(disegni_rossi(), 1)}
