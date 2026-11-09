"""Conversione coordinate mappa Syria di DCS <-> lat/lon (WGS84).

DCS usa una Trasversa di Mercatore: x = nord (m), y = est (m).
Parametri da pydcs (dcs/terrain/syria/projection.py).
"""
import math

A = 6378137.0
F = 1 / 298.257223563
E2 = F * (2 - F)
EP2 = E2 / (1 - E2)
K0 = 0.9996
LON0 = math.radians(39)
FE = 282801.00000003993
FN = -3879865.9999999935


def _M(phi):
    return A * ((1 - E2 / 4 - 3 * E2**2 / 64 - 5 * E2**3 / 256) * phi
                - (3 * E2 / 8 + 3 * E2**2 / 32 + 45 * E2**3 / 1024) * math.sin(2 * phi)
                + (15 * E2**2 / 256 + 45 * E2**3 / 1024) * math.sin(4 * phi)
                - (35 * E2**3 / 3072) * math.sin(6 * phi))


def ll_to_xy(lat, lon):
    phi, lam = math.radians(lat), math.radians(lon)
    N = A / math.sqrt(1 - E2 * math.sin(phi)**2)
    T = math.tan(phi)**2
    C = EP2 * math.cos(phi)**2
    Aa = (lam - LON0) * math.cos(phi)
    east = K0 * N * (Aa + (1 - T + C) * Aa**3 / 6 + (5 - 18 * T + T**2 + 72 * C - 58 * EP2) * Aa**5 / 120)
    north = K0 * (_M(phi) + N * math.tan(phi) * (Aa**2 / 2 + (5 - T + 9 * C + 4 * C**2) * Aa**4 / 24
                                                 + (61 - 58 * T + T**2 + 600 * C - 330 * EP2) * Aa**6 / 720))
    return north + FN, east + FE


def xy_to_ll(x, y):
    N_, E_ = x - FN, y - FE
    e1 = (1 - math.sqrt(1 - E2)) / (1 + math.sqrt(1 - E2))
    mu = N_ / K0 / (A * (1 - E2 / 4 - 3 * E2**2 / 64 - 5 * E2**3 / 256))
    p = (mu + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu) + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
         + (151 * e1**3 / 96) * math.sin(6 * mu) + (1097 * e1**4 / 512) * math.sin(8 * mu))
    C = EP2 * math.cos(p)**2
    T = math.tan(p)**2
    Nn = A / math.sqrt(1 - E2 * math.sin(p)**2)
    R = A * (1 - E2) / (1 - E2 * math.sin(p)**2)**1.5
    D = E_ / (Nn * K0)
    lat = p - (Nn * math.tan(p) / R) * (D**2 / 2 - (5 + 3 * T + 10 * C - 4 * C**2 - 9 * EP2) * D**4 / 24
                                       + (61 + 90 * T + 298 * C + 45 * T**2 - 252 * EP2 - 3 * C**2) * D**6 / 720)
    lon = LON0 + (D - (1 + 2 * T + C) * D**3 / 6 + (5 - 2 * C + 28 * T - 3 * C**2 + 8 * EP2 + 24 * T**2) * D**5 / 120) / math.cos(p)
    return math.degrees(lat), math.degrees(lon)


def dms(lat, lon):
    def f(v, pos, neg):
        h = pos if v >= 0 else neg
        v = abs(v)
        d = int(v)
        m = (v - d) * 60
        return "%s %02d°%06.3f'" % (h, d, m)
    return f(lat, 'N', 'S') + ' ' + f(lon, 'E', 'W')


def dist_brg(x1, y1, x2, y2):
    """Distanza (m) e rotta vera (gradi) da punto 1 a punto 2 (approssimata sulla griglia)."""
    dx, dy = x2 - x1, y2 - y1
    return math.hypot(dx, dy), (math.degrees(math.atan2(dy, dx)) + 360) % 360
