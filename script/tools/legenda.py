"""Legenda della mappa (strato Common), disegnata in mare a sud di Cipro.

Unica parte della mappa con testo: colori delle aree e significato dei simboli.
"""
from geo import ll_to_xy
import confini
import simboli

NERO = '0x202020ff'
ANGOLO = (34.32, 33.05)        # angolo in alto a sinistra (lat, lon)
RIGA = 5500.0                  # passo verticale tra le righe (m)
COL_TESTO = 9000.0             # distanza del testo dal bordo sinistro (m)


def _testo(nome, x, y, testo, dim, colore=NERO):
    return {'visible': True, 'primitiveType': 'TextBox', 'mapX': x, 'mapY': y, 'angle': 0,
            'text': testo, 'font': 'DejaVuLGCSansCondensed.ttf', 'fontSize': dim,
            'colorString': colore, 'fillColorString': '0x00000000', 'borderThickness': 0,
            'name': nome, 'layerName': 'Common'}


def _riquadro_pieno(nome, x_alto, y_sin, alt, larg, colore_bordo, colore_riempimento, spessore=2):
    pts = [(x_alto, y_sin), (x_alto, y_sin + larg), (x_alto - alt, y_sin + larg), (x_alto - alt, y_sin)]
    x0, y0 = pts[0]
    rel = {k: {'x': x - x0, 'y': y - y0} for k, (x, y) in enumerate(pts, 1)}
    rel[5] = {'x': 0.0, 'y': 0.0}
    pieno = {'visible': True, 'primitiveType': 'Polygon', 'polygonMode': 'free', 'mapX': x0, 'mapY': y0,
             'angle': 0, 'points': rel, 'colorString': '0x00000000', 'fillColorString': colore_riempimento,
             'thickness': 0, 'style': 'solid', 'name': nome + ' (fondo)', 'layerName': 'Common'}
    return [pieno, simboli.linea(nome, 'Common', pts, colore_bordo, spessore)]


def disegni():
    x0, y0 = ll_to_xy(*ANGOLO)
    righe = []     # (tipo, contenuto)
    righe.append(('titolo', 'LEGENDA'))
    righe.append(('sezione', 'AREE'))
    righe.append(('area', (confini.ROSSO, 'Ostile: Siria e Libano a controllo siriano')))
    righe.append(('area', (confini.BLU, 'Alleato: enclave di Aoun, zona navale USA')))
    righe.append(('area', (confini.GIALLO, 'Israele: neutrale, spazio aereo VIETATO')))
    righe.append(('area', (confini.GRIGIO, 'Neutrale: Giordania')))
    righe.append(('nota', 'Turchia (NATO): neutrale, attacco VIETATO'))
    righe.append(('nota', 'Cipro: neutrale, Akrotiri per dirottamento'))
    righe.append(('sezione', 'SIMBOLI   (rosso = siro-sovietici, blu = USA)'))
    for tipo in ('aerea', 'elicotteri', 'navale', 'terra', 'sam_lungo', 'sam_medio', 'sam_mobile'):
        righe.append(('simbolo', tipo))
    righe.append(('nota', 'Forze avversarie: stima intel al 2 ottobre 1989'))

    larghezza = 72000.0
    altezza = RIGA * (len(righe) + 1)
    ogg = _riquadro_pieno('Legenda', x0 + RIGA * 0.6, y0 - 3000, altezza, larghezza, NERO, '0xf4f0e4e0')

    for i, (tipo, cont) in enumerate(righe):
        x = x0 - i * RIGA          # centro della riga
        if tipo == 'titolo':
            ogg.append(_testo('Legenda titolo', x + 2000, y0, cont, 16))
        elif tipo == 'sezione':
            ogg.append(_testo('Legenda %d' % i, x + 1500, y0, cont, 11))
        elif tipo == 'nota':
            ogg.append(_testo('Legenda %d' % i, x + 1500, y0 + COL_TESTO, cont, 10))
        elif tipo == 'area':
            colori, testo = cont
            ogg += _riquadro_pieno('Legenda %d' % i, x + 1600, y0 + 1500, 3200, 4500, colori[0], colori[1])
            ogg.append(_testo('Legenda %d testo' % i, x + 1500, y0 + COL_TESTO, testo, 10))
        elif tipo == 'simbolo':
            ogg += simboli.simbolo(cont, 'Legenda %s' % cont, 'Common', x, y0 + 3800, NERO, scala=0.7)
            ogg.append(_testo('Legenda %s testo' % cont, x + 1500, y0 + COL_TESTO, simboli.TIPI[cont][0], 10))
    return ogg
