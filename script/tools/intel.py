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
# SA-6 e SA-8 sono mobili: la posizione e' l'ultima osservata.
SAM_ROSSI = [
    # niente SA-5 (decisione del giocatore: troppo difficili da gestire); al loro posto piu' SA-2
    (33.660, 36.820, 40, 'sa2', 'SA-2 Dumayr'),
    (34.570, 36.600, 40, 'sa2', 'SA-2 Al Qusayr'),
    (34.010, 36.210, 40, 'sa2', 'SA-2 Baalbek'),
    (34.850, 35.950, 40, 'sa2', 'SA-2 Tartus'),
    (33.580, 36.250, 40, 'sa2', 'SA-2 Damasco nord'),
    (33.400, 36.400, 40, 'sa2', 'SA-2 Damasco sud'),
    (33.520, 36.380, 22, 'sa3', 'SA-3 Damasco est'),
    (33.450, 36.180, 22, 'sa3', 'SA-3 Damasco ovest'),
    (34.760, 36.660, 40, 'sa2', 'SA-2 Homs'),
    (34.700, 36.800, 22, 'sa3', 'SA-3 Homs'),
    (35.160, 36.780, 40, 'sa2', 'SA-2 Hama'),
    (35.100, 36.680, 22, 'sa3', 'SA-3 Hama'),
    (36.240, 37.120, 40, 'sa2', 'SA-2 Aleppo'),
    (36.160, 37.220, 22, 'sa3', 'SA-3 Aleppo'),
    (35.450, 35.980, 40, 'sa2', 'SA-2 Latakia'),
    (35.520, 35.850, 22, 'sa3', 'SA-3 Latakia'),
    (34.890, 35.920, 22, 'sa3', 'SA-3 Tartus'),
    (33.850, 35.980, 25, 'sa6', 'SA-6 Bekaa'),
    (33.150, 36.050, 25, 'sa6', 'SA-6 fronte del Golan'),
    (33.780, 35.920, 10, 'sa8', 'SA-8 Bekaa'),
    (33.220, 36.120, 10, 'sa8', 'SA-8 fronte del Golan'),
    (33.480, 36.300, 10, 'sa8', 'SA-8 Damasco'),
]

# --- forze USA -----------------------------------------------------------------
BASI_BLU = [
    (37.002, 35.426, 'aerea', 'Incirlik', 'USAF: F-4E x12, KC-135 x2, E-3A'),
    (34.590, 32.988, 'aerea', 'Akrotiri (UK)', 'base di dirottamento'),
    (34.050, 35.450, 'navale', 'LHA-1 Tarawa', 'AH-64, CH-47, AV-8B'),
    (33.980, 35.630, 'terra', 'Jounieh', 'testa di ponte dei Marines'),
]
SAM_BLU = [
    (33.980, 35.630, 35, 'hawk', 'I-Hawk Jounieh'),
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
    (33.980, 35.630, 35, 'hawk', 'Hawk (stimato) Jounieh'),
]


# ---------------------------------------------------------------------------
def _basi(strato, basi, colore, prefisso):
    ogg = []
    for lat, lon, tipo, nome, _ in basi:
        x, y = ll_to_xy(lat, lon)
        ogg += simboli.simbolo(tipo, '%s %s' % (prefisso, nome), strato, x, y, colore)
    return ogg


def _sam(strato, siti, linea, tenue, prefisso):
    ogg = []
    for lat, lon, r_km, tipo, nome in siti:
        x, y = ll_to_xy(lat, lon)
        col_cerchio = tenue if tipo == 'sa5' else linea
        ogg.append(simboli.cerchio('%s %s (portata)' % (prefisso, nome), strato, x, y, r_km * 1000, col_cerchio,
                                   2 if tipo == 'sa5' else 3))
        ogg += simboli.simbolo(tipo, '%s %s' % (prefisso, nome), strato, x, y, linea)
    return ogg


def disegni_blu():
    return (_basi('Blue', BASI_BLU, B_LINEA, 'Propria')
            + _basi('Blue', BASI_ROSSE, R_LINEA, 'Intel')
            + _sam('Blue', SAM_BLU, B_LINEA, B_TENUE, 'Propria')
            + _sam('Blue', SAM_ROSSI, R_LINEA, R_TENUE, 'Intel'))


def disegni_rossi():
    return (_basi('Red', BASI_ROSSE, R_LINEA, 'Propria')
            + _basi('Red', BASI_BLU_VISTE_DAL_ROSSO, B_LINEA, 'Intel')
            + _sam('Red', SAM_ROSSI, R_LINEA, R_TENUE, 'Propria')
            + _sam('Red', SAM_BLU_VISTI_DAL_ROSSO, B_LINEA, B_TENUE, 'Intel'))


def aggiungi(mission):
    for strato in mission['drawings']['layers'].values():
        if strato['name'] == 'Blue':
            strato['objects'] = {k: o for k, o in enumerate(disegni_blu(), 1)}
        elif strato['name'] == 'Red':
            strato['objects'] = {k: o for k, o in enumerate(disegni_rossi(), 1)}
