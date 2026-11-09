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
    'sa5': ('SA-5 (lungo raggio) e portata', 9000),
    'sa2': ('SA-2 e portata', 5500),
    'sa3': ('SA-3 e portata', 5500),
    'sa6': ('SA-6 (mobile) e portata', 5000),
    'sa8': ('SA-8 (mobile) e portata', 4000),
    'hawk': ('Hawk (USA) e portata', 5500),
}
SAM = ('sa5', 'sa2', 'sa3', 'sa6', 'sa8', 'hawk')


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
    # SAM: x = nord, quindi l'angolo 0 mette la punta del triangolo a nord
    if tipo == 'sa5':
        return [linea(nome, strato, _poligono_regolare(x, y, h * 1.15, 3, 0), colore),
                linea(nome + ' interno', strato, _poligono_regolare(x, y, h * 0.55, 3, 0), colore)]
    if tipo == 'sa2':
        return [linea(nome, strato, _poligono_regolare(x, y, h * 1.15, 3, 0), colore)]
    if tipo == 'sa3':
        return [linea(nome, strato, _poligono_regolare(x, y, h * 1.15, 3, 180), colore)]
    if tipo == 'sa6':
        return [linea(nome, strato, _poligono_regolare(x, y, h, 6, 0), colore)]
    if tipo == 'sa8':
        return [cerchio(nome, strato, x, y, h, colore, 3, n=20),
                linea(nome + ' |', strato, [(x - h, y), (x + h, y)], colore, chiusa=False),
                linea(nome + ' -', strato, [(x, y - h), (x, y + h)], colore, chiusa=False)]
    if tipo == 'hawk':
        return [linea(nome, strato, _poligono_regolare(x, y, h * 1.15, 3, 0), colore),
                linea(nome + ' barra', strato, [(x - h * 0.15, y - h * 1.1), (x - h * 0.15, y + h * 1.1)], colore,
                      chiusa=False)]
    raise KeyError(tipo)
