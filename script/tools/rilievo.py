"""Lettura del file del rilievo del terreno (missione R00).

    t = Terreno.carica('rilievo_terreno.txt')
    t.punto(x, y)   -> dict con quota, pendenza, sup, edifici, strada (regione piu' fine che lo contiene)

Coordinate della mappa DCS: x = nord, y = est (metri).
"""
import numpy as np

CAMPI = ('quota', 'pendenza', 'sup', 'edifici', 'strada')
NAN = -9999


class Regione:
    def __init__(self, nome, x0, y0, passo, nx, ny):
        self.nome, self.x0, self.y0, self.passo, self.nx, self.ny = nome, x0, y0, passo, nx, ny
        self.dati = {c: np.full((nx, ny), NAN, dtype=np.int32) for c in CAMPI}
        self.righe_lette = 0

    def contiene(self, x, y):
        i = (x - self.x0) / self.passo
        j = (y - self.y0) / self.passo
        return 0 <= i <= self.nx - 1 and 0 <= j <= self.ny - 1

    def indici(self, x, y):
        return int(round((x - self.x0) / self.passo)), int(round((y - self.y0) / self.passo))


class Terreno:
    def __init__(self):
        self.regioni = []
        self.completo = False

    @classmethod
    def carica(cls, percorso):
        t = cls()
        reg = None
        with open(percorso, encoding='utf-8', errors='replace') as f:
            for riga in f:
                riga = riga.strip()
                if not riga or riga.startswith('#'):
                    continue
                if riga == 'FINE':
                    t.completo = True
                    break
                if riga.startswith('R,'):
                    _, nome, x0, y0, passo, nx, ny = riga.split(',')
                    reg = Regione(nome, float(x0), float(y0), int(passo), int(nx), int(ny))
                    t.regioni.append(reg)
                    continue
                i_str, resto = riga.split(',', 1)
                i = int(i_str)
                for j, cella in enumerate(resto.split(';')):
                    if cella == '3':                       # acqua
                        reg.dati['sup'][i, j] = 3
                    elif cella == 'E':                     # errore di misura
                        continue
                    else:
                        valori = cella.split(',')
                        for c, v in zip(CAMPI, valori):
                            reg.dati[c][i, j] = int(v)
                reg.righe_lette = i + 1
        return t

    def punto(self, x, y):
        """Valori nel punto, dalla regione con il passo piu' fine che lo contiene."""
        for reg in sorted(self.regioni, key=lambda r: r.passo):
            if reg.contiene(x, y):
                i, j = reg.indici(x, y)
                if i < reg.righe_lette:
                    out = {c: int(reg.dati[c][i, j]) for c in CAMPI}
                    out['regione'] = reg.nome
                    return out
        return None

    def riepilogo(self):
        righe = []
        for r in self.regioni:
            sup = r.dati['sup'][:r.righe_lette]
            n = sup.size
            terra = int(((sup == 1) | (sup == 4)).sum())
            acqua = int(((sup == 2) | (sup == 3)).sum())
            righe.append('%s: %d x %d punti (passo %d m), righe lette %d/%d, terra %d, acqua %d'
                         % (r.nome, r.nx, r.ny, r.passo, r.righe_lette, r.nx, terra, acqua))
        righe.append('rilievo completo' if self.completo else 'rilievo INCOMPLETO')
        return '\n'.join(righe)
