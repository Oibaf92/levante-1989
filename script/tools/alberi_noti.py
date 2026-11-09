"""Alberi rilevati dagli screenshot ravvicinati (verifica_alberi.py): conoscenza permanente.

Ogni screenshot ravvicinato verificato aggiunge:
  - la sua area coperta (rettangolo in coordinate mappa): li' sappiamo DOVE ci sono alberi e
    dove NO;
  - le posizioni degli alberi, arrotondate a una griglia da 3 m.
Il piazzatore usa questi dati per tenere ogni veicolo ad almeno RAGGIO_LIBERO dagli alberi.

File: campagna/terreno/alberi_noti.npz
"""
import math
import os

import numpy as np

QUI = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(QUI, '..', '..', 'campagna', 'terreno', 'alberi_noti.npz')
GRIGLIA = 3.0
RAGGIO_LIBERO = 14.0
SOGLIA = 3              # celle d'albero tollerate entro il raggio (pixel isolati, bordi dei campi)


class AlberiNoti:
    def __init__(self, percorso=FILE):
        self.percorso = percorso
        self.alberi = np.zeros((0, 2), dtype=np.int32)       # celle da 3 m
        self.aree = np.zeros((0, 4))                         # x_min, x_max, y_min, y_max
        self.zone = np.zeros((0, 3))                         # x, y, raggio: zone da evitare (segni BOSCO/SPOSTA)
        if os.path.exists(percorso):
            d = np.load(percorso)
            self.alberi, self.aree = d['alberi'], d['aree']
            if 'zone' in d.files:
                self.zone = d['zone']
        self._indice()

    def _indice(self):
        self._set = {}
        for i, j in self.alberi:
            self._set.setdefault((int(i) // 10, int(j) // 10), []).append((i, j))

    def salva(self):
        np.savez_compressed(self.percorso, alberi=self.alberi, aree=self.aree, zone=self.zone)

    def aggiungi_zona(self, x, y, raggio=300.0):
        self.zone = np.vstack([self.zone, np.array([[x, y, raggio]])])

    def in_zona_da_evitare(self, x, y):
        return bool(len(self.zone)) and bool((np.hypot(self.zone[:, 0] - x, self.zone[:, 1] - y) < self.zone[:, 2]).any())

    def aggiungi_verifica(self, r, area_pixel):
        """Aggiunge alberi e area coperta da un risultato di verifica_alberi.verifica()."""
        s, X0, Y0 = r['trasf']
        l, t, rr, bb = area_pixel
        ay, ax = np.nonzero(r['alberi'])
        x = X0 - s * ay
        y = Y0 + s * ax
        celle = np.unique(np.stack([np.round(x / GRIGLIA), np.round(y / GRIGLIA)], 1).astype(np.int32), axis=0)
        self.alberi = np.unique(np.vstack([self.alberi, celle]), axis=0)
        area = (X0 - s * (bb - 10), X0 - s * (t + 10), Y0 + s * (l + 10), Y0 + s * (rr - 10))
        self.aree = np.vstack([self.aree, np.array(area)[None]])
        self._indice()
        return len(celle)

    def coperto(self, x, y):
        return bool(((self.aree[:, 0] <= x) & (x <= self.aree[:, 1]) & (self.aree[:, 2] <= y) & (y <= self.aree[:, 3])).any()) \
            if len(self.aree) else False

    def alberi_vicini(self, x, y, raggio=RAGGIO_LIBERO):
        ci, cj = x / GRIGLIA, y / GRIGLIA
        r = raggio / GRIGLIA
        n = 0
        for bi in range(int((ci - r) // 10), int((ci + r) // 10) + 1):
            for bj in range(int((cj - r) // 10), int((cj + r) // 10) + 1):
                for i, j in self._set.get((bi, bj), ()):
                    if (i - ci) ** 2 + (j - cj) ** 2 <= r * r:
                        n += 1
        return n

    def libero(self, x, y, raggio=RAGGIO_LIBERO):
        """True/False se la zona e' stata verificata; None se non ne sappiamo nulla."""
        if self.in_zona_da_evitare(x, y):
            return False
        if not self.coperto(x, y):
            return None
        return self.alberi_vicini(x, y, raggio) <= SOGLIA

    def punto_libero_vicino(self, x, y, massimo=150.0, passo=5.0):
        """Il punto verificato senza alberi piu' vicino (o None)."""
        if self.libero(x, y) is not False:
            return x, y, 0.0
        d = passo
        while d <= massimo:
            n = max(8, int(2 * math.pi * d / passo))
            for k in range(n):
                a = 2 * math.pi * k / n
                px, py = x + d * math.cos(a), y + d * math.sin(a)
                if self.libero(px, py):
                    return px, py, d
            d += passo
        return None
