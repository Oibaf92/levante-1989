"""Importa dallo stato salvato in gioco le segnalazioni del giocatore (segni BOSCO e SPOSTA).

Uso: python3 importa_stato.py <stato_*.lua>
Le zone segnalate finiscono in campagna/terreno/alberi_noti.npz e verranno evitate
dal piazzatore in tutte le missioni successive.
"""
import sys

import luatable as lt
from alberi_noti import AlberiNoti


def main(percorso):
    _, stato = lt.parse(open(percorso, encoding='utf-8').read())
    pz = (stato.get('extra') or {}).get('piazzatore') or {}
    banca = AlberiNoti()
    n = 0
    for z in (pz.get('boschi') or {}).values():
        banca.aggiungi_zona(z['x'], z['y'], z.get('raggio', 300))
        n += 1
    banca.salva()
    print('zone da evitare importate: %d (totale %d)' % (n, len(banca.zone)))
    for s in (pz.get('spostamenti') or {}).values():
        print('  spostamento: %s (%s)' % (s['gruppo'], s.get('tipo', '')))


if __name__ == '__main__':
    main(sys.argv[1])
