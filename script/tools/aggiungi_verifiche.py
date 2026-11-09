"""Acquisisce screenshot ravvicinati (vista SAT, zoom massimo) di batterie piazzate.

Uso: python3 aggiungi_verifiche.py <missione.miz> <screenshot> [<screenshot> ...]

Per ogni screenshot: riconosce la batteria (dalle icone delle unita' della missione),
rileva gli alberi, li aggiunge a campagna/terreno/alberi_noti.npz e salva una copia
dello screenshot in campagna/terreno/verifiche_alberi/.
"""
import os
import shutil
import sys
import zipfile

import luatable as lt
import verifica_alberi as va
from alberi_noti import AlberiNoti

QUI = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(QUI, '..', '..', 'campagna', 'terreno', 'verifiche_alberi')


def gruppi_da_missione(miz):
    _, m = lt.parse(zipfile.ZipFile(miz).read('mission').decode('utf-8'))
    out = {}
    for lato in ('red', 'blue'):
        for c in m['coalition'][lato]['country'].values():
            for g in c.get('vehicle', {}).get('group', {}).values():
                out[g['name']] = [(u['type'], u['x'], u['y']) for u in g['units'].values()]
    return out


def main(miz, immagini):
    gruppi = gruppi_da_missione(miz)
    banca = AlberiNoti()
    os.makedirs(DEST, exist_ok=True)
    for img in immagini:
        r = va.identifica_e_verifica(img, gruppi)
        n = banca.aggiungi_verifica(r, va.AREA_MAPPA)
        nel_bosco = [u['tipo'] for u in r['unita'] if u['nel_bosco']]
        print('%-40s -> %-24s scala %.2f m/px, icone %d/%d, celle d\'albero %d, veicoli tra gli alberi: %s'
              % (os.path.basename(img), r['gruppo'], r['scala_m_px'], r['corrispondenze'], len(gruppi[r['gruppo']]),
                 n, ', '.join(nel_bosco) or 'nessuno'))
        dest = os.path.join(DEST, r['gruppo'].replace(' ', '_') + '.webp')
        from PIL import Image
        Image.open(img).convert('RGB').save(dest, lossless=True)
    banca.salva()
    print('banca dati: %d celle d\'albero, %d aree verificate' % (len(banca.alberi), len(banca.aree)))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
