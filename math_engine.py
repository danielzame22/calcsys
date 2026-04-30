# math_engine.py — Motor matemático offline con SymPy
"""
Interpreta texto en español y resuelve con SymPy.
Sin IA, sin internet. 100% local.
"""
import re as _re
from sympy import *
# restore re as the stdlib module (sympy shadows it with its own 're' symbol)
re = _re
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations,
    implicit_multiplication_application, convert_xor
)

x, y, z, t, n = symbols('x y z t n')
TRANSFORMS = standard_transformations + (implicit_multiplication_application, convert_xor)


# ── Preprocesado de texto ──────────────────────────────────────────────────────
def _clean(expr_str):
    """Normaliza la cadena antes de parsear."""
    s = expr_str.strip()
    # superscripts unicode → ^
    sup = {'⁰':'0','¹':'1','²':'2','³':'3','⁴':'4','⁵':'5','⁶':'6','⁷':'7','⁸':'8','⁹':'9'}
    for k, v in sup.items():
        s = s.replace(k, '^' + v)
    # palabras matemáticas
    replacements = {
        'sen': 'sin', 'tg': 'tan', 'arctg': 'atan',
        'arcsen': 'asin', 'arccos': 'acos',
        'raíz': 'sqrt', 'raiz': 'sqrt',
        'ln': 'log',  # log en sympy es ln; log base => log(x,b)
        'e^': 'exp(',  # se cierra más abajo si hace falta
        'π': 'pi', '∞': 'oo', 'inf': 'oo',
        '×': '*', '÷': '/', '·': '*',
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s


def _parse(s):
    return parse_expr(_clean(s), transformations=TRANSFORMS,
                      local_dict={'x':x,'y':y,'z':z,'t':t,'n':n,
                                  'pi':pi,'e':E,'oo':oo,'I':I})


# ── Detección de tipo de problema ─────────────────────────────────────────────
_KEYWORDS = {
    'integral':   ['integral', 'integra', 'antiderivada', '∫'],
    'derivada':   ['deriv', 'diferencia', 'd/dx', 'derivada'],
    'limite':     ['límite', 'limite', 'lim'],
    'ecuacion':   ['=', 'ecuaci', 'resuelve', 'halla', 'encuentra', 'despeja'],
    'sistema':    ['sistema', 'ecuaciones:'],
    'factorizar': ['factor', 'factoriza'],
    'simplificar':['simplif'],
    'expandir':   ['expand', 'expande'],
    'tabla':      ['tabla', 'valores'],
    'raices':     ['raíces', 'raices', 'ceros', 'zeros'],
    'log':        ['logaritm', 'log₂', 'log₁₀'],
}

def _detect(text):
    tl = text.lower()
    for kind, kws in _KEYWORDS.items():
        if any(k in tl for k in kws):
            return kind
    return 'expresion'


# ── Extraer expresión limpia del texto ────────────────────────────────────────
def _extract_expr(text):
    """Quita palabras clave y deja solo la expresión."""
    tl = text.lower()
    # quitar frases comunes
    remove_phrases = [
        'calcula la integral de', 'integral de', 'integra',
        'deriva', 'derivada de', 'calcula la derivada de',
        'calcula el límite de', 'límite de', 'limite de', 'lim',
        'resuelve', 'halla', 'encuentra', 'factoriza',
        'simplifica', 'expande', 'tabla de valores para',
        'tabla de', 'raíces de', 'raices de', 'ceros de',
        'calcula', 'dx', 'dy', 'dz', 'con respecto a x',
        'con respecto a', 'f(x) =', 'f(x)=',
    ]
    s = text
    for ph in remove_phrases:
        s = re.sub(ph, '', s, flags=re.IGNORECASE).strip()
    return s.strip()


# ── Helpers de formato ─────────────────────────────────────────────────────────
def _fmt(expr):
    """Convierte expresión sympy a texto legible."""
    return str(expr).replace('**', '^').replace('*', '·').replace('sqrt', '√')


def _steps_header(title):
    return f'══ {title.upper()} ══\n'


# ── Resolvers ──────────────────────────────────────────────────────────────────

def resolver_integral(text):
    # buscar variable de integración
    var = x
    if ' dy' in text: var = y
    if ' dz' in text: var = z
    if ' dt' in text: var = t

    # integral definida: buscar "entre A y B" o "[A,B]" o "de A a B"
    rng = re.search(r'(?:entre|de)\s*([-\d.]+)\s*(?:y|a)\s*([-\d.]+)', text, re.I)
    if not rng:
        rng = re.search(r'\[([^\]]+),([^\]]+)\]', text)

    raw = _extract_expr(text)
    try:
        expr = _parse(raw)
    except Exception:
        return 'No pude parsear la expresión. Intenta: "integral de x^2 dx"'

    out = _steps_header('integral')
    if rng:
        a, b = float(rng.group(1)), float(rng.group(2))
        indef = integrate(expr, var)
        result = integrate(expr, (var, a, b))
        out += f'Expresión:   {_fmt(expr)}\n'
        out += f'Intervalo:   [{a}, {b}]\n\n'
        out += f'Antiderivada: {_fmt(indef)} + C\n\n'
        out += f'Resultado:   {_fmt(result)}'
        try:
            out += f'  ≈  {float(result.evalf()):.6f}'
        except Exception:
            pass
    else:
        result = integrate(expr, var)
        out += f'Expresión:   {_fmt(expr)}\n\n'
        out += f'Resultado:   {_fmt(result)} + C'
    return out


def resolver_derivada(text):
    # orden de derivada
    orden = 1
    m = re.search(r'(\d+)[aª]?\s*(?:orden|vez)', text, re.I)
    if m:
        orden = int(m.group(1))

    raw = _extract_expr(text)
    try:
        expr = _parse(raw)
    except Exception:
        return 'No pude parsear. Intenta: "deriva x^3 - 4x + 2"'

    out = _steps_header('derivada')
    out += f'f(x)  =  {_fmt(expr)}\n\n'
    result = diff(expr, x, orden)
    label = "f'(x)" if orden == 1 else f'f^({orden})(x)'
    out += f'{label} =  {_fmt(result)}'

    # puntos críticos
    try:
        criticos = solve(result, x)
        if criticos:
            out += f'\n\nPuntos críticos:  x = {", ".join(_fmt(c) for c in criticos)}'
    except Exception:
        pass
    return out


def resolver_limite(text):
    # buscar "cuando x → valor" o "x->valor" o "x tiende a valor"
    m = re.search(r'(?:cuando\s+)?[xyz]\s*(?:→|->|tiende\s+a)\s*([-\d.]+|oo|∞|inf|cero|0)', text, re.I)
    punto = oo
    if m:
        raw_p = m.group(1).lower()
        if raw_p in ('oo', '∞', 'inf'):
            punto = oo
        elif raw_p == 'cero':
            punto = 0
        else:
            try: punto = float(raw_p)
            except: punto = oo

    raw = _extract_expr(text)
    # quitar "cuando x→..."
    raw = re.sub(r'(?:cuando\s+)?[xyz]\s*(?:→|->|tiende\s+a)\s*\S+', '', raw, flags=re.I).strip()
    try:
        expr = _parse(raw)
    except Exception:
        return 'No pude parsear. Intenta: "límite de (1+1/x)^x cuando x→∞"'

    out = _steps_header('límite')
    punto_str = '∞' if punto is oo else str(punto)
    out += f'lim(x→{punto_str})  {_fmt(expr)}\n\n'
    result = limit(expr, x, punto)
    out += f'Resultado:  {_fmt(result)}'
    try:
        out += f'  ≈  {float(result.evalf()):.6f}'
    except Exception:
        pass
    return out


def resolver_ecuacion(text):
    # sistema de ecuaciones?
    if '\n' in text or (' y ' in text.lower() and text.count('=') >= 2):
        return resolver_sistema(text)

    raw = _extract_expr(text)
    # separar por '='
    if '=' in raw:
        lhs, rhs = raw.split('=', 1)
        try:
            eq = _parse(lhs) - _parse(rhs)
        except Exception:
            return 'No pude parsear la ecuación.'
    else:
        try:
            eq = _parse(raw)
        except Exception:
            return 'No pude parsear la expresión.'

    out = _steps_header('ecuación')
    out += f'Ecuación:  {_fmt(_parse(raw.split("=")[0]) if "=" in raw else _parse(raw))} = {_fmt(_parse(raw.split("=")[1]) if "=" in raw else S.Zero)}\n\n'

    try:
        sols = solve(eq, x)
        if not sols:
            # intentar numéricamente
            sols_num = nsolve(eq, x, 0)
            out += f'Resultado (numérico):  x ≈ {float(sols_num):.6f}'
        else:
            out += 'Soluciones:\n'
            for i, s in enumerate(sols, 1):
                out += f'  x{i} = {_fmt(s)}'
                try: out += f'  ≈  {float(s.evalf()):.4f}'
                except: pass
                out += '\n'
    except Exception as e:
        out += f'No se pudo resolver simbólicamente.\nError: {e}'
    return out.rstrip()


def resolver_sistema(text):
    # extraer pares de ecuaciones - use raw text, not extract_expr
    raw_text = re.sub(r'sistema\s*:\s*', '', text, flags=re.I)
    lines = [l.strip() for l in re.split(r',|;|\n', raw_text, flags=re.I) if '=' in l]
    if len(lines) < 2:
        return 'Para un sistema escribe cada ecuación separada por coma o línea nueva.\nEj: 2x + y = 7, x - y = 1'

    eqs = []
    syms_used = set()
    for line in lines:
        line = _extract_expr(line)
        if '=' in line:
            lhs, rhs = line.split('=', 1)
            try:
                eq = _parse(lhs) - _parse(rhs)
                eqs.append(eq)
                for s in [x, y, z]:
                    if eq.has(s): syms_used.add(s)
            except Exception:
                pass

    out = _steps_header('sistema de ecuaciones')
    for i, eq in enumerate(eqs, 1):
        out += f'  ({i}) {_fmt(eq)} = 0\n'
    out += '\n'

    try:
        sol = solve(eqs, list(syms_used))
        if isinstance(sol, dict):
            for sym, val in sol.items():
                out += f'  {sym} = {_fmt(val)}'
                try: out += f'  ≈  {float(val.evalf()):.4f}'
                except: pass
                out += '\n'
        elif isinstance(sol, list) and sol:
            for sv in sol:
                out += str(sv) + '\n'
        else:
            out += 'Sin solución o infinitas soluciones.'
    except Exception as e:
        out += f'Error: {e}'
    return out.rstrip()


def resolver_factorizar(text):
    raw = _extract_expr(text)
    try:
        expr = _parse(raw)
    except Exception:
        return 'No pude parsear. Intenta: "factoriza x^2 - 9"'

    out = _steps_header('factorización')
    out += f'Expresión:  {_fmt(expr)}\n\n'
    result = factor(expr)
    out += f'Factorizado:  {_fmt(result)}\n'

    # raíces
    try:
        raices = solve(expr, x)
        if raices:
            out += f'\nRaíces:  x = {", ".join(_fmt(r) for r in raices)}'
    except Exception:
        pass
    return out


def resolver_simplificar(text):
    raw = _extract_expr(text)
    try:
        expr = _parse(raw)
    except Exception:
        return 'No pude parsear la expresión.'
    out = _steps_header('simplificación')
    out += f'Original:    {_fmt(expr)}\n'
    out += f'Simplificado: {_fmt(simplify(expr))}\n'
    out += f'Expandido:    {_fmt(expand(expr))}'
    return out


def resolver_tabla(text):
    # buscar rango
    rng = re.search(r'(?:entre|de)\s*([-\d.]+)\s*(?:y|a)\s*([-\d.]+)', text, re.I)
    a, b = -5, 5
    if rng:
        a, b = float(rng.group(1)), float(rng.group(2))

    import re as stdlib_re
    raw = stdlib_re.sub(r'tabla\s+de\s+valores\s+para\s*', '', text, flags=stdlib_re.I)
    raw = stdlib_re.sub(r'tabla\s+de\s*', '', raw, flags=stdlib_re.I)
    raw = stdlib_re.sub(r'entre\s+[\-\d\.]+\s+(?:y|a)\s+[\-\d\.]+', '', raw, flags=stdlib_re.I).strip()
    try:
        expr = _parse(raw)
    except Exception:
        return 'No pude parsear. Intenta: "tabla de valores para x^2 entre -3 y 3"'

    # limitar a 15 puntos
    steps = int(b - a)
    if steps > 14: steps = 14
    vals = [a + i*(b-a)/steps for i in range(steps+1)]

    out = _steps_header('tabla de valores')
    out += f'f(x) = {_fmt(expr)}\n\n'
    out += f'{"x":>8}  │  {"f(x)":>12}\n'
    out += '─' * 24 + '\n'
    for v in vals:
        try:
            fv = float(expr.subs(x, v).evalf())
            out += f'{v:>8.2f}  │  {fv:>12.4f}\n'
        except Exception:
            out += f'{v:>8.2f}  │  {"error":>12}\n'
    return out.rstrip()


def resolver_logaritmo(text):
    # detectar base
    base = None
    m = re.search(r'log[_₁₂₃]?(\d+)', text, re.I)
    if m:
        base = int(m.group(1))
    # log₂ etc.
    bases_unicode = {'₂':2,'₃':3,'₄':4,'₅':5,'₆':6,'₇':7,'₈':8,'₉':9,'₁₀':10}
    for k,v in bases_unicode.items():
        if k in text: base = v

    raw = _extract_expr(text)
    raw = re.sub(r'logaritm[oa]?\s*', '', raw, flags=re.I).strip()
    raw = re.sub(r'log[₀-₉₁₀_]*\d*', '', raw, flags=re.I).strip()
    raw = re.sub(r'[\(\)]', '', raw).strip()

    try:
        expr = _parse(raw) if raw else x
    except Exception:
        expr = x

    out = _steps_header('logaritmo')
    if base:
        result = log(expr, base)
        out += f'log_{base}({_fmt(expr)})\n\n'
    else:
        result = log(expr)
        out += f'ln({_fmt(expr)})\n\n'

    out += f'Simbólico:  {_fmt(result)}\n'
    try:
        num = float(result.evalf())
        out += f'Numérico:   {num:.6f}'
    except Exception:
        pass
    return out


def resolver_expresion(text):
    """Fallback: simplifica/evalúa la expresión tal cual."""
    raw = _extract_expr(text)
    try:
        expr = _parse(raw)
    except Exception:
        return (
            'No pude interpretar la expresión.\n\n'
            'Ejemplos válidos:\n'
            '  integral de x^2 dx\n'
            '  deriva x^3 - 4x\n'
            '  resuelve 2x + 5 = 13\n'
            '  límite de 1/x cuando x→∞\n'
            '  factoriza x^2 - 9\n'
            '  tabla de valores para sin(x) entre -3 y 3\n'
            '  sistema: 2x+y=7, x-y=1'
        )

    out = _steps_header('expresión')
    out += f'Input:       {_fmt(expr)}\n'
    out += f'Simplificado: {_fmt(simplify(expr))}\n'
    out += f'Expandido:   {_fmt(expand(expr))}\n'

    # si es numérica
    try:
        num = float(expr.evalf())
        out += f'Valor:       {num:.6f}'
    except Exception:
        pass

    # derivada por defecto
    try:
        d = diff(expr, x)
        if d != S.Zero:
            out += f"\nDerivada f'(x): {_fmt(d)}"
    except Exception:
        pass

    return out


# ── PUNTO DE ENTRADA PRINCIPAL ─────────────────────────────────────────────────
def resolver(texto):
    """
    Función pública. Recibe texto en español, retorna solución como string.
    """
    texto = texto.strip()
    if not texto:
        return 'Escribe una ecuación o problema.'

    kind = _detect(texto)

    try:
        if kind == 'integral':
            return resolver_integral(texto)
        elif kind == 'derivada':
            return resolver_derivada(texto)
        elif kind == 'limite':
            return resolver_limite(texto)
        elif kind == 'sistema':
            return resolver_sistema(texto)
        elif kind == 'ecuacion':
            return resolver_ecuacion(texto)
        elif kind == 'factorizar':
            return resolver_factorizar(texto)
        elif kind == 'simplificar':
            return resolver_simplificar(texto)
        elif kind == 'expandir':
            raw = _extract_expr(texto)
            expr = _parse(raw)
            return f'═══ EXPANDIR ═══\n\n{_fmt(expr)}\n\n= {_fmt(expand(expr))}'
        elif kind == 'tabla':
            return resolver_tabla(texto)
        elif kind == 'log':
            return resolver_logaritmo(texto)
        else:
            return resolver_expresion(texto)
    except Exception as e:
        return f'Error al resolver: {e}\n\nIntenta reformular el problema.'
