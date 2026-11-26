"""Guías TS Zenit Universidad · Química para Ingeniería (QIM100E UC).
Guía: 20 alternativas (A–E) + 3 desarrollo.  Simulada: 8 alternativas (32 pts) + 4 desarrollo (68 pts).
Uso:  from qim_guia import *;  ...;  build(spec, "out", claves(seed))"""
import sys, json, math, pathlib, random
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import pre_guia as P                      # reutiliza normalización LaTeX, verificación QR y parches
from pre_guia import G, render_math, esc, LETRAS, normalizar, chequear_tex
from collections import Counter

G.PRUEBAS["QIM"] = "TS Zenit Universidad · Química para Ingeniería"
EJE = "Química para Ingeniería"
H, A = "Resolver problemas", "Argumentar"

# ---------- formato numérico chileno ----------
def nf(x, d=2):
    s = f"{x:.{d}f}".replace("-", "−")
    return s.replace(".", ",")
def sf(x, sig=3):
    """x con 'sig' cifras significativas, coma decimal (sin notación científica)."""
    if x == 0: return "0"
    d = max(0, sig - 1 - int(math.floor(math.log10(abs(x)))))
    return nf(round(x, d), d)
def sci(x, sig=3, math_=True):
    e = int(math.floor(math.log10(abs(x)))); m = x / 10**e
    if round(abs(m), sig - 1) >= 10: m /= 10; e += 1
    ms = f"{m:.{sig-1}f}".replace(".", "{,}").replace("-", "-")
    t = f"{ms}\\times10^{{{e}}}" if e != 0 else ms
    return f"\\({t}\\)" if math_ else t

# ---------- helpers de contenido ----------
def Q(enun, alts, contenido, habilidad, dificultad, pasos, dis, idea, figura=None):
    """alts[0] es la correcta (5 alternativas); dis = explicaciones de alts[1..4]."""
    assert len(alts) == 5 and len(dis) == 4, (enun[:60], len(alts), len(dis))
    assert len(set(alts)) == 5, ("alternativas repetidas", enun[:60], alts)
    q = {"enunciado": enun, "_alts": alts, "_dis": dis, "eje": EJE, "contenido": contenido, "habilidad": habilidad,
         "dificultad": dificultad, "origen": "Original",
         "solucion": {"pasos": [{"t": t, "d": d} for t, d in pasos], "idea": idea}}
    if figura: q["figura"] = figura
    return q

def D(enun, respuesta, contenido, habilidad, dificultad, pasos, idea, puntos):
    return {"enunciado": enun, "desarrollo": True, "puntos": puntos, "alternativas": [], "clave": "Des.",
            "respuesta": respuesta, "eje": EJE, "contenido": contenido, "habilidad": habilidad, "dificultad": dificultad,
            "origen": "Original", "solucion": {"pasos": [{"t": t, "d": d} for t, d in pasos], "idea": idea}}

def claves(seed, n=20):
    r = random.Random(seed)
    while True:
        c = list("ABCDE" * (n // 5) + "ABCDE"[: n % 5]); r.shuffle(c)
        if all(len(set(c[i:i + 3])) > 1 for i in range(n - 2)): return c

def asignar_claves(pregs, cl):
    mc = [q for q in pregs if not q.get("desarrollo")]
    assert len(mc) == len(cl), (len(mc), len(cl))
    for q, L in zip(mc, cl):
        pos = "ABCDE".index(L)
        alts, dis = q.pop("_alts"), q.pop("_dis")
        otras = list(zip(alts[1:], dis))
        orden = otras[:pos] + [(alts[0], None)] + otras[pos:]
        q["alternativas"] = [a for a, _ in orden]
        q["clave"] = L
        q["solucion"]["distractores"] = {LETRAS[i]: d for i, (_, d) in enumerate(orden) if d is not None}

# ---------- render ----------
INSTR_G = [
    "Esta guía tiene dos partes. Parte I: 20 preguntas de selección múltiple con cinco alternativas (a, b, c, d y e); en cada una, solo una es correcta.",
    "Parte II: 3 preguntas de desarrollo. Muestra tu procedimiento con unidades y cifras significativas; la pauta indica cuántos puntos vale cada paso.",
    "Marca la Parte I en la hoja de respuestas al final del cuadernillo. Puedes usar calculadora científica.",
    "Preguntas originales, alineadas con los contenidos de QIM100E Química para Ingeniería (UC) y la bibliografía del curso (Petrucci, Chang, Brown).",
    "Cada pregunta tiene un código QR: escanéalo después de responder para ver su solución paso a paso.",
]
def INSTR_S(n_mc, n_d, pts_d, minutos):
    return [
        f"Esta prueba tiene dos partes. Parte I: {n_mc} preguntas de selección múltiple con cinco alternativas (a, b, c, d y e); en cada una, solo una es correcta ({4*n_mc} puntos, 4 cada una).",
        f"Parte II: {n_d} preguntas de desarrollo ({pts_d} puntos en total). Muestra tu procedimiento con unidades y cifras significativas; la pauta indica cuántos puntos vale cada paso.",
        f"Dispones de {minutos} minutos. Marca la Parte I en la hoja de respuestas al final del cuadernillo. Puedes usar calculadora científica.",
        "Preguntas originales, alineadas con los contenidos de QIM100E Química para Ingeniería (UC) y la bibliografía del curso (Petrucci, Chang, Brown).",
        "Cada pregunta tiene un código QR: escanéalo después de responder para ver su solución paso a paso.",
    ]
CSS_Q = P.CSS_EXTRA + """
.q.des.primera { break-before: auto; }
.parte2 h2 { font: 700 13pt Poppins, 'DejaVu Sans', sans-serif; color: #1B1F5E; margin: 2mm 0 1.5mm; }
.parte2 p { font-size: 9pt; color: #444; margin: 0 0 4mm; }
.datos { border: .6pt solid #1B1F5E; border-radius: 2mm; padding: 2mm 3mm; margin: 0 0 4mm; font-size: 8.6pt; }
.datos b.t { display: block; font: 700 7.5pt Poppins, 'DejaVu Sans', sans-serif; color: #1B1F5E; letter-spacing: .08em; text-transform: uppercase; margin-bottom: 1mm; }
table.enun { border-collapse: collapse; margin: 1.5mm 0; font-size: 8.6pt; }
table.enun th, table.enun td { border: .5pt solid #999; padding: .8mm 2.2mm; text-align: center; }
table.enun th { background: #EEF0FA; }
"""

def build_ensayo_html(spec, targets, labels):
    pregs = spec["preguntas"]; mc = [q for q in pregs if not q.get("desarrollo")]
    sim = spec.get("simulada")
    nivel = " · Nivel avanzado" if spec.get("exigencia") == "avanzada" else ""
    det = (f'{len(pregs)} preguntas · {spec["minutos"]} minutos · Código {esc(G.codigo(spec))}' if sim
           else f'{len(pregs)} preguntas{nivel} · Código {esc(G.codigo(spec))}')
    out = [G.header(spec, det)]
    instr = INSTR_S(len(mc), len(pregs) - len(mc), sum(q["puntos"] for q in pregs if q.get("desarrollo")), spec["minutos"]) if sim else INSTR_G
    out.append('<section class="instr"><b class="t">Instrucciones</b><ol>' + "".join(f"<li>{render_math(i)}</li>" for i in instr) + '</ol></section>')
    if spec.get("repaso"): out.append(f'<section class="repaso"><b class="t">Repaso</b>{render_math(spec["repaso"])}</section>')
    if spec.get("datos"): out.append(f'<section class="datos"><b class="t">Datos</b>{render_math(spec["datos"])}</section>')
    primera = True
    for k, q in enumerate(pregs, 1):
        fig = f'<div class="fig">{q["figura"]}</div>' if q.get("figura") else ""
        qr = f'<div class="qr">{G.qr_svg(targets[k])}<span>{labels[k]}</span></div>'
        if q.get("desarrollo"):
            if primera:
                out.append('<section class="pagebreak parte2"><h2>Parte II · Preguntas de desarrollo</h2><p>Responde en el espacio asignado mostrando todo tu desarrollo: '
                           'se evalúa el procedimiento, no solo el resultado. Al terminar, escanea el QR de cada pregunta para ver la solución completa y la pauta de corrección.</p></section>')
            out.append(f'<article class="q des{" primera" if primera else ""}"><div class="num">{k}.</div><div class="body"><div class="tag">{q["puntos"]} puntos</div>'
                       f'{render_math(q["enunciado"])}{fig}</div>{qr}</article>')
            primera = False
        else:
            out.append(f'<article class="q"><div class="num">{k}.</div><div class="body">{render_math(q["enunciado"])}{fig}{G.alts_html(q)}</div>{qr}</article>')
    out.append(f'<div class="fin">FIN DE LA {"PRUEBA" if sim else "GUÍA"}</div>')
    out.append(f'<section class="pagebreak">{G.mini(spec, " · Código " + esc(G.codigo(spec)))}<h2 class="sec">Hoja de respuestas</h2>'
               '<div class="campos"><span>Nombre</span><span>Curso</span><span>Fecha</span></div><div class="hoja">')
    for k in range(1, len(mc) + 1):
        out.append(f'<div><b>{k}</b>' + "".join(f'<i>{L}</i>' for L in LETRAS[:5]) + '</div>')
    out.append('</div></section>')
    rows = math.ceil(len(mc) / 4)
    out.append(f'<section class="pagebreak">{G.mini(spec)}<h2 class="solu">Solucionario</h2><table class="clav">')
    for r in range(rows):
        out.append('<tr style="height:13mm">' + "".join(
            f'<td>{c*rows+r+1} {mc[c*rows+r]["clave"]}</td>' if c*rows+r < len(mc) else '<td class="vacia"></td>' for c in range(4)) + '</tr>')
    out.append('</table><table class="desres"><thead><tr><th>N°</th><th>Desarrollo · respuesta final</th></tr></thead><tbody>')
    for k, q in enumerate(pregs, 1):
        if q.get("desarrollo"):
            out.append(f'<tr><td class="c">{k}</td><td>{render_math(q["respuesta"])}</td></tr>')
    out.append('</tbody></table></section>')
    cl = Counter(q["clave"] for q in mc)
    out.append(f'<section class="pagebreak">{G.mini(spec)}<h2 class="sec">Pauta de corrección</h2><div class="resumen">'
               f'<div><b>{len(pregs)}</b>{EJE}</div><div><b>{" · ".join(f"{L}{cl.get(L,0)}" for L in "ABCDE")}</b>Distribución de claves</div></div>'
               '<table class="pauta"><thead><tr><th>N°</th><th>Clave</th><th>Eje</th><th>Contenido evaluado</th><th>Habilidad</th>'
               + ('<th>Puntos</th>' if sim else '') + '<th>Origen</th></tr></thead><tbody>')
    for k, q in enumerate(pregs, 1):
        pts = (q["puntos"] if q.get("desarrollo") else 4)
        out.append(f'<tr><td class="c">{k}</td><td class="c">{q["clave"]}</td><td>{EJE}</td><td>{esc(q["contenido"])}</td>'
                   f'<td>{esc(q["habilidad"])}</td>' + (f'<td class="c">{pts}</td>' if sim else '') + '<td>Original</td></tr>')
    out.append('</tbody></table></section>')
    return G.doc_html(G.ENSAYO_CSS + G.SOL_CSS + CSS_Q, "".join(out))

def _revisar(spec):
    pregs = spec["preguntas"]; d = Counter(q["dificultad"] for q in pregs); hb = Counter(q["habilidad"] for q in pregs)
    n = len(pregs); av = []
    if not spec.get("simulada"):
        if spec.get("exigencia") == "avanzada":
            if d["facil"]: av.append(f"avanzada con {d['facil']} fáciles")
            if d["dificil"] + d["muy_dificil"] < math.ceil(.6 * n): av.append("faltan difíciles (≥60 %)")
            if d["muy_dificil"] < math.ceil(.2 * n): av.append("faltan muy difíciles (≥20 %)")
        else:
            if d["facil"] > math.floor(.15 * n): av.append("demasiadas fáciles (≤15 %)")
            if d["dificil"] + d["muy_dificil"] < math.ceil(.35 * n): av.append("faltan difíciles (≥35 %)")
    res = f"fácil {d['facil']} · media {d['media']} · difícil {d['dificil']} · muy difícil {d['muy_dificil']} | " + " · ".join(f"{k} {v}" for k, v in hb.items())
    return res, av

_MATH = _re2.compile(r"(\\\(.+?\\\)|\\\[.+?\\\])", _re2.S) if False else None
def _subs_txt(t):
    import re
    partes = re.split(r"(\\\(.+?\\\)|\\\[.+?\\\])", t, flags=re.S)
    for i in range(0, len(partes), 2):
        partes[i] = re.sub(r"(?<=[A-Za-zΔ\)])_([A-Za-záéíóúñ]+)", r"<sub>\1</sub>", partes[i])
    return "".join(partes)
def _subs(o):
    if isinstance(o, str): return _subs_txt(o)
    if isinstance(o, list): return [_subs(x) for x in o]
    if isinstance(o, dict): return {k: (_subs(v) if k not in ("figura", "dificultad", "habilidad", "eje", "origen", "codigo", "clave", "exigencia") else v) for k, v in o.items()}
    return o

def build(spec, outdir, cl):
    spec.update(_subs(spec))
    pregs = spec["preguntas"]
    asignar_claves(pregs, cl)
    spec.update(normalizar(spec))
    malos = chequear_tex(spec)
    if malos: raise SystemExit("LaTeX no soportado:\n" + "\n".join(sorted(set(malos))))
    spec.update({"prueba": "QIM", "tipo": "guia", "carpeta_soluciones": "https://tszenit.cl/soluciones"})
    pregs = spec["preguntas"]
    nd = sum(1 for q in pregs if q.get("desarrollo"))
    if spec.get("simulada"): assert len(pregs) == 12 and nd == 4 and sum(q["puntos"] for q in pregs if q.get("desarrollo")) == 68
    else: assert len(pregs) == 23 and nd == 3
    p = pathlib.Path(outdir); p.mkdir(parents=True, exist_ok=True)
    for q in pregs:
        if q.get("desarrollo"): q["alternativas"] = ["—"] * 5; q["clave"] = "A"
    sp = p / (spec["codigo"] + ".json"); sp.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    sys.argv = ["gen_paes.py", str(sp), str(p / spec["codigo"])]
    _rev, _bh = G.revisar_exigencia, G.build_ensayo_html
    def rev(spec_):
        for q in spec_["preguntas"]:
            if q.get("desarrollo"): q["alternativas"] = []; q["clave"] = "Des."
        return _revisar(spec_)
    G.revisar_exigencia, G.build_ensayo_html = rev, build_ensayo_html
    G.main()
    G.revisar_exigencia, G.build_ensayo_html = _rev, _bh
    for q in pregs:
        if q.get("desarrollo"): q["alternativas"] = []; q["clave"] = "Des."
    sp.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")

# ---------- química ----------
import re as _re2
MASAS = {"H": 1.008, "He": 4.003, "C": 12.01, "N": 14.01, "O": 16.00, "F": 19.00, "Na": 22.99, "Mg": 24.31, "Al": 26.98,
         "Si": 28.09, "P": 30.97, "S": 32.06, "Cl": 35.45, "K": 39.10, "Ca": 40.08, "Ti": 47.87, "Cr": 52.00, "Mn": 54.94,
         "Fe": 55.85, "Co": 58.93, "Ni": 58.69, "Cu": 63.55, "Zn": 65.38, "Br": 79.90, "Ag": 107.87, "I": 126.90,
         "Ba": 137.33, "Au": 196.97, "Pb": 207.2, "W": 183.84, "Mo": 95.95, "Pt": 195.08, "Po": 209.0}
NA = 6.022e23; R = 8.314; RL = 0.08206
def Mm(f):
    """Masa molar de una fórmula: 'Ca(NO3)2', 'CuSO4·5H2O'."""
    tot = 0.0
    for parte in f.split("·"):
        k = _re2.match(r"^(\d+)(.*)$", parte); mult = 1
        if k: mult, parte = int(k.group(1)), k.group(2)
        def _m(s):
            t, i = 0.0, 0
            while i < len(s):
                if s[i] == "(":
                    d, j = 1, i + 1
                    while d: d += (s[j] == "(") - (s[j] == ")"); j += 1
                    n = _re2.match(r"\d*", s[j:]).group(0); t += _m(s[i+1:j-1]) * (int(n) if n else 1); i = j + len(n)
                else:
                    e = _re2.match(r"[A-Z][a-z]?", s[i:]).group(0); i += len(e)
                    n = _re2.match(r"\d*", s[i:]).group(0); i += len(n); t += MASAS[e] * (int(n) if n else 1)
            return t
        tot += mult * _m(parte)
    return tot
_SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
def u(f):
    """Fórmula con subíndices Unicode: 'Ca(NO3)2' → 'Ca(NO₃)₂' (los coeficientes del hidrato quedan normales)."""
    return "·".join(_re2.sub(r"(?<=[A-Za-z\)])(\d+)", lambda m: m.group(1).translate(_SUB), p) for p in f.split("·"))
DATOS_MASAS = ("<p>Masas atómicas (g/mol): H 1,008 · C 12,01 · N 14,01 · O 16,00 · Na 22,99 · Mg 24,31 · Al 26,98 · S 32,06 · "
               "Cl 35,45 · K 39,10 · Ca 40,08 · Fe 55,85 · Cu 63,55. \\(N_A=6{,}022\\times10^{23}\\ \\mathrm{mol^{-1}}\\).</p>")
