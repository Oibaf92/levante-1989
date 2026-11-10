"""Costruisce missioni/P00_prova_piazzatore.miz

Missione di prova del piazzatore: le difese aeree siriane della situazione di pace
(siti noti, vedi tools/intel.py), qualche radar di scoperta e artiglieria
contraerea sulle basi, e la batteria I-Hawk dei Marines a Jounieh, piazzati dal
piazzatore sul terreno rilevato. Nessun aereo: si controlla dal Mission Editor
(vista SAT) o in gioco dalla mappa F10.

Uso:  python3 script/costruisci_p00.py
"""
import json
import os
import sys
import zipfile

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
sys.path.insert(0, os.path.join(QUI, 'tools'))

import luatable as lt  # noqa: E402
from geo import ll_to_xy, xy_to_ll  # noqa: E402
import intel  # noqa: E402
import piazzatore as pz  # noqa: E402

NOME = 'P00_prova_piazzatore'
SIRIA, USA = 47, 2

SETTORI = {'Damasco': (180, 320), 'Homs': (200, 330), 'Hama': (220, 340), 'Aleppo': (230, 360),
           'Latakia': (200, 340), 'Tartus': (190, 330), 'Bekaa': (190, 320), 'Golan': (170, 300),
           'Dumayr': (180, 330), 'Mezzeh': (180, 320)}
RAGGI = {'sa5': 12, 'sa6': 10, 'sa8': 8, 'aaa': 3, 'ewr': 15}


def intenzioni():
    out = []
    for lat, lon, _, tipo, nome in intel.SAM_ROSSI:
        chiave = next((k for k in SETTORI if k in nome), 'Damasco')
        out.append(pz.Intenzione(tipo, nome, (lat, lon), RAGGI.get(tipo, 6), SETTORI[chiave]))
    # radar di scoperta: alture dietro la costa e sull'Antilibano
    out.append(pz.Intenzione('ewr', 'EWR costa', (35.15, 36.10), 15, (200, 340)))
    out.append(pz.Intenzione('ewr', 'EWR Antilibano', (33.70, 36.35), 15, (180, 320)))
    # artiglieria contraerea attorno alle basi
    for nome, lat, lon, sett in (('AAA Mezzeh', 33.478, 36.224, 'Mezzeh'), ('AAA Al-Dumayr', 33.610, 36.749, 'Dumayr'),
                                 ('AAA Hama', 35.118, 36.712, 'Hama')):
        out.append(pz.Intenzione('aaa', nome, (lat, lon), RAGGI['aaa'], SETTORI[sett], obiettivo=(lat, lon)))
    # Marines a Jounieh
    for lat, lon, _, tipo, nome in intel.SAM_BLU:
        out.append(pz.Intenzione(tipo, nome, (lat, lon), 8, (30, 150), coalizione='blue', paese=USA))
    return out


BRIEFING = """LEVANTE 1989 - P00: PROVA DEL PIAZZATORE

Missione di controllo, senza aerei. Le batterie antiaeree della situazione di pace
sono state piazzate automaticamente sul terreno rilevato (pendenza, edifici,
vegetazione, strade, visibilita' radar).

COSA CONTROLLARE
1. Nel Mission Editor, vista SAT: le batterie devono stare su terreno aperto e
   pianeggiante, non in villaggi, boschi o pendii.
2. In gioco (mappa F10): all'avvio uno script verifica ogni veicolo e sposta di
   qualche metro quelli finiti su un ostacolo.
3. Se una batteria e' piazzata male: segno F10 con scritto SPOSTA vicino a lei
   (entro 5 km). Passa alla posizione alternativa successiva.
4. A fine prova manda stato e registro da Saved Games\\DCS\\Levante1989\\.
"""


def costruisci():
    terreno = pz.Terreno()
    piazzati = pz.piazza_tutti(terreno, intenzioni())
    carica = lambda n: lt.parse(open(os.path.join(QUI, 'base', n), encoding='utf-8').read())[1]  # noqa: E731
    m, w, o = carica('mission'), carica('warehouses'), carica('options')
    m['date'] = {'Year': 1989, 'Month': 10, 'Day': 2}
    m['start_time'] = 10 * 3600
    centro = ll_to_xy(34.2, 36.4)
    m['map'] = {'centerX': centro[0], 'centerY': centro[1], 'zoom': 500000}

    # paesi
    rossi = m['coalition']['red']['country']
    if not any(c['id'] == SIRIA for c in rossi.values()):
        rossi[len(rossi) + 1] = {'id': SIRIA, 'name': 'Syria'}
    paese_rosso = next(c for c in rossi.values() if c['id'] == SIRIA)
    paese_blu = next(c for c in m['coalition']['blue']['country'].values() if c['id'] == USA)
    paese_rosso['vehicle'] = {'group': {}}
    paese_blu['vehicle'] = {'group': {}}

    tabella_lua = {}
    gid, uid = 100, 1000
    righe = []
    for p in piazzati:
        dest = paese_blu if p.intenzione.coalizione == 'blue' else paese_rosso
        g = pz.gruppo_me(p, gid, uid, terreno)
        dest['vehicle']['group'][len(dest['vehicle']['group']) + 1] = g
        gid += 1
        uid += len(p.unita)
        cfg = pz.SISTEMI[p.intenzione.sistema]
        tabella_lua[p.intenzione.nome] = {
            'paese': p.intenzione.paese, 'abilita': p.intenzione.abilita, 'attuale': 1,
            'unita': {k: {'tipo': t, 'avanti': float(a), 'destra': float(dx), 'rotta': float(r)}
                      for k, (t, a, dx, r) in enumerate(pz.schema(cfg, p.intenzione.coalizione), 1)},
            'posizioni': {k: {'x': x, 'y': y, 'rotta': float(rt)}
                          for k, (x, y, rt) in enumerate([(p.x, p.y, p.rotta)] + p.alternative, 1)},
        }
        righe.append(pz.descrivi(p))

    diz = {'DictKey_descriptionText_1': BRIEFING, 'DictKey_descriptionRedTask_2': '', 'DictKey_descriptionBlueTask_3': '',
           'DictKey_descriptionNeutralsTask_4': '', 'DictKey_sortie_5': 'P00 - Prova del piazzatore'}
    m['descriptionText'] = 'DictKey_descriptionText_1'
    m['descriptionRedTask'] = 'DictKey_descriptionRedTask_2'
    m['descriptionBlueTask'] = 'DictKey_descriptionBlueTask_3'
    m['descriptionNeutralsTask'] = 'DictKey_descriptionNeutralsTask_4'
    m['sortie'] = 'DictKey_sortie_5'
    m['maxDictId'] = 5
    init = 'LEVANTE = { missione = "%s" }\n' % NOME + lt.dump('LEVANTE_PIAZZAMENTI', tabella_lua)
    risorse = {'ResKey_Action_1': 'p00_init.lua', 'ResKey_Action_2': 'levante_core.lua',
               'ResKey_Action_3': 'levante_piazzatore.lua'}
    for i, (commento, chiave) in enumerate((('INIT', 'ResKey_Action_1'), ('NUCLEO', 'ResKey_Action_2'),
                                            ('PIAZZATORE', 'ResKey_Action_3')), 1):
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
        z.writestr('l10n/DEFAULT/p00_init.lua', init)
        z.write(os.path.join(QUI, 'lua', 'levante_core.lua'), 'l10n/DEFAULT/levante_core.lua')
        z.write(os.path.join(QUI, 'lua', 'levante_piazzatore.lua'), 'l10n/DEFAULT/levante_piazzatore.lua')
    # registro dei piazzamenti
    reg = [{'nome': p.intenzione.nome, 'sistema': p.intenzione.sistema, 'lat_lon': [round(v, 5) for v in xy_to_ll(p.x, p.y)],
            'rotta': p.rotta, 'dettagli': p.dettagli,
            'alternative': [[round(v, 5) for v in xy_to_ll(a[0], a[1])] for a in p.alternative]} for p in piazzati]
    json.dump(reg, open(os.path.join(RADICE, 'campagna', 'terreno', 'piazzamenti_P00.json'), 'w'), indent=1, ensure_ascii=False)
    print('scritto', out)
    print('\n'.join(righe))
    return piazzati


if __name__ == '__main__':
    costruisci()
