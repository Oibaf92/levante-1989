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

ZONA_NAVALE_USA = [  # area operativa del gruppo portaerei
    (33.50, 34.60), (34.40, 34.30), (35.40, 34.90), (35.95, 35.20), (35.95, 35.55),
    (35.30, 35.55), (34.60, 35.55), (33.95, 35.30), (33.50, 35.15),
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
    (34.75, 34.95, 'ZONA OPERATIVA\nNAVALE USA', BLU, 14),
]


def _poligono(i, nome, punti, colori, spessore):
    xy = [ll_to_xy(lat, lon) for lat, lon in punti]
    x0, y0 = xy[0]
    return {
        'visible': True, 'primitiveType': 'Polygon', 'polygonMode': 'free',
        'mapX': x0, 'mapY': y0, 'angle': 0,
        'points': {k: {'x': x - x0, 'y': y - y0} for k, (x, y) in enumerate(xy, 1)},
        'colorString': colori[0], 'fillColorString': colori[1],
        'thickness': spessore, 'style': 'solid',
        'name': nome, 'layerName': 'Common',
    }


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
    for i, (nome, punti, colori, spessore) in enumerate(TERRITORI, 1):
        ogg.append(_poligono(i, nome, punti, colori, spessore))
    for i, (lat, lon, testo, colori, dim) in enumerate(ETICHETTE, 1):
        ogg.append(_testo(i, lat, lon, testo, colori, dim))
    return {k: o for k, o in enumerate(ogg, 1)}


def aggiungi(mission):
    for strato in mission['drawings']['layers'].values():
        if strato['name'] == 'Common':
            strato['objects'] = disegni()
            return
    raise KeyError('strato Common non trovato')
