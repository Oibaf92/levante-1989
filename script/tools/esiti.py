"""Esiti di un blocco: confronta le unita' messe nella missione (costruzione_Bk.json) con lo stato
salvato in gioco alla fine del volo (stato_<missione>.lua) e scrive campagna/GNN/esiti_Bk.json.

  distrutti      : unita' presenti all'inizio e assenti (o morte) nello stato
  fuori_servizio : {unita': ultimo blocco di fermo} per le unita' di terra e le navi danneggiate
                   (vita < 70%: fermo nel blocco dopo; < 30%: anche in quello successivo)
  posizioni      : {unita': [x, y]} posizione finale (unita' di terra e navi)
  perdite_aeree  : {lato: {tipo: n}}
  gruppi_distrutti: gruppi con tutte le unita' distrutte (escono dai rapporti intel delle due parti)
Gli aerei IA rimossi dopo il rientro (levante_prestazioni.lua, extra.rientrati) non sono perdite.
Le regole sono nel README (sezione Perdite).
"""
import json
import os

import luatable as lt

DANNO_LIEVE, DANNO_GRAVE = 0.70, 0.30


def esiti(stato, costruzione, blocco):
    vive = {}
    for g in (stato.get('gruppi') or {}).values():
        for u in (g.get('unita') or {}).values():
            vive[u['nome']] = u
    rientrati = set(((stato.get('extra') or {}).get('rientrati') or {}).keys())
    out = {'blocco': blocco, 'missione': stato.get('missione'), 'distrutti': [], 'fuori_servizio': {},
           'posizioni': {}, 'perdite_aeree': {}}
    for u in costruzione['unita']:
        s = vive.get(u['nome'])
        if u['nome'] in rientrati:
            continue
        if s is None or (s.get('vita') or 0) <= 0:
            out['distrutti'].append(u['nome'])
            if u['categoria'] in ('plane', 'helicopter'):
                per = out['perdite_aeree'].setdefault(u['lato'], {})
                per[u['tipo']] = per.get(u['tipo'], 0) + 1
            continue
        if u['categoria'] in ('vehicle', 'ship'):
            out['posizioni'][u['nome']] = [s['pos']['x'], s['pos']['y']]
            v0 = s.get('vita0') or 0
            if v0 > 0:
                r = s['vita'] / v0
                if r < DANNO_GRAVE:
                    out['fuori_servizio'][u['nome']] = blocco + 2
                elif r < DANNO_LIEVE:
                    out['fuori_servizio'][u['nome']] = blocco + 1
    per_gruppo = {}
    for u in costruzione['unita']:
        if u['nome'] not in rientrati:
            per_gruppo.setdefault(u['gruppo'], []).append(u['nome'])
    morti = set(out['distrutti'])
    out['gruppi_distrutti'] = sorted(g for g, nomi in per_gruppo.items() if all(n in morti for n in nomi))
    return out


def scrivi(percorso_stato, cartella, blocco):
    _, stato = lt.parse(open(percorso_stato, encoding='utf-8').read())
    costruzione = json.load(open(os.path.join(cartella, 'costruzione_B%d.json' % blocco), encoding='utf-8'))
    e = esiti(stato, costruzione, blocco)
    json.dump(e, open(os.path.join(cartella, 'esiti_B%d.json' % blocco), 'w'), indent=1, ensure_ascii=False)
    return e
