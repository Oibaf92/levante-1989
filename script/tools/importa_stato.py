"""Importa lo stato salvato in gioco alla fine di un volo.

Uso: python3 importa_stato.py <stato_*.lua>
- segnalazioni del giocatore (segni BOSCO e SPOSTA): le zone finiscono in
  campagna/terreno/alberi_noti.npz e verranno evitate dal piazzatore;
- se la missione e' un blocco (GNN_Bk_...): esiti del blocco (perdite, danni, posizioni) in
  campagna/GNN/esiti_Bk.json, usati per costruire il blocco successivo.
"""
import os
import re
import sys

import esiti as esiti_blocco

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
    if n:
        banca.salva()
    print('zone da evitare importate: %d (totale %d)' % (n, len(banca.zone)))
    for s in (pz.get('spostamenti') or {}).values():
        print('  spostamento: %s (%s)' % (s['gruppo'], s.get('tipo', '')))
    m = re.match(r'G(\d+)_B(\d+)_', stato.get('missione') or '')
    if m:
        giorno, blocco = int(m.group(1)), int(m.group(2))
        cartella = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'campagna', 'G%02d' % giorno)
        e = esiti_blocco.scrivi(percorso, cartella, blocco)
        print('esiti G%d blocco %d: %d distrutti, %d fuori servizio, perdite aeree %s'
              % (giorno, blocco, len(e['distrutti']), len(e['fuori_servizio']), e['perdite_aeree']))


if __name__ == '__main__':
    main(sys.argv[1])
