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
    d.text((30, y), 'Rotte vere. La nave si muove: WP5 e\' la sua posizione stimata dopo ~%d min.' % g['minuti_rientro'],
           font=font(13), fill=GRIGIO)
    y += 26

    y = _sezione(d, y + 4, 'CARICO')
    y = _riga(d, y, [(30, 'ST 1/8  AIM-9L     ST 2/7  AIM-7M     2 serbatoi 300 gal')], fm)
    y = _riga(d, y, [(30, 'ST 3/6  Mk-82 x2 (bersaglio A)')], fm)
    y = _riga(d, y, [(30, 'ST 4/5  BDU-33 x6 (bersaglio B, esercitazione)')], fm)
    y = _riga(d, y, [(30, 'Gregario: 2 AIM-54A, 3 AIM-7M, 2 AIM-9L (scorta)')], fm)

    y = _sezione(d, y + 6, 'CARBURANTE (indicativo)')
    y = _riga(d, y, [(30, 'JOKER 8.5   BINGO 7.0   (al poligono, migliaia di lb)')], fm)
    y = _riga(d, y, [(30, 'Rientro ~120 nm. Alla nave almeno 4.0 per l\'appontaggio.')], font(15))

    y = _sezione(d, y + 6, 'NOTE')
    fn = font(15)
    for t in [
        'Nessuna minaccia. Volo di addestramento: prenditi il tempo che serve.',
        'F10 > Levante 1989 > Informazioni poligono: coordinate esatte dei bersagli.',
        'F10 > Levante 1989 > Salva lo stato adesso: prova del salvataggio.',
        'A fine volo carica i file da  Saved Games\\DCS\\Levante1989\\',
        'Poligono tra gli alberi? Segno F10 con scritto POLIGONO: si sposta li\'.',
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

    dist, brg = dist_brg(*g['bers_a'], *g['rientro'])
    d.text((40, 712), 'Rientro: CVN-71 a ~%d nm per %03d dal poligono (stima a %d min)' % (
        round(dist / 1852), round(brg) % 360, g['minuti_rientro']), font=font(15, True), fill=BLU)
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


def _simbolo_pil(d, tipo, x, y, colore, r=9):
    if tipo in ('aerea', 'elicotteri'):
        d.rectangle([x - r, y - r, x + r, y + r], outline=colore, width=2)
        if tipo == 'elicotteri':
            d.line([x - r, y - r, x + r, y + r], fill=colore, width=2)
            d.line([x - r, y + r, x + r, y - r], fill=colore, width=2)
    elif tipo == 'navale':
        d.polygon([(x, y - r * 1.3), (x + r * 1.3, y), (x, y + r * 1.3), (x - r * 1.3, y)], outline=colore, width=2)
    elif tipo == 'terra':
        pts = [(x + r * 1.1 * math.sin(math.radians(72 * i)), y - r * 1.1 * math.cos(math.radians(72 * i))) for i in range(5)]
        d.polygon(pts, outline=colore, width=2)
    elif tipo in ('sa5', 'sa2', 'hawk'):
        k = 1.4 if tipo == 'sa5' else 1.0
        d.polygon([(x, y - r * k), (x + r * k, y + r * k * 0.8), (x - r * k, y + r * k * 0.8)], outline=colore, width=2)
        if tipo == 'sa5':
            d.polygon([(x, y - r * 0.5), (x + r * 0.5, y + r * 0.4), (x - r * 0.5, y + r * 0.4)], outline=colore, width=1)
        if tipo == 'hawk':
            d.line([x - r * 1.1, y + r * 0.15, x + r * 1.1, y + r * 0.15], fill=colore, width=2)
    elif tipo == 'sa3':
        d.polygon([(x, y + r), (x + r, y - r * 0.8), (x - r, y - r * 0.8)], outline=colore, width=2)
    elif tipo == 'sa6':
        d.polygon([(x + r * math.sin(math.radians(60 * i + 30)), y - r * math.cos(math.radians(60 * i + 30)))
                   for i in range(6)], outline=colore, width=2)
    elif tipo == 'sa8':
        d.ellipse([x - r * 0.8, y - r * 0.8, x + r * 0.8, y + r * 0.8], outline=colore, width=2)
        d.line([x - r * 0.8, y, x + r * 0.8, y], fill=colore, width=1)
        d.line([x, y - r * 0.8, x, y + r * 0.8], fill=colore, width=1)


def pagina_intel(g):
    """Dettaglio della mappa intel del blu: nomi e velivoli dietro ai simboli."""
    import intel
    img = Image.new('RGB', (W, H), CARTA)
    d = ImageDraw.Draw(img)
    _testata(d, 'INTEL - SITUAZIONE DI PACE', 'Stima USA al 2 ottobre 1989  |  i sistemi mobili possono essersi spostati')
    fn = font(14)
    fb = font(14, True)
    y = _sezione(d, 100, 'SIRIA E CONTINGENTE SOVIETICO - BASI')
    for lat, lon, tipo, nome, det in intel.BASI_ROSSE:
        _simbolo_pil(d, tipo, 42, y + 9, ROSSO, 7)
        d.text((62, y), nome, font=fb, fill=INCH)
        d.text((250, y), det, font=fn, fill=INCH)
        y += 22
    y = _sezione(d, y + 8, 'DIFESA AEREA (SA-6/SA-8: ultima posizione osservata)')
    for lat, lon, r_km, tipo, nome in intel.SAM_ROSSI:
        _simbolo_pil(d, tipo, 42, y + 9, ROSSO, 7)
        d.text((62, y), nome, font=fb, fill=INCH)
        d.text((480, y), 'portata ~%d km' % r_km, font=fn, fill=INCH)
        y += 22
    d.text((62, y + 2), 'Contingente aereo sovietico: basi non confermate.', font=fn, fill=ROSSO)
    y = _sezione(d, y + 34, 'FORZE USA')
    for lat, lon, tipo, nome, det in intel.BASI_BLU:
        _simbolo_pil(d, tipo, 42, y + 9, BLU, 7)
        d.text((62, y), nome, font=fb, fill=INCH)
        d.text((250, y), det, font=fn, fill=INCH)
        y += 22
    for lat, lon, r_km, tipo, nome in intel.SAM_BLU:
        _simbolo_pil(d, tipo, 42, y + 9, BLU, 7)
        d.text((62, y), nome, font=fb, fill=INCH)
        d.text((480, y), 'portata ~%d km' % r_km, font=fn, fill=INCH)
        y += 22
    d.text((62, y + 4), 'Legenda dei simboli: pagina 4 (CARTA).', font=fn, fill=GRIGIO)
    return img


# coste schematiche (solo per la carta della tavoletta; la mappa F10 ha il terreno vero)
CIPRO = [(35.10, 32.27), (34.76, 32.41), (34.65, 32.75), (34.57, 32.98), (34.67, 33.04), (34.70, 33.30),
         (34.90, 33.63), (34.96, 34.08), (35.12, 33.94), (35.30, 34.05), (35.50, 34.40), (35.69, 34.59),
         (35.55, 34.20), (35.40, 33.95), (35.34, 33.32), (35.40, 32.92), (35.18, 32.98), (35.05, 32.43)]
TURCHIA = [(36.02, 32.30), (36.02, 32.80), (36.10, 33.00), (36.14, 33.32), (36.32, 33.88), (36.60, 34.30),
           (36.78, 34.62), (36.80, 34.90), (36.70, 35.05), (36.60, 35.20), (36.56, 35.37), (36.62, 35.60),
           (36.77, 35.79), (36.59, 36.17), (36.41, 35.89), (36.08, 35.93), (35.92, 35.92), (35.90, 36.06),
           (36.00, 36.35), (36.22, 36.67), (36.65, 36.80), (36.65, 37.10), (36.83, 38.00), (37.50, 38.00),
           (37.50, 32.30)]


def pagina_carta(g):
    """Carta d'insieme: aree, simboli intel nelle posizioni esatte, rotta del volo."""
    import confini
    import intel
    from geo import ll_to_xy
    img = Image.new('RGB', (W, H), CARTA)
    d0 = ImageDraw.Draw(img)
    _testata(d0, 'CARTA D\'INSIEME', 'Rotta del volo e stima intel USA  |  legenda in fondo alla pagina')
    lat_s, lat_n, lon_o, lon_e = 32.30, 37.30, 32.35, 37.90
    xn, _ = ll_to_xy(lat_n, (lon_o + lon_e) / 2)
    xs, _ = ll_to_xy(lat_s, (lon_o + lon_e) / 2)
    _, yo = ll_to_xy((lat_s + lat_n) / 2, lon_o)
    _, ye = ll_to_xy((lat_s + lat_n) / 2, lon_e)
    aw, ah = W - 40, H - 180
    sc = min(aw / (ye - yo), ah / (xn - xs))
    aw, ah = int((ye - yo) * sc), int((xn - xs) * sc)
    carta = Image.new('RGB', (aw, ah), (200, 222, 236))          # mare
    d = ImageDraw.Draw(carta, 'RGBA')

    def p(x, y):
        return ((y - yo) * sc, (xn - x) * sc)

    def pl(lat, lon):
        return p(*ll_to_xy(lat, lon))

    def col(c, a=None):
        v = int(c, 16)
        r = ((v >> 24) & 255, (v >> 16) & 255, (v >> 8) & 255, v & 255)
        return r if a is None else r[:3] + (a,)
    for costa in (TURCHIA, CIPRO):
        d.polygon([pl(*q) for q in costa], fill=(232, 226, 210), outline=(150, 140, 120))
    oggetti = [o for o in confini.disegni().values() if not o['name'].startswith('Legenda')] + intel.disegni_blu()
    for o in oggetti:
        if o['primitiveType'] == 'Polygon':
            d.polygon([p(o['mapX'] + q['x'], o['mapY'] + q['y']) for q in o['points'].values()],
                      fill=col(o['fillColorString'], 80))
    for o in oggetti:
        if o['primitiveType'] == 'Line':
            larg = 1 if 'portata' in o['name'] else 2
            d.line([p(o['mapX'] + q['x'], o['mapY'] + q['y']) for q in o['points'].values()],
                   fill=col(o['colorString']), width=larg)
    for lat, lon, nome in ((36.95, 34.0, 'TURCHIA'), (35.05, 33.2, 'CIPRO')):
        x, y = pl(lat, lon)
        d.text((x, y), nome, font=font(13, True), fill=(120, 110, 90), anchor='mm')
    rotta = [g['cvn'], g['costa'], g['ip'], g['bers_a'], g['uscita'], g['rientro']]
    d.line([p(*q) for q in rotta], fill=(20, 20, 20, 255), width=3)
    for q, t in zip(rotta, ['CVN', '1', '2', '3', '4', '5']):
        x, y = p(*q)
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(20, 20, 20))
        d.text((x + 7, y - 18), t, font=font(14, True), fill=(20, 20, 20))
    ox, oy = (W - aw) // 2, 100
    img.paste(carta, (ox, oy))
    d0.rectangle([ox, oy, ox + aw, oy + ah], outline=INCH, width=2)
    yt = oy + ah + 12
    d0.text((24, yt), 'Nero: rotta del volo (numeri = waypoint).  Rosso: stima forze siro-sovietiche.', font=font(14), fill=INCH)
    d0.text((24, yt + 22), 'Blu: forze USA.  Posizioni esatte: i simboli possono sovrapporsi.', font=font(14), fill=INCH)
    d0.text((24, yt + 44), 'Coste schematiche, solo indicative.', font=font(14), fill=GRIGIO)
    # legenda dei simboli su due colonne
    import simboli
    y0 = yt + 78
    d0.text((24, y0), 'LEGENDA', font=font(15, True), fill=ROSSO)
    voci = list(simboli.TIPI.items())
    meta = (len(voci) + 1) // 2
    for i, (tipo, (descr, _)) in enumerate(voci):
        cx = 40 if i < meta else 420
        cy = y0 + 32 + (i % meta) * 22
        _simbolo_pil(d0, tipo, cx, cy, INCH, 7)
        d0.text((cx + 20, cy - 9), descr, font=font(14), fill=INCH)
    return img


def crea(g):
    return [_png(pagina_missione(g)), _png(pagina_poligono(g)), _png(pagina_intel(g)), _png(pagina_carta(g))]
