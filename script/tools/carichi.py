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
    'Su-25': {'appoggio': [(r'R-60', 2), (r'^B-8M1', 4), (r'^FAB-250', 4)]},
    'Tu-22M3': {'antinave': [(r'^Kh-22', 2)], 'bombe': [(r'OFAB-250', 2)]},
    'Mi-24V': {'appoggio': [(r'9M114', 2), (r'^B-8V20A|^UB-32', 4)]},
    # ------------------------------------------------------------------ blu
    'F-14A-135-GR-Early': {
        'aria-aria': [(r'^LAU-7 AIM-9L', 2), (r'^AIM-54A-Mk60', 4), (r'^AIM-7M$', 2), (r'^Fuel tank 300 gal$', 2)],
        'scorta': [(r'^LAU-7 AIM-9L', 2), (r'^AIM-54A-Mk60', 2), (r'^AIM-7M$', 3), (r'^Fuel tank 300 gal$', 2)],
    },
    'FA-18C_hornet': {
        'aria-aria': [(r'^AIM-9M Sidewinder', 2), (r'AIM-7M Sparrow', 6), (r'FPU-8A', 1)],
        'sead': [(r'^AIM-9M Sidewinder', 2), (r'^AGM-88C', 4), (r'^AIM-7M Sparrow', 2), (r'FPU-8A', 1)],
        'attacco': [(r'^AIM-9M Sidewinder', 2), (r'^Mk-83 - 1000lb', 4), (r'^AIM-7M Sparrow', 2), (r'FPU-8A', 1)],
    },
    'A6E': {'attacco': {1: '{HB_A6E_MK82_MER_6x}', 2: '{HB_A6E_AERO1D}', 4: '{HB_A6E_AERO1D}', 5: '{HB_A6E_MK82_MER_6x}'}},
    'F-4E-45MC': {'attacco': [(r'^6x Mk-82 - 500lb GP Bomb LD \(MER\)', 2), (r'AIM-7E', 4), (r'AIM-9J', 2)]},
    'AH-64D_BLK_II': {'appoggio': [(r'^M299 - 4 x AGM-114K Hellfire', 2), (r'^M261 - 19 x UnGd Rkts, 70 mm Hydra 70 M151 HE$', 2)]},
    'AV8BNA': {'appoggio': [(r'AIM-9M|AIM-9L', 2), (r'^Mk-82 - 500lb GP Bomb LD', 4)]},
}

SERBATOI = r'Fuel|FPU|PTB|300 gal|370|800L|1400L|1500|2000L|490 L'


def risolvi(tipo, nome):
    """{pilone: {'CLSID': ...}} per il carico 'nome' del velivolo 'tipo'."""
    if tipo not in CARICHI or nome not in CARICHI[tipo]:
        return {}
    spec = CARICHI[tipo][nome]
    if isinstance(spec, dict):
        return {n: {'CLSID': c} for n, c in sorted(spec.items())}
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
    return dict(sorted(out.items()))


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
