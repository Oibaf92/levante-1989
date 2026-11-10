"""Regole speciali della campagna (README, "Risorse e intelligence speciali" e "Piloti abbattuti").

Stato di campagna:
  campagna/risorse.json  {"aim54": {"scorta": 48, "giorno": 16}}
  campagna/piloti.json   [{"nome", "lato", "x", "y", "giorno", "blocco", "stato": a terra|recuperato|catturato}]

Dall'importazione di un blocco (estratto dello stato salvato in gioco, LEVANTE.extra):
  - AIM-54 lanciati dai blu -> scorta ridotta;
  - eiezioni -> piloti recuperati subito (mare o territorio amico) o a terra (CSAR);
  - piloti recuperati dagli elicotteri (extra.csar);
  - osservazioni per l'intel: tiri d'artiglieria rossa entro TPQ_RAGGIO dal radar AN/TPQ-37 (blu),
    unita' di terra nemiche entro TARPS_RAGGIO dalla traccia di un F-14 TARPS atterrato (blu).
"""
import json
import math
import os
import random

from geo import ll_to_xy, xy_to_ll

QUI = os.path.dirname(os.path.abspath(__file__))
CAMPAGNA = os.path.join(QUI, '..', '..', 'campagna')
AIM54_INIZIALE, AIM54_AL_GIORNO = 48, 4
TPQ_POS, TPQ_RAGGIO, TPQ_ERRORE = (33.95, 35.62), 30000, 300      # radar dei Marines nella testa di ponte
TARPS_RAGGIO = 5000
TESTA_DI_PONTE = [(34.15, 35.645), (34.12, 35.80), (34.00, 35.88), (33.88, 35.76), (33.81, 35.66),
                  (33.81, 35.60), (33.83, 35.55), (33.88, 35.50), (33.98, 35.60), (34.06, 35.62)]


def _file(nome):
    return os.path.join(CAMPAGNA, nome)


def carica(nome, vuoto):
    p = _file(nome)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else vuoto


def salva(nome, dati):
    json.dump(dati, open(_file(nome), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


def dentro(lat, lon, poligono):
    x, y = lon, lat
    ok = False
    n = len(poligono)
    for i in range(n):
        y1, x1 = poligono[i]
        y2, x2 = poligono[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-9) + x1:
            ok = not ok
    return ok


# ------------------------------------------------------------------ AIM-54
def scorta_aim54(giorno):
    """Scorta all'inizio della giornata: +4 per ogni giorno passato dall'ultimo aggiornamento."""
    r = carica('risorse.json', {})
    a = r.get('aim54') or {'scorta': AIM54_INIZIALE, 'giorno': giorno}
    if giorno > a['giorno']:
        a = {'scorta': a['scorta'] + AIM54_AL_GIORNO * (giorno - a['giorno']), 'giorno': giorno}
        r['aim54'] = a
        salva('risorse.json', r)
    return a['scorta']


# ------------------------------------------------------------------ piloti
def piloti_a_terra(giorno, lato=None):
    """Piloti ancora da recuperare; chi e' a terra da oltre la giornata successiva diventa catturato."""
    lista = carica('piloti.json', [])
    cambiato = False
    for p in lista:
        if p['stato'] == 'a terra' and giorno > p['giorno'] + 1:
            p['stato'] = 'catturato'
            cambiato = True
    if cambiato:
        salva('piloti.json', lista)
    return [p for p in lista if p['stato'] == 'a terra' and (lato is None or p['lato'] == lato)]


# ------------------------------------------------------------------ importazione di un blocco
def importa(extra, giorno, blocco, piazzamenti, stato):
    """Applica le regole a cio' che e' successo nel blocco; restituisce le osservazioni per l'intel."""
    extra = extra or {}
    # AIM-54
    lanciati = int(((extra.get('aim54') or {}).get(2)) or ((extra.get('aim54') or {}).get('2')) or 0)
    if lanciati:
        r = carica('risorse.json', {})
        a = r.get('aim54') or {'scorta': AIM54_INIZIALE, 'giorno': giorno}
        a['scorta'] = max(0, a['scorta'] - lanciati)
        r['aim54'] = a
        salva('risorse.json', r)
    # piloti
    piloti = carica('piloti.json', [])
    for e in (extra.get('eiezioni') or {}).values():
        lato = 'blue' if int(e['coal']) == 2 else 'red'
        lat, lon = xy_to_ll(e['x'], e['y'])
        in_testa = dentro(lat, lon, TESTA_DI_PONTE)
        amico = e.get('mare') or (in_testa if lato == 'blue' else not in_testa)
        piloti.append({'nome': e['nome'], 'tipo': e.get('tipo'), 'lato': lato, 'x': e['x'], 'y': e['y'],
                       'lat_lon': [round(lat, 4), round(lon, 4)], 'giorno': giorno, 'blocco': blocco,
                       'giocatore': bool(e.get('giocatore')), 'stato': 'recuperato' if amico else 'a terra'})
    for nome in (extra.get('csar') or {}):
        for p in piloti:
            if p['nome'] == nome and p['stato'] == 'a terra':
                p['stato'] = 'recuperato'
    salva('piloti.json', piloti)
    # osservazioni per l'intel blu
    sistemi = {p['nome']: p['sistema'] for p in piazzamenti}
    lati = {p['nome']: p['lato'] for p in piazzamenti}
    oss = []
    tx, ty = ll_to_xy(*TPQ_POS)
    visti = set()
    for t in (extra.get('tiri') or {}).values():
        g = t['gruppo']
        if lati.get(g) != 'red' or g in visti or math.hypot(t['x'] - tx, t['y'] - ty) > TPQ_RAGGIO:
            continue
        visti.add(g)
        a = random.uniform(0, 2 * math.pi)
        d = random.uniform(100, TPQ_ERRORE)
        lat, lon = xy_to_ll(t['x'] + d * math.cos(a), t['y'] + d * math.sin(a))
        oss.append({'lat': round(lat, 4), 'lon': round(lon, 4), 'tipo': sistemi.get(g, 'artiglieria'),
                    'nome': '%s localizzata' % sistemi.get(g, 'artiglieria').capitalize(), 'gruppo': g,
                    'fonte': 'AN/TPQ-37', 'visto': 'G%d B%d %s' % (giorno, blocco, t.get('ora', ''))})
    tracce = [t['punti'] for t in (extra.get('tarps') or {}).values() if t.get('atterrato')]
    punti = [(p['x'], p['y']) for tr in tracce for p in (tr.values() if isinstance(tr, dict) else tr)]
    if punti:
        for g in (stato.get('gruppi') or {}).values():
            if g.get('coalizione') != 'rosso' or g.get('categoria') != 'terra' or g['nome'] not in sistemi:
                continue
            un = list((g.get('unita') or {}).values())
            if not un:
                continue
            cx = sum(u['pos']['x'] for u in un) / len(un)
            cy = sum(u['pos']['y'] for u in un) / len(un)
            if any(math.hypot(cx - x, cy - y) < TARPS_RAGGIO for x, y in punti):
                lat, lon = xy_to_ll(cx, cy)
                sis = sistemi[g['nome']]
                raggio = {'sa2': 40, 'sa3': 22, 'sa5': 150, 'sa6': 25, 'sa8': 10}.get(sis)
                v = {'lat': round(lat, 4), 'lon': round(lon, 4), 'tipo': sis, 'nome': '%s (foto TARPS)' % sis.upper(),
                     'gruppo': g['nome'], 'fonte': 'TARPS', 'visto': 'G%d B%d' % (giorno, blocco)}
                if raggio:
                    v['raggio_km'] = raggio
                oss.append(v)
    return {'blu': oss, 'rosso': []}
