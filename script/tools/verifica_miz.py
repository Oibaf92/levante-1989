"""Controlli statici di una missione prima della consegna (errori che il Mission Editor rifiuta
o che bloccano il caricamento). Vedi docs/lezioni.md.

Uso:  python3 script/tools/verifica_miz.py <missione.miz>     (oppure verifica(m) dal codice)
"""
import collections
import sys
import zipfile

import luatable as lt

NOMINATIVI_NUMERICI = {0, 1, 7, 12, 16, 18, 19, 27, 68, 74}   # Russia, Ucraina, ... (id DCS dei paesi orientali)


def verifica(m):
    errori = []
    gid, uid, nomi = collections.Counter(), collections.Counter(), collections.Counter()
    for cn, co in m['coalition'].items():
        for c in co['country'].values():
            for cat in ('plane', 'helicopter', 'vehicle', 'ship', 'static'):
                for g in c.get(cat, {}).get('group', {}).values():
                    gid[g['groupId']] += 1
                    nomi[g['name']] += 1
                    punti = g.get('route', {}).get('points', {})
                    if cat != 'static' and punti and not any(p.get('ETA_locked') for p in punti.values()):
                        errori.append('%s: nessun punto di rotta con orario bloccato (il Mission Editor non salva)' % g['name'])
                    for u in g['units'].values():
                        uid[u['unitId']] += 1
                        if cat in ('plane', 'helicopter'):
                            cs = u.get('callsign')
                            numerico = c['id'] in NOMINATIVI_NUMERICI
                            if numerico and not isinstance(cs, int) or not numerico and not isinstance(cs, dict):
                                errori.append('%s: nominativo radio %r non valido per %s' % (u['name'], cs, c['name']))
    errori += ['groupId %s duplicato' % k for k, v in gid.items() if v > 1]
    errori += ['unitId %s duplicato' % k for k, v in uid.items() if v > 1]
    errori += ['nome di gruppo %r duplicato' % k for k, v in nomi.items() if v > 1]
    return errori


if __name__ == '__main__':
    m = lt.parse(zipfile.ZipFile(sys.argv[1]).read('mission').decode('utf-8'))[1]
    e = verifica(m)
    print('\n'.join(e) or 'nessun errore')
    sys.exit(1 if e else 0)
