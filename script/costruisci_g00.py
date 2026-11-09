"""Costruisce missioni/G00_ambientamento.miz

Volo di ambientamento: F-14A dalla CVN-71 Theodore Roosevelt, bombardamento
sul poligono NATO di Ceyhan (Turchia meridionale) e appontaggio.

Uso:  python3 script/costruisci_g00.py
"""
import copy
import math
import os
import sys
import zipfile

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
sys.path.insert(0, os.path.join(QUI, 'tools'))

import luatable as lt  # noqa: E402
from geo import ll_to_xy, xy_to_ll, dms  # noqa: E402
import kneeboard_g00  # noqa: E402
import confini  # noqa: E402
import intel  # noqa: E402

NOME = 'G00_ambientamento'
FT = 0.3048
KT = 0.514444


def carica(nome):
    return lt.parse(open(os.path.join(QUI, 'base', nome), encoding='utf-8').read())[1]


def sposta(x, y, rotta, dist):
    r = math.radians(rotta)
    return x + dist * math.cos(r), y + dist * math.sin(r)


# ---------------------------------------------------------------------------
# Geometria
# ---------------------------------------------------------------------------
ROTTA_NAVE = 250            # rotta base della portaerei (BRC)
VEL_NAVE = 25 * KT
CVN = ll_to_xy(35.95, 33.70)            # a nord di Cipro, ~200 km dalla costa siriana
CVN_FINE = sposta(*CVN, ROTTA_NAVE, VEL_NAVE * 3 * 3600)      # 3 ore di navigazione

BERS_A = ll_to_xy(36.7917, 35.3724)      # poligono di Ceyhan: campo aperto scelto dalla mappa del Mission Editor
BERS_B = sposta(*BERS_A, 90, 900)
ROTTA_ATTACCO = 40
IP = sposta(*BERS_A, ROTTA_ATTACCO + 180, 15000)
COSTA = ll_to_xy(36.60, 35.25)
USCITA = sposta(*BERS_A, 130, 20000)
MINUTI_RIENTRO = 70
RIENTRO = sposta(*CVN, ROTTA_NAVE, VEL_NAVE * MINUTI_RIENTRO * 60)   # dove sara' la nave al rientro

TACAN = (71, 'X', 'TR', 1158000000)
ICLS = 11
LINK4 = 336000000
ATC = 258.0

PRESET = {
    1: (258.0, 'TR Torre / CATCC'),
    2: (264.0, 'Strike'),
    3: (251.0, 'Poligono Ceyhan'),
    4: (305.0, 'Dodge interno'),
    5: (243.0, 'Guardia'),
}

# ---------------------------------------------------------------------------
# Unita'
# ---------------------------------------------------------------------------
ID_CVN, ID_CG, ID_FFG = 1, 2, 3


def punto(x, y, alt, vel, tipo='Turning Point', azione='Turning Point', nome='', compiti=None, **extra):
    p = {
        'alt': alt, 'alt_type': 'BARO', 'type': tipo, 'action': azione,
        'x': x, 'y': y, 'speed': vel, 'speed_locked': True,
        'ETA': 0, 'ETA_locked': False, 'formation_template': '', 'name': nome,
        'task': {'id': 'ComboTask', 'params': {'tasks': compiti or {}}},
    }
    p.update(extra)
    return p


def azione(n, ident, params):
    return {'enabled': True, 'auto': False, 'id': 'WrappedAction', 'number': n,
            'params': {'action': {'id': ident, 'params': params}}}


def gruppo_navale():
    hdg = math.radians(ROTTA_NAVE)
    compiti = {
        1: azione(1, 'ActivateBeacon', {'type': 4, 'AA': False, 'callsign': TACAN[2], 'modeChannel': TACAN[1],
                                        'channel': TACAN[0], 'system': 3, 'unitId': ID_CVN, 'bearing': True,
                                        'frequency': TACAN[3]}),
        2: azione(2, 'ActivateICLS', {'type': 131584, 'unitId': ID_CVN, 'channel': ICLS}),
        3: azione(3, 'ActivateLink4', {'frequency': LINK4, 'unitId': ID_CVN}),
        4: azione(4, 'ActivateACLS', {'unitId': ID_CVN}),
    }
    p1 = punto(*CVN, 0, VEL_NAVE, compiti=compiti, ETA_locked=True)
    p2 = punto(*CVN_FINE, 0, VEL_NAVE)
    cg = sposta(*CVN, ROTTA_NAVE + 150, 2500)
    ffg = sposta(*CVN, ROTTA_NAVE - 150, 3000)
    return {
        'visible': False, 'tasks': {}, 'uncontrollable': False, 'groupId': 1, 'hidden': False,
        'name': 'CVN-71 Roosevelt', 'x': CVN[0], 'y': CVN[1], 'start_time': 0,
        'units': {
            1: {'modulation': 0, 'skill': 'Average', 'type': 'CVN_71', 'unitId': ID_CVN, 'x': CVN[0], 'y': CVN[1],
                'name': 'CVN-71 Theodore Roosevelt', 'heading': hdg, 'frequency': int(ATC * 1e6)},
            2: {'modulation': 0, 'skill': 'Average', 'type': 'TICONDEROG', 'unitId': ID_CG, 'x': cg[0], 'y': cg[1],
                'name': 'CG-56 San Jacinto', 'heading': hdg, 'frequency': 127500000},
            3: {'modulation': 0, 'skill': 'Average', 'type': 'PERRY', 'unitId': ID_FFG, 'x': ffg[0], 'y': ffg[1],
                'name': 'FFG-49 Robert G. Bradley', 'heading': hdg, 'frequency': 127500000},
        },
        'route': {'points': {1: p1, 2: p2}},
    }


def canali_radio():
    base = {i: 225.0 + i for i in range(1, 31)}
    for k, (f, _) in PRESET.items():
        base[k] = f
    uhf = {i: base[i] for i in range(1, 21)}
    vuhf = {i: base[i] for i in range(1, 31)}
    return {
        1: {'channels': uhf, 'modulations': {}, 'channelsNames': {}},
        2: {'channels': vuhf, 'modulations': {i: 0 for i in vuhf}, 'channelsNames': {}},
    }


CARICO = {
    1: {'CLSID': '{LAU-7 wtip - AIM-9L}'},
    2: {'CLSID': '{SHOULDER AIM-7M}'},
    3: {'CLSID': '{F14-300gal}'},
    4: {'CLSID': '{BRU-32 MK-82}'},
    5: {'CLSID': '{MAK79_BDU33 3L}'},
    6: {'CLSID': '{MAK79_BDU33 3R}'},
    7: {'CLSID': '{BRU-32 MK-82}'},
    8: {'CLSID': '{F14-300gal}'},
    9: {'CLSID': '{SHOULDER AIM-7M}'},
    10: {'CLSID': '{LAU-7 wtip - AIM-9L}'},
}


# Partenza ritardata: a missione avviata la Supercarrier non usa piu' i posti 5-8,
# quindi gli aerei vengono messi piu' indietro sul ponte. Con partenza a t=0 DCS
# ignora il parcheggio scelto e usa il primo posto libero (il 5).
RITARDO_PARTENZA = 5

# Gregario di scorta: carico aria-aria classico del 1989
# (2 AIM-54 sui pallet anteriori, 3 AIM-7, 2 AIM-9)
CARICO_SCORTA = {
    1: {'CLSID': '{LAU-7 wtip - AIM-9L}'},         # stazione 1A
    2: {'CLSID': '{SHOULDER AIM-7M}'},             # 1B
    3: {'CLSID': '{F14-300gal}'},                  # 2
    4: {'CLSID': '{AIM_54A_Mk60}'},                # 3: pallet anteriore sinistro
    5: {'CLSID': '{BELLY AIM-7M}'},                # 4
    7: {'CLSID': '{AIM_54A_Mk60}'},                # 6: pallet anteriore destro
    8: {'CLSID': '{F14-300gal}'},                  # 7
    9: {'CLSID': '{SHOULDER AIM-7M}'},             # 8B
    10: {'CLSID': '{LAU-7 wtip - AIM-9L}'},        # 8A
}


def gruppo_f14(gid, uid, nome_gruppo, numero, caldo, parcheggio, uid_gregario, parcheggio_gregario):
    tipo_dec = 'TakeOffParkingHot' if caldo else 'TakeOffParking'
    az_dec = 'From Parking Area Hot' if caldo else 'From Parking Area'
    v_cr, v_att = 350 * KT, 420 * KT
    punti = {
        1: punto(*CVN, 0, 0, tipo=tipo_dec, azione=az_dec, linkUnit=ID_CVN, helipadId=ID_CVN,
                 ETA=RITARDO_PARTENZA, ETA_locked=True),
        2: punto(*COSTA, 15000 * FT, v_cr, nome='COSTA'),
        3: punto(*IP, 15000 * FT, v_cr, nome='IP'),
        4: punto(*BERS_A, 12000 * FT, v_att, nome='ST'),
        5: punto(*USCITA, 15000 * FT, v_cr, nome='USCITA'),
        6: punto(*RIENTRO, 3000 * FT, 300 * KT, nome='RIENTRO'),
        7: punto(*RIENTRO, 0, 150 * KT, tipo='Land', azione='Landing', linkUnit=ID_CVN, helipadId=ID_CVN),
    }
    callsign = {1: 5, 2: numero, 3: 1, 'name': 'Dodge%d1' % numero}
    unita = {
        'alt': 0, 'alt_type': 'BARO', 'livery_id': 'vf-84 elvis by reflected', 'skill': 'Client',
        'parking': parcheggio, 'parking_id': str(parcheggio), 'speed': 0,
        'AddPropAircraft': {'M61BURST': 2, 'IlsChannel': ICLS, 'KY28Key': 1, 'TacanBand': 0,
                            'INSAlignmentStored': True, 'RefuelingProbeCoverRemoved': False, 'TCS': 0,
                            'TacanChannel': TACAN[0], 'ALE39Loadout': 3},
        'type': 'F-14A-135-GR-Early', 'Radio': canali_radio(), 'unitId': uid,
        'psi': -math.radians(ROTTA_NAVE), 'heading': math.radians(ROTTA_NAVE),
        'onboard_num': '2%02d' % numero, 'DTC': {}, 'x': CVN[0], 'y': CVN[1],
        'name': 'Dodge %d-1' % numero, 'callsign': callsign,
        'payload': {'pylons': copy.deepcopy(CARICO), 'fuel': 7348, 'flare': 60, 'ammo_type': 1, 'chaff': 140, 'gun': 100},
    }
    gregario = copy.deepcopy(unita)
    gregario.update({
        'skill': 'High', 'unitId': uid_gregario, 'name': 'Dodge %d-2' % numero,
        'parking': parcheggio_gregario, 'parking_id': str(parcheggio_gregario),
        'onboard_num': '2%02d' % (numero + 10),
        'callsign': {1: 5, 2: numero, 3: 2, 'name': 'Dodge%d2' % numero},
        'payload': {'pylons': copy.deepcopy(CARICO_SCORTA), 'fuel': 7348, 'flare': 60, 'ammo_type': 1, 'chaff': 140, 'gun': 100},
    })
    return {
        'dynSpawnTemplate': False, 'modulation': 0, 'tasks': {}, 'DTC': {}, 'radioSet': True, 'task': 'CAP',
        'uncontrolled': False, 'taskSelected': True, 'groupId': gid, 'hidden': False,
        'NavTargetPoints': {
            1: {'x': COSTA[0], 'y': COSTA[1], 'index': 1, 'text_comment': 'FP'},
            2: {'x': IP[0], 'y': IP[1], 'index': 2, 'text_comment': 'IP'},
            3: {'x': BERS_A[0], 'y': BERS_A[1], 'index': 3, 'text_comment': 'ST'},
        },
        'x': CVN[0], 'y': CVN[1], 'name': nome_gruppo, 'communication': True, 'start_time': RITARDO_PARTENZA,
        'uncontrollable': False, 'frequency': PRESET[4][0],
        'units': {1: unita, 2: gregario}, 'route': {'points': punti},
    }


# Parcheggi sulla portaerei (Supercarrier: 1-4 sono le catapulte). Con la partenza a
# t=0 DCS non li rispetta: vedi RITARDO_PARTENZA. Il giocatore parte dal 10 (secondo elevatore, vicino all'isola) in entrambi gli slot:
# in giocatore singolo solo lo slot scelto viene creato. I gregari hanno posti propri;
# lo script G00 elimina all'avvio il gregario dello slot non scelto.
PARCHEGGIO_GIOCATORE = 10
PARCHEGGIO_GREGARIO_FREDDO = 11
PARCHEGGIO_GREGARIO_CALDO = 12

# Aerei statici sul ponte. Posizioni relative alla nave (m): x verso prua,
# y verso dritta (lato dell'isola); angolo relativo alla prua (radianti).
# Disposizione ripresa dalla missione "Siria 1989" del giocatore.
STATICI_PONTE = [
    ('A6E', 'va65-502-1991', -12.166, 31.611, 4.688),
    ('A6E', 'va65-511-1991', -135.927, 25.447, 5.823),
    ('A6E', 'va65-500-1991', -0.429, 30.808, 4.688),
    ('F-14A-135-GR-Early', 'vf-84 ghost by reflected', -90.178, 34.577, 4.671),
    ('F-14A-135-GR-Early', 'vf-41 aj100 1989 by reflected', 10.724, 34.830, 4.671),
    ('S-3B', 'VS-24 AJ', -116.186, 28.357, 4.636),
    ('S-3B', 'VS-24 AJ', -125.950, 27.297, 5.404),
]


def statici_ponte():
    h = math.radians(ROTTA_NAVE)
    gruppi = {}
    for i, (tipo, livrea, ox, oy, ang) in enumerate(STATICI_PONTE, 1):
        x = CVN[0] + ox * math.cos(h) - oy * math.sin(h)
        y = CVN[1] + ox * math.sin(h) + oy * math.cos(h)
        hdg = (h + ang) % (2 * math.pi)
        nome = 'Ponte %d %s' % (i, {'A6E': 'A-6E', 'F-14A-135-GR-Early': 'F-14A', 'S-3B': 'S-3B'}[tipo])
        gruppi[i] = {
            'heading': hdg, 'groupId': 10 + i, 'x': x, 'y': y, 'name': nome,
            'linkOffset': True, 'dead': False,
            'units': {1: {'tasks': {}, 'livery_id': livrea, 'category': 'Planes',
                          'offsets': {'x': ox, 'y': oy, 'angle': ang}, 'type': tipo,
                          'unitId': 10 + i, 'rate': 50, 'x': x, 'y': y, 'name': nome, 'heading': hdg}},
            'route': {'points': {1: {'alt': 0, 'type': '', 'action': '', 'linkUnit': ID_CVN, 'x': x, 'y': y,
                                     'formation_template': '', 'name': '', 'speed': 0}}},
        }
    return gruppi


# ---------------------------------------------------------------------------
# Testi
# ---------------------------------------------------------------------------
def ll(p):
    return dms(*xy_to_ll(*p))


BRIEFING = """FUOCO SUL LEVANTE - GIORNO 0: AMBIENTAMENTO
2 ottobre 1989, ore 07:30 locali. Mediterraneo orientale.

SITUAZIONE
La USS Theodore Roosevelt (CVN-71) e' appena arrivata nel Mediterraneo orientale. La crisi in Libano peggiora, ma per ora non ci sono ostilita'. Prima che le cose si complichino, il CAG vuole che ogni equipaggio voli una sortita di qualificazione sul poligono NATO di Ceyhan, concesso dall'aeronautica turca.

MISSIONE
Dodge, decollo dalla Roosevelt, trasferimento sul poligono di Ceyhan, passaggi di bombardamento sui due bersagli, rientro e appontaggio.

ESECUZIONE
1. Decollo: Dodge 1-1 parte a freddo, Dodge 2-1 e' gia' in moto (scegli lo slot). Il tuo gregario (Dodge x-2) parte come te e ti scorta per tutto il volo: comandi radio F1.
2. COSTA (WP1): ingresso a terra a ovest di Karatas, 15.000 ft.
3. IP (WP2): 15 km a sud-ovest del bersaglio. Corsa d'attacco per 040.
4. Bersaglio A (WP3, ST): tre carri in disuso, fumo ARANCIONE. Usa le 2 Mk-82.
5. Bersaglio B: 900 m a est di A, cerchio di fuoristrada, fumo BLU. Usa le 6 BDU-33 da esercitazione.
6. Il poligono comunica distanza e radiale di ogni impatto. Passaggi quanti ne vuoi, nessuna fretta.
7. USCITA (WP4) e RIENTRO (WP5): la nave naviga per 250 a 25 nodi. Appontaggio Case I.

CARICO
Tu: 2 AIM-9L, 2 AIM-7M, 2 serbatoi da 300 gal, 2 Mk-82, 6 BDU-33.
Gregario (scorta): 2 AIM-54A, 3 AIM-7M, 2 AIM-9L, 2 serbatoi da 300 gal.

NOTE
- Nessuna minaccia: il volo e' di addestramento.
- Menu F10 > Levante 1989: informazioni sul poligono e salvataggio manuale dello stato.
- Se il poligono non ti piace (alberi, case, terreno), sulla mappa F10 aggiungi un segno con scritto POLIGONO: i bersagli si spostano li' e la posizione viene ricordata anche nei voli successivi.
- Questa missione serve anche a provare il salvataggio dello stato: a fine volo carica i file da Saved Games\\DCS\\Levante1989\\.
"""

COMPITO_BLU = """Volo di qualificazione: bombardamento sul poligono di Ceyhan e appontaggio sulla Roosevelt.

TACAN CVN-71: {tacan}   ICLS: canale {icls}   Link 4: {link4:.1f} MHz   ACLS attivo
Torre / CATCC: {atc:.3f} MHz (preset 1)
Poligono Ceyhan: preset 3   Interno Dodge: preset 4

Bersaglio A: {la}
Bersaglio B: {lb}
""".format(tacan='%d%s "%s"' % TACAN[:3], icls=ICLS, link4=LINK4 / 1e6, atc=ATC, la=ll(BERS_A), lb=ll(BERS_B))


# ---------------------------------------------------------------------------
# Missione
# ---------------------------------------------------------------------------
def costruisci():
    m = carica('mission')
    w = carica('warehouses')
    o = carica('options')

    m['date'] = {'Year': 1989, 'Month': 10, 'Day': 2}
    m['start_time'] = 7 * 3600 + 30 * 60
    m['weather'].update({
        'name': 'Levante - sereno', 'enable_fog': False, 'enable_dust': False, 'dust_density': 0,
        'season': {'temperature': 24}, 'qnh': 762, 'groundTurbulence': 0, 'type_weather': 0,
        'visibility': {'distance': 80000}, 'fog': {'visibility': 0, 'thickness': 0},
        'wind': {'atGround': {'speed': 3, 'dir': 70}, 'at2000': {'speed': 5, 'dir': 80}, 'at8000': {'speed': 10, 'dir': 90}},
        'clouds': {'thickness': 200, 'density': 0, 'base': 3000, 'iprecptns': 0},
    })
    m['map'] = {'centerX': (CVN[0] + BERS_A[0]) / 2, 'centerY': (CVN[1] + BERS_A[1]) / 2, 'zoom': 200000}

    blu = m['coalition']['blue']
    blu['bullseye'] = {'x': BERS_A[0], 'y': BERS_A[1]}
    usa = next(c for c in blu['country'].values() if c['name'] == 'USA')
    usa['ship'] = {'group': {1: gruppo_navale()}}
    usa['plane'] = {'group': {
        1: gruppo_f14(2, 4, 'Dodge 1 (avvio a freddo)', 1, False, PARCHEGGIO_GIOCATORE, 6, PARCHEGGIO_GREGARIO_FREDDO),
        2: gruppo_f14(3, 5, 'Dodge 2 (motori accesi)', 2, True, PARCHEGGIO_GIOCATORE, 7, PARCHEGGIO_GREGARIO_CALDO),
    }}
    usa['static'] = {'group': statici_ponte()}

    # confini e fazioni sulla mappa (strato Common)
    confini.aggiungi(m)
    # quadro di intelligence di partenza (strati Blue e Red)
    intel.aggiungi(m)

    # magazzini delle navi (uno per unita')
    modello = w['warehouses'][0]
    w['warehouses'] = {}
    for uid in (ID_CVN, ID_CG, ID_FFG):
        mag = copy.deepcopy(modello)
        mag['coalition'] = 'blue'
        w['warehouses'][uid] = mag

    # testi
    diz = {
        'DictKey_descriptionText_1': BRIEFING,
        'DictKey_descriptionRedTask_2': 'Nessun compito: missione di addestramento del blu.',
        'DictKey_descriptionBlueTask_3': COMPITO_BLU,
        'DictKey_descriptionNeutralsTask_4': '',
        'DictKey_sortie_5': 'G00 - Ambientamento',
    }
    m['descriptionText'] = 'DictKey_descriptionText_1'
    m['descriptionRedTask'] = 'DictKey_descriptionRedTask_2'
    m['descriptionBlueTask'] = 'DictKey_descriptionBlueTask_3'
    m['descriptionNeutralsTask'] = 'DictKey_descriptionNeutralsTask_4'
    m['sortie'] = 'DictKey_sortie_5'
    m['maxDictId'] = 5

    # script all'avvio
    init = ('LEVANTE = { missione = "%s", poligono = { x = %.1f, y = %.1f } }' % (NOME, BERS_A[0], BERS_A[1]))
    risorse = {
        'ResKey_Action_1': 'Moose.lua',
        'ResKey_Action_2': 'levante_core.lua',
        'ResKey_Action_3': 'G00_ambientamento.lua',
        'ResKey_ImageBriefing_1': 'briefing_g00.png',
    }
    risorse['ResKey_Action_4'] = 'levante_init.lua'
    azioni = [
        ('INIT', 'a_do_script_file(getValueResourceByKey("ResKey_Action_4"));',
         {'predicate': 'a_do_script_file', 'file': 'ResKey_Action_4'}),
        ('MOOSE', 'a_do_script_file(getValueResourceByKey("ResKey_Action_1"));', {'predicate': 'a_do_script_file', 'file': 'ResKey_Action_1'}),
        ('NUCLEO', 'a_do_script_file(getValueResourceByKey("ResKey_Action_2"));', {'predicate': 'a_do_script_file', 'file': 'ResKey_Action_2'}),
        ('G00', 'a_do_script_file(getValueResourceByKey("ResKey_Action_3"));', {'predicate': 'a_do_script_file', 'file': 'ResKey_Action_3'}),
    ]
    for i, (commento, codice, regola) in enumerate(azioni, 1):
        m['trig']['actions'][i] = codice
        m['trig']['conditions'][i] = 'return(true)'
        m['trig']['flag'][i] = True
        m['trig']['funcStartup'][i] = 'if mission.trig.conditions[%d]() then mission.trig.actions[%d]() end' % (i, i)
        m['trigrules'][i] = {'rules': {}, 'comment': commento, 'eventlist': '', 'predicate': 'triggerStart',
                             'actions': {1: regola}}
    m['pictureFileNameB'] = {1: 'ResKey_ImageBriefing_1'}

    # tavolette (kneeboard)
    os.makedirs(os.path.join(RADICE, 'missioni'), exist_ok=True)
    pagine = kneeboard_g00.crea(dict(
        cvn=CVN, rotta_nave=ROTTA_NAVE, bers_a=BERS_A, bers_b=BERS_B, ip=IP, costa=COSTA, uscita=USCITA,
        rientro=RIENTRO, minuti_rientro=MINUTI_RIENTRO, tacan=TACAN, icls=ICLS, link4=LINK4, preset=PRESET, rotta_attacco=ROTTA_ATTACCO))

    out = os.path.join(RADICE, 'missioni', NOME + '.miz')
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mission', lt.dump('mission', m))
        z.writestr('warehouses', lt.dump('warehouses', w))
        z.writestr('options', lt.dump('options', o))
        z.writestr('theatre', 'Syria')
        z.writestr('l10n/DEFAULT/dictionary', lt.dump('dictionary', diz))
        z.writestr('l10n/DEFAULT/mapResource', lt.dump('mapResource', risorse))
        z.write(os.path.join(QUI, 'lib', 'Moose.lua'), 'l10n/DEFAULT/Moose.lua')
        z.write(os.path.join(QUI, 'lua', 'levante_core.lua'), 'l10n/DEFAULT/levante_core.lua')
        z.write(os.path.join(QUI, 'lua', 'G00_ambientamento.lua'), 'l10n/DEFAULT/G00_ambientamento.lua')
        z.writestr('l10n/DEFAULT/levante_init.lua', init + '\n')
        z.writestr('l10n/DEFAULT/briefing_g00.png', pagine[0])
        for i, png in enumerate(pagine, 1):
            z.writestr('KNEEBOARD/IMAGES/G00_%02d.png' % i, png)
    for i, png in enumerate(pagine, 1):
        open(os.path.join(RADICE, 'missioni', 'G00_tavoletta_%d.png' % i), 'wb').write(png)
    print('scritto', out)


if __name__ == '__main__':
    costruisci()
