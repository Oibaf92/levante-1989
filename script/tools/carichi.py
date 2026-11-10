"""Menu dei carichi d'armi (era 1989) per i velivoli della campagna.

Ogni carico: {pilone: espressione regolare sul nome dell'arma in DCS}. Il risolutore
trova il CLSID esatto in script/dati/piloni.json; un pilone che non trova nulla e'
un errore (carico non valido), cosi' non si generano mai piloni vuoti per sbaglio.
"""
import json
import os
import re

QUI = os.path.dirname(os.path.abspath(__file__))
PILONI = json.load(open(os.path.join(QUI, '..', 'dati', 'piloni.json'), encoding='utf-8'))

# Ogni carico: lista di (espressione regolare sul nome dell'arma, quantita' di piloni).
# Ogni carico e' una di due forme:
#   - lista di (espressione regolare sul nome dell'arma, quantita' di piloni), in ordine di
#     assegnazione: il risolutore trova piloni e CLSID;
#   - dizionario {pilone: CLSID} gia' verificato in DCS (es. dalla missione del giocatore).
# Versioni dei missili (autunno 1989, scelte dal giocatore): AIM-54C Mk47, AIM-7MH, AIM-9M.
# L'F-4E in DCS non ha l'AIM-7MH: usa l'AIM-7M.
# F-14 (stazioni DCS: 1/10 punte ala, 2/9 spalle, 3/8 serbatoi, 4-7 ventre; 4 e 7 = pallet anteriori)
_F54, _F7, _F9, _FT = 'AIM-54C-Mk47', 'AIM-7MH', 'LAU-7 AIM-9M', 'Fuel tank 300 gal'
F14_232 = {(1, 10): _F9, (2, 9, 5): _F7, (3, 8): _FT, (4, 7): _F54}       # 2 AIM-54 sui pallet anteriori, 3 AIM-7, 2 AIM-9
F14_062 = {(1, 10): _F9, (2, 9, 4, 5, 6, 7): _F7, (3, 8): _FT}            # 0 AIM-54, 6 AIM-7, 2 AIM-9
# F/A-18C (stazioni 1/9 punte ala, 2/8 ala esterne, 3/7 ala interne, 4/6 fusoliera, 5 centrale)
_H9, _H7F, _H7A, _HT = 'AIM-9M Sidewinder IR AAM', 'AIM-7MH Sparrow Semi-Active Radar', \
    'LAU-115C - AIM-7MH Sparrow Semi-Active Radar', 'FPU-8A Fuel Tank 330 gallons'
FA18_CAP_4 = {(1, 9): _H9, (2, 8): _H7A, (4, 6): _H7F, (3, 7): _HT}               # 2 AIM-9, 4 AIM-7, 2 serbatoi alari
FA18_CAP_6 = {(1, 9): _H9, (2, 3, 7, 8): _H7A, (4, 6): _H7F, (5,): _HT}           # 6 AIM-7, 1 serbatoio: AUTONOMIA RIDOTTA

# carichi con autonomia ridotta: minuti massimi sull'obiettivo senza rifornimento (oltre -> avviso)
AUTONOMIA_RIDOTTA = {'FA-18C_hornet': {'cap 2-6 serbatoio centrale': 40, 'sead pesante': 40, 'cas': 40},
                     'F-4E-45MC': {'strike Mk-82 pesante': 20, 'attacco': 20}}

F14_CARICHI = {'cap 2-3-2': F14_232, 'cap 0-6-2': F14_062,
               'aria-aria': F14_232, 'scorta': F14_232}   # nomi storici = 2-3-2 (definizioni per nome, vedi _tabella)

def _fisso(tipo, mappa):
    """{pilone: nome esatto dell'arma} -> {pilone: CLSID}, verificando che l'arma esista su quel
    pilone (script/dati/piloni.json). Errore subito se un nome e' sbagliato."""
    pil = PILONI[tipo]['pilastri']
    out = {}
    for n, nome in mappa.items():
        if nome not in pil.get(str(n), {}):
            raise KeyError('%s pilone %s: arma "%s" non disponibile' % (tipo, n, nome))
        out[n] = pil[str(n)][nome]
    return out


def _simm(sx_dx, **singoli):
    """Coppie simmetriche {(sx, dx): arma} + piloni singoli -> {pilone: arma}."""
    out = {}
    for coppia, arma in sx_dx.items():
        for n in coppia:
            out[n] = arma
    out.update({int(k[1:]): v for k, v in singoli.items()})
    return out


# ---------------------------------------------------------------------------------- F/A-18C
_HARM = 'AGM-88C HARM - High Speed Anti-Radiation Missile'
_H_BASE = {(1, 9): _H9, (4, 6): _H7F}                     # autodifesa: 2 AIM-9 + 2 AIM-7 in fusoliera
FA18 = {
    'sead': {**_H_BASE, (2, 8): _HARM, (3, 7): _HT},
    'sead pesante': {**_H_BASE, (2, 3, 7, 8): _HARM, (5,): _HT},
    'strike Mk-84': {**_H_BASE, (2, 8): 'Mk-84 - 2000lb GP Bomb LD', (3, 7): _HT},
    'strike Mk-83': {**_H_BASE, (2, 8): 'BRU-33 with 2 x Mk-83 - 1000lb GP Bomb LD', (3, 7): _HT},
    'cas': {**_H_BASE, (2, 8): 'BRU-33 with 2 x Mk-20 Rockeye - 490lbs CBU, 247 x HEAT Bomblets',
            (3, 7): 'LAU-117 - AGM-65F - Maverick F (IIR ASM)', (5,): _HT},
    'antinave': {**_H_BASE, (2, 8): 'AGM-84D Harpoon AShM', (3, 7): _HT},
}

# ------------------------------------------------------------------------------------- F-4E
# stazioni: 1/13 ala esterne, 3/11 ala interne, 2-4/10-12 binari AIM-9, 5/6/8/9 pozzetti AIM-7
# (6 = anteriore sinistro: pod ALQ-131 o Pave Spike), 7 centrale
_P9, _P7, _PT, _PECM = 'AIM-9M Sidewinder IR AAM', 'AIM-7M Sparrow Semi-Active Radar', \
    'Sargent Fletcher Fuel Tank 370 gallons', 'ALQ-131 - ECM Pod Rack'
_P_BASE = {(2, 12): _P9, (5, 8, 9): _P7, (6,): _PECM, (1, 13): _PT}
F4E = {
    'cap': {(2, 4, 10, 12): _P9, (5, 6, 8, 9): _P7, (1, 13): _PT, (3,): 'ALQ-131 - ECM Pod'},
    'strike Mk-82': {**_P_BASE, (7,): '6x Mk-82 - 500lb GP Bomb LD (MER)'},
    'strike Mk-82 pesante': {**_P_BASE, (1, 13): '6x Mk-82 - 500lb GP Bomb LD (MER)'},   # senza serbatoi
    'cas maverick': {**_P_BASE, (3, 11): '3x AGM-65B - Maverick B (TV Guided) (LAU-88)'},
    'cas cbu': {**_P_BASE, (7,): '4x CBU-87 - 202 x CEM Cluster Bomb (MER)',
                (3, 11): '2x CBU-87 - 202 x CEM Cluster Bomb (TER)'},
    'sead': {**_P_BASE, (3, 11): 'AGM-45B Shrike ARM (LAU-34)', (7,): '4x CBU-87 - 202 x CEM Cluster Bomb (MER)'},
    'strike laser GBU-12': {**_P_BASE, (6,): 'AN/AVQ-23 Pave Spike - Targeting Pod Rack',
                            (3, 11): '2x GBU-12 - 500lb Laser Guided Bomb (TER)'},
    'strike laser GBU-10': {**_P_BASE, (6,): 'AN/AVQ-23 Pave Spike - Targeting Pod Rack',
                            (3, 11): 'GBU-10 - 2000lb Laser Guided Bomb'},
}

# -------------------------------------------------------------------------------------- F-14
# aria-terra: eccezione voluta dal giocatore (nella realta' dal 1990-92); niente pod di puntamento
_F_BASE = {(1, 10): _F9, (2, 9): _F7, (3, 8): _FT}
F14_AT = {
    'strike Mk-84': {**_F_BASE, (4, 5, 6, 7): 'Mk-84'},
    'strike Mk-82': {**_F_BASE, (4, 7): 'MAK79 4 Mk-82', (5, 6): 'MAK79 3 Mk-82'},   # 14 Mk-82
}

# ----------------------------------------------------------------------------------- AH-64D
_HF, _HY = 'M299 - 4 x AGM-114K Hellfire', 'M261 - 19 x UnGd Rkts, 70 mm Hydra 70 M151 HE'
AH64 = {
    'anticarro': {(1, 2, 3, 4): _HF},
    'appoggio': {(1, 4): _HF, (2, 3): _HY},
    'fanteria': {(1,): _HF, (2, 3, 4): _HY},
}

# ------------------------------------------------------------------------------------ Su-25
_S60, _SB8 = 'R-60M (AA-8 Aphid-B) - IR AAM', 'B-8M1 - 20 x UnGd Rkts, 80 mm S-8KOM HEAT/Frag'
SU25 = {
    'appoggio': {(1, 10): _S60, (2, 5, 6, 9): _SB8, (3, 4, 7, 8): 'FAB-250M-62 - 250 kg GP Bomb LD'},
    'anticarro': {(1, 10): _S60, (2, 9): _SB8, (3, 4, 7, 8): 'RBK-250 - 42 x PTAB-2.5M, 250kg CBU Medium HEAT/AP',
                  (5, 6): 'SPPU-22-1 - 2 x 23mm  GSh-23L Autocannon Pod'},
    'strike': {(1, 10): _S60, (2, 3, 4, 7, 8, 9): 'FAB-500M-62 - 500 kg GP Bomb LD', (5, 6): 'Fuel tank 800L Wing'},
    'precisione': {(1, 10): _S60, (5, 6): 'Kh-29L (AS-14 Kedge) - 657kg, ASM, Semi-Act Laser',
                   (4, 7): 'Kh-25ML (AS-10 Karen) - 300kg, ASM, Semi-Act Laser', (2, 9): _SB8,
                   (3, 8): 'Fuel tank 800L Wing'},
}

# ----------------------------------------------------------------------------- Mi-24P, Mi-8MT
_SH, _B8V = '2 x 9M114 Shturm (AT-6 Spiral) - ATGM, SACLOS, HEAT', 'B-8V20A - 20 x UnGd Rkts, 80 mm S-8KOM HEAT/Frag'
_GUV = 'GUV-8700 w AP-30 - 30mm Grenade Launcher'
MI24P = {
    'anticarro': {(1, 2, 5, 6): _SH, (3, 4): _B8V},
    'appoggio': {(1, 6): _SH, (2, 3, 4, 5): _B8V},
    'fanteria': {(1, 6): _SH, (2, 5): _GUV, (3, 4): _B8V},
}
MI8 = {
    'trasporto': {},
    'armato': {(1, 6): _GUV, (2, 3, 4, 5): _B8V},
}


def _tabella(tipo, carichi):
    return {nome: _fisso(tipo, _simm(c)) for nome, c in carichi.items()}


CARICHI = {
    # ------------------------------------------------------------------ rosso
    'MiG-29 Fulcrum': {'aria-aria': {1: '{MISSILE_R-60M_APU-60}', 2: '{MISSILE_R-60M_APU-60}', 3: '{MISSILE_R-27R_APU-470}',
                                     4: '{PTB_1500_MIG29A}', 5: '{MISSILE_R-27R_APU-470}', 6: '{MISSILE_R-60M_APU-60}',
                                     7: '{MISSILE_R-60M_APU-60}'}},
    'MiG-23MLD': {'aria-aria': {2: '{CCF898C9-5BC7-49A4-9D1E-C3ED3D5166A1}', 3: '{B0DBC591-0F52-4F7D-AD7B-51E67725FB81}',
                                4: '{A5BAEAB7-6FAF-4236-AF72-0FD900F493F9}', 5: '{275A2855-4A79-4B2D-B082-91EA2ADF4691}',
                                6: '{CCF898C9-5BC7-49A4-9D1E-C3ED3D5166A1}'}},
    'MiG-21Bis': {'aria-aria': {1: '{R-60 2L}', 2: '{R-3R}', 3: '{PTB_800_MIG21}', 4: '{R-3R}', 5: '{R-60 2R}', 6: '{ASO-2}'},
                  'attacco': [(r'^FAB-250', 2), (r'^APU-60-1M with R-60 ', 2), (r'Fuel Tank 490 L Central', 1)]},
    'MiG-25PD': {'aria-aria': [(r'R-40R', 2), (r'R-40T', 2)]},
    'Su-17M4': {'bombe': [(r'^FAB-500M-62', 6), (r'R-60M', 2)],
                'razzi': [(r'^B-8M1 - 20 x UnGd Rkts, 80 mm S-8KOM', 4), (r'^MBD3-U6-68 - 2 x OFAB-250', 2), (r'R-60M', 2)]},
    'Su-24M': {'bombe': [(r'^FAB-500M-62', 4), (r'^FAB-250M-62', 4)],
               'antiradar': [(r'^Kh-58U', 2), (r'^Kh-25MPU', 2), (r'Fuel tank 2000L', 1)]},
    'Su-25': _tabella('Su-25', SU25),
    'Tu-22M3': {'antinave': [(r'^Kh-22', 2)], 'bombe': [(r'OFAB-250', 2)]},
    'Mi-24V': {'appoggio': [(r'9M114', 2), (r'^B-8V20A|^UB-32', 4)]},
    'Mi-24P': _tabella('Mi-24P', MI24P),
    'Mi-8MT': _tabella('Mi-8MT', MI8),
    # ------------------------------------------------------------------ blu
    # F-14: carichi CAP tipici indicati dal giocatore (AIM-54 - AIM-7 - AIM-9), piloni fissati a mano.
    'F-14A-135-GR-Early': _tabella('F-14A-135-GR-Early', {**F14_CARICHI, **F14_AT}),
    'F-14B': _tabella('F-14B', {**F14_CARICHI, **F14_AT}),
    'FA-18C_hornet': {
        **_tabella('FA-18C_hornet', {'cap 2-4 serbatoi ali': FA18_CAP_4, 'cap 2-6 serbatoio centrale': FA18_CAP_6,
                                     'aria-aria': FA18_CAP_4, **FA18}),
        'attacco': _tabella('FA-18C_hornet', FA18)['strike Mk-83'],      # nome storico
    },
    'A6E': {'attacco': {1: '{HB_A6E_MK82_MER_6x}', 2: '{HB_A6E_AERO1D}', 4: '{HB_A6E_AERO1D}', 5: '{HB_A6E_MK82_MER_6x}'}},
    'F-4E-45MC': {**_tabella('F-4E-45MC', F4E), 'attacco': _tabella('F-4E-45MC', F4E)['strike Mk-82 pesante']},
    'AH-64D_BLK_II': _tabella('AH-64D_BLK_II', AH64),
    'AV8BNA': {'appoggio': [(r'AIM-9M|AIM-9L', 2), (r'^Mk-82 - 500lb GP Bomb LD', 4)]},
}

SERBATOI = r'Fuel|FPU|PTB|300 gal|370|800L|1400L|1500|2000L|490 L'

# Era 1989 (docs/lezioni.md): niente GPS, niente AIM-120 / R-77, niente pod di puntamento moderni,
# niente armi entrate in servizio dopo il 1989. Eccezione voluta dal giocatore: AH-64D e CH-47F
# (velivoli e loro armamento).
ERA_VIETATE = (r'AIM-120|AMRAAM|AIM-9X|R-77|RVV-AE|GBU-3[12]|GBU-38|GBU-54|JDAM|AGM-154|JSOW|CBU-97|CBU-10[345]'
               r'|WCMD|SLAM|AGM-84[EHK]|LITENING|AAQ-28|ATFLIR|ASQ-228|LANTIRN|GPS')
ERA_ECCEZIONI = ('AH-64D_BLK_II', 'CH-47Fbl1')


def fuori_era(tipo, pyloni):
    """Elenco delle armi non ammesse nel 1989 in un carico {pilone: {'CLSID': ...}}."""
    if tipo in ERA_ECCEZIONI:
        return []
    inv = {c: k for opz in PILONI.get(tipo, {}).get('pilastri', {}).values() for k, c in opz.items()}
    out = []
    for n, v in pyloni.items():
        nome = inv.get(v['CLSID'], '') + ' ' + v['CLSID']
        if re.search(ERA_VIETATE, nome):
            out.append('%s (pilone %s)' % (nome.strip(), n))
    return out


def risolvi(tipo, nome):
    """{pilone: {'CLSID': ...}} per il carico 'nome' del velivolo 'tipo'."""
    if tipo not in CARICHI or nome not in CARICHI[tipo]:
        return {}
    spec = CARICHI[tipo][nome]
    if isinstance(spec, dict):
        out = {n: {'CLSID': c} for n, c in sorted(spec.items())}
        _controlla_era(tipo, nome, out)
        return out
    pil = {int(k): v for k, v in PILONI[tipo]['pilastri'].items()}
    centro = (min(pil) + max(pil)) / 2
    out = {}
    for espr, quanti in spec:
        compat = {n: next(c for k, c in opz.items() if re.search(espr, k)) for n, opz in pil.items()
                  if n not in out and any(re.search(espr, k) for k in opz)}
        if len(compat) < quanti:
            raise ValueError('%s/%s: %r su %d piloni, liberi solo %s' % (tipo, nome, espr, quanti, sorted(compat)))
        # serbatoi verso il centro, armi verso l'esterno, a coppie simmetriche
        verso_centro = bool(re.search(SERBATOI, espr))
        ordine = sorted(compat, key=lambda n: (abs(n - centro) if verso_centro else -abs(n - centro), n))
        for n in ordine[:quanti]:
            out[n] = {'CLSID': compat[n]}
    out = dict(sorted(out.items()))
    _controlla_era(tipo, nome, out)
    return out


def _controlla_era(tipo, nome, pyloni):
    vietate = fuori_era(tipo, pyloni)
    if vietate:
        raise ValueError('%s/%s: armi fuori era 1989: %s' % (tipo, nome, '; '.join(vietate)))


def nomi_armi(tipo, nome):
    pil = PILONI.get(tipo, {}).get('pilastri', {})
    inv = {}
    for n, opzioni in pil.items():
        for k, c in opzioni.items():
            inv[c] = k
    return {n: inv.get(v['CLSID'], v['CLSID']) for n, v in risolvi(tipo, nome).items()}


if __name__ == '__main__':
    errori = 0
    for tipo, carichi in CARICHI.items():
        for nome in carichi:
            try:
                armi = nomi_armi(tipo, nome)
                print('%-20s %-10s ok: %s' % (tipo, nome, '; '.join('%s=%s' % (k, v[:28]) for k, v in sorted(armi.items()))))
            except ValueError as e:
                errori += 1
                print('ERRORE', e)
    print('errori:', errori)
