"""Anteprima degli strati di disegno alla scala di riferimento (M_PER_PX)."""
import sys
from PIL import Image, ImageDraw, ImageFont
import confini
import intel

M_PER_PX = 150.0   # scala di riferimento (m per pixel)
import geo


def _col(s, a=None):
    v = int(s, 16)
    c = ((v >> 24) & 255, (v >> 16) & 255, (v >> 8) & 255, v & 255)
    return c if a is None else c[:3] + (a,)


def disegna(oggetti, uscita, lat0=32.6, lat1=36.5, lon0=34.6, lon1=38.6):
    x0, _ = geo.ll_to_xy(lat1, (lon0 + lon1) / 2)
    _, y0 = geo.ll_to_xy((lat0 + lat1) / 2, lon0)
    x1, _ = geo.ll_to_xy(lat0, (lon0 + lon1) / 2)
    _, y1 = geo.ll_to_xy((lat0 + lat1) / 2, lon1)
    s = M_PER_PX
    W, H = int((y1 - y0) / s), int((x0 - x1) / s)
    img = Image.new('RGB', (W, H), (236, 232, 220))
    d = ImageDraw.Draw(img, 'RGBA')

    def p(x, y):
        return ((y - y0) / s, (x0 - x) / s)
    for o in oggetti:
        if o['primitiveType'] == 'Polygon':
            pts = [p(o['mapX'] + q['x'], o['mapY'] + q['y']) for q in o['points'].values()]
            d.polygon(pts, fill=_col(o['fillColorString'], 45))
        elif o['primitiveType'] == 'Line':
            pts = [p(o['mapX'] + q['x'], o['mapY'] + q['y']) for q in o['points'].values()]
            d.line(pts, fill=_col(o['colorString']), width=max(1, int(o['thickness']) - 1))
    for o in oggetti:
        if o['primitiveType'] == 'TextBox':
            f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', int(o['fontSize']))
            d.multiline_text(p(o['mapX'], o['mapY']), o['text'], font=f, fill=_col(o['colorString'], 255))
    img.save(uscita)


if __name__ == '__main__':
    common = list(confini.disegni().values())
    disegna(common + intel.disegni_blu(), sys.argv[1] + '_blu.png')
    disegna(common + intel.disegni_rossi(), sys.argv[1] + '_rosso.png')
