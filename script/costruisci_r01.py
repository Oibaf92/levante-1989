"""Costruisce missioni/R01_mappa_foreste.miz

Missione di riferimento per mappare i boschi di DCS dagli screenshot del Mission
Editor (vista ALT). Contiene solo disegni:
  - crocette magenta a coordinate note, su una griglia di ~12 km con uno scarto
    pseudo-casuale fisso: ogni gruppo di crocette e' riconoscibile e permette di
    ricavare posizione e scala di ogni screenshot;
  - riquadri numerati T01..Tnn che indicano cosa inquadrare.
Le posizioni delle crocette sono salvate in campagna/terreno/marcatori_foreste.json.

Uso:  python3 script/costruisci_r01.py
"""
import json
import os
import random
import sys
import zipfile

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
sys.path.insert(0, os.path.join(QUI, 'tools'))

import luatable as lt  # noqa: E402
from geo import ll_to_xy, xy_to_ll  # noqa: E402
import simboli  # noqa: E402

NOME = 'R01_mappa_foreste'
AREA = (32.55, 37.05, 34.85, 37.30)      # lat sud, lat nord, lon ovest, lon est
PASSO = 12000.0                            # m tra le crocette
SCARTO = 3000.0                            # m di scarto massimo (fisso, seme 1989)
BRACCIO = 1200.0                           # m: meta' lunghezza della crocetta
TESSERA = (80000.0, 120000.0)              # m: riquadro da inquadrare (nord-sud, est-ovest)
MAGENTA = '0xff00ffff'
CIANO = '0x00b4c8ff'


def limiti():
    ang = [ll_to_xy(la, lo) for la in AREA[:2] for lo in AREA[2:]]
    return (min(a[0] for a in ang), max(a[0] for a in ang), min(a[1] for a in ang), max(a[1] for a in ang))


def marcatori():
    x0, x1, y0, y1 = limiti()
    rnd = random.Random(1989)
    out = []
    i = 0
    x = x0
    while x <= x1:
        y = y0
        while y <= y1:
            mx = x + rnd.uniform(-SCARTO, SCARTO)
            my = y + rnd.uniform(-SCARTO, SCARTO)
            out.append({'id': i, 'x': round(mx, 1), 'y': round(my, 1)})
            i += 1
            y += PASSO
        x += PASSO
    return out


def tessere():
    x0, x1, y0, y1 = limiti()
    alt, larg = TESSERA
    out = []
    n = 1
    x = x1
    while x - alt < x1 and x > x0:            # da nord verso sud
        y = y0
        while y < y1:
            out.append({'nome': 'T%02d' % n, 'x_nord': x, 'x_sud': x - alt, 'y_ovest': y, 'y_est': y + larg})
            n += 1
            y += larg
        x -= alt
    return out


def disegni():
    ogg = []
    for m in marcatori():
        x, y, a = m['x'], m['y'], BRACCIO
        ogg.append(simboli.linea('Crocetta %d' % m['id'], 'Common',
                                 [(x, y - a), (x, y + a), (x, y), (x - a, y), (x + a, y)], MAGENTA, 3, chiusa=False))
    for t in tessere():
        pts = [(t['x_nord'], t['y_ovest']), (t['x_nord'], t['y_est']), (t['x_sud'], t['y_est']), (t['x_sud'], t['y_ovest'])]
        ogg.append(simboli.linea('Riquadro ' + t['nome'], 'Common', pts, CIANO, 4))
        ogg.append({'visible': True, 'primitiveType': 'TextBox', 'mapX': t['x_nord'] - 2500, 'mapY': t['y_ovest'] + 2500,
                    'angle': 0, 'text': t['nome'], 'font': 'DejaVuLGCSansCondensed.ttf', 'fontSize': 28,
                    'colorString': CIANO, 'fillColorString': '0x00000000', 'borderThickness': 0,
                    'name': 'Etichetta ' + t['nome'], 'layerName': 'Common'})
    return ogg


BRIEFING = """LEVANTE 1989 - R01: MAPPA DEI BOSCHI

Missione da aprire solo nel Mission Editor, non da volare.

1. Apri la missione nel Mission Editor e scegli la vista ALT (in basso).
2. Per ogni riquadro azzurro T01, T02, ... inquadralo in modo che stia tutto nello schermo e
   lo riempia il piu' possibile, poi fai uno screenshot.
3. Le crocette magenta servono a me per calibrare le immagini: devono vedersi bene.
4. Chiudi i pannelli laterali, se puoi, per avere piu' mappa visibile.
5. Manda gli screenshot chiamandoli col nome del riquadro (T01.png, T02.png, ...).
"""


def costruisci():
    carica = lambda n: lt.parse(open(os.path.join(QUI, 'base', n), encoding='utf-8').read())[1]  # noqa: E731
    m = carica('mission')
    w = carica('warehouses')
    o = carica('options')
    m['date'] = {'Year': 1989, 'Month': 10, 'Day': 1}
    m['start_time'] = 12 * 3600
    centro = ll_to_xy(34.8, 36.0)
    m['map'] = {'centerX': centro[0], 'centerY': centro[1], 'zoom': 600000}
    for strato in m['drawings']['layers'].values():
        strato['objects'] = {}
        if strato['name'] == 'Common':
            strato['objects'] = {k: o for k, o in enumerate(disegni(), 1)}
    diz = {'DictKey_descriptionText_1': BRIEFING, 'DictKey_descriptionRedTask_2': '', 'DictKey_descriptionBlueTask_3': '',
           'DictKey_descriptionNeutralsTask_4': '', 'DictKey_sortie_5': 'R01 - Mappa dei boschi'}
    m['descriptionText'] = 'DictKey_descriptionText_1'
    m['descriptionRedTask'] = 'DictKey_descriptionRedTask_2'
    m['descriptionBlueTask'] = 'DictKey_descriptionBlueTask_3'
    m['descriptionNeutralsTask'] = 'DictKey_descriptionNeutralsTask_4'
    m['sortie'] = 'DictKey_sortie_5'
    m['maxDictId'] = 5
    w['warehouses'] = {}
    out = os.path.join(RADICE, 'missioni', NOME + '.miz')
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mission', lt.dump('mission', m))
        z.writestr('warehouses', lt.dump('warehouses', w))
        z.writestr('options', lt.dump('options', o))
        z.writestr('theatre', 'Syria')
        z.writestr('l10n/DEFAULT/dictionary', lt.dump('dictionary', diz))
        z.writestr('l10n/DEFAULT/mapResource', lt.dump('mapResource', {}))
    dati = {'passo': PASSO, 'scarto': SCARTO, 'braccio': BRACCIO, 'marcatori': marcatori(), 'tessere': tessere()}
    os.makedirs(os.path.join(RADICE, 'campagna', 'terreno'), exist_ok=True)
    json.dump(dati, open(os.path.join(RADICE, 'campagna', 'terreno', 'marcatori_foreste.json'), 'w'), indent=1)
    print('scritto', out, '-', len(dati['marcatori']), 'crocette,', len(dati['tessere']), 'riquadri')
    for t in dati['tessere']:
        n = xy_to_ll(t['x_nord'], t['y_ovest'])
        s = xy_to_ll(t['x_sud'], t['y_est'])
        print('  %s  da N%.2f E%.2f  a N%.2f E%.2f' % (t['nome'], n[0], n[1], s[0], s[1]))


if __name__ == '__main__':
    costruisci()
