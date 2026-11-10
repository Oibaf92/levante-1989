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
import types
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
import verifica_miz  # noqa: E402
import confini  # noqa: E402
import intel  # noqa: E402
import rapporto_intel  # noqa: E402
import regole_speciali  # noqa: E402
import meteo  # noqa: E402
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

AIM54_PER_CARICO = {'cap 2-3-2': 2, 'aria-aria': 2, 'scorta': 2}

# rete di difesa aerea (levante_iads.lua): batterie gestite e unita' che fanno da osservatori a vista
SAM_IADS = ('sa2', 'sa3', 'sa5', 'sa6', 'sa8', 'hawk')
OSSERVATORI = ('aaa', 'contraerea_mobile', 'carri', 'meccanizzata')

# livello dell'IA in base al logoramento (frazione persa): sotto la soglia -> livello
LOGORAMENTO_ABILITA = ((0.20, 'High'), (0.40, 'Good'), (9.99, 'Average'))

# Piano radio blu (MHz, UHF AM). I canali preimpostati del giocatore sono in Costruttore.canali().
RADIO_BLU = {'guardia': 243.0, 'pacchetto': 251.0, 'cvn': 258.0, 'lha': 256.0, 'incirlik': 360.1,
             'awacs': 264.0, 'cisterna': 270.0, 'interno': 301.0}
RADIO_RIEMPI = 225.0            # canali liberi: 225 + numero del canale
# Modelli delle radio dei moduli (canali di default, banda, modulazioni), ricavati da missioni
# salvate dal Mission Editor del giocatore: script/dati/radio_modelli.json.
RADIO_MODELLI = {k: v for k, v in json.load(open(os.path.join(QUI, 'dati', 'radio_modelli.json'), encoding='utf-8')).items()
                 if not k.startswith('_')}

# Livree scelte dal giocatore (C00 salvata dal suo Mission Editor). Per tipo e paese: lista di
# squadriglie, assegnate a rotazione volo per volo (stesso volo = stessa squadriglia).
# CVW-8 sulla Roosevelt nel 1989: F-14A di VF-84 e VF-41.
LIVREE = {   # (paese, tipo): [(livrea, base del numero di bordo o None, carichi a cui si applica o None)]
    (USA, 'F-14A-135-GR-Early'): [('vf-84 ghost by reflected', 200, None), ('vf-41 aj100 1989 by reflected', 100, None),
                                  ('vf-84 jaws by reflected', 200, None), ('vf-41 aj105 1989 by reflected', 100, None)],
    (USA, 'FA-18C_hornet'): [('vfa-87', 400, None)],              # solo VFA-87 (scelta del giocatore)
    (USA, 'F-4E-45MC'): [('rs68-381_e1_526tfs', None, None)],
    (USA, 'AH-64D_BLK_II'): [('12th combat aviation brigade griffins', None, None)],
    (USA, 'CH-47Fbl1'): [('us army dark green', None, None)],
    (RUSSIA, 'Su-25'): [('field camo scheme #1 (native)', None, None)],
    (SIRIA, 'MiG-29 Fulcrum'): [('syria af', None, None)],
    (RUSSIA, 'MiG-29 Fulcrum'): [('air force standard', None, None)],
    (SIRIA, 'MiG-23MLD'): [('Syria_2', None, None)],
    (SIRIA, 'Mi-24P'): [('syaaf', None, None)],
    (RUSSIA, 'Mi-24P'): [('af 440 ovp', None, None)],
    (SIRIA, 'Mi-8MT'): [('Russia_VVS_Standard', None, ('trasporto', 'nessuno')), ('Russia_VVS_Standard_2', None, ('armato',))],
    (RUSSIA, 'Mi-8MT'): [('Russia_VVS_Standard', None, ('trasporto', 'nessuno')), ('Russia_VVS_Standard_2', None, ('armato',))],
}

# tipi di partenza del giocatore -> (tipo, azione) del primo punto di rotta
PARTENZE = {'freddo': ('TakeOffParking', 'From Parking Area'), 'caldo': ('TakeOffParkingHot', 'From Parking Area Hot'),
            'pista': ('TakeOff', 'From Runway')}

MARGINE_SITI_KM = 40      # un sito fisso entra nella missione se un volo nemico passa entro portata + margine

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


def chiavi_int(v):
    """JSON trasforma le chiavi intere in stringhe: le riporta interi (servono per le tabelle della missione)."""
    if isinstance(v, dict):
        return {(int(k) if isinstance(k, str) and k.isdigit() else k): chiavi_int(x) for k, x in v.items()}
    if isinstance(v, list):
        return [chiavi_int(x) for x in v]
    return v


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
    def __init__(self, giorno, blocco=None, osservatore=False):
        self.giorno = giorno
        self.blocco = blocco
        self.osservatore = osservatore      # missione da osservare: tutti i voli all'IA, vista libera
        self.cartella = os.path.join(RADICE, 'campagna', 'G%02d' % giorno)
        self.par = json.load(open(os.path.join(self.cartella, 'parametri.json'), encoding='utf-8'))
        self.ordini = {lato: json.load(open(os.path.join(RADICE, d, 'ordini_G%02d.json' % giorno), encoding='utf-8'))
                       for lato, d in (('blue', 'blu'), ('red', 'rosso'))}
        self.cnt = Contatori()
        self.avvisi = []
        self.resoconto = {'piazzamenti': [], 'voli': [], 'avvisi': self.avvisi, 'unita': []}
        if blocco:
            b = self.par['blocchi'][blocco - 1]
            self.inizio, self.fine, self.nome_blocco = b['inizio'], b['fine'], b.get('nome', 'blocco %d' % blocco)
            self.nome = 'G%02d_B%d_%s' % (giorno, blocco, self.par['data'])
            self._ordini_del_blocco()
            self.esiti_prec = self._carica_json('esiti_B%d.json' % (blocco - 1)) if blocco > 1 else {}
        else:
            self.inizio, self.fine, self.nome_blocco = self.par['inizio'], self.par.get('fine', self.par['inizio']), ''
            self.nome = 'G%02d_%s' % (giorno, self.par['data'])
            self.esiti_prec = {}
        self.t0 = hm(self.inizio)
        if osservatore:
            self.nome += '_OSSERVATORE'
            for o in self.ordini['blue'].get('missioni_aeree', []) + self.ordini['red'].get('missioni_aeree', []):
                o['giocatore'] = False
        carica = lambda n: lt.parse(open(os.path.join(QUI, 'base', n), encoding='utf-8').read())[1]  # noqa: E731
        self.m, self.w, self.o = carica('mission'), carica('warehouses'), carica('options')
        self.terreno = pz.Terreno()
        self.gruppi_aerei = {}            # nome missione -> (lato, gruppo)
        self.decolli_nave = {}
        self.conta_livree = {}
        self.piano_radio = []             # (MHz, nome volo, ruolo)
        self.conta_speciali = {}          # AWACS/TANKER -> ultimo nome usato
        self.numeri_chiamata = {}         # (paese, nome) -> ultimo numero di gruppo (1-9)
        self._rinomina_doppi()
        self.navi = {}

    def _carica_json(self, nome):
        """Carica un JSON della giornata; le chiavi numeriche (tabelle Lua salvate in JSON) tornano interi."""
        p = os.path.join(self.cartella, nome)
        return chiavi_int(json.load(open(p, encoding='utf-8'))) if os.path.exists(p) else {}

    def _ordini_del_blocco(self):
        """Correzioni dei comandanti tra un blocco e l'altro: <parte>/ordini_GNN_Bk.json sostituisce i voli
        di quel blocco e aggiunge o sostituisce (per nome) unita' di terra."""
        for lato, d in (('blue', 'blu'), ('red', 'rosso')):
            p = os.path.join(RADICE, d, 'ordini_G%02d_B%d.json' % (self.giorno, self.blocco))
            if not os.path.exists(p):
                continue
            agg = json.load(open(p, encoding='utf-8'))
            base = self.ordini[lato]
            if 'missioni_aeree' in agg:
                base['missioni_aeree'] = [o for o in base.get('missioni_aeree', []) if not self.nel_blocco(o)] + \
                    [dict(o, blocco=self.blocco) for o in agg['missioni_aeree']]
            nuove = {u['nome']: u for u in agg.get('unita_terra', [])}
            base['unita_terra'] = [u for u in base.get('unita_terra', []) if u['nome'] not in nuove] + list(nuove.values())
            self.terra_cambiata = getattr(self, 'terra_cambiata', set()) | set(nuove)
            if agg.get('intento_generale'):
                base['intento_generale'] = agg['intento_generale']

    def nel_blocco(self, o):
        """Un volo appartiene al blocco se lo dice ('blocco') o, se non lo dice, se decolla nella sua finestra."""
        if not self.blocco:
            return True
        if o.get('blocco'):
            return int(o['blocco']) == self.blocco
        return hm(self.inizio) <= hm(o.get('decollo', self.inizio)) < hm(self.fine)

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

    def _pos_nave(self, nome, predefinita):
        """Posizione di partenza di una nave: dove era alla fine del blocco precedente, se nota."""
        p = (self.esiti_prec or {}).get('posizioni', {}).get(nome)
        return (p[0], p[1]) if p else ll_to_xy(*predefinita)

    def navi_blu(self):
        self.navi_vento = {}
        hdg = math.radians(self.prua_contro_vento(CVN_SCARTO))
        cx, cy = self._pos_nave('CVN-71 Theodore Roosevelt', CVN_POS)
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
        lx, ly = self._pos_nave('LHA-1 Tarawa', LHA_POS)
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
             'route': {'points': {1: wpt(tx, ty, 0, 0, ETA_locked=True)}}}
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
        # siti fissi rossi ancora attivi e non ripetuti negli ordini; quelli lontani dai voli blu del
        # blocco restano nella campagna ma non entrano nella missione (prestazioni)
        nomi = {it.nome for it, _ in out}
        punti_blu = self.punti_voli('blue')
        for lat, lon, r, tipo, nome in intel.SAM_ROSSI:
            if tipo in ('sa5', 'sa2', 'sa3') and nome not in SITI_DISTRUTTI and nome not in nomi:
                sx, sy = ll_to_xy(lat, lon)
                raggio = (pz.SISTEMI[tipo]['portata_km'] + MARGINE_SITI_KM) * 1000
                if not any(math.hypot(sx - x, sy - y) < raggio for x, y in punti_blu):
                    self.resoconto.setdefault('fuori_missione', []).append(nome)
                    continue
                sett = (180, 330)
                it = pz.Intenzione(tipo, nome, (lat, lon), 6 if tipo != 'sa5' else 12, sett, (lat, lon),
                                   coalizione='red', paese=SIRIA, abilita=self.abilita('red'))
                out.append((it, {'missione': 'difesa'}))
        return out

    ORDINE_PIAZZAMENTO = {'sa5': 0, 'ewr': 1, 'sa2': 2, 'sa3': 3, 'hawk': 3, 'sa6': 4, 'sa8': 5, 'aaa': 6,
                          'artiglieria': 7, 'lanciarazzi': 7, 'carri': 8, 'meccanizzata': 8, 'contraerea_mobile': 9}

    def punti_voli(self, lato):
        """Punti significativi dei voli di una parte nel blocco: obiettivi e punti di rotta."""
        out = []
        for o in self.ordini[lato].get('missioni_aeree', []):
            if not self.nel_blocco(o):
                continue
            for p in ([o['obiettivo']] if o.get('obiettivo') else []) + list(o.get('rotta') or []):
                out.append(ll_to_xy(*p))
        return out

    def forze_terra(self):
        """Unita' di terra. Primo blocco (o missione intera): tutte piazzate dal piazzatore. Blocchi
        successivi: si riparte dallo stato del blocco precedente (campagna/GNN/terra_B<k-1>.json + esiti):
        unita' distrutte tolte, danneggiate fuori servizio, posizioni aggiornate; si piazzano solo le
        unita' nuove o cambiate negli ordini del blocco."""
        self.piazzamenti_lua = {}
        voci = self.intenzioni_terra()
        cache = self._carica_json('terra_B%d.json' % (self.blocco - 1)) if self.blocco and self.blocco > 1 else {}
        cambiate = getattr(self, 'terra_cambiata', set())
        tenute, gia = [], []
        eliminati = set(cache.get('eliminati', [])) - cambiate     # gruppi distrutti: non si ricreano dagli ordini
        for voce in cache.get('gruppi', []):
            if voce['nome'] in cambiate:
                continue
            g_cache, g = self._gruppo_dagli_esiti(voce)
            if g_cache:
                voce = dict(voce, gruppo=g_cache)       # i fermi restano nella giornata, fuori dalla missione
            if not g_cache:
                eliminati.add(voce['nome'])
            if g:
                tenute.append((voce, g))
            elif g_cache:
                nuova_cache_fermi = getattr(self, '_fermi', [])
                nuova_cache_fermi.append(voce)
                self._fermi = nuova_cache_fermi
                gia.append(types.SimpleNamespace(
                    x=g['x'], y=g['y'], intenzione=types.SimpleNamespace(sistema=voce['sistema']),
                    unita=[(u['type'], u['x'], u['y'], 0) for u in g['units'].values()]))
        nomi_tenuti = ({v['nome'] for v in cache.get('gruppi', [])} - cambiate) | eliminati
        da_piazzare = [(it, o) for it, o in voci if it.nome not in nomi_tenuti]
        piazzati = []
        for it in sorted([it for it, _ in da_piazzare], key=lambda i: self.ORDINE_PIAZZAMENTO.get(i.sistema, 9)):
            try:
                piazzati.append(pz.piazza(self.terreno, it, gia + piazzati))
            except ValueError as e:
                self.avvisi.append('%s: non piazzata (%s)' % (it.nome, e))
        per_nome = {u_it.nome: ordine for u_it, ordine in da_piazzare}
        nuova_cache = []
        for voce, g in tenute:
            self._aggiungi_terra(voce, g)
            nuova_cache.append(voce)
        nuova_cache += getattr(self, '_fermi', [])
        for p in piazzati:
            voce, g = self._gruppo_da_piazzamento(p, per_nome[p.intenzione.nome])
            self._aggiungi_terra(voce, g)
            nuova_cache.append(dict(voce, gruppo=g))
        if self.blocco:
            json.dump({'blocco': self.blocco, 'gruppi': nuova_cache, 'eliminati': sorted(eliminati)},
                      open(os.path.join(self.cartella, 'terra_B%d.json' % self.blocco), 'w'),
                      indent=1, ensure_ascii=False)

    def _aggiungi_terra(self, voce, g):
        paese_id = USA if voce['lato'] == 'blue' else SIRIA
        self.aggiungi_gruppo(voce['lato'], 'vehicle', paese_id, 'USA' if voce['lato'] == 'blue' else 'Syria', g)
        self.piazzamenti_lua[voce['nome']] = voce['lua']
        self.resoconto['piazzamenti'].append(voce['resoconto'])

    def _gruppo_dagli_esiti(self, voce):
        """Applica gli esiti del blocco precedente a un gruppo della giornata.
        Restituisce (gruppo per la giornata, gruppo per la missione): il primo senza i distrutti, il
        secondo anche senza i fuori servizio (None se non resta nessun veicolo in servizio)."""
        es = self.esiti_prec or {}
        distrutti = set(es.get('distrutti', []))
        fermi = {n for n, fino in (voce.get('fermi') or {}).items() if int(fino) >= self.blocco}
        fermi |= {n for n, fino in (es.get('fuori_servizio') or {}).items() if int(fino) >= self.blocco}
        voce['fermi'] = {n: f for n, f in {**(voce.get('fermi') or {}), **(es.get('fuori_servizio') or {})}.items()
                         if int(f) >= self.blocco}
        pos = es.get('posizioni', {})
        g_cache = copy.deepcopy(voce['gruppo'])
        rimaste = {}
        for u in g_cache['units'].values():
            if u['name'] in distrutti:
                continue
            if u['name'] in pos:
                u['x'], u['y'] = pos[u['name']]
            rimaste[len(rimaste) + 1] = u
        if not rimaste:
            return None, None
        g_cache['units'] = rimaste
        g = copy.deepcopy(g_cache)
        unita = {}
        for u in g['units'].values():
            if u['name'] in fermi:
                continue
            u['unitId'] = self.cnt.unita
            self.cnt.unita += 1
            unita[len(unita) + 1] = u
        if not unita:
            return g_cache, None
        g['units'] = unita
        g['groupId'] = self.cnt.g()
        g['x'], g['y'] = unita[1]['x'], unita[1]['y']
        punti = g['route']['points']
        punti[1]['x'], punti[1]['y'] = g['x'], g['y']
        return g_cache, g

    def _gruppo_da_piazzamento(self, p, ordine):
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
        cfg = pz.SISTEMI[p.intenzione.sistema]
        lua = {
            'paese': paese_id, 'abilita': p.intenzione.abilita, 'attuale': 1,
            'unita': {k: {'tipo': t, 'avanti': float(a), 'destra': float(dx), 'rotta': float(r)}
                      for k, (t, a, dx, r) in enumerate(pz.schema(cfg, lato), 1)},
            'posizioni': {k: {'x': x, 'y': y, 'rotta': float(rt)}
                          for k, (x, y, rt) in enumerate([(p.x, p.y, p.rotta)] + p.alternative, 1)},
        }
        res = {'lato': lato, 'nome': p.intenzione.nome, 'sistema': p.intenzione.sistema, 'missione': missione,
               'lat_lon': [round(v, 5) for v in xy_to_ll(p.x, p.y)], 'dettagli': p.dettagli}
        return {'lato': lato, 'nome': p.intenzione.nome, 'sistema': p.intenzione.sistema, 'lua': lua, 'resoconto': res}, g

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
        decollo = max(0, hm(o.get('decollo', self.inizio)) - self.t0)
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
        carico_nome = o.get('carico') or 'nessuno'
        scelte = [x for x in LIVREE.get((paese_id, tipo), [])
                  if x[2] is None or any(carico_nome.startswith(r) for r in x[2])] or LIVREE.get((paese_id, tipo))
        livrea = None
        if scelte:
            n_liv = self.conta_livree.get((paese_id, tipo), 0)
            self.conta_livree[(paese_id, tipo)] = n_liv + 1
            livrea = scelte[n_liv % len(scelte)]
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
            if livrea:
                u['livery_id'] = livrea[0]
                if livrea[1] is not None:              # numero di bordo della squadriglia (es. VF-41 1xx)
                    u['onboard_num'] = '%03d' % (livrea[1] + (idx * 2 + k) % 100)
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
            voli = [(k, o) for k, o in enumerate(self.ordini[lato].get('missioni_aeree', []), 1) if self.nel_blocco(o)]
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
        b = self.meteo_blocco
        verso = w['wind']['atGround']['dir']
        kt = w['wind']['atGround']['speed'] / KT
        mmhg = w.get('qnh', 760)
        extra = ''
        if b.get('nebbia'):
            extra += ' Nebbia sulla costa (visibilita\' %.1f km).' % (b['nebbia']['visibilita_m'] / 1000)
        if b.get('polvere_m'):
            extra += ' Foschia e polvere.'
        return ('Vento al suolo da %03d/%d kt (2000 m: da %03d/%d kt). QNH %.2f inHg (%d hPa). %s, base %d ft. '
                'Visibilita\' %d km. %d C.%s' % ((verso + 180) % 360, round(kt), (w['wind']['at2000']['dir'] + 180) % 360,
                                               round(w['wind']['at2000']['speed'] / KT), mmhg / 25.4, round(mmhg * 1.33322),
                                               meteo.DESCRIZIONE_NUBI.get(b['nubi'], b['nubi']).capitalize(),
                                               round(b['base_m'] / FT, -2), w['visibility']['distance'] // 1000,
                                               b['temperatura'], extra))

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

    def canali_volo(self, volo, n):
        """Canali per una radio con n canali. Se la lista comune non ci sta, si tolgono nell'ordine:
        interni degli altri voli, Incirlik, cisterne; il proprio interno e la guardia restano."""
        lista = [(f, d) for _, f, d in self.canali()]
        for scarta in (lambda d: d.startswith('Interno') and d != 'Interno %s' % volo,
                       lambda d: d.startswith('Incirlik'), lambda d: d.startswith('Cisterna')):
            while len(lista) > n and any(scarta(d) for _, d in lista):
                idx = max(i for i, (_, d) in enumerate(lista) if scarta(d))
                lista.pop(idx)
        return [(k, f, d) for k, (f, d) in enumerate(lista[:n], 1)]

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
            for r, dati in modello.items():
                ch = {int(k): f for k, f in dati['channels'].items()}
                if dati['banda'] == 'UHF':          # il piano blu e' in UHF; VHF e FM restano di default
                    for pos, f, _ in self.canali_volo(nome, len(ch)):
                        ch[pos] = f
                radio[int(r)] = {'channels': ch, 'modulations': {int(k): v for k, v in dati['modulations'].items()},
                                 'channelsNames': {}}
            for u in g['units'].values():
                u['Radio'] = copy.deepcopy(radio)

    # ----------------------------------------------------------------- mappa
    def disegni(self):
        confini.aggiungi(self.m)
        # carta intel di ciascuna parte: dal suo rapporto del blocco (mai dalle posizioni vere)
        self.rapporti = {p: self.rapporto(p) for p in ('blu', 'rosso')}
        proprie = {'Blue': intel._basi('Blue', intel.BASI_BLU, intel.B_LINEA, 'Propria')
                   + intel._sam('Blue', intel.SAM_BLU, intel.B_LINEA, intel.B_TENUE, 'Propria')
                   + rapporto_intel.disegni(self.rapporti['blu'], 'Blue', intel.R_LINEA, intel.R_TENUE),
                   'Red': intel._basi('Red', intel.BASI_ROSSE, intel.R_LINEA, 'Propria')
                   + rapporto_intel.disegni(self.rapporti['rosso'], 'Red', intel.B_LINEA, intel.B_TENUE)}
        for strato in self.m['drawings']['layers'].values():
            if strato['name'] in proprie:
                strato['objects'] = {k: o for k, o in enumerate(proprie[strato['name']], 1)}
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

    def risorse_e_piloti(self):
        """AIM-54 contati (i voli di F-14 oltre la scorta passano al carico 0-6-2) e piloti a terra da
        soccorrere (un soldato per pilota nella posizione dell'eiezione, CSAR)."""
        self.aim54 = regole_speciali.scorta_aim54(self.giorno)
        resto = self.aim54
        for o in self.ordini['blue'].get('missioni_aeree', []):
            if not self.nel_blocco(o) or not o['velivolo'].startswith('F-14'):
                continue
            n = 2 if o.get('giocatore') else max(1, min(4, int(o.get('numero', 2))))
            servono = n * AIM54_PER_CARICO.get(o.get('carico'), 0)
            if servono > resto:
                self.avvisi.append('RISORSE: %s: AIM-54 non disponibili (scorta %d), carico cambiato in cap 0-6-2'
                                   % (o['nome'], resto))
                o['carico'] = 'cap 0-6-2'
            else:
                resto -= servono
        self.piloti_lua = {}
        for p in regole_speciali.piloti_a_terra(self.giorno):
            coal, paese, tipo = (2, USA, 'Soldier M4') if p['lato'] == 'blue' else (1, SIRIA, 'Infantry AK')
            nome = 'Pilota %s' % p['nome']
            uid = self.cnt.u()
            g = {'name': nome, 'groupId': self.cnt.g(), 'x': p['x'], 'y': p['y'], 'start_time': 0, 'hidden': False,
                 'visible': False, 'tasks': {}, 'task': 'Ground Nothing', 'uncontrollable': False,
                 'units': {1: {'type': tipo, 'name': nome, 'unitId': uid, 'x': p['x'], 'y': p['y'], 'heading': 0,
                               'skill': 'Average', 'playerCanDrive': False}},
                 'route': {'points': {1: wpt(p['x'], p['y'], 0, 0, azione='Off Road', ETA_locked=True)}}}
            self.aggiungi_gruppo(p['lato'], 'vehicle', paese, 'USA' if p['lato'] == 'blue' else 'Syria', g)
            self.piloti_lua[p['nome']] = {'x': p['x'], 'y': p['y'], 'coal': coal}
            self.avvisi.append('CSAR: pilota %s (%s) a terra in %s' % (p['nome'], p['lato'], p.get('lat_lon')))

    def dati_iads(self):
        """Tabella LEVANTE_IADS per levante_iads.lua: batterie SAM e sensori di ogni rete (rossa = 1, blu = 2)."""
        dati = {1: {'sam': {}, 'sensori': {}}, 2: {'sam': {}, 'sensori': {}}}
        for p in self.resoconto['piazzamenti']:
            coal = 2 if p['lato'] == 'blue' else 1
            if p['sistema'] in SAM_IADS:
                riserva = p.get('missione') == 'riserva' or 'riserva' in p['nome'].lower()
                dati[coal]['sam'][p['nome']] = {'tipo': p['sistema'], 'portata': pz.SISTEMI[p['sistema']]['portata_km'] * 1000,
                                                'mobile': p['sistema'] in ('sa6', 'sa8', 'hawk'), 'riserva': riserva}
            elif p['sistema'] == 'ewr':
                dati[coal]['sensori'][p['nome']] = 'radar'
            elif p['sistema'] in OSSERVATORI:
                dati[coal]['sensori'][p['nome']] = 'vista'
        for nome, (lato, g, o) in self.gruppi_aerei.items():
            if o['tipo'] == 'AWACS':
                dati[2 if lato == 'blue' else 1]['sensori'][nome] = 'awacs'
        return dati

    def rapporto(self, parte):
        """Rapporto intel della parte per questo blocco (o il piu' recente); in mancanza, la stima
        iniziale senza i siti gia' distrutti."""
        r = rapporto_intel.piu_recente(parte, self.giorno, self.blocco or 1)
        return r or rapporto_intel.iniziale(parte, self.giorno, self.blocco or 1, SITI_DISTRUTTI)

    # ----------------------------------------------------------------- tutto
    def costruisci(self):
        m = self.m
        anno, mese, giorno = (int(v) for v in self.par['data'].split('-'))
        m['date'] = {'Year': anno, 'Month': mese, 'Day': giorno}
        m['start_time'] = self.t0
        # meteo della giornata (campagna/GNN/meteo.json), nel momento del blocco
        self.meteo_giornata = meteo.della_giornata(self.giorno, self.par['data'])
        self.meteo_blocco = self.meteo_giornata['blocchi'][meteo.momento_blocco(self.nome_blocco, self.inizio)]
        m['weather'].update(meteo.tempo_dcs(self.meteo_blocco))
        m['weather']['name'] = 'Levante G%d' % self.giorno
        cx, cy = ll_to_xy(34.2, 35.3)
        m['map'] = {'centerX': cx, 'centerY': cy, 'zoom': 400000}
        m['forcedOptions'] = {'optionsView': 'optview_allies', 'labels': 0}
        if self.osservatore:
            m['forcedOptions'] = {'optionsView': 'optview_all', 'labels': 1, 'externalViews': True}
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

        self.risorse_e_piloti()
        self.navi_blu()
        self.navi_rosse()
        self.forze_terra()
        self.tutti_i_voli()
        self.disegni()
        self.avvisi += ['ERRORE: ' + e for e in verifica_miz.verifica(self.m)]
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
        inizio, fine = hm(self.inizio), hm(self.fine)
        # Levante, ora locale: alba ~05:30-06:30, tramonto ~16:45-19:45 secondo la stagione; margine prudente
        if inizio < 5 * 3600 or fine > 19 * 3600 + 30 * 60:
            self.avvisi.append('ORARIO: missione %s-%s fuori dal giorno, ma il giocatore non ha chiesto la notte'
                               % (self.inizio, self.fine))

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
                if not self.nel_blocco(a):
                    continue
                t = hm(a.get('decollo', self.inizio))
                finestre.append((t, t + (int(a.get('durata_min', 60)) + 40) * 60, max(1, min(4, int(a.get('numero', 2))))))
        picco = max([sum(n for s, e, n in finestre if s <= t < e) for t, _, _ in finestre] or [0])
        for lato, nome_l in (('blue', 'blu'), ('red', 'rosso')):
            fin = [(hm(a.get('decollo', self.inizio)), hm(a.get('decollo', self.inizio)) + (int(a.get('durata_min', 60)) + 40) * 60,
                    max(1, min(4, int(a.get('numero', 2))))) for a in self.ordini[lato].get('missioni_aeree', []) if self.nel_blocco(a)]
            pl = max([sum(n for s, e, n in fin if s <= t < e) for t, _, _ in fin] or [0])
            lim = ((self.par.get('limiti') or {}).get(nome_l) or {}).get('aerei_in_volo_max', BILANCIO['aerei_in_volo'] // 2)
            if pl > lim:
                self.avvisi.append('LIMITI: %s con %d aerei in volo contemporaneamente (stima), oltre il tetto di %d: '
                                   'ordini da correggere dal comandante' % (nome_l, pl, lim))
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
        nome = self.nome
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
        init = ('LEVANTE = { missione = "%s" }\n' % nome
                + ('LEVANTE_DEBUG = true\n' if self.osservatore else '') + lt.dump('LEVANTE_PIAZZAMENTI', self.piazzamenti_lua)
                + '\n' + lt.dump('LEVANTE_NAVI', self.navi_vento)
                + '\n' + lt.dump('LEVANTE_IADS', self.dati_iads())
                + '\n' + lt.dump('LEVANTE_ARTIGLIERIA', {p['nome']: True for p in self.resoconto['piazzamenti']
                                                          if p['sistema'] in ('artiglieria', 'lanciarazzi')})
                + '\n' + lt.dump('LEVANTE_TARPS', {n: True for n, (_, _, o) in self.gruppi_aerei.items()
                                                    if o.get('carico') == 'ricognizione TARPS'})
                + '\n' + lt.dump('LEVANTE_PILOTI', self.piloti_lua)
                + '\n' + lt.dump('LEVANTE_AIM54', {'nave': 'CVN-71 Theodore Roosevelt', 'scorta': self.aim54})
                + '\n' + lt.dump('LEVANTE_GIOCATORE', {n: True for n, (_, _, o) in self.gruppi_aerei.items() if o.get('giocatore')}))
        risorse = {'ResKey_Action_1': 'init.lua', 'ResKey_Action_2': 'levante_core.lua', 'ResKey_Action_3': 'levante_piazzatore.lua',
                   'ResKey_Action_4': 'levante_navi.lua', 'ResKey_Action_5': 'levante_prestazioni.lua',
                   'ResKey_Action_6': 'levante_iads.lua', 'ResKey_Action_7': 'levante_regole.lua'}
        for i, (commento, chiave) in enumerate((('INIT', 'ResKey_Action_1'), ('NUCLEO', 'ResKey_Action_2'),
                                                ('PIAZZATORE', 'ResKey_Action_3'), ('NAVI', 'ResKey_Action_4'),
                                                ('PRESTAZIONI', 'ResKey_Action_5'), ('IADS', 'ResKey_Action_6'),
                                                ('REGOLE', 'ResKey_Action_7')), 1):
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
            z.write(os.path.join(QUI, 'lua', 'levante_prestazioni.lua'), 'l10n/DEFAULT/levante_prestazioni.lua')
            z.write(os.path.join(QUI, 'lua', 'levante_iads.lua'), 'l10n/DEFAULT/levante_iads.lua')
            z.write(os.path.join(QUI, 'lua', 'levante_regole.lua'), 'l10n/DEFAULT/levante_regole.lua')
            for k, png in enumerate(tavolette, 1):
                z.writestr('KNEEBOARD/IMAGES/G%02d_%02d.png' % (self.giorno, k), png)
        for lato, co in self.m['coalition'].items():
            for c in co['country'].values():
                for cat in ('plane', 'helicopter', 'vehicle', 'ship'):
                    for g in c.get(cat, {}).get('group', {}).values():
                        for u in g['units'].values():
                            self.resoconto['unita'].append({'nome': u['name'], 'gruppo': g['name'], 'tipo': u['type'],
                                                            'lato': lato, 'categoria': cat})
        nome_c = 'costruzione_B%d.json' % self.blocco if self.blocco else 'costruzione.json'
        json.dump(self.resoconto, open(os.path.join(self.cartella, nome_c), 'w'), indent=1, ensure_ascii=False)
        return out


GUIDA_OSSERVATORE = """MISSIONE DA OSSERVARE (nessun volo del giocatore, tutto all'IA, carte scoperte)

Si entra come spettatore: mappa F10 con tutte le unita' ed etichette, viste esterne libere
(F2 aerei, F7 unita' di terra, F9 navi; CTRL+Z/Z per accelerare o rallentare il tempo).
Gli script scrivono a schermo cosa fanno (righe con l'ora):
- rete di difesa aerea: radar dei SAM accesi/spenti, silenzio dopo un antiradar, spostamenti dopo il tiro,
  ricerca autonoma quando la rete e' cieca;
- navi: rotta contro vento (prua, nodi, vento);
- aerei IA rientrati e rimossi; eiezioni; lanci di AIM-54.
A fine prova mandare dcs.log e i file di Saved Games\\DCS\\Levante1989\\."""


if __name__ == '__main__':
    import briefing_giornata
    giorno = int(sys.argv[1])
    argomenti = [a for a in sys.argv[2:] if not a.startswith('--')]
    blocco = int(argomenti[0]) if argomenti else None
    osservatore = '--osservatore' in sys.argv
    c = Costruttore(giorno, blocco, osservatore).costruisci()
    bb, br, tav = briefing_giornata.prepara(c)
    if osservatore:
        bb['testo'] = (GUIDA_OSSERVATORE + '\n\n========== BRIEFING BLU ==========\n\n' + bb['testo']
                       + '\n\n========== BRIEFING ROSSO ==========\n\n' + br)
        bb['titolo'] += ' [OSSERVATORE]'
    out = c.scrivi(bb, br, tav)
    print('scritto', out)
    print('gruppi di terra: %d, voli: %d' % (len(c.resoconto['piazzamenti']), len(c.resoconto['voli'])))
    for a in c.avvisi:
        print('AVVISO:', a)
