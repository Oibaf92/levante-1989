"""Briefing e tavolette di una giornata (solo per la parte BLU, quella del giocatore)."""
import io
import os
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
sys.path.insert(0, os.path.join(QUI, 'tools'))

from PIL import Image, ImageDraw  # noqa: E402
from geo import ll_to_xy, xy_to_ll, dms, dist_brg  # noqa: E402
import kneeboard_g00 as kb  # noqa: E402
import intel  # noqa: E402

NOMI_VELIVOLO = {'F-14A-135-GR-Early': 'F-14A', 'FA-18C_hornet': 'F/A-18C', 'F-4E-45MC': 'F-4E', 'AH-64D_BLK_II': 'AH-64D',
                 'CH-47Fbl1': 'CH-47F', 'A6E': 'A-6E', 'E-2C': 'E-2C', 'S-3B Tanker': 'S-3B', 'KC135MPRS': 'KC-135',
                 'AV8BNA': 'AV-8B'}
BASI = {'CVN-71': 'CVN-71 Roosevelt (TACAN 71X "TR", ICLS 11, torre 258.000)',
        'LHA-1': 'LHA-1 Tarawa (TACAN 64X "TAR")', 'Incirlik': 'Incirlik (Turchia)'}
FREQ = [('251.000', 'Pacchetto / interno di volo'), ('258.000', 'CVN-71 torre / CATCC'), ('264.000', 'AWACS "Occhio Falco"'),
        ('270.000', 'Tanker'), ('243.000', 'Guardia')]


def _testo_volo(o):
    v = NOMI_VELIVOLO.get(o['velivolo'], o['velivolo'])
    righe = ['%s — %s, %d x %s, decollo previsto %s da %s' % (o['nome'].upper(), o['tipo'], o['numero'], v, o['decollo'],
                                                      BASI.get(o['base'], o['base']))]
    if o.get('obiettivo'):
        righe.append('  Obiettivo / zona: %s, raggio %s km, quota %s ft, durata %s min'
                     % (dms(*o['obiettivo']), o.get('raggio_km', '-'), o.get('quota_ft', '-'), o.get('durata_min', '-')))
    if o.get('note'):
        righe.append('  ' + o['note'])
    return '\n'.join(righe)


def prepara(c):
    ob = c.ordini['blue']
    voli = ob['missioni_aeree']
    giocatore = [o for o in voli if o.get('giocatore')]
    altri = [o for o in voli if not o.get('giocatore')]
    sit = open(os.path.join(c.cartella, 'situazione_pubblica.md'), encoding='utf-8').read()
    fronte = sit.split('## La linea del fronte')[1].split('## Perdite')[0].strip()
    testo = ('FUOCO SUL LEVANTE - GIORNO %d (17 ottobre 1989)\n\n' % c.giorno
             + 'SITUAZIONE\nQuindici giorni di guerra. La testa di ponte dei Marines e dell\'esercito di Aoun avanza '
               'lentamente sotto il fuoco continuo dell\'artiglieria siriana; la difesa aerea siro-sovietica e\' ancora '
               'temibile e i siriani contendono la superiorita\' aerea sopra il Libano.\n\n'
             + 'LINEA DEL FRONTE\n' + fronte.replace('**', '') + '\n\n'
             + 'INTENTO DEL COMANDANTE\n' + ob.get('intento_generale', '') + '\n\n'
             + 'I TUOI VOLI (scegli lo slot)\n' + '\n\n'.join(_testo_volo(o) for o in giocatore) + '\n\n'
             + 'VOLI AMICI IN AREA\n' + '\n'.join('- %s: %s, %d x %s, decollo %s'
                                                   % (o['nome'], o['tipo'], o['numero'], NOMI_VELIVOLO.get(o['velivolo'], o['velivolo']),
                                                      o['decollo']) for o in altri) + '\n\n'
             + 'MINACCE NOTE (intel di ieri sera)\n'
             + '- SA-5 Dumayr e Homs: coprono il Libano sopra i 15.000 ft.\n'
             + '- SA-6 mobili nella Bekaa; uno segnalato il G13 vicino a Sofar. SA-8 attorno ad Aley e Bhamdoun.\n'
             + '- Artiglieria sulle alture di Aley e del Chouf, Grad tra Sofar e Dahr el-Baidar.\n'
             + '- MiG-29 da Dumayr e Sayqal, attacchi all\'alba di Su-22/Su-24, Su-25 sul fronte.\n\n'
             + 'NOTE\n- I tuoi voli sono pronti subito: l\'orario di decollo e\' quello previsto dal piano, '
               'regolati sul resto del pacchetto (es. la SEAD prima dello strike).\n- La mappa F10 mostra solo le forze amiche. La carta intel (strato blu) e la tavoletta INTEL '
               'riportano la stima di ieri: i SAM mobili possono essersi spostati.\n'
             + '- Spazio aereo israeliano e territorio turco: vietati.\n'
             + '- Lo stato si salva da solo: a fine volo manda stato e registro da Saved Games\\DCS\\Levante1989\\.')
    compito = 'Scegli uno dei voli: ' + ', '.join('%s (%s)' % (o['nome'], NOMI_VELIVOLO.get(o['velivolo'], o['velivolo']))
                                                for o in giocatore) + '. Frequenze: ' + ', '.join('%s %s' % f for f in FREQ)
    rosso = 'Missione della giornata %d preparata per il giocatore blu.' % c.giorno
    tav = [_png(_pagina_ordini(c, giocatore, altri))] + [_png(_pagina_volo(c, o)) for o in giocatore] + [_png(_pagina_intel())]
    return {'titolo': '17 ottobre 1989', 'testo': testo, 'compito': compito}, rosso, tav


def _png(img):
    b = io.BytesIO()
    img.save(b, 'PNG', optimize=True)
    return b.getvalue()


def _pagina_ordini(c, giocatore, altri):
    img = Image.new('RGB', (kb.W, kb.H), kb.CARTA)
    d = ImageDraw.Draw(img)
    kb._testata(d, 'GIORNO %d - ORDINI' % c.giorno, '17 ottobre 1989  |  06:30-09:30  |  testa di ponte Jounieh - Beirut Est')
    y = kb._sezione(d, 104, 'COMUNICAZIONI')
    fm = kb.font(16, mono=True)
    for f, n in FREQ:
        y = kb._riga(d, y, [(30, f), (140, n)], fm)
    y = kb._riga(d, y, [(30, 'CVN-71: TACAN 71X "TR", ICLS 11   LHA-1: TACAN 64X "TAR"')], kb.font(15, mono=True))
    y = kb._sezione(d, y + 6, 'I TUOI VOLI')
    fb = kb.font(15, True)
    fn = kb.font(14)
    for o in giocatore:
        y = kb._riga(d, y, [(30, '%s  %s  %dx %s  decollo %s  da %s' % (o['nome'].upper(), o['tipo'], o['numero'],
                                                                        NOMI_VELIVOLO.get(o['velivolo'], o['velivolo']),
                                                                        o['decollo'], o['base']))], fb)
    y = kb._sezione(d, y + 6, 'VOLI AMICI')
    for o in altri:
        y = kb._riga(d, y, [(30, '%-16s %-9s %dx %-8s %s  %s' % (o['nome'], o['tipo'], o['numero'],
                                                                NOMI_VELIVOLO.get(o['velivolo'], o['velivolo']), o['decollo'], o['base']))],
                     kb.font(14, mono=True))
    y = kb._sezione(d, y + 6, 'LINEA DEL FRONTE')
    for t in ['Beirut porto - Baabda - Aley est - Bhamdoun - Mtein - Faraya - Afqa - nord di Jbeil',
              'A est e a sud della linea: territorio nemico. Obiettivo USA: Dahr el-Baidar (N33.81 E35.75).',
              'Vietati: spazio aereo israeliano, territorio turco.']:
        y = kb._riga(d, y, [(30, t)], fn)
    return img


def _pagina_volo(c, o):
    img = Image.new('RGB', (kb.W, kb.H), kb.CARTA)
    d = ImageDraw.Draw(img)
    v = NOMI_VELIVOLO.get(o['velivolo'], o['velivolo'])
    kb._testata(d, '%s - %s' % (o['nome'].upper(), o['tipo']), '%d x %s  |  decollo %s  |  %s' % (o['numero'], v, o['decollo'], o['base']))
    y = kb._sezione(d, 104, 'COMPITO')
    fn = kb.font(15)
    parole = (o.get('note') or '').split()
    riga = ''
    for p in parole:
        if len(riga) + len(p) > 80:
            y = kb._riga(d, y, [(30, riga)], fn)
            riga = ''
        riga += p + ' '
    if riga:
        y = kb._riga(d, y, [(30, riga)], fn)
    y = kb._sezione(d, y + 8, 'PIANO DI VOLO')
    fm = kb.font(15, mono=True)
    y = kb._riga(d, y, [(30, 'WP'), (80, 'PUNTO'), (210, 'COORDINATE'), (560, 'RV/DIST')], kb.font(14, True, mono=True), kb.GRIGIO)
    tipo_base, dati = c.base(o['base'], 'blue')
    punti = [('0', o['base'][:10], (dati[-2], dati[-1]))]
    for k, (lat, lon) in enumerate(o.get('rotta') or [], 1):
        punti.append((str(k), 'rotta', ll_to_xy(lat, lon)))
    if o.get('obiettivo'):
        punti.append((str(len(punti)), 'OBIETTIVO', ll_to_xy(*o['obiettivo'])))
    prec = None
    for wp, nome, p in punti:
        rv = ''
        if prec:
            dist, brg = dist_brg(*prec, *p)
            rv = '%03d/%5.1f nm' % (round(brg) % 360, dist / 1852)
        y = kb._riga(d, y, [(30, wp), (80, nome), (210, dms(*xy_to_ll(*p))), (560, rv)], fm)
        prec = p
    y = kb._sezione(d, y + 8, 'PARAMETRI')
    for t in ['Raggio d\'azione: %s km   Quota: %s ft   Durata: %s min' % (o.get('raggio_km', '-'), o.get('quota_ft', '-'), o.get('durata_min', '-')),
              'Carico: %s' % o.get('carico', '-'),
              'La rotta e\' una traccia: la nave naviga contro vento (prua %03d circa).' % round(c.prua_contro_vento(9)) if o['base'] == 'CVN-71' else '']:
        if t:
            y = kb._riga(d, y, [(30, t)], fn)
    return img


def _pagina_intel():
    img = Image.new('RGB', (kb.W, kb.H), kb.CARTA)
    d = ImageDraw.Draw(img)
    kb._testata(d, 'INTEL - GIORNO 15', 'Stima USA aggiornata a ieri sera  |  i sistemi mobili possono essersi spostati')
    y = kb._sezione(d, 104, 'DIFESA AEREA')
    fn = kb.font(14)
    fb = kb.font(14, True)
    from costruisci_giornata import SITI_DISTRUTTI
    for lat, lon, r, tipo, nome in intel.SAM_ROSSI:
        stato = 'DISTRUTTO' if nome in SITI_DISTRUTTI else 'portata ~%d km' % r
        kb._simbolo_pil(d, tipo, 42, y + 9, kb.GRIGIO if nome in SITI_DISTRUTTI else kb.ROSSO, 7)
        d.text((62, y), nome, font=fb, fill=kb.GRIGIO if nome in SITI_DISTRUTTI else kb.INCH)
        d.text((480, y), stato, font=fn, fill=kb.INCH)
        y += 22
    y = kb._sezione(d, y + 8, 'AGGIORNAMENTI')
    for t in ['SA-6 segnalato il G13 vicino a Sofar (N33.79 E35.71); almeno 2 SA-6 tra Zahle e Chtaura.',
              'SA-8 ad Aley e Bhamdoun a protezione delle artiglierie.',
              'Artiglieria: alture di Aley (N33.80 E35.60) e Chouf (N33.70 E35.60).',
              'Grad tra Sofar e Dahr el-Baidar. Brigata corazzata (T-72, BMP) tra Aley e Bhamdoun.',
              'MiG-29 da Dumayr e Sayqal; MiG-23/21 da Mezzeh, Marj Ruhayyil, Khalkhalah.',
              'Attacchi all\'alba di Su-22/Su-24; Su-25 sovietici sul fronte; A-50 a est di Homs.']:
        y = kb._riga(d, y, [(30, '- ' + t)], fn)
    return img
