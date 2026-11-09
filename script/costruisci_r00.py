"""Costruisce missioni/R00_rilievo_terreno.miz

Missione senza aerei: uno script campiona il terreno di DCS (quota, pendenza,
superficie, edifici, distanza dalle strade) e lo salva in
Saved Games\\DCS\\Levante1989\\rilievo_terreno.txt.

Uso:  python3 script/costruisci_r00.py
"""
import os
import sys
import zipfile

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
sys.path.insert(0, os.path.join(QUI, 'tools'))

import luatable as lt  # noqa: E402
from geo import ll_to_xy  # noqa: E402

NOME = 'R00_rilievo_terreno'

# (nome, lat sud, lat nord, lon ovest, lon est, passo in metri)
REGIONI = [
    ('generale', 32.20, 37.40, 34.70, 41.20, 2000),     # tutta l'area dei combattimenti
    ('dettaglio', 32.60, 35.40, 35.00, 37.30, 1000),    # Libano, Golan, Siria occidentale
]


def regione_xy(nome, lat_s, lat_n, lon_o, lon_e, passo):
    angoli = [ll_to_xy(la, lo) for la in (lat_s, lat_n) for lo in (lon_o, lon_e)]
    x0 = min(a[0] for a in angoli)
    x1 = max(a[0] for a in angoli)
    y0 = min(a[1] for a in angoli)
    y1 = max(a[1] for a in angoli)
    nx = int((x1 - x0) // passo) + 1
    ny = int((y1 - y0) // passo) + 1
    return {'nome': nome, 'x0': round(x0, 1), 'y0': round(y0, 1), 'passo': passo, 'nx': nx, 'ny': ny}


def parametri_lua():
    righe = ['LEVANTE_RILIEVO = {', '  regioni = {']
    for r in (regione_xy(*g) for g in REGIONI):
        righe.append('    { nome = "%(nome)s", x0 = %(x0).1f, y0 = %(y0).1f, passo = %(passo)d, nx = %(nx)d, ny = %(ny)d },' % r)
    righe += ['  },', '}', '']
    return '\n'.join(righe)


BRIEFING = """LEVANTE 1989 - R00: RILIEVO DEL TERRENO

Questa non e' una missione di volo. Uno script misura il terreno di DCS su una griglia
che copre tutta l'area dei combattimenti: quota, pendenza, tipo di superficie, edifici
vicini e distanza dalla strada piu' vicina.

COSA FARE
1. Avvia la missione e lascia che giri. Non serve pilotare nulla.
2. Non mettere in pausa: i messaggi in alto mostrano l'avanzamento in percentuale.
3. Al messaggio RILIEVO COMPLETATO chiudi la missione.
4. Carica il file  Saved Games\\DCS\\Levante1989\\rilievo_terreno.txt

Il file serve a piazzare SAM, artiglieria e unita' di terra in posizioni sensate.
"""


def costruisci():
    carica = lambda n: lt.parse(open(os.path.join(QUI, 'base', n), encoding='utf-8').read())[1]  # noqa: E731
    m = carica('mission')
    w = carica('warehouses')
    o = carica('options')
    m['date'] = {'Year': 1989, 'Month': 10, 'Day': 1}
    m['start_time'] = 12 * 3600
    centro = ll_to_xy(34.0, 36.0)
    m['map'] = {'centerX': centro[0], 'centerY': centro[1], 'zoom': 400000}
    diz = {
        'DictKey_descriptionText_1': BRIEFING,
        'DictKey_descriptionRedTask_2': '',
        'DictKey_descriptionBlueTask_3': '',
        'DictKey_descriptionNeutralsTask_4': '',
        'DictKey_sortie_5': 'R00 - Rilievo del terreno',
    }
    m['descriptionText'] = 'DictKey_descriptionText_1'
    m['descriptionRedTask'] = 'DictKey_descriptionRedTask_2'
    m['descriptionBlueTask'] = 'DictKey_descriptionBlueTask_3'
    m['descriptionNeutralsTask'] = 'DictKey_descriptionNeutralsTask_4'
    m['sortie'] = 'DictKey_sortie_5'
    m['maxDictId'] = 5
    risorse = {'ResKey_Action_1': 'r00_parametri.lua', 'ResKey_Action_2': 'R00_rilievo.lua'}
    for i, (commento, chiave) in enumerate((('PARAMETRI', 'ResKey_Action_1'), ('RILIEVO', 'ResKey_Action_2')), 1):
        m['trig']['actions'][i] = 'a_do_script_file(getValueResourceByKey("%s"));' % chiave
        m['trig']['conditions'][i] = 'return(true)'
        m['trig']['flag'][i] = True
        m['trig']['funcStartup'][i] = 'if mission.trig.conditions[%d]() then mission.trig.actions[%d]() end' % (i, i)
        m['trigrules'][i] = {'rules': {}, 'comment': commento, 'eventlist': '', 'predicate': 'triggerStart',
                             'actions': {1: {'predicate': 'a_do_script_file', 'file': chiave}}}
    w['warehouses'] = {}
    out = os.path.join(RADICE, 'missioni', NOME + '.miz')
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mission', lt.dump('mission', m))
        z.writestr('warehouses', lt.dump('warehouses', w))
        z.writestr('options', lt.dump('options', o))
        z.writestr('theatre', 'Syria')
        z.writestr('l10n/DEFAULT/dictionary', lt.dump('dictionary', diz))
        z.writestr('l10n/DEFAULT/mapResource', lt.dump('mapResource', risorse))
        z.writestr('l10n/DEFAULT/r00_parametri.lua', parametri_lua())
        z.write(os.path.join(QUI, 'lua', 'R00_rilievo.lua'), 'l10n/DEFAULT/R00_rilievo.lua')
    print('scritto', out)
    print(parametri_lua())


if __name__ == '__main__':
    costruisci()
