"""Piazzatore: dalla "intenzione" del comandante alla posizione delle unita'.

Un'intenzione dice COSA e PERCHE', non DOVE esattamente:

    Intenzione(sistema='sa6', nome='SA-6 Bekaa', centro=(33.85, 35.98), raggio_km=10,
               settore=(200, 320), obiettivo=(33.85, 35.99))

Il piazzatore:
  1. raccoglie i punti candidati della banca dati del terreno entro il raggio;
  2. scarta quelli non adatti (acqua, pendenza, edifici, vegetazione, strada lontana)
     controllando tutta l'area della batteria, non solo il centro;
  3. assegna un punteggio: visibilita' radar nel settore da coprire (linea di vista
     calcolata sulle quote del rilievo, curvatura terrestre inclusa), posizione
     rilevata rispetto ai dintorni, distanza dall'obiettivo da proteggere,
     distanza dagli altri siti gia' piazzati, una piccola parte casuale;
  4. sceglie il migliore e prepara 3 alternative (per la segnalazione SPOSTA);
  5. dispone i veicoli secondo lo schema realistico del sistema, orientato verso
     la minaccia.

Coordinate della mappa DCS: x = nord, y = est (metri). Rotte in gradi veri.
"""
import math
import os
import random
import zlib
from dataclasses import dataclass, field

import numpy as np

from geo import ll_to_xy, xy_to_ll

QUI = os.path.dirname(os.path.abspath(__file__))
TERRENO = os.path.join(QUI, '..', '..', 'campagna', 'terreno', 'terreno_completo.npz')


# ---------------------------------------------------------------------------
# Banca dati del terreno
# ---------------------------------------------------------------------------
class Terreno:
    def __init__(self, percorso=TERRENO):
        d = np.load(percorso)
        self.regioni = []
        for nome in ('dettaglio', 'generale'):              # dalla piu' fine
            x0, y0, passo, nx, ny = d[nome + '__meta']
            campi = {k.split('__')[1]: d[k] for k in d.files if k.startswith(nome + '__') and not k.endswith('meta')}
            self.regioni.append({'nome': nome, 'x0': x0, 'y0': y0, 'passo': passo, 'nx': int(nx), 'ny': int(ny), **campi})

    def _regione(self, x, y):
        for r in self.regioni:
            i = (x - r['x0']) / r['passo']
            j = (y - r['y0']) / r['passo']
            if 0 <= i <= r['nx'] - 1 and 0 <= j <= r['ny'] - 1:
                return r, i, j
        return None, None, None

    def valore(self, campo, x, y):
        r, i, j = self._regione(x, y)
        if r is None:
            return None
        return int(r[campo][int(round(i)), int(round(j))])

    def quota(self, x, y):
        """Quota interpolata (bilineare); l'acqua conta come 0 m."""
        x = np.atleast_1d(np.asarray(x, dtype=float))
        y = np.atleast_1d(np.asarray(y, dtype=float))
        out = np.zeros(x.shape)
        fatto = np.zeros(x.shape, dtype=bool)
        for r in self.regioni:
            i = (x - r['x0']) / r['passo']
            j = (y - r['y0']) / r['passo']
            dentro = (~fatto) & (i >= 0) & (j >= 0) & (i <= r['nx'] - 1) & (j <= r['ny'] - 1)
            if not dentro.any():
                continue
            q = r['quota'].astype(float)
            q = np.where(q < -1000, 0.0, q)
            ii, jj = i[dentro], j[dentro]
            i0 = np.clip(np.floor(ii).astype(int), 0, r['nx'] - 2)
            j0 = np.clip(np.floor(jj).astype(int), 0, r['ny'] - 2)
            fi, fj = ii - i0, jj - j0
            v = (q[i0, j0] * (1 - fi) * (1 - fj) + q[i0 + 1, j0] * fi * (1 - fj)
                 + q[i0, j0 + 1] * (1 - fi) * fj + q[i0 + 1, j0 + 1] * fi * fj)
            out[dentro] = v
            fatto |= dentro
        return out

    def candidati(self, cx, cy, raggio):
        """Punti entro il raggio: griglia da 1 km dove c'e', altrimenti quella da 2 km."""
        tutti_pts, tutti_attr = [], {c: [] for c in ('quota', 'pendenza', 'sup', 'edifici', 'strada', 'vegetazione')}
        coperto = []                                   # estensioni delle regioni gia' usate (piu' fini)
        passo_min = None
        for r in self.regioni:
            i_min = int(max(0, (cx - raggio - r['x0']) // r['passo']))
            i_max = int(min(r['nx'] - 1, (cx + raggio - r['x0']) // r['passo'] + 1))
            j_min = int(max(0, (cy - raggio - r['y0']) // r['passo']))
            j_max = int(min(r['ny'] - 1, (cy + raggio - r['y0']) // r['passo'] + 1))
            if i_min <= i_max and j_min <= j_max:
                ii, jj = np.mgrid[i_min:i_max + 1, j_min:j_max + 1]
                xs = r['x0'] + ii * r['passo']
                ys = r['y0'] + jj * r['passo']
                dentro = np.hypot(xs - cx, ys - cy) <= raggio
                for (ax0, ax1, ay0, ay1) in coperto:
                    dentro &= ~((xs >= ax0) & (xs <= ax1) & (ys >= ay0) & (ys <= ay1))
                if dentro.any():
                    ii, jj = ii[dentro], jj[dentro]
                    tutti_pts.append(np.stack([xs[dentro], ys[dentro]], 1))
                    for c in tutti_attr:
                        tutti_attr[c].append(r[c][ii, jj])
                    passo_min = r['passo'] if passo_min is None else min(passo_min, r['passo'])
            coperto.append((r['x0'], r['x0'] + (r['nx'] - 1) * r['passo'], r['y0'], r['y0'] + (r['ny'] - 1) * r['passo']))
        if not tutti_pts:
            return np.zeros((0, 2)), {}, None
        return np.vstack(tutti_pts), {c: np.concatenate(v) for c, v in tutti_attr.items()}, passo_min


# ---------------------------------------------------------------------------
# Sistemi: vincoli, punteggio e disposizione dei veicoli
# ---------------------------------------------------------------------------
# Schema dei veicoli: (tipo DCS, avanti m, destra m, rotta relativa gradi).
# "avanti" = verso il centro del settore da coprire.
def _cerchio(tipo, raggio, n, sfasamento=0.0, rotta_verso_esterno=True):
    out = []
    for k in range(n):
        a = math.radians(sfasamento + 360.0 * k / n)
        out.append((tipo, raggio * math.cos(a), raggio * math.sin(a), math.degrees(a) if rotta_verso_esterno else 0.0))
    return out


SISTEMI = {
    'sa2': dict(
        descrizione='SA-2 (S-75) postazione fissa',
        raggio_area=250, pendenza_max=6, edifici_max=0, vegetazione_max=10, strada_max=3000,
        portata_km=40, quota_bersaglio=200, peso_radar=1.0, dist_obiettivo=(3000, 25000), spaziatura=6000,
        schema=[('SNR_75V', 0, 0, 0), ('p-19 s-125 sr', -160, 20, 0), ('S_75_ZIL', -220, -60, 90)]
               + _cerchio('S_75M_Volhov', 85, 6, 30),
    ),
    'sa3': dict(
        descrizione='SA-3 (S-125) postazione fissa',
        raggio_area=200, pendenza_max=6, edifici_max=0, vegetazione_max=10, strada_max=3000,
        portata_km=22, quota_bersaglio=100, peso_radar=1.0, dist_obiettivo=(2000, 15000), spaziatura=5000,
        schema=[('snr s-125 tr', 0, 0, 0), ('p-19 s-125 sr', -130, -20, 0)]
               + _cerchio('5p73 s-125 ln', 65, 4, 45),
    ),
    'sa5': dict(
        descrizione='SA-5 (S-200) complesso fisso',
        raggio_area=450, pendenza_max=5, edifici_max=0, vegetazione_max=10, strada_max=5000,
        portata_km=150, quota_bersaglio=5000, peso_radar=0.6, dist_obiettivo=(0, 40000), spaziatura=30000,
        schema=[('RPC_5N62V', 0, 0, 0), ('RLS_19J6', -300, 0, 0), ('P14_SR', -380, 220, 0)]
               + [('S-200_Launcher', 160 * math.cos(math.radians(a)), 160 * math.sin(math.radians(a)), a)
                  for a in (-75, -45, -15, 15, 45, 75)],
    ),
    'sa6': dict(
        descrizione='SA-6 (Kub) batteria mobile',
        raggio_area=300, pendenza_max=10, edifici_max=0, vegetazione_max=20, strada_max=1500,
        portata_km=25, quota_bersaglio=100, peso_radar=1.0, dist_obiettivo=(1500, 15000), spaziatura=6000,
        schema=[('Kub 1S91 str', 0, 0, 0), ('Kub 2P25 ln', 180, -150, 0), ('Kub 2P25 ln', 200, 160, 0),
                ('Kub 2P25 ln', -150, -220, 0), ('Kub 2P25 ln', -170, 200, 0)],
    ),
    'sa8': dict(
        descrizione='SA-8 (Osa) sezione mobile',
        raggio_area=200, pendenza_max=12, edifici_max=0, vegetazione_max=25, strada_max=1000,
        portata_km=10, quota_bersaglio=50, peso_radar=0.8, dist_obiettivo=(500, 8000), spaziatura=3000,
        schema=[('Osa 9A33 ln', 0, -150, 0), ('Osa 9A33 ln', 60, 160, 0)],
    ),
    'aaa': dict(
        descrizione='Artiglieria contraerea (ZSU-23-4, S-60 con radar SON-9)',
        raggio_area=150, pendenza_max=12, edifici_max=6, vegetazione_max=30, strada_max=2000,
        portata_km=6, quota_bersaglio=50, peso_radar=0.2, dist_obiettivo=(300, 2500), spaziatura=1500,
        schema=[('SON_9', 0, 0, 0), ('S-60_Type59_Artillery', 50, -50, 0), ('S-60_Type59_Artillery', 50, 50, 0),
                ('S-60_Type59_Artillery', -50, -50, 0), ('S-60_Type59_Artillery', -50, 50, 0),
                ('ZSU-23-4 Shilka', 120, 0, 0)],
    ),
    'ewr': dict(
        descrizione='Radar di scoperta (55G6)',
        raggio_area=100, pendenza_max=15, edifici_max=0, vegetazione_max=30, strada_max=4000,
        portata_km=150, quota_bersaglio=500, peso_radar=1.5, dist_obiettivo=(0, 30000), spaziatura=20000,
        schema=[('55G6 EWR', 0, 0, 0)],
    ),
    'hawk': dict(
        descrizione='I-Hawk (USA) batteria',
        # difende un'area costiera densamente abitata: tollera qualche edificio nei dintorni
        raggio_area=250, pendenza_max=10, edifici_max=4, vegetazione_max=25, strada_max=2000,
        portata_km=35, quota_bersaglio=100, peso_radar=1.0, dist_obiettivo=(1000, 12000), spaziatura=6000,
        schema=[('Hawk pcp', 0, 0, 0), ('Hawk sr', -120, -40, 0), ('Hawk tr', 40, 0, 0),
                ('Hawk ln', 120, -110, 0), ('Hawk ln', 150, 0, 0), ('Hawk ln', 120, 110, 0)],
    ),
}


@dataclass
class Intenzione:
    sistema: str
    nome: str
    centro: tuple                 # (lat, lon) attorno a cui cercare
    raggio_km: float = 8.0
    settore: tuple = (0, 360)     # rotte da coprire (da, a), in senso orario
    obiettivo: tuple = None       # (lat, lon) da proteggere; se None = centro
    coalizione: str = 'red'
    paese: int = 47               # 47 = Siria
    abilita: str = 'Good'


@dataclass
class Piazzamento:
    intenzione: Intenzione
    x: float
    y: float
    rotta: float                  # verso il centro del settore (gradi)
    punteggio: float
    dettagli: dict
    unita: list = field(default_factory=list)          # (tipo, x, y, rotta_gradi)
    alternative: list = field(default_factory=list)    # [(x, y, rotta), ...]


# ---------------------------------------------------------------------------
R_TERRA_EFF = 6371000.0 * 4.0 / 3.0       # raggio terrestre efficace per la propagazione radar


def _settore_rotte(settore, n):
    a, b = settore
    ampiezza = (b - a) % 360 or 360
    return [(a + ampiezza * (k + 0.5) / n) % 360 for k in range(n)]


def visibilita(terreno, pts, quota_antenna, settore, portata, quota_bersaglio, n_rotte=12, distanze=None):
    """Frazione di punti-bersaglio visibili (a quota_bersaglio sul terreno) nel settore, per ogni candidato."""
    if distanze is None:
        distanze = [d for d in (3000, 6000, 10000, 15000, 22000, 35000, 50000, 80000, 120000) if d <= portata] or [portata]
    rotte = np.radians(_settore_rotte(settore, n_rotte))
    n = len(pts)
    visibili = np.zeros(n)
    totale = 0
    passi = 24
    q0 = terreno.quota(pts[:, 0], pts[:, 1]) + quota_antenna
    for r in rotte:
        cr, sr = math.cos(r), math.sin(r)
        for D in distanze:
            # quota del bersaglio
            tx = pts[:, 0] + D * cr
            ty = pts[:, 1] + D * sr
            qt = terreno.quota(tx, ty) + quota_bersaglio
            # profilo lungo la linea di vista
            ok = np.ones(n, dtype=bool)
            for k in range(1, passi):
                f = k / passi
                d = D * f
                px = pts[:, 0] + d * cr
                py = pts[:, 1] + d * sr
                qp = terreno.quota(px, py)
                # quota della linea di vista in quel punto, con la curvatura terrestre
                linea = q0 + (qt - q0) * f - d * (D - d) / (2 * R_TERRA_EFF)
                ok &= qp <= linea
            visibili += ok
            totale += 1
    return visibili / max(totale, 1)


def _rilievo_relativo(terreno, pts, raggio=2000):
    q = terreno.quota(pts[:, 0], pts[:, 1])
    somme = np.zeros(len(pts))
    for a in range(0, 360, 45):
        r = math.radians(a)
        somme += terreno.quota(pts[:, 0] + raggio * math.cos(r), pts[:, 1] + raggio * math.sin(r))
    return q - somme / 8


def _filtro_area(terreno, pts, attr, passo, cfg):
    """Vincoli sul punto e sui vicini che cadono nell'area della batteria."""
    ok = (attr['sup'] == 1) | (attr['sup'] == 4)
    ok &= attr['pendenza'] <= cfg['pendenza_max']
    ok &= attr['edifici'] <= cfg['edifici_max']
    ok &= (attr['vegetazione'] < 0) | (attr['vegetazione'] <= cfg['vegetazione_max'])
    ok &= (attr['strada'] >= 0) & (attr['strada'] <= cfg['strada_max'])
    # area della batteria: controlla quota sul perimetro (pendenza dell'intera area)
    ra = cfg['raggio_area']
    q0 = terreno.quota(pts[:, 0], pts[:, 1])
    for a in range(0, 360, 45):
        r = math.radians(a)
        qa = terreno.quota(pts[:, 0] + ra * math.cos(r), pts[:, 1] + ra * math.sin(r))
        ok &= np.abs(qa - q0) / ra * 100 <= cfg['pendenza_max'] * 1.3
    return ok


def _orienta(schema, x, y, rotta):
    r = math.radians(rotta)
    cr, sr = math.cos(r), math.sin(r)
    out = []
    for tipo, avanti, destra, rot_rel in schema:
        ux = x + avanti * cr - destra * sr
        uy = y + avanti * sr + destra * cr
        out.append((tipo, ux, uy, (rotta + rot_rel) % 360))
    return out


def piazza(terreno, intenzione, gia_piazzati=(), seme=1989, evitare=()):
    """Piazza un'intenzione; se i candidati validi sono pochi allarga la ricerca (fino al doppio del raggio)."""
    ultimo = None
    for fattore in (1.0, 1.5, 2.0):
        try:
            p = _piazza(terreno, intenzione, gia_piazzati, seme, evitare, fattore)
        except ValueError as e:
            if not isinstance(ultimo, Piazzamento):
                ultimo = e
            continue
        if p.dettagli['candidati_validi'] >= 8 or fattore == 2.0:
            p.dettagli['raggio_usato_km'] = round(intenzione.raggio_km * fattore, 1)
            return p
        ultimo = p
    if isinstance(ultimo, Piazzamento):
        return ultimo
    raise ultimo


def _piazza(terreno, intenzione, gia_piazzati, seme, evitare, fattore):
    cfg = SISTEMI[intenzione.sistema]
    cx, cy = ll_to_xy(*intenzione.centro)
    ox, oy = ll_to_xy(*(intenzione.obiettivo or intenzione.centro))
    pts, attr, passo = terreno.candidati(cx, cy, intenzione.raggio_km * 1000 * fattore)
    if not len(pts):
        raise ValueError('%s: nessun dato del terreno attorno al centro' % intenzione.nome)
    ok = _filtro_area(terreno, pts, attr, passo, cfg)
    for ex, ey in evitare:                                    # punti segnalati con SPOSTA
        ok &= np.hypot(pts[:, 0] - ex, pts[:, 1] - ey) > 1500
    if ok.sum() == 0:
        raise ValueError('%s: nessun punto adatto entro %.0f km' % (intenzione.nome, intenzione.raggio_km * fattore))
    pts, attr = pts[ok], {k: v[ok] for k, v in attr.items()}

    # punteggio
    vis = visibilita(terreno, pts, 8.0, intenzione.settore, cfg['portata_km'] * 1000, cfg['quota_bersaglio'])
    rel = np.clip(_rilievo_relativo(terreno, pts) / 100.0, -1, 1)
    d_obi = np.hypot(pts[:, 0] - ox, pts[:, 1] - oy)
    dmin, dmax = cfg['dist_obiettivo']
    pen_obi = np.where(d_obi < dmin, (dmin - d_obi) / max(dmin, 1), np.where(d_obi > dmax, (d_obi - dmax) / dmax, 0))
    pen_vic = np.zeros(len(pts))
    for p in gia_piazzati:
        d = np.hypot(pts[:, 0] - p.x, pts[:, 1] - p.y)
        sp = max(cfg['spaziatura'], SISTEMI[p.intenzione.sistema]['spaziatura']) / 2
        pen_vic += np.clip((sp - d) / sp, 0, 1)
    rnd = np.random.default_rng(seme + zlib.crc32(intenzione.nome.encode())).random(len(pts))
    punteggio = (cfg['peso_radar'] * 2.0 * vis + 0.3 * rel - 1.5 * pen_obi - 2.0 * pen_vic
                 - 0.002 * attr['strada'] / 100.0 + 0.15 * rnd)

    ordine = np.argsort(-punteggio)
    scelti = []
    for k in ordine:                                          # migliore + 3 alternative ben separate
        if all(math.hypot(pts[k, 0] - pts[s, 0], pts[k, 1] - pts[s, 1]) > max(2000, cfg['raggio_area'] * 4) for s in scelti):
            scelti.append(k)
        if len(scelti) == 4:
            break
    a, b = intenzione.settore
    centro_settore = (a + ((b - a) % 360 or 360) / 2) % 360
    k = scelti[0]
    p = Piazzamento(intenzione, float(pts[k, 0]), float(pts[k, 1]), centro_settore, float(punteggio[k]),
                    dict(visibilita=round(float(vis[k]), 2), rilievo_m=round(float(rel[k] * 100)),
                         dist_obiettivo_km=round(float(d_obi[k]) / 1000, 1), pendenza=int(attr['pendenza'][k]),
                         strada_m=int(attr['strada'][k]), vegetazione=int(attr['vegetazione'][k]),
                         quota=int(attr['quota'][k]), candidati_validi=int(len(pts))))
    p.unita = _orienta(cfg['schema'], p.x, p.y, p.rotta)
    p.alternative = [(float(pts[s, 0]), float(pts[s, 1]), centro_settore) for s in scelti[1:]]
    return p


def piazza_tutti(terreno, intenzioni, seme=1989):
    fatti = []
    # prima i sistemi con piu' vincoli (fissi, grandi), poi i mobili
    ordine = {'sa5': 0, 'ewr': 1, 'sa2': 2, 'sa3': 3, 'hawk': 3, 'sa6': 4, 'sa8': 5, 'aaa': 6}
    for it in sorted(intenzioni, key=lambda i: ordine.get(i.sistema, 9)):
        fatti.append(piazza(terreno, it, fatti, seme))
    return fatti


# ---------------------------------------------------------------------------
# Conversione in gruppi del Mission Editor
# ---------------------------------------------------------------------------
def gruppo_me(p, group_id, primo_unit_id, terreno=None):
    unita = {}
    for k, (tipo, x, y, rotta) in enumerate(p.unita, 1):
        unita[k] = {'type': tipo, 'x': x, 'y': y, 'name': '%s-%d' % (p.intenzione.nome, k),
                    'heading': math.radians(rotta), 'skill': p.intenzione.abilita, 'playerCanDrive': False,
                    'unitId': primo_unit_id + k - 1}
    quota = float(terreno.quota(p.x, p.y)[0]) if terreno else 0.0
    return {
        'visible': False, 'lateActivation': False, 'tasks': {}, 'uncontrollable': False, 'task': 'Ground Nothing',
        'taskSelected': True, 'hidden': False, 'groupId': group_id, 'name': p.intenzione.nome,
        'x': p.x, 'y': p.y, 'start_time': 0, 'units': unita,
        'route': {'spans': {}, 'points': {1: {
            'alt': quota, 'type': 'Turning Point', 'ETA': 0, 'alt_type': 'BARO', 'formation_template': '',
            'x': p.x, 'y': p.y, 'ETA_locked': True, 'speed': 0, 'action': 'Off Road', 'speed_locked': True,
            'task': {'id': 'ComboTask', 'params': {'tasks': {}}}}}},
    }


def descrivi(p):
    lat, lon = xy_to_ll(p.x, p.y)
    d = p.dettagli
    return ('%-34s N%.4f E%.4f  quota %4d m  pend %2d%%  strada %4d m  veg %3s  vis %.2f  obiettivo %.1f km  (%d candidati)'
            % (p.intenzione.nome, lat, lon, d['quota'], d['pendenza'], d['strada_m'],
               '-' if d['vegetazione'] < 0 else '%d%%' % d['vegetazione'], d['visibilita'], d['dist_obiettivo_km'],
               d['candidati_validi']))
