"""Simboli della mappa: una forma per tipo di installazione, il colore per la fazione.

Tutte le forme sono linee chiuse (l'unico tipo di disegno che DCS rende in modo
affidabile). Coordinate della mappa DCS: x = nord, y = est, in metri.
"""
import math

# tipo -> (descrizione per la legenda, dimensione del simbolo in metri)
TIPI = {
    'aerea': ('Base aerea', 4000),
    'elicotteri': ('Base elicotteri', 4000),
    'navale': ('Base navale / nave', 5000),
    'terra': ('Forze di terra', 4500),
    'sam_lungo': ('SAM a lungo raggio (SA-5) e portata', 8000),
    'sam_medio': ('SAM a medio raggio (SA-2/3, Hawk) e portata', 5000),
    'sam_mobile': ('Zona SAM mobili (SA-6/8) e portata', 3500),
}


def linea(nome, strato, punti, colore, spessore=3, chiusa=True):
    x0, y0 = punti[0]
    pts = {k: {'x': x - x0, 'y': y - y0} for k, (x, y) in enumerate(punti, 1)}
    if chiusa:
        pts[len(punti) + 1] = {'x': 0.0, 'y': 0.0}
    return {'visible': True, 'primitiveType': 'Line', 'lineMode': 'free', 'closed': chiusa,
            'mapX': x0, 'mapY': y0, 'points': pts, 'colorString': colore,
            'thickness': spessore, 'style': 'solid', 'name': nome, 'layerName': strato}


def _poligono_regolare(x, y, raggio, lati, rotazione_gradi):
    return [(x + raggio * math.cos(math.radians(rotazione_gradi + 360 * i / lati)),
             y + raggio * math.sin(math.radians(rotazione_gradi + 360 * i / lati))) for i in range(lati)]


def cerchio(nome, strato, x, y, raggio, colore, spessore=2, n=48):
    return linea(nome, strato, _poligono_regolare(x, y, raggio, n, 0), colore, spessore)


def simbolo(tipo, nome, strato, x, y, colore, scala=1.0):
    """Restituisce la lista di oggetti che disegnano il simbolo del tipo indicato."""
    lato = TIPI[tipo][1] * scala
    h = lato / 2
    if tipo == 'aerea':
        return [linea(nome, strato, [(x - h, y - h), (x - h, y + h), (x + h, y + h), (x + h, y - h)], colore)]
    if tipo == 'elicotteri':
        return [linea(nome, strato, [(x - h, y - h), (x - h, y + h), (x + h, y + h), (x + h, y - h)], colore),
                linea(nome + ' /', strato, [(x - h, y - h), (x + h, y + h)], colore, chiusa=False),
                linea(nome + ' \\', strato, [(x - h, y + h), (x + h, y - h)], colore, chiusa=False)]
    if tipo == 'navale':
        return [linea(nome, strato, _poligono_regolare(x, y, h * 1.3, 4, 0), colore)]
    if tipo == 'terra':
        return [linea(nome, strato, _poligono_regolare(x, y, h * 1.1, 5, 0), colore)]
    if tipo in ('sam_lungo', 'sam_medio'):
        # triangolo con la punta a nord (x = nord: angolo 0)
        return [linea(nome, strato, _poligono_regolare(x, y, h * 1.15, 3, 0), colore)]
    if tipo == 'sam_mobile':
        return [cerchio(nome, strato, x, y, h, colore, 3, n=16)]
    raise KeyError(tipo)
