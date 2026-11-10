"""Rigenera script/dati/piloni.json dai sorgenti di pydcs (planes.py, helicopters.py, weapons_data.py).

Uso:  python3 script/tools/estrai_piloni.py <cartella che contiene il pacchetto dcs di pydcs>
Legge i file come testo (non importa pydcs, che richiede pyproj). Per ogni velivolo:
{"pilastri": {numero: {nome arma: CLSID}}, "carburante": kg interni}.
"""
import json
import os
import re
import sys

QUI = os.path.dirname(os.path.abspath(__file__))


def armi(testo):
    out = {}
    for m in re.finditer(r'\n    (\w+) = \{"clsid": "((?:[^"\\]|\\.)*)", "name": "((?:[^"\\]|\\.)*)"', testo):
        out[m.group(1)] = (m.group(2), m.group(3).replace('\\"', '"').replace('\\\\', '\\'))
    return out


def velivoli(testo, armi_):
    out = {}
    for m in re.finditer(r'\nclass (\w+)\((?:PlaneType|HelicopterType)\):(.*?)(?=\nclass |\Z)', testo, re.S):
        corpo = m.group(2)
        ident = re.search(r'\n    id = "(.*?)"', corpo)
        if not ident:
            continue
        carb = re.search(r'\n    fuel_max = ([\d.]+)', corpo)
        pil = {}
        for p in re.finditer(r'\n    class Pylon(\d+):(.*?)(?=\n    class |\n    pylons|\Z)', corpo, re.S):
            for _, n, w in re.findall(r'(\w+) = \((\d+), Weapons\.(\w+)\)', p.group(2)):
                if w in armi_:
                    clsid, nome = armi_[w]
                    pil.setdefault(n, {})[nome] = clsid
        out[ident.group(1)] = {'pilastri': pil, 'carburante': float(carb.group(1)) if carb else None}
    return out


if __name__ == '__main__':
    base = os.path.join(sys.argv[1], 'dcs')
    a = armi(open(os.path.join(base, 'weapons_data.py'), encoding='utf-8').read())
    tutti = {}
    for f in ('planes.py', 'helicopters.py'):
        tutti.update(velivoli(open(os.path.join(base, f), encoding='utf-8').read(), a))
    dest = os.path.join(QUI, '..', 'dati', 'piloni.json')
    vecchio = json.load(open(dest, encoding='utf-8'))
    utili = set(vecchio) | {'F-14B', 'MiG-29A', 'MiG-29S'}
    nuovo = {k: v for k, v in tutti.items() if k in utili}
    json.dump(nuovo, open(dest, 'w', encoding='utf-8'), indent=1, ensure_ascii=False, sort_keys=True)
    print('velivoli:', len(nuovo), 'mancanti:', sorted(utili - set(nuovo)))
