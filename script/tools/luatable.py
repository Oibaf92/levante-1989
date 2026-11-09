"""Lettura e scrittura delle tabelle Lua usate nei file .miz di DCS.

parse(testo)          -> (nome, valore)   es. ("mission", {...})
dump(nome, valore)    -> testo Lua nel formato del Mission Editor

Le chiavi intere restano int, quelle stringa restano str: l'ordine e i tipi
vengono preservati, cosi' un file letto e riscritto resta equivalente.
"""
import re

_TOKEN = re.compile(
    r'\s*(?:--\[\[.*?\]\]|--[^\n]*)?\s*'
    r'(?:(\[\[.*?\]\])|("(?:\\.|\\\n|[^"\\])*")|'
    r'(-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)|'
    r'(true|false|nil)\b|([A-Za-z_][A-Za-z0-9_]*)|(\S))',
    re.S,
)

_ESC = {'n': '\n', 't': '\t', 'r': '\r', '"': '"', "'": "'", '\\': '\\', '\n': '\n', 'a': '\a', 'b': '\b', 'f': '\f', 'v': '\v'}


def _unescape(s):
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i + 1 < len(s):
            n = s[i + 1]
            if n.isdigit():
                j = i + 1
                while j < len(s) and j < i + 4 and s[j].isdigit():
                    j += 1
                out.append(chr(int(s[i + 1:j])))
                i = j
                continue
            out.append(_ESC.get(n, n))
            i += 2
        else:
            out.append(c)
            i += 1
    return ''.join(out)


def _lex(text):
    pos = 0
    n = len(text)
    while pos < n:
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            break
        pos = m.end()
        ls, st, num, kw, ident, ch = m.groups()
        if ls is not None:
            yield ('s', ls[2:-2])
        elif st is not None:
            yield ('s', _unescape(st[1:-1]))
        elif num is not None:
            yield ('n', float(num) if any(c in num for c in '.eE') else int(num))
        elif kw is not None:
            yield ('k', {'true': True, 'false': False, 'nil': None}[kw])
        elif ident is not None:
            yield ('i', ident)
        elif ch is not None:
            yield ('c', ch)


def parse(text):
    toks = list(_lex(text))
    p = 0

    def value():
        nonlocal p
        kind, v = toks[p]
        p += 1
        if kind == 'c' and v == '{':
            d, idx = {}, 1
            while True:
                if toks[p] == ('c', '}'):
                    p += 1
                    return d
                if toks[p] == ('c', '['):
                    p += 1
                    key = value()
                    p += 2  # ']' '='
                    d[key] = value()
                elif toks[p][0] == 'i' and toks[p + 1] == ('c', '='):
                    key = toks[p][1]
                    p += 2
                    d[key] = value()
                else:
                    d[idx] = value()
                    idx += 1
                if toks[p] in (('c', ','), ('c', ';')):
                    p += 1
        if kind == 'c' and v == '-':  # numero negativo separato
            k2, v2 = toks[p]
            p += 1
            return -v2
        return v

    name = toks[0][1]
    p = 2
    return name, value()


def _str(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\\n') + '"'


def _scalar(v):
    if v is True:
        return 'true'
    if v is False:
        return 'false'
    if v is None:
        return 'nil'
    if isinstance(v, str):
        return _str(v)
    if isinstance(v, float):
        if v.is_integer() and abs(v) < 1e15:
            return repr(v)
        return repr(v)
    return str(v)


def _dump(v, indent, out):
    if isinstance(v, dict):
        out.append('\n' + '\t' * indent + '{\n')
        for k, x in v.items():
            key = '[%s]' % (_str(k) if isinstance(k, str) else k)
            out.append('\t' * (indent + 1) + key + ' = ')
            if isinstance(x, dict):
                _dump(x, indent + 1, out)
                out.append(', -- end of %s\n' % key)
            else:
                out.append(_scalar(x) + ',\n')
        out.append('\t' * indent + '}')
    else:
        out.append(_scalar(v))


def dump(name, value):
    out = [name + ' = ']
    _dump(value, 0, out)
    out.append(' -- end of %s\n' % name)
    return ''.join(out)
