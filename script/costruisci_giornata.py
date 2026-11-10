"""Costruisce la missione di una giornata della campagna dagli ordini dei due comandanti.

Uso:  python3 script/costruisci_giornata.py 15

Legge:
  campagna/G<n>/parametri.json, situazione_pubblica.md
  blu/ordini_G<n>.json, rosso/ordini_G<n>.json
Scrive:
  missioni/G<n>_<data>.miz
  campagna/G<n>/costruzione.json   (resoconto dell'arbitro: piazzamenti, voli, avvisi)

La missione e' pensata per il giocatore BLU: solo il blu ha posti pilotabili, briefing e
tavolette; le unita' rosse non compaiono sulla mappa F10 del giocatore (solo alleati).
"""
import copy
import json
import math
import os
import sys
import zipfile

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
sys.path.insert(0, os.path.join(QUI, 'tools'))

import luatable as lt  # noqa: E402
from geo import ll_to_xy, xy_to_ll, dms, dist_brg  # noqa: E402
import piazzatore as pz  # noqa: E402
import carichi  # noqa: E402
import confini  # noqa: E402
import intel  # noqa: E402
import legenda  # noqa: E402  (usata da confini)

USA, SIRIA, RUSSIA = 2, 47, 0
KT = 0.514444
FT = 0.3048

AEROPORTI = {a['nome']: a for a in json.load(open(os.path.join(QUI, 'dati', 'aeroporti_syria.json'), encoding='utf-8'))}
ALIAS_BASI = {'Damasco': 'Damascus', 'Tiyas (T4)': 'Tiyas', 'T4': 'Tiyas', 'Latakia': 'Bassel Al-Assad'}

# velivoli: (categoria, velocita' di crociera m/s, quota di crociera m, abilita' AI)
PROFILO = {
    'F-14A-135-GR-Early': ('plane', 230, 7600), 'FA-18C_hornet': ('plane', 230, 7600), 'A6E': ('plane', 210, 6100),
    'F-4E-45MC': ('plane', 230, 7000), 'AV8BNA': ('plane', 200, 4500), 'E-2C': ('plane', 150, 7600),
    'S-3B Tanker': ('plane', 170, 6100), 'KC135MPRS': ('plane', 200, 7600), 'E-3A': ('plane', 200, 9000),
    'MiG-29 Fulcrum': ('plane', 230, 7000), 'MiG-23MLD': ('plane', 230, 7000), 'MiG-21Bis': ('plane', 220, 6000),
    'MiG-25PD': ('plane', 260, 10000), 'Su-17M4': ('plane', 220, 3000), 'Su-24M': ('plane', 230, 2000),
    'Su-25': ('plane', 190, 2500), 'Tu-22M3': ('plane', 250, 9000), 'A-50': ('plane', 180, 9000),
    'AH-64D_BLK_II': ('helicopter', 55, 150), 'CH-47Fbl1': ('helicopter', 60, 200),
    'Mi-24V': ('helicopter', 60, 150), 'Mi-8MT': ('helicopter', 55, 200),
}
COMPITO_DCS = {'CAP': 'CAP', 'GCI': 'Intercept', 'SCORTA': 'Escort', 'STRIKE': 'Ground Attack', 'CAS': 'CAS',
               'SEAD': 'SEAD', 'ANTINAVE': 'Antiship Strike', 'AWACS': 'AWACS', 'TANKER': 'Refueling',
               'TRASPORTO': 'Transport'}
NOMI_CHIAMATA = {'CAP': 1, 'GCI': 1, 'SCORTA': 4, 'STRIKE': 5, 'CAS': 6, 'SEAD': 7, 'ANTINAVE': 5,
                 'TRASPORTO': 8, 'AWACS': 1, 'TANKER': 1}
NOMI_CHIAMATA_TESTO = {1: 'Enfield', 2: 'Springfield', 3: 'Uzi', 4: 'Colt', 5: 'Dodge', 6: 'Ford', 7: 'Chevy', 8: 'Pontiac'}
# AWACS e cisterne hanno liste proprie (l'indice 1 e' Overlord / Texaco)
NOMI_CHIAMATA_SPECIALI = {'AWACS': {1: 'Overlord', 2: 'Magic', 3: 'Wizard', 4: 'Focus', 5: 'Darkstar'},
                          'TANKER': {1: 'Texaco', 2: 'Arco', 3: 'Shell'}}
# Paesi con nominativi numerici nel Mission Editor (gli altri, Siria compresa, usano nome+numeri:
# un numero dove l'editor si aspetta una tabella blocca il caricamento della missione)
PAESI_NOMINATIVO_NUMERICO = {0}          # Russia

# media intensita': batterie SAM nemiche che possono coprire l'obiettivo di un volo del giocatore
SAM_PERICOLOSI = ('sa2', 'sa3', 'sa6', 'sa8', 'hawk')
MAX_SAM_SU_OBIETTIVO = 3

# livello dell'IA in base al logoramento (frazione persa): sotto la soglia -> livello
LOGORAMENTO_ABILITA = ((0.20, 'High'), (0.40, 'Good'), (9.99, 'Average'))

# Piano radio blu (MHz, UHF AM). I canali preimpostati del giocatore sono in Costruttore.canali().
RADIO_BLU = {'guardia': 243.0, 'pacchetto': 251.0, 'cvn': 258.0, 'lha': 256.0, 'incirlik': 360.1,
             'awacs': 264.0, 'cisterna': 270.0, 'interno': 301.0}
RADIO_RIEMPI = 225.0            # canali liberi: 225 + numero del canale
# Modelli delle radio dei moduli: {radio: (numero di canali, tabella 'modulations' presente)}.
# Solo strutture viste in missioni salvate dal Mission Editor (G00 per l'F-14).
RADIO_MODELLI = {'F-14A-135-GR-Early': {1: (20, False), 2: (30, True)},
                 'F-14B': {1: (20, False), 2: (30, True)}}

# tipi di partenza del giocatore -> (tipo, azione) del primo punto di rotta
PARTENZE = {'freddo': ('TakeOffParking', 'From Parking Area'), 'caldo': ('TakeOffParkingHot', 'From Parking Area Hot'),
            'pista': ('TakeOff', 'From Runway')}

# Bilancio delle unita' per il PC del giocatore (i7-7700K 4 core / 8 thread, 64 GB, DCS MT).
# Il collo di bottiglia e' la simulazione (CPU), non la grafica: vedi docs/lezioni.md.
BILANCIO = {'unita_totali': 300, 'unita_terra': 220, 'aerei_in_volo': 28, 'terra_vicino_giocatore': 120, 'navi': 12}

# posizione delle navi
CVN_POS = (35.75, 33.95)     # a nord di Cipro, ~160 km dalla Siria; a ovest c'e' mare aperto per la tratta contro vento
CVN_SCARTO = 9          # ponte angolato: il vento deve arrivare ~9 gradi a sinistra della prua
LHA_POS = (34.05, 35.45)
TARTUS_FLOTTA = (34.912, 35.840)
INGRESSO_EST = (34.60, 40.80)        # da dove arrivano i velivoli "aria" rossi

# siti fissi persi prima del G15 (verita' dell'arbitro)
SITI_DISTRUTTI = {'SA-2 Damasco nord', 'SA-2 Latakia', 'SA-3 Damasco ovest', 'SA-3 Tartus'}

TESTA_DI_PONTE = [(34.15, 35.645), (34.12, 35.80), (34.00, 35.88), (33.88, 35.76), (33.81, 35.66),
                  (33.81, 35.60), (33.83, 35.55), (33.88, 35.50), (33.95, 35.57), (33.98, 35.61), (34.06, 35.63)]
LINEA_FRONTE = [(33.88, 35.50), (33.83, 35.55), (33.81, 35.60), (33.81, 35.66), (33.88, 35.76),
                (34.00, 35.88), (34.12, 35.80), (34.15, 35.645)]


# ---------------------------------------------------------------------------
class Contatori:
    def __init__(self):
        self.gruppo = 1
        self.unita = 1

    def g(self):
        self.gruppo += 1
        return self.gruppo - 1

    def u(self):
        self.unita += 1
        return self.unita - 1


def hm(s):
    h, m = s.split(':')
    return int(h) * 3600 + int(m) * 60


def wpt(x, y, alt, vel, tipo='Turning Point', azione='Turning Point', compiti=None, nome='', alt_tipo='BARO', **extra):
    p = {'alt': alt, 'alt_type': alt_tipo, 'type': tipo, 'action': azione, 'x': x, 'y': y, 'speed': vel,
         'speed_locked': True, 'ETA': 0, 'ETA_locked': False, 'formation_template': '', 'name': nome,
         'task': {'id': 'ComboTask', 'params': {'tasks': compiti or {}}}}
    p.update(extra)
    return p


def compiti_combo(lista):
    out = {}
    for k, t in enumerate(lista, 1):
        t = dict(t)
        t.setdefault('enabled', True)
        t.setdefault('auto', False)
        t['number'] = k
        out[k] = t
    return out


def t_orbita(alt, vel, durata_s=None, schema='Race-Track'):
    orbita = {'id': 'Orbit', 'params': {'altitude': alt, 'pattern': schema, 'speed': vel}}
    if durata_s:
        return {'id': 'ControlledTask', 'params': {'task': orbita, 'stopCondition': {'duration': durata_s}}}
    return orbita


def t_ingaggia(tipi, dist=60000):
    return {'id': 'EngageTargets', 'params': {'targetTypes': {k: v for k, v in enumerate(tipi, 1)}, 'priority': 0,
                                              'maxDistEnabled': True, 'maxDist': dist}}


def t_ingaggia_zona(x, y, r, tipi):
    return {'id': 'EngageTargetsInZone', 'params': {'x': x, 'y': y, 'zoneRadius': r, 'priority': 0,
                                                    'targetTypes': {k: v for k, v in enumerate(tipi, 1)}}}


def t_bombardamento(x, y, alt):
    return {'id': 'Bombing', 'params': {'x': x, 'y': y, 'attackQty': 1, 'expend': 'All', 'groupAttack': True,
                                        'weaponType': 1073741822, 'altitude': alt, 'altitudeEnabled': False,
                                        'attackQtyLimit': False, 'directionEnabled': False}}


def t_azione(ident, params):
    return {'id': 'WrappedAction', 'params': {'action': {'id': ident, 'params': params}}}


# ---------------------------------------------------------------------------
class Costruttore:
    def __init__(self, giorno):
        self.giorno = giorno
        self.cartella = os.path.join(RADICE, 'campagna', 'G%02d' % giorno)
        self.par = json.load(open(os.path.join(self.cartella, 'parametri.json'), encoding='utf-8'))
        self.ordini = {lato: json.load(open(os.path.join(RADICE, d, 'ordini_G%02d.json' % giorno), encoding='utf-8'))
                       for lato, d in (('blue', 'blu'), ('red', 'rosso'))}
        self.cnt = Contatori()
        self.avvisi = []
        self.resoconto = {'piazzamenti': [], 'voli': [], 'avvisi': self.avvisi}
        self.t0 = hm(self.par['inizio'])
        carica = lambda n: lt.parse(open(os.path.join(QUI, 'base', n), encoding='utf-8').read())[1]  # noqa: E731
        self.m, self.w, self.o = carica('mission'), carica('warehouses'), carica('options')
        self.terreno = pz.Terreno()
        self.gruppi_aerei = {}            # nome missione -> (lato, gruppo)
        self.decolli_nave = {}
        self.piano_radio = []             # (MHz, nome volo, ruolo)
        self.conta_speciali = {}          # AWACS/TANKER -> ultimo nome usato
        self.numeri_chiamata = {}         # (paese, nome) -> ultimo numero di gruppo (1-9)
        self._rinomina_doppi()
        self.navi = {}

    def _rinomina_doppi(self):
        """Nomi uguali tra le due parti (DCS vuole nomi unici): aggiunge una sigla di parte."""
        nomi = {}
        for lato, ordini in self.ordini.items():
            for voce in ordini.get('missioni_aeree', []) + ordini.get('unita_terra', []):
                nomi.setdefault(voce['nome'], set()).add(lato)
        doppi = {n for n, lati in nomi.items() if len(lati) > 1}
        for lato, ordini in self.ordini.items():
            sigla = ' (USA)' if lato == 'blue' else ' (SY)'
            for voce in ordini.get('missioni_aeree', []) + ordini.get('unita_terra', []):
                if voce['nome'] in doppi:
                    self.avvisi.append('nome %r usato da entrambe le parti: diventa %r' % (voce['nome'], voce['nome'] + sigla))
                    voce['nome'] += sigla
            for voce in ordini.get('missioni_aeree', []):
                if voce.get('scorta_di') in doppi:
                    voce['scorta_di'] += sigla

    # ----------------------------------------------------------------- paesi
    def paese(self, lato, cat, id_paese, nome):
        paesi = self.m['coalition'][lato]['country']
        c = next((c for c in paesi.values() if c['id'] == id_paese), None)
        if c is None:
            c = {'id': id_paese, 'name': nome}
            paesi[len(paesi) + 1] = c
        c.setdefault(cat, {'group': {}})
        return c[cat]['group']

    def aggiungi_gruppo(self, lato, cat, id_paese, nome_paese, g):
        gr = self.paese(lato, cat, id_paese, nome_paese)
        gr[len(gr) + 1] = g

    # ----------------------------------------------------------------- navi
    def prua_contro_vento(self, scarto=0):
        """Prua iniziale stimata contro vento. Nel file di missione wind.dir e' la direzione VERSO
        cui soffia il vento; in volo levante_navi.lua ricalcola comunque la rotta sul vento reale."""
        verso = self.m['weather']['wind']['atGround']['dir']
        return (verso + 180 + scarto) % 360

    def navi_blu(self):
        self.navi_vento = {}
        hdg = math.radians(self.prua_contro_vento(CVN_SCARTO))
        cx, cy = ll_to_xy(*CVN_POS)
        fine = (cx + 20 * KT * 4 * 3600 * math.cos(hdg), cy + 20 * KT * 4 * 3600 * math.sin(hdg))
        ids = [self.cnt.u() for _ in range(4)]
        tacan = t_azione('ActivateBeacon', {'type': 4, 'AA': False, 'callsign': 'TR', 'modeChannel': 'X', 'channel': 71,
                                            'system': 3, 'unitId': ids[0], 'bearing': True, 'frequency': 1158000000})
        icls = t_azione('ActivateICLS', {'type': 131584, 'unitId': ids[0], 'channel': 11})
        link4 = t_azione('ActivateLink4', {'frequency': 336000000, 'unitId': ids[0]})
        acls = t_azione('ActivateACLS', {'unitId': ids[0]})
        tipi = [('CVN_71', 'CVN-71 Theodore Roosevelt', 0, 0, 258000000), ('TICONDEROG', 'CG-56 San Jacinto', -2500, 1500, 127500000),
                ('TICONDEROG', 'CG-60 Normandy', 2500, -1500, 127500000), ('PERRY', 'FFG-49 Robert G. Bradley', -3000, -2000, 127500000)]
        unita = {}
        for k, (tipo, nome, a, d, f) in enumerate(tipi):
            ux = cx + a * math.cos(hdg) - d * math.sin(hdg)
            uy = cy + a * math.sin(hdg) + d * math.cos(hdg)
            unita[k + 1] = {'type': tipo, 'name': nome, 'unitId': ids[k], 'x': ux, 'y': uy, 'heading': hdg,
                            'skill': 'Excellent', 'modulation': 0, 'frequency': f}
        g = {'visible': False, 'tasks': {}, 'uncontrollable': False, 'groupId': self.cnt.g(), 'hidden': False,
             'name': 'CVN-71 Roosevelt', 'x': cx, 'y': cy, 'start_time': 0, 'units': unita,
             'route': {'points': {1: wpt(cx, cy, 0, 20 * KT, compiti=compiti_combo([tacan, icls, link4, acls]), ETA_locked=True),
                                  2: wpt(*fine, 0, 20 * KT)}}}
        self.navi_vento['CVN-71 Roosevelt'] = {'vento_ponte_kt': 28, 'min_kt': 12, 'max_kt': 30, 'scarto': CVN_SCARTO,
                                               'tratta_nm': 80, 'comandi': {k: c['params']['action'] for k, c in enumerate((tacan, icls, link4, acls), 1)}}
        self.aggiungi_gruppo('blue', 'ship', USA, 'USA', g)
        self.navi['CVN-71'] = (ids[0], cx, cy)
        # LHA
        lx, ly = ll_to_xy(*LHA_POS)
        lid = [self.cnt.u(), self.cnt.u()]
        hl = math.radians(self.prua_contro_vento())
        fl = (lx + 15 * KT * 4 * 3600 * math.cos(hl), ly + 15 * KT * 4 * 3600 * math.sin(hl))
        tacan2 = t_azione('ActivateBeacon', {'type': 4, 'AA': False, 'callsign': 'TAR', 'modeChannel': 'X', 'channel': 64,
                                             'system': 3, 'unitId': lid[0], 'bearing': True, 'frequency': 1151000000})
        g2 = {'visible': False, 'tasks': {}, 'uncontrollable': False, 'groupId': self.cnt.g(), 'hidden': False,
              'name': 'LHA-1 Tarawa', 'x': lx, 'y': ly, 'start_time': 0,
              'units': {1: {'type': 'LHA_Tarawa', 'name': 'LHA-1 Tarawa', 'unitId': lid[0], 'x': lx, 'y': ly,
                            'heading': hl, 'skill': 'Excellent', 'modulation': 0, 'frequency': int(RADIO_BLU['lha'] * 1e6)},
                        2: {'type': 'PERRY', 'name': 'FFG-36 Underwood', 'unitId': lid[1], 'x': lx + 1500, 'y': ly - 1500,
                            'heading': hl, 'skill': 'Excellent', 'modulation': 0, 'frequency': 127500000}},
              'route': {'points': {1: wpt(lx, ly, 0, 15 * KT, compiti=compiti_combo([tacan2]), ETA_locked=True),
                                   2: wpt(*fl, 0, 15 * KT)}}}
        self.navi_vento['LHA-1 Tarawa'] = {'vento_ponte_kt': 25, 'min_kt': 8, 'max_kt': 20, 'scarto': 0,
                                           'tratta_nm': 50, 'comandi': {1: tacan2['params']['action']}}
        self.aggiungi_gruppo('blue', 'ship', USA, 'USA', g2)
        self.navi['LHA-1'] = (lid[0], lx, ly)
        for uid in ids + lid:
            self.w['warehouses'][uid] = copy.deepcopy(self.modello_magazzino)
            self.w['warehouses'][uid]['coalition'] = 'blue'

    def navi_rosse(self):
        tx, ty = ll_to_xy(*TARTUS_FLOTTA)
        unita = {}
        for k, (tipo, nome, dx, dy) in enumerate([('MOSCOW', 'Slava (Tartus)', 0, 0), ('REZKY', 'Krivak II (Tartus)', 500, 400),
                                                  ('MOLNIYA', 'Molniya (Tartus)', -400, 300)], 1):
            unita[k] = {'type': tipo, 'name': nome, 'unitId': self.cnt.u(), 'x': tx + dx, 'y': ty + dy,
                        'heading': math.radians(270), 'skill': self.abilita('red'), 'modulation': 0, 'frequency': 127500000}
        g = {'visible': False, 'tasks': {}, 'uncontrollable': False, 'groupId': self.cnt.g(), 'hidden': False,
             'name': 'Squadra sovietica Tartus', 'x': tx, 'y': ty, 'start_time': 0, 'units': unita,
             'route': {'points': {1: wpt(tx, ty, 0, 0)}}}
        self.aggiungi_gruppo('red', 'ship', RUSSIA, 'Russia', g)

    # ----------------------------------------------------------------- terra
    def intenzioni_terra(self):
        out = []
        for lato, ordini in self.ordini.items():
            for u in ordini.get('unita_terra', []):
                tipo = u['tipo']
                if tipo not in pz.SISTEMI:
                    self.avvisi.append('%s: tipo di unita\' sconosciuto %s, ignorata' % (u.get('nome'), tipo))
                    continue
                obiettivo = u.get('obiettivo') or u['centro']
                if u.get('missione') == 'fuoco' and u.get('bersaglio_fuoco'):
                    obiettivo = u['bersaglio_fuoco']
                it = pz.Intenzione(tipo, u['nome'], tuple(u['centro']), float(u.get('raggio_km', 5)),
                                   tuple(u.get('settore', (0, 360))), tuple(obiettivo),
                                   coalizione=lato, paese=USA if lato == 'blue' else SIRIA,
                                   abilita=self.abilita(lato),
                                   dentro=TESTA_DI_PONTE if lato == 'blue' else None,
                                   fuori=TESTA_DI_PONTE if lato == 'red' else None)
                out.append((it, u))
        # siti fissi rossi ancora attivi e non ripetuti negli ordini
        nomi = {it.nome for it, _ in out}
        for lat, lon, r, tipo, nome in intel.SAM_ROSSI:
            if tipo in ('sa5', 'sa2', 'sa3') and nome not in SITI_DISTRUTTI and nome not in nomi:
                sett = (180, 330)
                it = pz.Intenzione(tipo, nome, (lat, lon), 6 if tipo != 'sa5' else 12, sett, (lat, lon),
                                   coalizione='red', paese=SIRIA, abilita=self.abilita('red'))
                out.append((it, {'missione': 'difesa'}))
        return out

    def forze_terra(self):
        voci = self.intenzioni_terra()
        piazzati = []
        ordine = {'sa5': 0, 'ewr': 1, 'sa2': 2, 'sa3': 3, 'hawk': 3, 'sa6': 4, 'sa8': 5, 'aaa': 6,
                  'artiglieria': 7, 'lanciarazzi': 7, 'carri': 8, 'meccanizzata': 8, 'contraerea_mobile': 9}
        for it in sorted([it for it, _ in voci], key=lambda i: ordine.get(i.sistema, 9)):
            try:
                piazzati.append(pz.piazza(self.terreno, it, piazzati))
            except ValueError as e:
                self.avvisi.append('%s: non piazzata (%s)' % (it.nome, e))
        per_nome = {u_it.nome: ordine for u_it, ordine in voci}
        self.piazzamenti_lua = {}
        for p in piazzati:
            ordine = per_nome[p.intenzione.nome]
            lato = p.intenzione.coalizione
            g = pz.gruppo_me(p, self.cnt.g(), self.cnt.unita, self.terreno)
            self.cnt.unita += len(p.unita)
            g['hidden'] = False
            punti = g['route']['points']
            missione = ordine.get('missione', 'difesa')
            if missione == 'attacco' and ordine.get('avanza_verso'):
                ax, ay = ll_to_xy(*ordine['avanza_verso'])
                punti[2] = wpt(ax, ay, float(self.terreno.quota(ax, ay)[0]), 5.5, azione='Off Road')
                punti[1]['speed'] = 5.5
                punti[1]['ETA_locked'] = True
            if missione == 'fuoco' and ordine.get('bersaglio_fuoco'):
                bx, by = ll_to_xy(*ordine['bersaglio_fuoco'])
                d = math.hypot(bx - p.x, by - p.y)
                portata = pz.SISTEMI[p.intenzione.sistema]['portata_km'] * 1000
                if d > portata:
                    self.avvisi.append('%s: bersaglio a %.1f km, oltre la portata (%.0f km): sparera\' solo se si avvicina'
                                       % (p.intenzione.nome, d / 1000, portata / 1000))
                fuoco = {'id': 'FireAtPoint', 'params': {'x': bx, 'y': by, 'zoneRadius': 400, 'expendQty': 60,
                                                         'expendQtyEnabled': True, 'weaponType': 1073741822,
                                                         'alt_type': 0, 'counterbattaryRadius': 0}}
                punti[1]['task']['params']['tasks'] = compiti_combo([fuoco])
            paese_id = USA if lato == 'blue' else SIRIA
            self.aggiungi_gruppo(lato, 'vehicle', paese_id, 'USA' if lato == 'blue' else 'Syria', g)
            cfg = pz.SISTEMI[p.intenzione.sistema]
            self.piazzamenti_lua[p.intenzione.nome] = {
                'paese': paese_id, 'abilita': p.intenzione.abilita, 'attuale': 1,
                'unita': {k: {'tipo': t, 'avanti': float(a), 'destra': float(dx), 'rotta': float(r)}
                          for k, (t, a, dx, r) in enumerate(pz.schema(cfg, lato), 1)},
                'posizioni': {k: {'x': x, 'y': y, 'rotta': float(rt)}
                              for k, (x, y, rt) in enumerate([(p.x, p.y, p.rotta)] + p.alternative, 1)},
            }
            self.resoconto['piazzamenti'].append({'lato': lato, 'nome': p.intenzione.nome, 'sistema': p.intenzione.sistema,
                                                  'missione': missione, 'lat_lon': [round(v, 5) for v in xy_to_ll(p.x, p.y)],
                                                  'dettagli': p.dettagli})

    # ----------------------------------------------------------------- aria
    def base(self, nome, lato):
        """(tipo, dati): 'nave' (unitId, x, y) | 'aeroporto' (id, x, y) | 'aria' (x, y)."""
        if nome in self.navi:
            uid, x, y = self.navi[nome]
            return 'nave', (uid, x, y)
        if nome.startswith('aria'):
            return 'aria', ll_to_xy(*INGRESSO_EST)
        n = ALIAS_BASI.get(nome, nome)
        a = AEROPORTI.get(n)
        if a is None:
            raise ValueError('base sconosciuta: %s' % nome)
        return 'aeroporto', (a['id'], a['x'], a['y'])

    def volo(self, lato, o, idx):
        tipo = o['velivolo']
        cat, vel, quota_std = PROFILO.get(tipo, ('plane', 220, 6000))
        mis = o['tipo']
        quota = o.get('quota_ft', 0) * FT or quota_std
        if cat == 'helicopter':
            quota = min(quota, 300)
        n = max(1, min(4, int(o.get('numero', 2))))
        if o.get('giocatore') and lato == 'blue':
            # standard: il giocatore + un gregario IA; diverso solo se il giocatore lo chiede
            n = int((self.par.get('aerei_giocatore') or {}).get(o['nome'], 2))
        tb, dati_base = self.base(o['base'], lato)
        ox, oy = ll_to_xy(*o['obiettivo']) if o.get('obiettivo') else (dati_base[-2], dati_base[-1])
        r_zona = float(o.get('raggio_km', 20)) * 1000
        durata = int(o.get('durata_min', 40)) * 60
        decollo = max(0, hm(o.get('decollo', self.par['inizio'])) - self.t0)
        if o.get('giocatore') and lato == 'blue':
            decollo = 0          # il giocatore entra subito in cabina; l'orario resta nel briefing come previsto
        if o['base'] in self.navi:
            # ponte di volo: almeno 5 s dall'avvio (posti 5-8 della Supercarrier) e decolli distanziati
            occupati = self.decolli_nave.setdefault(o['base'], [])
            decollo = max(decollo, 5)
            while any(abs(decollo - t) < 45 for t in occupati):
                decollo += 45
            occupati.append(decollo)
        gid = self.cnt.g()
        alt_tipo = 'RADIO' if cat == 'helicopter' else 'BARO'

        # partenza
        partenza = self.partenza_giocatore(o['nome']) if (o.get('giocatore') and lato == 'blue') else None
        if partenza == 'aria':
            bx, by = dati_base[-2], dati_base[-1]
            r = math.atan2(oy - by, ox - bx)
            p0 = wpt(bx + 20000 * math.cos(r), by + 20000 * math.sin(r), quota, vel, ETA=decollo, ETA_locked=True)
            if tb == 'nave':
                fine = wpt(bx, by, 0, 0, tipo='Land', azione='Landing', linkUnit=dati_base[0], helipadId=dati_base[0])
            elif tb == 'aeroporto':
                fine = wpt(bx, by, 0, 0, tipo='Land', azione='Landing', airdromeId=dati_base[0])
            else:
                fine = wpt(bx, by, quota, vel, nome='uscita')
        elif tb == 'nave':
            uid, bx, by = dati_base
            tipo_p, azione_p = PARTENZE.get(partenza, PARTENZE['freddo'])
            p0 = wpt(bx, by, 0, 0, tipo=tipo_p, azione=azione_p, linkUnit=uid, helipadId=uid, ETA=decollo, ETA_locked=True)
            fine = wpt(bx, by, 0, 0, tipo='Land', azione='Landing', linkUnit=uid, helipadId=uid)
        elif tb == 'aeroporto':
            aid, bx, by = dati_base
            tipo_p, azione_p = PARTENZE.get(partenza, PARTENZE['pista'])
            p0 = wpt(bx, by, 0, 0, tipo=tipo_p, azione=azione_p, airdromeId=aid, ETA=decollo, ETA_locked=True)
            fine = wpt(bx, by, 0, 0, tipo='Land', azione='Landing', airdromeId=aid)
        else:
            bx, by = dati_base
            p0 = wpt(bx, by, quota, vel, ETA=decollo, ETA_locked=True)
            fine = wpt(bx, by, quota, vel, nome='uscita')
        punti = [p0]
        for lat, lon in o.get('rotta') or []:
            x, y = ll_to_xy(lat, lon)
            punti.append(wpt(x, y, quota, vel, alt_tipo=alt_tipo))

        compiti_iniziali = []
        compiti_obiettivo = []
        if mis in ('CAP', 'GCI'):
            compiti_iniziali.append(t_ingaggia(['Air'], 80000 if mis == 'GCI' else 60000))
            compiti_obiettivo.append(t_orbita(quota, vel * 0.85, durata))
        elif mis == 'SCORTA':
            pass                                         # completato dopo (serve l'id del gruppo scortato)
        elif mis == 'STRIKE':
            compiti_obiettivo.append(t_bombardamento(ox, oy, quota))
        elif mis == 'CAS':
            compiti_obiettivo.append(t_ingaggia_zona(ox, oy, r_zona, ['Ground Units']))
            compiti_obiettivo.append(t_orbita(quota, vel * 0.8, durata, 'Circle'))
        elif mis == 'SEAD':
            compiti_obiettivo.append(t_ingaggia_zona(ox, oy, r_zona, ['Air Defence']))
            compiti_obiettivo.append(t_orbita(quota, vel * 0.85, durata, 'Circle'))
        elif mis == 'ANTINAVE':
            compiti_obiettivo.append(t_ingaggia_zona(ox, oy, r_zona, ['Ships']))
        elif mis == 'AWACS':
            compiti_iniziali.append({'id': 'AWACS', 'params': {}})
            compiti_obiettivo.append(t_orbita(quota, vel, durata or 3 * 3600))
        elif mis == 'TANKER':
            compiti_iniziali.append({'id': 'Tanker', 'params': {}})
            compiti_obiettivo.append(t_orbita(quota, vel, durata or 3 * 3600))
        elif mis == 'TRASPORTO':
            compiti_obiettivo.append({'id': 'Land', 'params': {'x': ox, 'y': oy, 'duration': 300, 'durationFlag': True}})
        compiti_iniziali.append(t_azione('Option', {'name': 0, 'value': 2 if mis in ('AWACS', 'TANKER', 'TRASPORTO') else 0}))
        p0['task']['params']['tasks'] = compiti_combo(compiti_iniziali)
        punti.append(wpt(ox, oy, quota, vel, compiti=compiti_combo(compiti_obiettivo), nome=o['nome'], alt_tipo=alt_tipo))
        if mis in ('AWACS', 'TANKER', 'CAP', 'GCI'):
            # seconda gamba del circuito
            r = math.radians(dist_brg(dati_base[-2], dati_base[-1], ox, oy)[1] + 90)
            punti.append(wpt(ox + 40000 * math.cos(r), oy + 40000 * math.sin(r), quota, vel, alt_tipo=alt_tipo))
        punti.append(fine)

        # unita'
        giocatore = bool(o.get('giocatore')) and lato == 'blue'
        carico = carichi.risolvi(tipo, o.get('carico', '')) if o.get('carico') not in (None, 'nessuno') else {}
        if o.get('carico') in carichi.AUTONOMIA_RIDOTTA.get(tipo, {}) and int(o.get('durata_min', 40)) > carichi.AUTONOMIA_RIDOTTA[tipo][o['carico']]:
            self.avvisi.append('AUTONOMIA: %s (%s, carico "%s") resta %s min sull\'obiettivo, oltre i %d consigliati: serve una cisterna'
                               % (o['nome'], tipo, o['carico'], o.get('durata_min'), carichi.AUTONOMIA_RIDOTTA[tipo][o['carico']]))
        carb = carichi.PILONI.get(tipo, {}).get('carburante') or 3000
        unita = {}
        paese_id = USA if lato == 'blue' else (RUSSIA if tipo in ('Su-25', 'Tu-22M3', 'A-50') else SIRIA)
        speciali = NOMI_CHIAMATA_SPECIALI.get(mis)
        if speciali:
            self.conta_speciali[mis] = self.conta_speciali.get(mis, 0) % len(speciali) + 1
            nome_ch, testo_ch = self.conta_speciali[mis], speciali[self.conta_speciali[mis]]
        else:
            nome_ch = NOMI_CHIAMATA.get(mis, 1)
            testo_ch = NOMI_CHIAMATA_TESTO[nome_ch]
        num_ch = self.numeri_chiamata.get((paese_id, testo_ch), 0) % 9 + 1
        self.numeri_chiamata[(paese_id, testo_ch)] = num_ch
        for k in range(n):
            u = {'type': tipo, 'unitId': self.cnt.u(), 'name': '%s-%d' % (o['nome'], k + 1),
                 'skill': ('Client' if (giocatore and k == 0) else self.abilita(lato)),
                 'x': p0['x'] + 40 * k, 'y': p0['y'] + 40 * k, 'alt': p0['alt'], 'alt_type': p0['alt_type'],
                 'heading': 0, 'psi': 0, 'speed': p0['speed'],
                 'payload': {'pylons': copy.deepcopy(carico), 'fuel': carb, 'flare': 60, 'chaff': 60, 'gun': 100}}
            if paese_id in PAESI_NOMINATIVO_NUMERICO:
                u['callsign'] = 100 + idx * 10 + k
            else:
                u['callsign'] = {1: nome_ch, 2: num_ch, 3: k + 1, 'name': '%s%d%d' % (testo_ch, num_ch, k + 1)}
            u['onboard_num'] = '%03d' % (100 + idx * 10 + k) if lato == 'blue' else '%02d' % (10 + idx * 2 + k)
            unita[k + 1] = u
        g = {'name': o['nome'], 'groupId': gid, 'task': COMPITO_DCS.get(mis, 'CAP'), 'taskSelected': True,
             'x': p0['x'], 'y': p0['y'], 'start_time': decollo, 'hidden': lato == 'red', 'uncontrolled': False,
             'uncontrollable': False, 'communication': True, 'frequency': self.frequenza_volo(lato, o, giocatore),
             'modulation': 0, 'radioSet': False, 'tasks': {}, 'units': unita,
             'route': {'points': {k + 1: p for k, p in enumerate(punti)}}}
        self.gruppi_aerei[o['nome']] = (lato, g, o)
        self.aggiungi_gruppo(lato, cat, paese_id, {USA: 'USA', SIRIA: 'Syria', RUSSIA: 'Russia'}[paese_id], g)
        self.resoconto['voli'].append({'lato': lato, 'nome': o['nome'], 'tipo': mis, 'velivolo': tipo, 'numero': n,
                                       'base': o['base'], 'decollo': o.get('decollo'), 'giocatore': giocatore})

    def scorte(self):
        for nome, (lato, g, o) in self.gruppi_aerei.items():
            if o['tipo'] != 'SCORTA':
                continue
            scortato = self.gruppi_aerei.get(o.get('scorta_di', ''))
            if not scortato:
                self.avvisi.append('%s: gruppo da scortare %r non trovato, diventa una CAP' % (nome, o.get('scorta_di')))
                g['task'] = 'CAP'
                g['route']['points'][1]['task']['params']['tasks'] = compiti_combo([t_ingaggia(['Air'])])
                continue
            sg = scortato[1]
            # stessa partenza e stesso orario del gruppo scortato
            g['start_time'] = sg['start_time']
            p0 = g['route']['points'][1]
            p0['ETA'] = sg['start_time']
            esc = {'id': 'Escort', 'params': {'groupId': sg['groupId'], 'pos': {'x': -500, 'y': 300, 'z': 600},
                                              'lastWptIndexFlag': False, 'lastWptIndexFlagChangedManually': True,
                                              'engagementDistMax': 60000, 'targetTypes': {1: 'Planes'}}}
            p0['task']['params']['tasks'] = compiti_combo([esc])

    def tutti_i_voli(self):
        for lato in ('blue', 'red'):
            voli = list(enumerate(self.ordini[lato].get('missioni_aeree', []), 1))
            voli.sort(key=lambda kv: not kv[1].get('giocatore'))      # prima i voli del giocatore (ponte libero)
            for k, o in voli:
                try:
                    self.volo(lato, o, k)
                except Exception as e:  # noqa: BLE001
                    self.avvisi.append('%s (%s): volo scartato: %s' % (o.get('nome'), lato, e))
        self.scorte()
        self.preimposta_radio()

    # ----------------------------------------------------------------- radio
    def frequenza_volo(self, lato, o, giocatore):
        """Frequenza del gruppo e piano radio blu (canali preimpostati del giocatore)."""
        if lato != 'blue':
            return 124
        tipo = o['tipo']
        if tipo == 'AWACS':
            f = RADIO_BLU['awacs'] + 0.5 * sum(1 for v in self.piano_radio if v[2] == 'AWACS')
        elif tipo == 'TANKER':
            f = RADIO_BLU['cisterna'] + sum(1 for v in self.piano_radio if v[2] == 'TANKER')
        elif giocatore:
            f = RADIO_BLU['interno'] + sum(1 for v in self.piano_radio if v[2] == 'GIOCATORE')
        else:
            return RADIO_BLU['pacchetto']
        self.piano_radio.append((f, o['nome'], 'GIOCATORE' if giocatore else tipo))
        return f

    def meteo(self):
        """Riga meteo per briefing e tavolette (unita' USA: nodi, piedi, inHg; anche hPa)."""
        w = self.m['weather']
        verso = w['wind']['atGround']['dir']
        kt = w['wind']['atGround']['speed'] / KT
        mmhg = w.get('qnh', 760)
        return ('Vento al suolo da %03d/%d kt (2000 m: da %03d/%d kt). QNH %.2f inHg (%d hPa). Nubi %d/10, base %d ft. '
                'Visibilita\' %d km.' % ((verso + 180) % 360, round(kt), (w['wind']['at2000']['dir'] + 180) % 360,
                                         round(w['wind']['at2000']['speed'] / KT), mmhg / 25.4, round(mmhg * 1.33322),
                                         w['clouds'].get('density', 0), round(w['clouds'].get('base', 0) / FT, -2),
                                         w['visibility']['distance'] // 1000))

    def canali(self):
        """Canali preimpostati uguali per tutti i velivoli del giocatore: [(canale, MHz, descrizione)]."""
        lista = [(RADIO_BLU['pacchetto'], 'Pacchetto (comune ai voli d\'attacco)')]
        lista += [(f, 'AWACS "%s"' % n) for f, n, t in self.piano_radio if t == 'AWACS']
        lista += [(f, 'Cisterna "%s"' % n) for f, n, t in self.piano_radio if t == 'TANKER']
        lista += [(RADIO_BLU['cvn'], 'CVN-71 torre / CATCC'), (RADIO_BLU['lha'], 'LHA-1 Tarawa torre'),
                  (RADIO_BLU['incirlik'], 'Incirlik torre')]
        lista += [(f, 'Interno %s' % n) for f, n, t in self.piano_radio if t == 'GIOCATORE']
        lista.append((RADIO_BLU['guardia'], 'Guardia'))
        return [(k, f, d) for k, (f, d) in enumerate(lista, 1)]

    def preimposta_radio(self):
        """Canali preimpostati nei velivoli del giocatore (giocatore e gregario), secondo il modello
        della radio del modulo (struttura ricavata da missioni salvate dal Mission Editor)."""
        canali = self.canali()
        for nome, (lato, g, o) in self.gruppi_aerei.items():
            if lato != 'blue' or not o.get('giocatore'):
                continue
            tipo = g['units'][1]['type']
            modello = RADIO_MODELLI.get(tipo)
            if not modello:
                self.avvisi.append('RADIO: %s (%s): canali non preimpostati, manca il modello della radio del modulo' % (nome, tipo))
                continue
            radio = {}
            for r, (n_canali, modulazioni) in modello.items():
                ch = {i: RADIO_RIEMPI + i for i in range(1, n_canali + 1)}
                for k, f, _ in canali:
                    if k <= n_canali:
                        ch[k] = f
                radio[r] = {'channels': ch, 'modulations': {i: 0 for i in ch} if modulazioni else {}, 'channelsNames': {}}
            for u in g['units'].values():
                u['Radio'] = copy.deepcopy(radio)

    # ----------------------------------------------------------------- mappa
    def disegni(self):
        confini.aggiungi(self.m)
        intel.aggiungi(self.m)
        # stima blu: i siti distrutti non ci sono piu'
        for strato in self.m['drawings']['layers'].values():
            if strato['name'] == 'Blue':
                strato['objects'] = {k: o for k, o in enumerate(
                    [o for o in strato['objects'].values() if not any(n in o['name'] for n in SITI_DISTRUTTI)], 1)}
            if strato['name'] == 'Common':
                ogg = list(strato['objects'].values())
                xy = [ll_to_xy(*q) for q in TESTA_DI_PONTE]
                for pezzo in confini._pezzi_convessi(xy):
                    x0, y0, pts = confini._punti_relativi([xy[i] for i in pezzo])
                    ogg.insert(0, {'visible': True, 'primitiveType': 'Polygon', 'polygonMode': 'free', 'mapX': x0, 'mapY': y0,
                                   'angle': 0, 'points': pts, 'colorString': '0x00000000', 'fillColorString': '0x1f5fcc55',
                                   'thickness': 0, 'style': 'solid', 'name': 'Testa di ponte G%d' % self.giorno, 'layerName': 'Common'})
                fx = [ll_to_xy(*q) for q in LINEA_FRONTE]
                x0, y0 = fx[0]
                ogg.append({'visible': True, 'primitiveType': 'Line', 'lineMode': 'free', 'closed': False, 'mapX': x0, 'mapY': y0,
                            'points': {k: {'x': x - x0, 'y': y - y0} for k, (x, y) in enumerate(fx, 1)},
                            'colorString': '0x000000ff', 'thickness': 6, 'style': 'solid',
                            'name': 'Linea del fronte G%d' % self.giorno, 'layerName': 'Common'})
                strato['objects'] = {k: o for k, o in enumerate(ogg, 1)}

    # ----------------------------------------------------------------- tutto
    def costruisci(self):
        m = self.m
        anno, mese, giorno = (int(v) for v in self.par['data'].split('-'))
        m['date'] = {'Year': anno, 'Month': mese, 'Day': giorno}
        m['start_time'] = self.t0
        m['weather'].update({
            'name': 'Levante G%d' % self.giorno, 'enable_fog': False, 'enable_dust': False, 'dust_density': 0,
            'season': {'temperature': 22}, 'qnh': 760, 'groundTurbulence': 2, 'type_weather': 0,
            'visibility': {'distance': 60000}, 'fog': {'visibility': 0, 'thickness': 0},
            'wind': {'atGround': {'speed': 5, 'dir': 90}, 'at2000': {'speed': 8, 'dir': 95}, 'at8000': {'speed': 15, 'dir': 100}},
            'clouds': {'thickness': 600, 'density': 4, 'base': 2500, 'iprecptns': 0},
        })
        cx, cy = ll_to_xy(34.2, 35.3)
        m['map'] = {'centerX': cx, 'centerY': cy, 'zoom': 400000}
        m['forcedOptions'] = {'optionsView': 'optview_allies', 'labels': 0}
        m['coalition']['blue']['bullseye'] = dict(zip(('x', 'y'), ll_to_xy(34.0, 35.4)))
        m['coalition']['red']['bullseye'] = dict(zip(('x', 'y'), ll_to_xy(33.8, 36.2)))
        self.modello_magazzino = self.w['warehouses'][0]
        self.w['warehouses'] = {}
        # basi: proprieta'
        for nome in self.par.get('basi_rosse', []):
            a = AEROPORTI.get(ALIAS_BASI.get(nome, nome))
            if a:
                self.w['airports'][a['id']]['coalition'] = 'RED'
        self.w['airports'][AEROPORTI['Incirlik']['id']]['coalition'] = 'BLUE'

        self.navi_blu()
        self.navi_rosse()
        self.forze_terra()
        self.tutti_i_voli()
        self.disegni()
        self.verifica_prestazioni()
        self.verifica_orario()
        self.verifica_intensita()
        return self

    def verifica_intensita(self):
        """Conflitto di media intensita', missioni del giocatore sopravvivibili: avvisa se l'obiettivo
        di un volo del giocatore e' coperto da troppe batterie SAM nemiche (SA-5 escluso: si
        evita volando bassi). I voli SEAD sono esclusi: le batterie sono il loro bersaglio."""
        lato_g = 'blue'
        nemici = [(ll_to_xy(*p['lat_lon']), pz.SISTEMI[p['sistema']]['portata_km'] * 1000, p['nome'])
                  for p in self.resoconto['piazzamenti']
                  if p['lato'] != lato_g and p['sistema'] in SAM_PERICOLOSI]
        for a in self.ordini['blue'].get('missioni_aeree', []):
            if not a.get('giocatore') or a['tipo'] == 'SEAD' or not a.get('obiettivo'):
                continue
            ox, oy = ll_to_xy(*a['obiettivo'])
            coprono = [n for (x, y), r, n in nemici if math.hypot(x - ox, y - oy) < r]
            if len(coprono) > MAX_SAM_SU_OBIETTIVO:
                self.avvisi.append('INTENSITA: obiettivo di %s coperto da %d batterie SAM nemiche (max %d)'
                                   % (a['nome'], len(coprono), MAX_SAM_SU_OBIETTIVO))

    def abilita(self, lato):
        """Livello dell'IA: High di partenza, cala con il logoramento della parte (frazione di
        aerei/equipaggi persi rispetto all'ordine di battaglia iniziale, che l'arbitro scrive in
        parametri.json -> "logoramento": {"blu": 0.1, "rosso": 0.3})."""
        perso = float((self.par.get('logoramento') or {}).get('blu' if lato == 'blue' else 'rosso', 0))
        for soglia, livello in LOGORAMENTO_ABILITA:
            if perso < soglia:
                return livello
        return LOGORAMENTO_ABILITA[-1][1]

    def partenza_giocatore(self, volo):
        """Tipo di partenza dei voli del giocatore: lo decide il giocatore a ogni missione
        (parametri.json, "partenza_giocatore": "freddo" | "caldo" | "pista" | "aria", oppure
        {nome volo: tipo}). Se manca la missione non si costruisce: va chiesto."""
        p = self.par.get('partenza_giocatore')
        if isinstance(p, dict):
            p = p.get(volo, p.get('*'))
        if p not in ('freddo', 'caldo', 'pista', 'aria'):
            raise SystemExit('Partenza del volo giocatore "%s" non indicata (freddo/caldo/pista/aria): '
                             'chiederla al giocatore e scriverla in parametri.json -> partenza_giocatore' % volo)
        return p

    def verifica_orario(self):
        """Il giocatore vola di giorno (mattina; alba e tramonto vanno bene). Notte solo se chiesta:
        parametri.json -> "notte": true."""
        if self.par.get('notte'):
            return
        inizio, fine = hm(self.par['inizio']), hm(self.par.get('fine', self.par['inizio']))
        # Levante, ora locale: alba ~05:30-06:30, tramonto ~16:45-19:45 secondo la stagione; margine prudente
        if inizio < 5 * 3600 or fine > 19 * 3600 + 30 * 60:
            self.avvisi.append('ORARIO: missione %s-%s fuori dal giorno, ma il giocatore non ha chiesto la notte'
                               % (self.par['inizio'], self.par.get('fine', '?')))

    def verifica_prestazioni(self):
        """Controlla il bilancio delle unita' (docs/lezioni.md, PC del giocatore: i7-7700K 4 core)."""
        conta = {'plane': 0, 'helicopter': 0, 'vehicle': 0, 'ship': 0, 'static': 0}
        terra = []
        for co in self.m['coalition'].values():
            for c in co['country'].values():
                for cat in conta:
                    for g in c.get(cat, {}).get('group', {}).values():
                        conta[cat] += len(g['units'])
                        if cat == 'vehicle':
                            terra += [(u['x'], u['y']) for u in g['units'].values()]
        # aerei in volo nello stesso momento: decollo -> decollo + durata + 40 min di transito
        finestre = []
        for ordini in self.ordini.values():
            for a in ordini.get('missioni_aeree', []):
                t = hm(a.get('decollo', self.par['inizio']))
                finestre.append((t, t + (int(a.get('durata_min', 60)) + 40) * 60, max(1, min(4, int(a.get('numero', 2))))))
        picco = max([sum(n for s, e, n in finestre if s <= t < e) for t, _, _ in finestre] or [0])
        # unita' di terra vicino agli obiettivi del giocatore
        vicine = 0
        obiettivi = [ll_to_xy(*a['obiettivo']) for a in self.ordini['blue'].get('missioni_aeree', [])
                     if a.get('giocatore') and a.get('obiettivo')]
        for x, y in terra:
            if any(math.hypot(x - ox, y - oy) < 30000 for ox, oy in obiettivi):
                vicine += 1
        totale = sum(conta.values())
        self.resoconto['prestazioni'] = dict(conta, totale=totale, aerei_in_volo_picco=picco, terra_vicino_giocatore=vicine)
        for valore, limite, cosa in ((totale, BILANCIO['unita_totali'], "unita' totali"),
                                     (conta['vehicle'], BILANCIO['unita_terra'], "unita' di terra"),
                                     (picco, BILANCIO['aerei_in_volo'], 'aerei in volo contemporaneamente (stima)'),
                                     (vicine, BILANCIO['terra_vicino_giocatore'], "unita' di terra entro 30 km dagli obiettivi del giocatore"),
                                     (conta['ship'], BILANCIO['navi'], 'navi')):
            if valore > limite:
                self.avvisi.append('PRESTAZIONI: %d %s, oltre il limite di %d' % (valore, cosa, limite))

    def scrivi(self, briefing_blu, briefing_rosso, tavolette):
        nome = 'G%02d_%s' % (self.giorno, self.par['data'])
        diz = {'DictKey_descriptionText_1': briefing_blu['testo'], 'DictKey_descriptionRedTask_2': briefing_rosso,
               'DictKey_descriptionBlueTask_3': briefing_blu['compito'], 'DictKey_descriptionNeutralsTask_4': '',
               'DictKey_sortie_5': 'G%d - %s' % (self.giorno, briefing_blu['titolo'])}
        m = self.m
        m['descriptionText'] = 'DictKey_descriptionText_1'
        m['descriptionRedTask'] = 'DictKey_descriptionRedTask_2'
        m['descriptionBlueTask'] = 'DictKey_descriptionBlueTask_3'
        m['descriptionNeutralsTask'] = 'DictKey_descriptionNeutralsTask_4'
        m['sortie'] = 'DictKey_sortie_5'
        m['maxDictId'] = 5
        init = ('LEVANTE = { missione = "%s" }\n' % nome + lt.dump('LEVANTE_PIAZZAMENTI', self.piazzamenti_lua)
                + '\n' + lt.dump('LEVANTE_NAVI', self.navi_vento))
        risorse = {'ResKey_Action_1': 'init.lua', 'ResKey_Action_2': 'levante_core.lua', 'ResKey_Action_3': 'levante_piazzatore.lua',
                   'ResKey_Action_4': 'levante_navi.lua'}
        for i, (commento, chiave) in enumerate((('INIT', 'ResKey_Action_1'), ('NUCLEO', 'ResKey_Action_2'),
                                                ('PIAZZATORE', 'ResKey_Action_3'), ('NAVI', 'ResKey_Action_4')), 1):
            m['trig']['actions'][i] = 'a_do_script_file(getValueResourceByKey("%s"));' % chiave
            m['trig']['conditions'][i] = 'return(true)'
            m['trig']['flag'][i] = True
            m['trig']['funcStartup'][i] = 'if mission.trig.conditions[%d]() then mission.trig.actions[%d]() end' % (i, i)
            m['trigrules'][i] = {'rules': {}, 'comment': commento, 'eventlist': '', 'predicate': 'triggerStart',
                                 'actions': {1: {'predicate': 'a_do_script_file', 'file': chiave}}}
        out = os.path.join(RADICE, 'missioni', nome + '.miz')
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('mission', lt.dump('mission', m))
            z.writestr('warehouses', lt.dump('warehouses', self.w))
            z.writestr('options', lt.dump('options', self.o))
            z.writestr('theatre', 'Syria')
            z.writestr('l10n/DEFAULT/dictionary', lt.dump('dictionary', diz))
            z.writestr('l10n/DEFAULT/mapResource', lt.dump('mapResource', risorse))
            z.writestr('l10n/DEFAULT/init.lua', init)
            z.write(os.path.join(QUI, 'lua', 'levante_core.lua'), 'l10n/DEFAULT/levante_core.lua')
            z.write(os.path.join(QUI, 'lua', 'levante_piazzatore.lua'), 'l10n/DEFAULT/levante_piazzatore.lua')
            z.write(os.path.join(QUI, 'lua', 'levante_navi.lua'), 'l10n/DEFAULT/levante_navi.lua')
            for k, png in enumerate(tavolette, 1):
                z.writestr('KNEEBOARD/IMAGES/G%02d_%02d.png' % (self.giorno, k), png)
        json.dump(self.resoconto, open(os.path.join(self.cartella, 'costruzione.json'), 'w'), indent=1, ensure_ascii=False)
        return out


if __name__ == '__main__':
    import briefing_giornata
    giorno = int(sys.argv[1])
    c = Costruttore(giorno).costruisci()
    bb, br, tav = briefing_giornata.prepara(c)
    out = c.scrivi(bb, br, tav)
    print('scritto', out)
    print('gruppi di terra: %d, voli: %d' % (len(c.resoconto['piazzamenti']), len(c.resoconto['voli'])))
    for a in c.avvisi:
        print('AVVISO:', a)
