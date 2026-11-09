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


# ---------------------------------------------------------------------------
# Vegetazione (dagli screenshot SAT della missione R01, griglia da 250 m)
# ---------------------------------------------------------------------------
class Vegetazione:
    def __init__(self, percorso_npz):
        d = np.load(percorso_npz)
        self.f = d['frazione']
        self.x0, self.y0, self.passo = float(d['x0']), float(d['y0']), float(d['passo'])

    def frazione(self, x, y, raggio=500.0):
        """Frazione media di vegetazione entro 'raggio' metri (None se l'area non e' coperta)."""
        r = int(round(raggio / self.passo))
        i = int(round((x - self.x0) / self.passo))
        j = int(round((y - self.y0) / self.passo))
        if i < -r or j < -r or i > self.f.shape[0] + r or j > self.f.shape[1] + r:
            return None
        blocco = self.f[max(0, i - r):i + r + 1, max(0, j - r):j + r + 1]
        if blocco.size == 0 or np.all(np.isnan(blocco)):
            return None
        return float(np.nanmean(blocco))

    def su_regione(self, reg, raggio=500.0):
        """Matrice (percentuale 0-100, -1 = non coperta) per ogni punto di una regione del rilievo."""
        out = np.full((reg.nx, reg.ny), -1, dtype=np.int32)
        for i in range(reg.nx):
            x = reg.x0 + i * reg.passo
            for j in range(reg.ny):
                v = self.frazione(x, reg.y0 + j * reg.passo, raggio)
                if v is not None:
                    out[i, j] = int(round(v * 100))
        return out


def carica_tutto(percorso_rilievo, percorso_vegetazione=None):
    """Terreno con il campo aggiuntivo 'vegetazione' (% entro 500 m, -1 = sconosciuta)."""
    t = Terreno.carica(percorso_rilievo)
    veg = Vegetazione(percorso_vegetazione) if percorso_vegetazione else None
    for reg in t.regioni:
        reg.dati['vegetazione'] = veg.su_regione(reg) if veg else np.full((reg.nx, reg.ny), -1, dtype=np.int32)
    return t
