"""Quadro di intelligence di partenza (2 ottobre 1989, prima delle ostilita').

Situazione di PACE: basi permanenti e siti antiaerei fissi noti, come li stima
ciascuna parte. Ogni parte vede solo il proprio strato sulla mappa F10:
  - strato "Blue": forze USA proprie + stima USA delle forze siro-sovietiche
  - strato "Red":  forze siro-sovietiche proprie + stima delle forze USA

Sulla mappa nessuna scritta: ogni installazione e' un simbolo (simboli.py, legenda
in legenda.py); il dettaglio (nomi, velivoli) e' sulle tavolette.

E' il punto di partenza fissato dall'arbitro. I comandanti possono spostare i
sistemi mobili (SA-6, SA-8, ...): in guerra questa mappa puo' essere superata.
Posizioni approssimate.
"""
from geo import ll_to_xy
import simboli

R_LINEA = '0xcc1f1fff'
R_TENUE = '0xcc1f1f90'
B_LINEA = '0x1f5fccff'
B_TENUE = '0x1f5fcc90'

# --- forze siro-sovietiche: (lat, lon, tipo, nome, dettaglio) ----------------
BASI_ROSSE = [
    (35.404, 35.950, 'aerea', 'Latakia', 'MiG-21, elicotteri'),
    (35.118, 36.712, 'aerea', 'Hama', 'MiG-21'),
    (34.490, 36.908, 'aerea', 'Shayrat', 'MiG-23, Su-22'),
    (34.523, 37.630, 'aerea', 'Tiyas (T4)', 'MiG-23, MiG-25'),
    (33.610, 36.749, 'aerea', 'Al-Dumayr', 'MiG-23, MiG-29'),
    (33.680, 37.217, 'aerea', 'Sayqal', 'MiG-23'),
    (34.557, 38.317, 'aerea', 'Palmyra', 'MiG-25'),
    (33.478, 36.224, 'elicotteri', 'Mezzeh', 'elicotteri, ricognizione'),
    (33.289, 36.455, 'aerea', 'Marj Ruhayyil', 'MiG-21, MiG-23'),
    (33.078, 36.541, 'aerea', 'Khalkhalah', 'MiG-21'),
    (34.569, 36.571, 'aerea', 'Al Qusayr', 'MiG-21'),
    (33.426, 36.519, 'aerea', 'Damasco', 'trasporti'),
    (33.851, 35.987, 'elicotteri', 'Rayak (Bekaa)', 'Mi-24, Mi-8'),
    (35.732, 37.104, 'aerea', 'Abu al-Duhur', 'MiG-21'),
    (36.187, 37.581, 'aerea', 'Kuweires', 'scuola di volo'),
    (34.905, 35.865, 'navale', 'Tartus', 'punto d\'appoggio della flotta sovietica'),
]

# siti SAM: (lat, lon, raggio km, tipo, nome)
SAM_ROSSI = [
    (33.660, 36.820, 150, 'sam_lungo', 'SA-5 Dumayr'),
    (34.600, 36.740, 150, 'sam_lungo', 'SA-5 Homs'),
    (33.510, 36.290, 35, 'sam_medio', 'SA-2/SA-3 Damasco'),
    (34.730, 36.710, 30, 'sam_medio', 'SA-2/SA-3 Homs'),
    (35.130, 36.750, 25, 'sam_medio', 'SA-2/SA-3 Hama'),
    (36.200, 37.160, 30, 'sam_medio', 'SA-2/SA-3 Aleppo'),
    (35.520, 35.850, 25, 'sam_medio', 'SA-2/SA-3 Latakia'),
    (34.890, 35.920, 25, 'sam_medio', 'SA-2/SA-3 Tartus'),
    (33.850, 35.980, 30, 'sam_mobile', 'SA-6 mobili, Bekaa'),
    (33.150, 36.050, 30, 'sam_mobile', 'SA-6/SA-8 mobili, fronte del Golan'),
]

# --- forze USA -----------------------------------------------------------------
BASI_BLU = [
    (37.002, 35.426, 'aerea', 'Incirlik', 'USAF: F-4E x12, KC-135 x2, E-3A'),
    (34.590, 32.988, 'aerea', 'Akrotiri (UK)', 'base di dirottamento'),
    (34.050, 35.450, 'navale', 'LHA-1 Tarawa', 'AH-64, CH-47, AV-8B'),
    (33.980, 35.630, 'terra', 'Jounieh', 'testa di ponte dei Marines'),
]
SAM_BLU = [
    (33.980, 35.630, 35, 'sam_medio', 'I-Hawk Jounieh'),
]

# cio' che il rosso sa delle forze USA
BASI_BLU_VISTE_DAL_ROSSO = [
    (37.002, 35.426, 'aerea', 'Incirlik', 'aerei USA rilevati (F-4)'),
    (34.590, 32.988, 'aerea', 'Akrotiri (UK)', 'possibile dirottamento USA'),
    (34.050, 35.450, 'navale', 'Nave d\'assalto USA', 'al largo di Jounieh'),
    (33.980, 35.630, 'terra', 'Jounieh', 'sbarco dei Marines'),
    (35.900, 33.900, 'navale', 'Gruppo portaerei USA', 'posizione stimata, in movimento'),
]
SAM_BLU_VISTI_DAL_ROSSO = [
    (33.980, 35.630, 35, 'sam_medio', 'Hawk (stimato) Jounieh'),
]


# ---------------------------------------------------------------------------
DISTANZA_MINIMA = 7000.0      # m tra due simboli; se piu' vicini, il secondo viene scostato


def _posto_libero(x, y, occupati):
    """Scosta il simbolo verso est (poi altre direzioni) se tocca un simbolo gia' disegnato."""
    import math
    for passo in range(0, 6):
        for ang in (90, 0, 180, 270, 45, 135, 225, 315):
            d = passo * DISTANZA_MINIMA
            px, py = x + d * math.cos(math.radians(ang)), y + d * math.sin(math.radians(ang))
            if all(math.hypot(px - ox, py - oy) >= DISTANZA_MINIMA for ox, oy in occupati):
                return px, py
            if passo == 0:
                break
    return x, y


def _basi(strato, basi, colore, prefisso, occupati):
    ogg = []
    for lat, lon, tipo, nome, _ in basi:
        x, y = _posto_libero(*ll_to_xy(lat, lon), occupati)
        occupati.append((x, y))
        ogg += simboli.simbolo(tipo, '%s %s' % (prefisso, nome), strato, x, y, colore)
    return ogg


def _sam(strato, siti, linea, tenue, prefisso, occupati):
    ogg = []
    for lat, lon, r_km, tipo, nome in siti:
        x, y = ll_to_xy(lat, lon)
        col_cerchio = tenue if tipo == 'sam_lungo' else linea
        # il cerchio di portata resta centrato sul sito vero, il simbolo puo' essere scostato
        ogg.append(simboli.cerchio('%s %s (portata)' % (prefisso, nome), strato, x, y, r_km * 1000, col_cerchio,
                                   2 if tipo == 'sam_lungo' else 3))
        sx, sy = _posto_libero(x, y, occupati)
        occupati.append((sx, sy))
        ogg += simboli.simbolo(tipo, '%s %s' % (prefisso, nome), strato, sx, sy, linea)
    return ogg


def disegni_blu():
    occ = []
    return (_basi('Blue', BASI_BLU, B_LINEA, 'Propria', occ)
            + _basi('Blue', BASI_ROSSE, R_LINEA, 'Intel', occ)
            + _sam('Blue', SAM_BLU, B_LINEA, B_TENUE, 'Propria', occ)
            + _sam('Blue', SAM_ROSSI, R_LINEA, R_TENUE, 'Intel', occ))


def disegni_rossi():
    occ = []
    return (_basi('Red', BASI_ROSSE, R_LINEA, 'Propria', occ)
            + _basi('Red', BASI_BLU_VISTE_DAL_ROSSO, B_LINEA, 'Intel', occ)
            + _sam('Red', SAM_ROSSI, R_LINEA, R_TENUE, 'Propria', occ)
            + _sam('Red', SAM_BLU_VISTI_DAL_ROSSO, B_LINEA, B_TENUE, 'Intel', occ))


def aggiungi(mission):
    for strato in mission['drawings']['layers'].values():
        if strato['name'] == 'Blue':
            strato['objects'] = {k: o for k, o in enumerate(disegni_blu(), 1)}
        elif strato['name'] == 'Red':
            strato['objects'] = {k: o for k, o in enumerate(disegni_rossi(), 1)}
