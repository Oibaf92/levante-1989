"""Costruisce missioni/C00_prova_carichi.miz

Missione di controllo dei carichi: un gruppo (slot Client) per ogni carico del catalogo
(script/tools/carichi.py) dei moduli del giocatore, in volo in una griglia sopra il mare a sud
di Cipro (blu a ovest, rossi a est). Nel Mission Editor si apre ogni gruppo e si controlla il
carico; i carichi non validi compaiono vuoti o segnalati dall'editor.

Il giocatore ci aggiunge due MiG-29 (carico R-73 e carico d'attacco) e la salva dal Mission
Editor: dalla missione salvata si ricavano anche le strutture delle radio dei moduli.

Uso:  python3 script/costruisci_c00.py
"""
import os
import sys
import zipfile

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
sys.path.insert(0, os.path.join(QUI, 'tools'))
sys.path.insert(0, QUI)

import luatable as lt  # noqa: E402
from geo import ll_to_xy  # noqa: E402
import carichi  # noqa: E402
import verifica_miz  # noqa: E402
from costruisci_giornata import wpt, NOMI_CHIAMATA_TESTO  # noqa: E402

NOME = 'C00_prova_carichi'
USA, RUSSIA = 2, 0
STORICI = {'aria-aria', 'scorta', 'attacco'}       # alias di altri carichi
MODULI = {   # tipo -> (lato, elicottero, nome breve)
    'F-14A-135-GR-Early': ('blue', False, 'F-14A'),
    'FA-18C_hornet': ('blue', False, 'F-18C'), 'F-4E-45MC': ('blue', False, 'F-4E'),
    'AH-64D_BLK_II': ('blue', True, 'AH-64D'), 'CH-47Fbl1': ('blue', True, 'CH-47F'),
    'Su-25': ('red', False, 'Su-25'), 'MiG-29 Fulcrum': ('red', False, 'MiG-29'), 'Mi-24P': ('red', True, 'Mi-24P'), 'Mi-8MT': ('red', True, 'Mi-8'),
}
ORIGINE = {'blue': (34.25, 33.30), 'red': (34.25, 34.10)}   # mare a sud di Cipro
PASSO = 3000                                              # m tra i gruppi

BRIEFING = """LEVANTE 1989 - C00: PROVA DEI CARICHI

Un gruppo per ogni carico del catalogo (docs/lezioni.md), tutti slot Client in volo sopra il mare.
Il nome del gruppo e' "<velivolo> <carico>".

COSA FARE
1. Nel Mission Editor apri ogni gruppo e guarda la pagina del carico: segnala quelli vuoti,
   incompleti o che l'editor rifiuta.
2. Aggiungi due MiG-29 (paese a tua scelta) come Client: uno con il CAP con R-73, uno con un
   carico d'attacco.
3. Salva la missione dal Mission Editor e mandala: serve anche per le radio dei moduli.
"""


def gruppi():
    out = []
    for tipo, (lato, eli, breve) in MODULI.items():
        nomi = [n for n in carichi.CARICHI.get(tipo, {}) if n not in STORICI] or ['nessuno']
        for nome in nomi:
            out.append((lato, eli, tipo, breve, nome))
    return out


def costruisci():
    carica = lambda n: lt.parse(open(os.path.join(QUI, 'base', n), encoding='utf-8').read())[1]  # noqa: E731
    m, w, o = carica('mission'), carica('warehouses'), carica('options')
    m['date'] = {'Year': 1989, 'Month': 10, 'Day': 2}
    m['start_time'] = 9 * 3600
    cx, cy = ll_to_xy(34.25, 33.7)
    m['map'] = {'centerX': cx, 'centerY': cy, 'zoom': 150000}
    paesi = {}
    for lato, pid, pnome in (('blue', USA, 'USA'), ('red', RUSSIA, 'Russia')):
        lista = m['coalition'][lato]['country']
        paese = next((c for c in lista.values() if c['id'] == pid), None)
        if paese is None:
            paese = {'id': pid, 'name': pnome}
            lista[len(lista) + 1] = paese
        paese['plane'] = {'group': {}}
        paese['helicopter'] = {'group': {}}
        paesi[lato] = paese
    gid, uid = 1, 1
    conta = {'blue': 0, 'red': 0}
    righe = []
    for lato, eli, tipo, breve, nome in gruppi():
        k = conta[lato]
        conta[lato] += 1
        x0, y0 = ll_to_xy(*ORIGINE[lato])
        x, y = x0 - (k // 6) * PASSO, y0 + (k % 6) * PASSO
        alt, vel = (300, 50) if eli else (3000, 200)
        piloni = carichi.risolvi(tipo, nome) if nome != 'nessuno' else {}
        carb = carichi.PILONI.get(tipo, {}).get('carburante') or 2000
        u = {'type': tipo, 'unitId': uid, 'name': '%s %s' % (breve, nome), 'skill': 'Client', 'x': x, 'y': y,
             'alt': alt, 'alt_type': 'BARO', 'heading': 0, 'psi': 0, 'speed': vel,
             'payload': {'pylons': piloni, 'fuel': carb, 'flare': 60, 'chaff': 60, 'gun': 100}}
        if lato == 'blue':
            n_ch = (k % 9) + 1
            u['callsign'] = {1: 1, 2: n_ch, 3: 1, 'name': '%s%d1' % (NOMI_CHIAMATA_TESTO[1], n_ch)}
            u['onboard_num'] = '%03d' % (100 + k)
        else:
            u['callsign'] = 100 + k
            u['onboard_num'] = '%02d' % (10 + k)
        g = {'name': '%s %s' % (breve, nome), 'groupId': gid, 'task': 'Nothing', 'taskSelected': True, 'x': x, 'y': y,
             'start_time': 0, 'hidden': False, 'uncontrolled': False, 'uncontrollable': False, 'communication': True,
             'frequency': 251 if lato == 'blue' else 124, 'modulation': 0, 'radioSet': False, 'tasks': {},
             'units': {1: u},
             'route': {'points': {1: wpt(x, y, alt, vel, ETA_locked=True), 2: wpt(x + 20000, y, alt, vel)}}}
        cat = 'helicopter' if eli else 'plane'
        gr = paesi[lato][cat]['group']
        gr[len(gr) + 1] = g
        righe.append('%-5s %-28s %s' % (lato, g['name'], '; '.join('%s=%s' % (n, v[:30])
                                                               for n, v in carichi.nomi_armi(tipo, nome).items())
                                        if nome != 'nessuno' else '-'))
        gid += 1
        uid += 1
    diz = {'DictKey_descriptionText_1': BRIEFING, 'DictKey_descriptionRedTask_2': BRIEFING,
           'DictKey_descriptionBlueTask_3': BRIEFING, 'DictKey_descriptionNeutralsTask_4': '',
           'DictKey_sortie_5': 'C00 - Prova dei carichi'}
    m['descriptionText'] = 'DictKey_descriptionText_1'
    m['descriptionRedTask'] = 'DictKey_descriptionRedTask_2'
    m['descriptionBlueTask'] = 'DictKey_descriptionBlueTask_3'
    m['descriptionNeutralsTask'] = 'DictKey_descriptionNeutralsTask_4'
    m['sortie'] = 'DictKey_sortie_5'
    m['maxDictId'] = 5
    m['forcedOptions'] = {'optionsView': 'optview_all', 'labels': 1}
    errori = verifica_miz.verifica(m)
    if errori:
        raise SystemExit('missione non valida:\n' + '\n'.join(errori))
    out = os.path.join(RADICE, 'missioni', NOME + '.miz')
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mission', lt.dump('mission', m))
        z.writestr('warehouses', lt.dump('warehouses', w))
        z.writestr('options', lt.dump('options', o))
        z.writestr('theatre', 'Syria')
        z.writestr('l10n/DEFAULT/dictionary', lt.dump('dictionary', diz))
        z.writestr('l10n/DEFAULT/mapResource', lt.dump('mapResource', {}))
    print('scritto', out, '-', gid - 1, 'gruppi')
    print('\n'.join(righe))


if __name__ == '__main__':
    costruisci()
