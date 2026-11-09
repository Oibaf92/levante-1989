"""Tavolette (kneeboard) per G00: carta di missione e schema del poligono."""
import io
import math

from PIL import Image, ImageDraw, ImageFont

from geo import xy_to_ll, dms, dist_brg

W, H = 800, 1200
CARTA = (238, 232, 214)
INCH = (25, 25, 30)
GRIGIO = (110, 105, 95)
ROSSO = (170, 30, 30)
BLU = (30, 70, 160)
ARANCIO = (215, 120, 20)

_F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
_M = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono%s.ttf'


def font(dim, bold=False, mono=False):
    return ImageFont.truetype((_M if mono else _F) % ('-Bold' if bold else ''), dim)


def _png(img):
    b = io.BytesIO()
    img.save(b, 'PNG', optimize=True)
    return b.getvalue()


def _testata(d, titolo, sotto):
    d.rectangle([0, 0, W, 86], fill=INCH)
    d.text((24, 14), titolo, font=font(30, True), fill=CARTA)
    d.text((24, 54), sotto, font=font(17), fill=(200, 195, 180))


def _sezione(d, y, testo):
    d.text((24, y), testo, font=font(19, True), fill=ROSSO)
    d.line([24, y + 27, W - 24, y + 27], fill=ROSSO, width=2)
    return y + 36


def _riga(d, y, colonne, f, colore=INCH):
    for x, t in colonne:
        d.text((x, y), t, font=f, fill=colore)
    return y + f.size + 9


def pagina_missione(g):
    img = Image.new('RGB', (W, H), CARTA)
    d = ImageDraw.Draw(img)
    _testata(d, 'G00 - AMBIENTAMENTO', 'DODGE  |  F-14A  |  CVN-71 Theodore Roosevelt  |  2 OTT 1989, 07:30 L')

    y = _sezione(d, 104, 'COMUNICAZIONI')
    fm = font(17, mono=True)
    for k in sorted(g['preset']):
        f, nome = g['preset'][k]
        y = _riga(d, y, [(30, 'CH %-2d' % k), (110, '%7.3f' % f), (220, nome)], fm)

    y = _sezione(d, y + 6, 'NAVIGAZIONE PORTAEREI')
    tc = g['tacan']
    y = _riga(d, y, [(30, 'TACAN  %d%s  "%s"' % (tc[0], tc[1], tc[2])), (360, 'ICLS  CH %d' % g['icls'])], fm)
    y = _riga(d, y, [(30, 'LINK 4  %.1f MHz' % (g['link4'] / 1e6)), (360, 'ACLS  attivo')], fm)
    y = _riga(d, y, [(30, 'BRC %03d   25 kt   Case I' % g['rotta_nave'])], fm)

    y = _sezione(d, y + 6, 'PIANO DI VOLO')
    fh = font(15, True, mono=True)
    y = _riga(d, y, [(30, 'WP'), (78, 'NOME'), (190, 'COORDINATE'), (520, 'QUOTA'), (610, 'RV/DIST')], fh, GRIGIO)
    tappe = [
        ('0', 'CVN', g['cvn'], 'mare', None),
        ('1', 'COSTA', g['costa'], '15000', g['cvn']),
        ('2', 'IP', g['ip'], '15000', g['costa']),
        ('3', 'ST (A)', g['bers_a'], '12000', g['ip']),
        ('-', 'BERS. B', g['bers_b'], '-', g['bers_a']),
        ('4', 'USCITA', g['uscita'], '15000', g['bers_a']),
        ('5', 'RIENTRO', g['rientro'], '3000', g['uscita']),
    ]
    fs = font(15, mono=True)
    for wp, nome, p, q, prec in tappe:
        rv = ''
        if prec:
            dist, brg = dist_brg(*prec, *p)
            rv = '%03d/%4.1f nm' % (round(brg) % 360, dist / 1852)
        y = _riga(d, y, [(30, wp), (78, nome), (190, dms(*xy_to_ll(*p))), (520, q), (610, rv)], fs)
    d.text((30, y), 'Rotte vere. La nave si muove: WP5 e\' la sua posizione stimata dopo ~55 min.', font=font(13), fill=GRIGIO)
    y += 26

    y = _sezione(d, y + 4, 'CARICO')
    y = _riga(d, y, [(30, 'ST 1/8  AIM-9L     ST 2/7  AIM-7M     2 serbatoi 300 gal')], fm)
    y = _riga(d, y, [(30, 'ST 3/6  Mk-82 x2 (bersaglio A)')], fm)
    y = _riga(d, y, [(30, 'ST 4/5  BDU-33 x6 (bersaglio B, esercitazione)')], fm)

    y = _sezione(d, y + 6, 'CARBURANTE (indicativo)')
    y = _riga(d, y, [(30, 'JOKER 6.0   BINGO 4.5   (migliaia di lb)')], fm)

    y = _sezione(d, y + 6, 'NOTE')
    fn = font(15)
    for t in [
        'Nessuna minaccia. Volo di addestramento: prenditi il tempo che serve.',
        'F10 > Levante 1989 > Informazioni poligono: coordinate esatte dei bersagli.',
        'F10 > Levante 1989 > Salva lo stato adesso: prova del salvataggio.',
        'A fine volo carica i file da  Saved Games\\DCS\\Levante1989\\',
    ]:
        y = _riga(d, y, [(30, '- ' + t)], fn)
    return img


def pagina_poligono(g):
    img = Image.new('RGB', (W, H), CARTA)
    d = ImageDraw.Draw(img)
    _testata(d, 'POLIGONO DI CEYHAN', 'Poligono NATO - Turchia meridionale  |  vista dall\'alto, nord in alto')

    # area disegno: 760 x 700, scala tale da contenere IP, A, B
    cx, cy = W / 2, 480
    scala = 300 / 18000      # 18 km (distanza IP) = 300 px
    ax, ay = g['bers_a']

    def schermo(p):
        dx, dy = p[0] - ax, p[1] - ay       # dx = nord, dy = est
        return cx + dy * scala, cy - dx * scala

    # griglia ad anelli ogni 5 km
    for r_km in (5, 10, 15):
        r = r_km * 1000 * scala
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(200, 192, 170), width=1)
        d.text((cx + r + 4, cy - 10), '%d km' % r_km, font=font(12), fill=GRIGIO)
    # nord
    d.polygon([(W - 60, 130), (W - 70, 160), (W - 50, 160)], fill=INCH)
    d.text((W - 66, 104), 'N', font=font(18, True), fill=INCH)

    ip = schermo(g['ip'])
    a = schermo(g['bers_a'])
    b = schermo(g['bers_b'])
    us = schermo(g['uscita'])
    # corsa d'attacco
    d.line([ip, a], fill=ROSSO, width=4)
    d.line([a, us], fill=GRIGIO, width=2)
    ang = math.radians(g['rotta_attacco'])
    mx, my = (ip[0] + a[0]) / 2, (ip[1] + a[1]) / 2
    d.text((mx + 14, my), 'CORSA %03d' % g['rotta_attacco'], font=font(18, True), fill=ROSSO)
    # freccia
    fx, fy = a[0] - 40 * math.sin(ang), a[1] + 40 * math.cos(ang)
    d.polygon([(fx + 12 * math.sin(ang), fy - 12 * math.cos(ang)),
               (fx - 8 * math.cos(ang), fy - 8 * math.sin(ang)),
               (fx + 8 * math.cos(ang), fy + 8 * math.sin(ang))], fill=ROSSO)
    d.ellipse([ip[0] - 9, ip[1] - 9, ip[0] + 9, ip[1] + 9], outline=INCH, width=3)
    d.text((ip[0] - 30, ip[1] + 12), 'IP (WP2)', font=font(16, True), fill=INCH)
    d.text((us[0] + 10, us[1] - 8), 'USCITA (WP4)', font=font(14), fill=GRIGIO)
    # bersagli
    for p, col, nome in ((a, ARANCIO, 'A'), (b, BLU, 'B')):
        d.ellipse([p[0] - 11, p[1] - 11, p[0] + 11, p[1] + 11], fill=col)
        d.text((p[0] - 6, p[1] - 11), nome, font=font(17, True), fill=CARTA)

    # riquadro ingrandito dei bersagli
    bx0, by0 = 40, 760
    d.rectangle([bx0, by0, W - 40, by0 + 200], outline=INCH, width=2)
    d.text((bx0 + 10, by0 + 6), 'DETTAGLIO BERSAGLI (900 m tra A e B)', font=font(15, True), fill=INCH)
    pa, pb = (bx0 + 220, by0 + 115), (bx0 + 500, by0 + 115)
    for i in range(4):
        t = math.radians(i * 90)
        q = (pa[0] + 55 * math.sin(t), pa[1] - 55 * math.cos(t))
        d.rectangle([q[0] - 5, q[1] - 3, q[0] + 5, q[1] + 3], fill=GRIGIO)
    for dx, dy in ((0, 0), (8, -5), (-7, -7)):
        d.rectangle([pa[0] + dx - 6, pa[1] + dy - 4, pa[0] + dx + 6, pa[1] + dy + 4], fill=ARANCIO)
    d.text((pa[0] - 110, pa[1] + 62), 'A: 3 carri, camion a 80 m', font=font(14), fill=INCH)
    d.ellipse([pb[0] - 36, pb[1] - 36, pb[0] + 36, pb[1] + 36], outline=GRIGIO, width=1)
    for i in range(6):
        t = math.radians(i * 60)
        q = (pb[0] + 36 * math.sin(t), pb[1] - 36 * math.cos(t))
        d.rectangle([q[0] - 4, q[1] - 3, q[0] + 4, q[1] + 3], fill=GRIGIO)
    d.rectangle([pb[0] - 6, pb[1] - 4, pb[0] + 6, pb[1] + 4], fill=BLU)
    d.text((pb[0] - 50, pb[1] + 62), 'B: blindato, cerchio a 50 m', font=font(14), fill=INCH)
    d.text((bx0 + 600, by0 + 60), 'FUMO', font=font(14, True), fill=INCH)
    d.text((bx0 + 600, by0 + 82), 'A arancione', font=font(14), fill=ARANCIO)
    d.text((bx0 + 600, by0 + 104), 'B blu', font=font(14), fill=BLU)
    d.text((bx0 + 600, by0 + 126), 'ogni 5 min', font=font(14), fill=GRIGIO)

    y = _sezione(d, 980, 'PROFILO SUGGERITO (indicativo)')
    fm = font(16, mono=True)
    for t in [
        'Ingresso 10-12.000 ft, picchiata 30 gradi, 450 kt',
        'Sgancio ~4.500 ft AGL, richiamata non sotto i 3.000 ft',
        'Mk-82: rispetta la distanza di sicurezza dalle schegge',
        'Punteggio: distanza e radiale di ogni impatto a schermo',
    ]:
        y = _riga(d, y, [(30, t)], fm)
    return img


def crea(g):
    return [_png(pagina_missione(g)), _png(pagina_poligono(g))]
