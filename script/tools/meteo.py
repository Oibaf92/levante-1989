"""Meteo della campagna: tempo plausibile per il Levante in autunno, con continuita' tra i giorni
e un'evoluzione nella giornata (alba, mezzogiorno, pomeriggio).

Regimi (si passa dall'uno all'altro giorno per giorno, con probabilita' che dipendono dal mese):
  sereno        alta pressione: cielo limpido o poche nubi, brezza di mare nel pomeriggio
  variabile     nubi sparse o irregolari, cumuli sulle montagne nel pomeriggio
  perturbazione fronte da ovest: nubi basse e compatte, pioggia, vento forte da sud-ovest/ovest
                (dura 1-2 giorni; piu' frequente da fine ottobre)
  foschia       vento da est dal deserto: foschia o polvere, visibilita' ridotta, caldo secco
Il meteo si genera una volta per giornata (campagna/GNN/meteo.json, uguale per tutti) e ogni blocco
lo usa. La previsione (testo) e' pubblica: la leggono i comandanti e il giocatore; il tempo reale puo'
discostarsi un po' dalla previsione.

Nel file della missione wind.dir e' la direzione VERSO cui soffia il vento (docs/lezioni.md).
Nubi: preset di DCS 2.9 (Preset1-27 dal poco nuvoloso al coperto, RainyPreset1-3 con pioggia).

Uso:  python3 script/tools/meteo.py <giorno>     (genera e stampa la previsione)
"""
import json
import os
import random
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
CAMPAGNA = os.path.join(QUI, '..', '..', 'campagna')

# probabilita' di passaggio tra regimi; la riga 'perturbazione' vale dal secondo giorno di fronte
TRANSIZIONI = {
    'sereno':        {'sereno': 0.60, 'variabile': 0.25, 'perturbazione': 0.07, 'foschia': 0.08},
    'variabile':     {'sereno': 0.35, 'variabile': 0.35, 'perturbazione': 0.20, 'foschia': 0.10},
    'perturbazione': {'sereno': 0.20, 'variabile': 0.60, 'perturbazione': 0.20, 'foschia': 0.00},
    'foschia':       {'sereno': 0.55, 'variabile': 0.25, 'perturbazione': 0.05, 'foschia': 0.15},
}
STAGIONE = {9: 0.6, 10: 1.0, 11: 1.6, 12: 2.0}   # moltiplicatore delle perturbazioni per mese

NOMI_REGIME = {'sereno': 'alta pressione, tempo stabile', 'variabile': 'tempo variabile',
               'perturbazione': 'passaggio di una perturbazione da ovest', 'foschia': 'vento dal deserto, foschia'}
# preset di nubi per regime e momento della giornata
NUBI = {
    'sereno':        {'alba': ('Preset1', 2400), 'mezzogiorno': ('Preset2', 2700), 'pomeriggio': ('Preset4', 2700)},
    'variabile':     {'alba': ('Preset5', 2000), 'mezzogiorno': ('Preset8', 1800), 'pomeriggio': ('Preset12', 1700)},
    'perturbazione': {'alba': ('RainyPreset1', 900), 'mezzogiorno': ('RainyPreset2', 800), 'pomeriggio': ('Preset20', 1100)},
    'foschia':       {'alba': ('Preset1', 3000), 'mezzogiorno': ('Preset1', 3200), 'pomeriggio': ('Preset2', 3200)},
}
DESCRIZIONE_NUBI = {'Preset1': 'poche nubi', 'Preset2': 'poche nubi', 'Preset4': 'nubi sparse',
                    'Preset5': 'nubi sparse', 'Preset8': 'nubi sparse e irregolari', 'Preset12': 'nuvoloso con cumuli',
                    'Preset20': 'molto nuvoloso', 'RainyPreset1': 'coperto con pioggia',
                    'RainyPreset2': 'coperto con pioggia e rovesci'}


def _vento(rnd, regime, momento):
    """(direzione DA cui soffia, m/s) al suolo, a 2000 m e a 8000 m."""
    if regime == 'foschia':
        da, v = rnd.uniform(70, 120), rnd.uniform(3, 7)
    elif regime == 'perturbazione':
        da, v = rnd.uniform(220, 280), rnd.uniform(7, 12)
    else:
        # brezza: debole all'alba (da terra, da est), di mare da ovest a mezzogiorno e pomeriggio
        if momento == 'alba':
            da, v = rnd.uniform(60, 140), rnd.uniform(1, 3)
        else:
            da, v = rnd.uniform(240, 300), rnd.uniform(3, 6) * (1.3 if momento == 'pomeriggio' else 1.0)
    quota2 = (da + rnd.uniform(-20, 30)) % 360, v * rnd.uniform(1.4, 2.0) + 2
    quota8 = (rnd.uniform(240, 290) if regime != 'foschia' else rnd.uniform(200, 260)), rnd.uniform(12, 25)
    return (round(da) % 360, round(v, 1)), (round(quota2[0]), round(quota2[1], 1)), (round(quota8[0]), round(quota8[1], 1))


def genera(giorno, data, regime_prec=None, seme=None):
    rnd = random.Random(seme if seme is not None else 1989 * 100 + giorno)
    mese = int(data.split('-')[1])
    if regime_prec is None:
        regime = 'sereno'
    else:
        pesi = dict(TRANSIZIONI[regime_prec])
        pesi['perturbazione'] *= STAGIONE.get(mese, 1.0)
        regime = rnd.choices(list(pesi), weights=list(pesi.values()))[0]
    qnh = {'sereno': (1015, 1022), 'variabile': (1008, 1016), 'perturbazione': (998, 1008), 'foschia': (1006, 1013)}[regime]
    qnh_hpa = rnd.uniform(*qnh)
    temp = {9: 28, 10: 24, 11: 19, 12: 15}.get(mese, 22) + (3 if regime == 'foschia' else -3 if regime == 'perturbazione' else 0)
    blocchi = {}
    for momento in ('alba', 'mezzogiorno', 'pomeriggio'):
        suolo, q2, q8 = _vento(rnd, regime, momento)
        preset, base = NUBI[regime][momento]
        vis = {'sereno': 60000, 'variabile': 40000, 'perturbazione': 12000, 'foschia': 6000}[regime]
        nebbia = regime in ('sereno', 'variabile') and momento == 'alba' and rnd.random() < 0.15
        blocchi[momento] = {
            'vento_da': suolo, 'vento_2000_da': q2, 'vento_8000_da': q8,
            'nubi': preset, 'base_m': int(base * rnd.uniform(0.9, 1.15)),
            'visibilita_m': int(vis * rnd.uniform(0.8, 1.2)),
            'nebbia': {'spessore_m': int(rnd.uniform(80, 200)), 'visibilita_m': int(rnd.uniform(1500, 4000))} if nebbia else None,
            'polvere_m': int(rnd.uniform(3000, 7000)) if regime == 'foschia' else None,
            'temperatura': round(temp + {'alba': -5, 'mezzogiorno': 2, 'pomeriggio': 1}[momento]),
            'qnh_hpa': round(qnh_hpa + rnd.uniform(-1.5, 1.5), 1),
            'turbolenza': 0 if momento == 'alba' else (20 if regime == 'perturbazione' else 8),
        }
    return {'giorno': giorno, 'data': data, 'regime': regime, 'blocchi': blocchi,
            'previsione': previsione(regime, blocchi, rnd)}


def previsione(regime, blocchi, rnd):
    """Testo pubblico: per alba / mezzogiorno / pomeriggio. Valori arrotondati, come una previsione vera."""
    righe = ['Situazione: %s.' % NOMI_REGIME[regime]]
    for momento, b in blocchi.items():
        da, v = b['vento_da']
        extra = []
        if b['nebbia']:
            extra.append('possibili banchi di nebbia sulla costa')
        if b['polvere_m']:
            extra.append('foschia e polvere, visibilita\' %d-%d km' % (b['polvere_m'] // 1000 - 1, b['polvere_m'] // 1000 + 2))
        righe.append('%s: %s, base circa %d m; vento da %s %d-%d nodi; %d gradi sulla costa%s.' % (
            momento.capitalize(), DESCRIZIONE_NUBI.get(b['nubi'], b['nubi']), round(b['base_m'], -2),
            punto_cardinale(da), max(0, round(v / 0.5144) - 3), round(v / 0.5144) + 3, b['temperatura'],
            ('; ' + ', '.join(extra)) if extra else ''))
    return '\n'.join(righe)


def punto_cardinale(gradi):
    nomi = ['nord', 'nord-est', 'est', 'sud-est', 'sud', 'sud-ovest', 'ovest', 'nord-ovest']
    return nomi[int((gradi % 360 + 22.5) // 45) % 8]


def tempo_dcs(b):
    """Dizionario weather della missione per un blocco (si fonde con quello di base)."""
    def v(coppia):
        da, ms = coppia
        return {'dir': (da + 180) % 360, 'speed': ms}     # nel file: direzione VERSO cui soffia
    w = {
        'wind': {'atGround': v(b['vento_da']), 'at2000': v(b['vento_2000_da']), 'at8000': v(b['vento_8000_da'])},
        'season': {'temperature': b['temperatura']},
        'qnh': round(b['qnh_hpa'] / 1.33322, 1),
        'groundTurbulence': b['turbolenza'],
        'type_weather': 0,
        'visibility': {'distance': b['visibilita_m']},
        'clouds': {'preset': b['nubi'], 'base': b['base_m'], 'thickness': 200, 'density': 0, 'iprecptns': 0},
        'enable_fog': bool(b['nebbia']),
        'fog': {'thickness': b['nebbia']['spessore_m'], 'visibility': b['nebbia']['visibilita_m']} if b['nebbia']
        else {'thickness': 0, 'visibility': 0},
        'enable_dust': bool(b['polvere_m']),
        'dust_density': b['polvere_m'] or 0,
    }
    return w


def momento_blocco(nome_blocco, inizio):
    if nome_blocco in ('alba', 'mezzogiorno', 'pomeriggio'):
        return nome_blocco
    h = int(inizio.split(':')[0])
    return 'alba' if h < 9 else ('mezzogiorno' if h < 14 else 'pomeriggio')


def della_giornata(giorno, data):
    """Meteo della giornata: dal file se esiste, altrimenti generato dal regime del giorno prima e salvato."""
    p = os.path.join(CAMPAGNA, 'G%02d' % giorno, 'meteo.json')
    if os.path.exists(p):
        return json.load(open(p, encoding='utf-8'))
    prec = os.path.join(CAMPAGNA, 'G%02d' % (giorno - 1), 'meteo.json')
    regime_prec = json.load(open(prec, encoding='utf-8'))['regime'] if os.path.exists(prec) else None
    m = genera(giorno, data, regime_prec)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(m, open(p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    return m


def aggiorna_situazione(giorno, testo):
    """Scrive la previsione nella sezione '## Meteo previsto' della situazione pubblica della giornata."""
    p = os.path.join(CAMPAGNA, 'G%02d' % giorno, 'situazione_pubblica.md')
    if not os.path.exists(p):
        return False
    s = open(p, encoding='utf-8').read()
    sezione = '## Meteo previsto\n' + testo + '\n\n'
    if '## Meteo previsto' in s:
        i = s.index('## Meteo previsto')
        j = s.find('\n## ', i + 5)
        s = s[:i] + sezione + (s[j + 1:] if j >= 0 else '')
    else:
        s = s.rstrip() + '\n\n' + sezione
    open(p, 'w', encoding='utf-8').write(s)
    return True


if __name__ == '__main__':
    g = int(sys.argv[1])
    par = json.load(open(os.path.join(CAMPAGNA, 'G%02d' % g, 'parametri.json'), encoding='utf-8'))
    m = della_giornata(g, par['data'])
    print(m['previsione'])
    if aggiorna_situazione(g, m['previsione']):
        print('(previsione scritta nella situazione pubblica)')
