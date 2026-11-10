"""Versione "a carte scoperte" di una giornata, solo per i test.

Uso:  python3 script/tools/apri_test.py <giorno>

Il giocatore la chiede esplicitamente quando vuole vedere tutto (missione di prova).
Produce, senza ricostruire la missione (stesse posizioni della versione normale):
  - missioni/GNN_<data>_TEST.miz : mappa F10 con tutte le unita' di entrambe le parti
    (optview_all, etichette), briefing blu + rosso;
  - campagna/GNN/dossier_test.md : intenti, ordini, schieramenti e voli di entrambe le parti,
    avvisi dell'arbitro;
  - campagna/GNN/mappa_test.png  : il fronte libanese con tutte le unita' di terra e gli
    obiettivi dei voli.
La versione normale (separazione delle informazioni) resta invariata.
"""
import glob
import json
import os
import sys
import zipfile

from PIL import Image, ImageDraw, ImageFont

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(os.path.dirname(QUI))
sys.path.insert(0, QUI)
sys.path.insert(0, os.path.dirname(QUI))
import luatable as lt  # noqa: E402
from geo import dms  # noqa: E402

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def _ll(p):
    return '%.3f, %.3f' % (p[0], p[1])


def miz_test(giorno):
    src = sorted(glob.glob(os.path.join(RADICE, 'missioni', 'G%02d_*.miz' % giorno)))
    src = [s for s in src if not s.endswith('_TEST.miz')][0]
    out = src[:-4] + '_TEST.miz'
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zo:
        for info in zi.infolist():
            dati = zi.read(info.filename)
            if info.filename == 'mission':
                n, m = lt.parse(dati.decode('utf-8'))
                m['forcedOptions'] = {'optionsView': 'optview_all', 'labels': 1}
                dati = lt.dump(n, m).encode('utf-8')
            elif info.filename == 'l10n/DEFAULT/dictionary':
                n, d = lt.parse(dati.decode('utf-8'))
                d['DictKey_descriptionText_1'] = (
                    '*** VERSIONE DI TEST A CARTE SCOPERTE: mappa F10 con tutte le unita\' ***\n\n'
                    + d['DictKey_descriptionText_1'] + '\n\n========== BRIEFING ROSSO ==========\n\n'
                    + d['DictKey_descriptionRedTask_2'])
                d['DictKey_sortie_5'] = d['DictKey_sortie_5'] + ' [TEST]'
                dati = lt.dump(n, d).encode('utf-8')
            zo.writestr(info, dati)
    return out


def dossier(giorno, costr, ordini):
    righe = ['# G%02d - dossier di test (carte scoperte)' % giorno, '',
             'Generato da `script/tools/apri_test.py`. Contiene le informazioni di **entrambe le parti**: '
             'solo per le missioni di prova.', '']
    voli = {(v['lato'], v['nome']): v for v in costr['voli']}
    piaz = {}
    for p in costr['piazzamenti']:
        piaz.setdefault(p['nome'].replace(' (USA)', '').replace(' (SY)', ''), []).append(p)
    for lato, titolo in (('blue', 'BLU - USA / Libano (Aoun)'), ('red', 'ROSSO - Siria / URSS')):
        o = ordini[lato]
        righe += ['## %s' % titolo, '', '**Intento:** ' + o['intento_generale'], '', '### Voli', '',
                  '| Volo | Tipo | Aerei | Base | Decollo | Obiettivo | Quota | Durata | Note |',
                  '|---|---|---|---|---|---|---|---|---|']
        for a in o['missioni_aeree']:
            v = voli.get((lato, a['nome']), {})
            nome = a['nome'] + (' **(giocatore)**' if v.get('giocatore') else '')
            if (lato, a['nome']) not in voli:
                nome += ' (NON IN MISSIONE)'
            righe.append('| %s | %s | %dx %s | %s | %s | %s r%s km | %s ft | %s min | %s |' % (
                nome, a['tipo'], a['numero'], a['velivolo'], a['base'].split(' (')[0], a['decollo'],
                _ll(a['obiettivo']), a.get('raggio_km', ''), a.get('quota_ft', ''), a.get('durata_min', ''),
                (('scorta: %s. ' % a['scorta_di']) if a.get('scorta_di') else '') + a.get('note', '').replace('|', '/')))
        righe += ['', '### Unita\' di terra', '',
                  '| Unita\' | Sistema | Missione | Posizione reale | Note del piazzatore |', '|---|---|---|---|---|']
        nomi_ordini = [u['nome'] for u in o['unita_terra']]
        fissi = [p['nome'] for p in costr['piazzamenti'] if p['lato'] == lato
                 and p['nome'].replace(' (USA)', '').replace(' (SY)', '') not in nomi_ordini]
        for nome in nomi_ordini + fissi:
            u = next((x for x in o['unita_terra'] if x['nome'] == nome), None)
            ps = [p for p in piaz.get(nome.replace(' (USA)', '').replace(' (SY)', ''), []) if p['lato'] == lato]
            if not ps:
                righe.append('| %s | %s | %s | NON PIAZZATA | |' % (nome, u['tipo'] if u else '', u.get('missione', '') if u else ''))
                continue
            p = ps[0]
            det = p.get('dettagli', {})
            note = []
            if det.get('vincoli_allentati'):
                note.append('vincoli allentati liv. %d' % det['vincoli_allentati'])
            if det.get('scorrimento_m'):
                note.append('scorso %d m' % det['scorrimento_m'])
            if u and u.get('bersaglio_fuoco'):
                note.append('fuoco su %s' % _ll(u['bersaglio_fuoco']))
            if u and u.get('avanza_verso'):
                note.append('avanza verso %s' % _ll(u['avanza_verso']))
            if not u:
                note.append('sito fisso')
            la, lo = p['lat_lon']
            righe.append('| %s | %s | %s | %s (%.4f, %.4f) | %s |' % (
                p['nome'], p['sistema'], p.get('missione', ''), dms(la, lo), la, lo, '; '.join(note)))
        righe.append('')
    righe += ['## Avvisi dell\'arbitro', ''] + ['- ' + a for a in costr['avvisi']] + ['']
    for lato, nome in (('blue', 'blu'), ('red', 'rosso')):
        f = os.path.join(RADICE, nome, 'diario.md')
        if os.path.exists(f):
            righe += ['## Diario del comandante %s' % nome, '', open(f, encoding='utf-8').read().split('\n', 1)[1].strip(), '']
    return '\n'.join(righe)


def mappa(giorno, costr, ordini, uscita, lat0=33.55, lat1=34.45, lon0=35.30, lon1=36.30):
    import costruisci_giornata as cg
    W = 1800
    H = int(W * (lat1 - lat0) / ((lon1 - lon0) * 0.829))
    img = Image.new('RGB', (W, H + 60), (238, 234, 222))
    d = ImageDraw.Draw(img, 'RGBA')
    f, fb = ImageFont.truetype(FONT, 15), ImageFont.truetype(FONT_B, 22)

    def p(la, lo):
        return ((lo - lon0) / (lon1 - lon0) * W, 60 + (lat1 - la) / (lat1 - lat0) * H)
    # costa approssimata: meridiano grigio a ovest del fronte non disponibile -> griglia
    for k in range(int(lat0 * 10) + 1, int(lat1 * 10) + 1):
        d.line([p(k / 10, lon0), p(k / 10, lon1)], fill=(0, 0, 0, 25))
        d.text(p(k / 10, lon0), ' %.1fN' % (k / 10), font=f, fill=(90, 90, 90))
    for k in range(int(lon0 * 10) + 1, int(lon1 * 10) + 1):
        d.line([p(lat0, k / 10), p(lat1, k / 10)], fill=(0, 0, 0, 25))
        d.text(p(lat1, k / 10), '%.1fE' % (k / 10), font=f, fill=(90, 90, 90))
    d.polygon([p(*q) for q in cg.TESTA_DI_PONTE], fill=(60, 110, 220, 40), outline=(60, 110, 220, 200))
    d.line([p(*q) for q in cg.LINEA_FRONTE], fill=(0, 0, 0, 220), width=4)
    colori = {'blue': (30, 80, 200), 'red': (200, 30, 30)}
    # obiettivi dei voli
    for lato in ('blue', 'red'):
        for a in ordini[lato]['missioni_aeree']:
            la, lo = a['obiettivo']
            if not (lat0 < la < lat1 and lon0 < lo < lon1):
                continue
            x, y = p(la, lo)
            d.line([x - 7, y - 7, x + 7, y + 7], fill=colori[lato] + (160,), width=2)
            d.line([x - 7, y + 7, x + 7, y - 7], fill=colori[lato] + (160,), width=2)
            d.text((x + 8, y + 4), '%s %s' % (a['nome'], a['decollo']), font=f, fill=colori[lato] + (170,))
    ordine_nomi = {lato: {u['nome']: u for u in ordini[lato]['unita_terra']} for lato in ordini}
    for pz in costr['piazzamenti']:
        la, lo = pz['lat_lon']
        if not (lat0 < la < lat1 and lon0 < lo < lon1):
            continue
        x, y = p(la, lo)
        c = colori[pz['lato']]
        s = pz['sistema']
        if s.startswith('sa') or s in ('hawk', 'contraerea_mobile', 'aaa'):
            d.polygon([(x, y - 9), (x - 8, y + 6), (x + 8, y + 6)], fill=c)
        elif s in ('artiglieria', 'lanciarazzi'):
            d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=c)
        else:
            d.rectangle([x - 7, y - 6, x + 7, y + 6], fill=c)
        d.text((x + 10, y - 9), pz['nome'], font=f, fill=c)
        u = ordine_nomi[pz['lato']].get(pz['nome'].replace(' (USA)', '').replace(' (SY)', ''))
        bers = u and (u.get('bersaglio_fuoco') or u.get('avanza_verso'))
        if bers:
            d.line([(x, y), p(*bers)], fill=c + (130,), width=2)
    d.rectangle([0, 0, W, 58], fill=(28, 28, 32))
    d.text((16, 14), 'G%02d - CARTE SCOPERTE: unita\' di terra reali e obiettivi dei voli' % giorno, font=fb, fill=(240, 235, 220))
    d.text((W - 640, 20), 'triangolo: contraerea   cerchio: artiglieria   quadrato: manovra   x: obiettivo volo',
           font=f, fill=(200, 200, 200))
    img.save(uscita)


def main(giorno):
    cart = os.path.join(RADICE, 'campagna', 'G%02d' % giorno)
    costr = json.load(open(os.path.join(cart, 'costruzione.json'), encoding='utf-8'))
    ordini = {lato: json.load(open(os.path.join(RADICE, nome, 'ordini_G%02d.json' % giorno), encoding='utf-8'))
              for lato, nome in (('blue', 'blu'), ('red', 'rosso'))}
    print('scritto', miz_test(giorno))
    open(os.path.join(cart, 'dossier_test.md'), 'w', encoding='utf-8').write(dossier(giorno, costr, ordini))
    mappa(giorno, costr, ordini, os.path.join(cart, 'mappa_test.png'))
    print('scritti', os.path.join(cart, 'dossier_test.md'), os.path.join(cart, 'mappa_test.png'))


if __name__ == '__main__':
    main(int(sys.argv[1]))
