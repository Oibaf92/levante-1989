"""Rapporti intel per parte e per blocco: cio' che un comandante sa (o crede di sapere) del nemico.

File riservati: blu/intel_GNN_Bk.json e rosso/intel_GNN_Bk.json (ognuno li vede solo la sua parte).
Da questi si disegnano la carta intel F10 della parte del giocatore e la tavoletta INTEL: mai dalle
posizioni vere (docs/lezioni.md, Mappa F10).

Formato:
{ "parte": "blu", "giorno": 16, "blocco": 1,
  "basi": [ {"lat":..,"lon":..,"tipo":"aerea","nome":"..","dettaglio":".."} ],
  "sam":  [ {"lat":..,"lon":..,"raggio_km":25,"tipo":"sa6","nome":"..","gruppo":"<nome vero se noto>",
             "certezza":"confermato|probabile|vecchio","fonte":"..","visto":"G16 B1"} ],
  "terra":[ {"lat":..,"lon":..,"tipo":"artiglieria","nome":"..","gruppo":"..","certezza":"..","fonte":"..","visto":".."} ],
  "note": ["testo", ...] }

Uso:  python3 script/tools/rapporto_intel.py <giorno> <blocco>
      crea i rapporti del blocco dal rapporto precedente + esiti del blocco precedente
      (+ osservazioni registrate negli esiti), oppure, se non ce n'e', dalla stima iniziale (intel.py).
"""
import json
import os
import sys

from geo import ll_to_xy
import intel
import simboli

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.join(QUI, '..', '..')
CARTELLE = {'blu': 'blu', 'rosso': 'rosso'}
MOBILI = {'sa6', 'sa8', 'aaa', 'carri', 'meccanizzata', 'artiglieria', 'lanciarazzi', 'contraerea_mobile'}
DEGRADO = {'confermato': 'probabile', 'probabile': 'vecchio', 'vecchio': None}    # None: si cancella


def percorso(parte, giorno, blocco):
    return os.path.join(RADICE, CARTELLE[parte], 'intel_G%02d_B%d.json' % (giorno, blocco))


def carica(parte, giorno, blocco):
    p = percorso(parte, giorno, blocco)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None


def piu_recente(parte, giorno, blocco):
    """Il rapporto valido per un blocco: quello del blocco, o il piu' recente precedente (anche dei giorni prima)."""
    for g in range(giorno, 0, -1):
        for b in (range(blocco, 0, -1) if g == giorno else range(9, 0, -1)):
            r = carica(parte, g, b)
            if r:
                return r
    return None


def iniziale(parte, giorno, blocco, distrutti=()):
    """Stima di partenza (situazione di pace, intel.py), senza i siti gia' distrutti."""
    if parte == 'blu':
        basi, sam = intel.BASI_ROSSE, intel.SAM_ROSSI
    else:
        basi, sam = intel.BASI_BLU_VISTE_DAL_ROSSO, intel.SAM_BLU_VISTI_DAL_ROSSO
    return {
        'parte': parte, 'giorno': giorno, 'blocco': blocco,
        'basi': [{'lat': a, 'lon': o, 'tipo': t, 'nome': n, 'dettaglio': d} for a, o, t, n, d in basi],
        'sam': [{'lat': a, 'lon': o, 'raggio_km': r, 'tipo': t, 'nome': n, 'gruppo': n,
                 'certezza': 'probabile' if t in MOBILI else 'confermato', 'fonte': 'stima iniziale', 'visto': '-'}
                for a, o, r, t, n in sam if n not in distrutti],
        'terra': [], 'note': [],
    }


def aggiorna(prec, giorno, blocco, esiti=None):
    """Rapporto del blocco dal precedente: i sistemi mobili invecchiano, i gruppi distrutti
    spariscono, le osservazioni del blocco precedente (esiti['osservazioni'][parte]) entrano confermate."""
    esiti = esiti or {}
    parte = prec['parte']
    morti_gruppi = set(esiti.get('gruppi_distrutti', []))
    nuovo = {'parte': parte, 'giorno': giorno, 'blocco': blocco, 'basi': prec.get('basi', []),
             'sam': [], 'terra': [], 'note': []}
    for chiave in ('sam', 'terra'):
        for v in prec.get(chiave, []):
            if v.get('gruppo') in morti_gruppi:
                continue
            v = dict(v)
            if v['tipo'] in MOBILI:
                v['certezza'] = DEGRADO.get(v.get('certezza', 'probabile'))
                if v['certezza'] is None:
                    continue
            nuovo[chiave].append(v)
    for oss in (esiti.get('osservazioni') or {}).get(parte, []):
        chiave = 'sam' if oss['tipo'].startswith('sa') or oss['tipo'] == 'hawk' else 'terra'
        nuovo[chiave] = [v for v in nuovo[chiave] if v.get('gruppo') != oss.get('gruppo')]
        nuovo[chiave].append(dict(oss, certezza='confermato'))
    return nuovo


def salva(rapporto):
    p = percorso(rapporto['parte'], rapporto['giorno'], rapporto['blocco'])
    json.dump(rapporto, open(p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    return p


# ------------------------------------------------------------------- disegno
COLORI = {'confermato': 1.0, 'probabile': 0.75, 'vecchio': 0.45}


def _colore(base, certezza):
    """Stesso colore, piu' trasparente quando l'informazione e' meno certa."""
    alfa = int(int(base[-2:], 16) * COLORI.get(certezza, 1.0))
    return base[:-2] + '%02x' % alfa


def disegni(rapporto, strato, linea, tenue):
    ogg = []
    for v in rapporto.get('basi', []):
        x, y = ll_to_xy(v['lat'], v['lon'])
        ogg += simboli.simbolo(v['tipo'], 'Intel %s' % v['nome'], strato, x, y, linea)
    for v in rapporto.get('sam', []):
        x, y = ll_to_xy(v['lat'], v['lon'])
        col = _colore(linea, v.get('certezza'))
        ogg.append(simboli.cerchio('Intel %s (portata)' % v['nome'], strato, x, y, v['raggio_km'] * 1000,
                                   tenue if v['tipo'] == 'sa5' else col, 2 if v['tipo'] == 'sa5' else 3))
        ogg += simboli.simbolo(v['tipo'], 'Intel %s' % v['nome'], strato, x, y, col)
    for v in rapporto.get('terra', []):
        x, y = ll_to_xy(v['lat'], v['lon'])
        ogg += simboli.simbolo('terra', 'Intel %s' % v['nome'], strato, x, y, _colore(linea, v.get('certezza')), 0.7)
    return ogg


def main(giorno, blocco):
    for parte in ('blu', 'rosso'):
        if blocco > 1:
            prec = carica(parte, giorno, blocco - 1) or iniziale(parte, giorno, blocco - 1)
            p = os.path.join(RADICE, 'campagna', 'G%02d' % giorno, 'esiti_B%d.json' % (blocco - 1))
            es = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
            r = aggiorna(prec, giorno, blocco, es)
        else:
            prec = piu_recente(parte, giorno - 1, 9) if giorno > 1 else None
            r = aggiorna(prec, giorno, blocco) if prec else iniziale(parte, giorno, blocco)
        print('scritto', salva(r), '- SAM %d, terra %d' % (len(r['sam']), len(r['terra'])))


if __name__ == '__main__':
    main(int(sys.argv[1]), int(sys.argv[2]))
