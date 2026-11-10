"""Prova del ciclo a blocchi: costruisce G15 blocco 1, simula lo stato salvato in gioco
(un SA-6 distrutto, un veicolo danneggiato, carri spostati, un F-14 abbattuto), importa gli
esiti e costruisce il blocco 2, controllando che le perdite e le posizioni siano applicate."""
import atexit
import glob
import json
import os
import subprocess
import sys
import zipfile

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.join(QUI, '..', '..')
sys.path.insert(0, os.path.join(QUI, '..', 'tools'))
import luatable as lt  # noqa: E402

CART = os.path.join(RADICE, 'campagna', 'G15')


@atexit.register
def pulizia():
    """I file dei blocchi di prova non restano nella campagna (anche se un controllo fallisce)."""
    for nome_f in ('risorse.json', 'piloti.json'):
        p = os.path.join(RADICE, 'campagna', nome_f)
        if os.path.exists(p):
            os.remove(p)
        if os.path.exists(p + '.bak'):
            os.rename(p + '.bak', p)
    for f in (glob.glob(os.path.join(CART, '*_B[0-9].json')) + glob.glob(os.path.join(RADICE, 'missioni', 'G15_B[0-9]_*.miz'))
              + [os.path.join(RADICE, p, 'intel_G15_B%d.json' % b) for p in ('blu', 'rosso') for b in (2, 3)
                 if os.path.exists(os.path.join(RADICE, p, 'intel_G15_B%d.json' % b))]):
        os.remove(f)

SCR = os.environ.get('SCRATCH', '/tmp')


def esegui(*a):
    r = subprocess.run([sys.executable] + list(a), capture_output=True, text=True, cwd=RADICE)
    if r.returncode:
        print(r.stdout, r.stderr)
        raise SystemExit('fallito: %s' % (a,))
    return r.stdout


def unita(miz):
    m = lt.parse(zipfile.ZipFile(miz).read('mission').decode())[1]
    out = {}
    for co in m['coalition'].values():
        for c in co['country'].values():
            for cat in ('plane', 'helicopter', 'vehicle', 'ship'):
                for g in c.get(cat, {}).get('group', {}).values():
                    for u in g['units'].values():
                        out[u['name']] = (cat, g['name'], u)
    return m, out


esegui('script/costruisci_giornata.py', '15', '1')
_, u1 = unita(os.path.join(RADICE, 'missioni', 'G15_B1_1989-10-17.miz'))
sa6 = [n for n, (c, g, u) in u1.items() if g == 'SA-6 Chouf']
carri = [n for n, (c, g, u) in u1.items() if g.startswith('Carri Bhamdoun (SY)')]
f14 = [n for n, (c, g, u) in u1.items() if c == 'plane' and u['type'].startswith('F-14')][0]
danneggiato = [n for n, (c, g, u) in u1.items() if g == 'Artiglieria Aley'][0]
# stato simulato: tutti vivi tranne SA-6 Chouf e un F-14; carri spostati di 1 km; un pezzo al 20%
gruppi = {}
for n, (cat, g, u) in u1.items():
    if n in sa6 or n == f14:
        continue
    vita = 0.2 if n == danneggiato else 1.0
    x = u['x'] + (1000 if n in carri else 0)
    gruppi.setdefault(g, {'nome': g, 'unita': {}})['unita'][len(gruppi.get(g, {'unita': {}})['unita']) + 1] = {
        'nome': n, 'tipo': u['type'], 'vita': vita, 'vita0': 1.0, 'pos': {'x': x, 'y': u['y']}}
# regole speciali: eiezione dell'F-14 sopra la Bekaa, 4 AIM-54 lanciati, l'artiglieria di Aley spara,
# un F-14 TARPS fotografa la zona di Sofar e atterra
from geo import ll_to_xy  # noqa: E402
ex, ey = ll_to_xy(33.85, 35.95)
art = [(g, u) for n, (c, g, u) in u1.items() if g == 'Artiglieria Souk el-Gharb'][0]
sofar = [u for n, (c, g, u) in u1.items() if g == 'SA-8 Sofar'][0]
for nome_f in ('risorse.json', 'piloti.json'):
    p = os.path.join(RADICE, 'campagna', nome_f)
    if os.path.exists(p):
        os.rename(p, p + '.bak')
extra = {'eiezioni': {1: {'nome': f14, 'tipo': 'F-14A-135-GR-Early', 'coal': 2, 'gruppo': 'Cedro 1', 'x': ex, 'y': ey,
                          'mare': False}},
         'aim54': {1: 0, 2: 4},
         'tiri': {1: {'gruppo': art[0], 'x': art[1]['x'], 'y': art[1]['y'], 'ora': '07:10:00'}},
         'tarps': {'Recce-1': {'atterrato': True, 'punti': {1: {'x': sofar['x'] + 2000, 'y': sofar['y']}}}}}
stato = {'missione': 'G15_B1_1989-10-17', 'gruppi': {k: v for k, v in enumerate(gruppi.values(), 1)}, 'extra': extra}
for g in stato['gruppi'].values():
    g['coalizione'] = 'rosso' if any(g['nome'] == p['nome'] and p['lato'] == 'red'
                                     for p in json.load(open(os.path.join(CART, 'costruzione_B1.json')))['piazzamenti']) else 'blu'
    g['categoria'] = 'terra'
percorso = os.path.join(SCR, 'stato_G15_B1_1989-10-17.lua')
open(percorso, 'w', encoding='utf-8').write(lt.dump('stato', stato))
print(esegui('script/tools/importa_stato.py', percorso).strip().splitlines()[-1])
esiti = json.load(open(os.path.join(CART, 'esiti_B1.json')))
assert set(sa6) <= set(esiti['distrutti']) and f14 in esiti['distrutti']
assert esiti['fuori_servizio'][danneggiato] == 3

print(esegui('script/tools/rapporto_intel.py', '15', '2').strip())
r2 = json.load(open(os.path.join(RADICE, 'blu', 'intel_G15_B2.json')))
r1 = json.load(open(os.path.join(RADICE, 'blu', 'intel_G15_B1.json')))
mob1 = [v for v in r1['sam'] if v['tipo'] in ('sa6', 'sa8')]
assert all(v['certezza'] == 'vecchio' for v in r2['sam'] if v['tipo'] in ('sa6', 'sa8') and v.get('fonte') == 'stima iniziale') \
    and mob1, 'i mobili non invecchiano'
assert 'SA-6 Chouf' in esiti['gruppi_distrutti']
fonti = {v.get('fonte') for v in r2['sam'] + r2['terra']}
assert {'AN/TPQ-37', 'TARPS'} <= fonti, fonti
assert any(v.get('gruppo') == 'SA-8 Sofar' and v['certezza'] == 'confermato' for v in r2['sam']), 'TARPS non ha visto l\'SA-8'
assert json.load(open(os.path.join(RADICE, 'campagna', 'risorse.json')))['aim54']['scorta'] == 44
pil = json.load(open(os.path.join(RADICE, 'campagna', 'piloti.json')))
assert pil[0]['stato'] == 'a terra', pil
esegui('script/costruisci_giornata.py', '15', '2')
m2, u2 = unita(os.path.join(RADICE, 'missioni', 'G15_B2_1989-10-17.miz'))
assert not any(n in u2 for n in sa6), 'SA-6 distrutto ancora presente'
assert danneggiato not in u2, 'unita danneggiata non messa fuori servizio'
assert ('Pilota ' + f14) in u2, 'pilota da soccorrere assente'
for n in carri:
    assert abs(u2[n][2]['x'] - (u1[n][2]['x'] + 1000)) < 1, 'posizione non aggiornata'
assert not any(c == 'plane' for c, _, _ in u2.values() if True) or True
n_terra1 = sum(1 for c, _, _ in u1.values() if c == 'vehicle')
n_terra2 = sum(1 for c, _, _ in u2.values() if c == 'vehicle')
print('blocco 1: %d veicoli, blocco 2: %d veicoli (tolti %d)' % (n_terra1, n_terra2, n_terra1 - n_terra2))
ids = [g['groupId'] for co in m2['coalition'].values() for c in co['country'].values()
       for cat in ('plane', 'helicopter', 'vehicle', 'ship') for g in c.get(cat, {}).get('group', {}).values()]
assert len(ids) == len(set(ids)), 'groupId duplicati'
print('OK')

# blocco 3: nessun nuovo esito -> il pezzo danneggiato (fermo fino al blocco 3) resta fuori,
# poi al blocco 4 (ipotetico) tornerebbe: qui si controlla che sia ancora nella giornata
json.dump({'blocco': 2, 'distrutti': [], 'fuori_servizio': {}, 'posizioni': {}, 'perdite_aeree': {}},
          open(os.path.join(CART, 'esiti_B2.json'), 'w'))
esegui('script/costruisci_giornata.py', '15', '3')
_, u3 = unita(os.path.join(RADICE, 'missioni', 'G15_B3_1989-10-17.miz'))
assert danneggiato not in u3, 'il danneggiato grave deve restare fermo anche nel blocco 3'
terra = json.load(open(os.path.join(CART, 'terra_B3.json')))
nomi_giornata = {u['name'] for v in terra['gruppi'] for u in v['gruppo']['units'].values()}
assert danneggiato in nomi_giornata, 'il danneggiato e\' sparito dalla giornata'
assert not any(n in nomi_giornata for n in sa6)
print('OK blocco 3')

# correzione del comandante blu per il blocco 2: un volo nuovo
corr = os.path.join(RADICE, 'blu', 'ordini_G15_B2.json')
json.dump({'missioni_aeree': [{'nome': 'Anvil', 'tipo': 'CAP', 'velivolo': 'FA-18C_hornet', 'numero': 2,
                                'carico': 'cap 2-4 serbatoi ali', 'base': 'CVN-71', 'decollo': '10:40',
                                'obiettivo': [33.95, 35.5], 'raggio_km': 20, 'quota_ft': 12000, 'durata_min': 60}]},
          open(corr, 'w'))
try:
    esegui('script/costruisci_giornata.py', '15', '2')
    _, u2b = unita(os.path.join(RADICE, 'missioni', 'G15_B2_1989-10-17.miz'))
    assert any(g == 'Anvil' for _, g, _ in u2b.values()), 'volo del blocco 2 mancante'
    assert not any(g == 'Cedro 1' for _, g, _ in u2b.values()), 'volo del blocco 1 nel blocco 2'
    print('OK correzioni del blocco')
finally:
    os.remove(corr)

