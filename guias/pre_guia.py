"""Guías TS Zenit Universidad · Precálculo: 20 alternativas + 3 desarrollo (mismo formato que TSZ-PRE-*).
Uso desde un script de contenido:  from pre_guia import *;  ...;  build(spec_dict, "out")"""
import sys, json, math, pathlib, hashlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import gen_paes as G
from gen_paes import render_math, esc, LETRAS
from collections import Counter

G.PRUEBAS["PRE"] = "TS Zenit Universidad · Precálculo"
_area0 = G.area
G.area = lambda p: "MAT1" if str(p).upper() == "PRE" else _area0(p)
EJE = "Precálculo"

# ---------- helpers de contenido ----------
def Q(enun, alts, contenido, habilidad, dificultad, pasos, dis, idea, figura=None):
    """alts[0] es la correcta; dis = explicaciones de alts[1], alts[2], alts[3] (mismo orden)."""
    assert len(alts) == 4 and len(dis) == 3
    q = {"enunciado": enun, "_alts": alts, "_dis": dis, "eje": EJE, "contenido": contenido, "habilidad": habilidad,
         "dificultad": dificultad, "origen": "Original",
         "solucion": {"pasos": [{"t": t, "d": d} for t, d in pasos], "idea": idea}}
    if figura: q["figura"] = figura
    return q

def D(enun, respuesta, contenido, habilidad, dificultad, pasos, idea, puntos=6):
    return {"enunciado": enun, "desarrollo": True, "puntos": puntos, "alternativas": [], "clave": "Des.",
            "respuesta": respuesta, "eje": EJE, "contenido": contenido, "habilidad": habilidad, "dificultad": dificultad,
            "origen": "Original", "solucion": {"pasos": [{"t": t, "d": d} for t, d in pasos], "idea": idea}}

def asignar_claves(pregs, claves):
    mc = [q for q in pregs if not q.get("desarrollo")]
    assert len(mc) == len(claves), (len(mc), len(claves))
    c = Counter(claves)
    assert all(4 <= c[L] <= 6 for L in "ABCD"), c
    assert all(not (claves[i] == claves[i+1] == claves[i+2] == claves[i+3]) for i in range(len(claves)-3))
    for q, L in zip(mc, claves):
        pos = "ABCD".index(L)
        alts, dis = q.pop("_alts"), q.pop("_dis")
        otras = list(zip(alts[1:], dis))
        orden = otras[:pos] + [(alts[0], None)] + otras[pos:]
        q["alternativas"] = [a for a, _ in orden]
        q["clave"] = L
        q["solucion"]["distractores"] = {LETRAS[i]: d for i, (_, d) in enumerate(orden) if d is not None}

# ---------- parches de render ----------
INSTR = [
    "Esta guía tiene dos partes. Parte I: 20 preguntas de alternativas. Cada pregunta tiene 4 opciones, señaladas con las letras A, B, C y D, de las cuales solo una es correcta.",
    "Marca tus respuestas en la hoja de respuestas al final del cuadernillo.",
    "Las figuras que aparecen son solo indicativas.",
    "Parte II: 3 preguntas de desarrollo (desde la 21). Responde en el espacio asignado mostrando tu procedimiento; no van en la hoja de respuestas.",
    "Preguntas originales, alineadas con los contenidos de Precálculo de J. Stewart (Matemáticas para el cálculo).",
    "Cada pregunta tiene un código QR: escanéalo después de responder para ver su solución paso a paso.",
]
CSS_EXTRA = """
.q.des { border-bottom: none; break-before: page; min-height: 190mm; align-content: start; }
.q.des .tag { margin-top: 0; }
.q.des .body ol.partes { margin: 1.5mm 0 0; padding-left: 0; list-style: none; display: grid; gap: 1.2mm; }
table.desres { width: 100%; border-collapse: collapse; margin-top: 7mm; font-size: 8.6pt; }
table.desres th { background: #1B1F5E; color: #fff; text-align: left; padding: 1.4mm 2mm; font: 600 8pt Poppins, 'DejaVu Sans', sans-serif; }
table.desres td { border-bottom: .5pt solid #bbb; padding: 1.6mm 2mm; vertical-align: top; }
table.desres td.c { text-align: center; font-weight: 700; width: 9mm; }
.resfinal { margin: 4mm 0 1mm; font: 700 10.5pt Poppins, 'DejaVu Sans', sans-serif; color: #1F7A4D; }
.resfinal + div { margin-bottom: 2mm; }
"""

def solutions_sections(spec):
    out = []
    for k, q in enumerate(spec["preguntas"], 1):
        s = q.get("solucion", {})
        fig = f'<div class="fig">{q["figura"]}</div>' if q.get("figura") else ""
        pasos = "".join(f'<li><div><strong>{render_math(p.get("t",""))}</strong><div>{render_math(p.get("d",""))}</div></div></li>' for p in s.get("pasos", []))
        etiqueta = esc(q.get("eje")) + (" · " + esc(q.get("contenido")) if q.get("contenido") else "")
        if q.get("desarrollo"):
            cuerpo = (f'<div class="enun">{render_math(q["enunciado"])}{fig}</div>'
                      f'<p class="resfinal">Respuesta final</p><div>{render_math(q["respuesta"])}</div>'
                      f'<h3>Desarrollo paso a paso</h3><ol class="pasos">{pasos}</ol>')
        else:
            dis = "".join(f'<li><b>{L})</b><span>{render_math(t)}</span></li>' for L, t in sorted(s.get("distractores", {}).items()))
            cuerpo = (f'<div class="enun">{render_math(q["enunciado"])}{fig}</div>{G.alts_html(q, True)}'
                      f'<p class="clave">Respuesta correcta: {q["clave"]}</p><h3>Paso a paso</h3><ol class="pasos">{pasos}</ol>'
                      + (f'<h3>¿Por qué no las otras?</h3><ul class="dis">{dis}</ul>' if dis else ""))
        out.append(f'<section class="sol" id="p{k}">{G.mini(spec, " · Solucionario")}<div class="solh"><h2>Solución de la pregunta {k}</h2><span>{etiqueta}</span></div>'
                   + cuerpo + (f'<div class="idea"><strong>Idea clave.</strong> {render_math(s["idea"])}</div>' if s.get("idea") else "") + '</section>')
    return "".join(out)
G.solutions_sections = solutions_sections
G.build_solutions_html = lambda spec: G.doc_html(G.SOL_CSS + CSS_EXTRA, solutions_sections(spec))

def build_ensayo_html(spec, targets, labels):
    pregs = spec["preguntas"]; mc = [q for q in pregs if not q.get("desarrollo")]
    nivel = " · Nivel avanzado" if G.nivel_exigencia(spec) == "avanzada" else ""
    out = [G.header(spec, f'{len(pregs)} preguntas{nivel} · Código {esc(G.codigo(spec))}')]
    out.append('<section class="instr"><b class="t">Instrucciones</b><ol>' + "".join(f"<li>{render_math(i)}</li>" for i in INSTR) + '</ol></section>')
    out.append(f'<section class="repaso"><b class="t">Repaso</b>{render_math(spec["repaso"])}</section>')
    for k, q in enumerate(pregs, 1):
        fig = f'<div class="fig">{q["figura"]}</div>' if q.get("figura") else ""
        qr = f'<div class="qr">{G.qr_svg(targets[k])}<span>{labels[k]}</span></div>'
        if q.get("desarrollo"):
            out.append(f'<article class="q des"><div class="num">{k}.</div><div class="body"><div class="tag">{q["puntos"]} puntos</div>'
                       f'{render_math(q["enunciado"])}{fig}</div>{qr}</article>')
        else:
            out.append(f'<article class="q"><div class="num">{k}.</div><div class="body">{render_math(q["enunciado"])}{fig}{G.alts_html(q)}</div>{qr}</article>')
    out.append('<div class="fin">FIN DE LA GUÍA</div>')
    out.append(f'<section class="pagebreak">{G.mini(spec, " · Código " + esc(G.codigo(spec)))}<h2 class="sec">Hoja de respuestas</h2>'
               '<div class="campos"><span>Nombre</span><span>Curso</span><span>Fecha</span></div><div class="hoja">')
    for k in range(1, len(mc) + 1):
        out.append(f'<div><b>{k}</b>' + "".join(f'<i>{L}</i>' for L in LETRAS[:4]) + '</div>')
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
    claves = Counter(q["clave"] for q in mc)
    out.append(f'<section class="pagebreak">{G.mini(spec)}<h2 class="sec">Pauta de corrección</h2><div class="resumen">'
               f'<div><b>{len(pregs)}</b>Precálculo</div><div><b>{" · ".join(f"{L}{claves.get(L,0)}" for L in "ABCD")}</b>Distribución de claves</div></div>'
               '<table class="pauta"><thead><tr><th>N°</th><th>Clave</th><th>Eje</th><th>Contenido evaluado</th><th>Habilidad</th><th>Dificultad</th><th>Origen</th></tr></thead><tbody>')
    ND = {"facil": "Fácil", "media": "Media", "dificil": "Difícil", "muy_dificil": "Muy difícil"}
    for k, q in enumerate(pregs, 1):
        out.append(f'<tr><td class="c">{k}</td><td class="c">{q["clave"]}</td><td>{EJE}</td><td>{esc(q["contenido"])}</td>'
                   f'<td>{esc(q["habilidad"])}</td><td>{ND[q["dificultad"]]}</td><td>Original</td></tr>')
    out.append('</tbody></table></section>')
    return G.doc_html(G.ENSAYO_CSS + G.SOL_CSS + CSS_EXTRA, "".join(out))
G.build_ensayo_html = build_ensayo_html

def build(spec, outdir, claves):
    asignar_claves(spec["preguntas"], claves)
    spec.update(normalizar(spec))
    malos = chequear_tex(spec)
    if malos: raise SystemExit("LaTeX no soportado:\n" + "\n".join(sorted(set(malos))))
    spec.update({"prueba": "PRE", "tipo": "guia", "carpeta_soluciones": "https://tszenit.cl/soluciones"})
    n = len(spec["preguntas"]); assert n == 23 and sum(1 for q in spec["preguntas"] if q.get("desarrollo")) == 3
    p = pathlib.Path(outdir); p.mkdir(parents=True, exist_ok=True)
    sp = p / (spec["codigo"] + ".json"); sp.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    sys.argv = ["gen_paes.py", str(sp), str(p / spec["codigo"])]
    for q in spec["preguntas"]:   # main() exige 4/5 alternativas: los desarrollo pasan la validación con relleno
        if q.get("desarrollo"): q["alternativas"] = ["—"] * 4; q["clave"] = "A"
    sp.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    _rev = G.revisar_exigencia
    def rev(spec_):   # se llama justo después de la validación: aquí se restauran los desarrollo
        for q in spec_["preguntas"]:
            if q.get("desarrollo"): q["alternativas"] = []; q["clave"] = "Des."
        return _rev(spec_)
    G.revisar_exigencia = rev
    G.main()
    G.revisar_exigencia = _rev

# ---------- normalización de LaTeX para mathtext ----------
import re as _re
def _arg(s, i):
    while i < len(s) and s[i] == " ": i += 1
    if i >= len(s): return "", i
    if s[i] == "{":
        d, j = 0, i
        while j < len(s):
            d += (s[j] == "{") - (s[j] == "}")
            if d == 0: return "{" + _fix_cmds(s[i+1:j]) + "}", j+1
            j += 1
        return s[i:], len(s)
    if s[i] == "\\":
        m = _re.match(r"\\[A-Za-z]+", s[i:]); return "{" + m.group(0) + "}", i + len(m.group(0))
    return "{" + s[i] + "}", i + 1
def _cmdargs(s, cmd, n):
    out, i = "", 0
    pat = "\\" + cmd
    while True:
        j = s.find(pat, i)
        if j < 0: return out + s[i:]
        k = j + len(pat)
        if k < len(s) and s[k].isalpha(): out += s[i:k]; i = k; continue
        out += s[i:j] + pat; i = k
        if cmd == "sqrt" and i < len(s) and s[i] == "[":
            e = s.index("]", i); out += s[i:e+1]; i = e + 1
        for _ in range(n):
            a, i = _arg(s, i); out += a
def _fix_cmds(t):
    return _cmdargs(_cmdargs(_cmdargs(t, "frac", 2), "binom", 2), "sqrt", 1)
def tex_norm(t):
    t = t.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    t = _re.sub(r"\\[td]frac", r"\\frac", t)
    t = t.replace("°", r"^{\circ}")
    t = _cmdargs(t, "frac", 2); t = _cmdargs(t, "binom", 2); t = _cmdargs(t, "sqrt", 1)
    t = _re.sub(r"\\mathbb\s*([A-Za-z])", r"\\mathbb{\1}", t)
    t = _re.sub(r"\\iff(?![A-Za-z])", r"\\Leftrightarrow ", t)
    t = _re.sub(r"\\ge(?![A-Za-z])", r"\\geq ", t); t = _re.sub(r"\\le(?![A-Za-z])", r"\\leq ", t)
    t = _re.sub(r"\\ne(?![A-Za-z])", r"\\neq ", t)
    t = _re.sub(r"\\bmod(?![A-Za-z])", r"\\ \\mathrm{mod}\\ ", t)
    t = _re.sub(r"\\binom\{([^{}]*)\}\{([^{}]*)\}", r"\\left(\\genfrac{}{}{0}{}{\1}{\2}\\right)", t)
    return t
def _norm_html(s):
    s = _re.sub(r"\\\[(.+?)\\\]", lambda m: "\\[" + tex_norm(m.group(1)) + "\\]", s, flags=_re.S)
    return _re.sub(r"\\\((.+?)\\\)", lambda m: "\\(" + tex_norm(m.group(1)) + "\\)", s, flags=_re.S)
def normalizar(o):
    if isinstance(o, str): return _norm_html(o)
    if isinstance(o, list): return [normalizar(x) for x in o]
    if isinstance(o, dict): return {k: normalizar(v) for k, v in o.items()}
    return o
def chequear_tex(spec):
    malos = []
    def walk(o):
        if isinstance(o, str):
            for m in _re.finditer(r"\\\((.+?)\\\)|\\\[(.+?)\\\]", o, _re.S):
                t = m.group(1) or m.group(2)
                try: G.TextPath((0, 0), f"${t}$", size=10, prop=G._FP)
                except Exception as e: malos.append(t)
        elif isinstance(o, list): [walk(x) for x in o]
        elif isinstance(o, dict): [walk(v) for v in o.values()]
    walk(spec); return malos

_vq = G.verify_qr
def _verify_qr(targets):
    r = _vq(targets)
    if "FALLAN" not in r: return r
    import cv2, numpy as np
    det, bad = cv2.QRCodeDetectorAruco(), []
    for k, tg in targets.items():
        m = np.array(G.qr_matrix(tg), dtype=np.uint8)
        img = cv2.resize(np.pad((1 - m) * 255, 4, constant_values=255).astype(np.uint8), None, fx=10, fy=10, interpolation=cv2.INTER_NEAREST)
        if det.detectAndDecode(img)[0] != tg: bad.append(k)
    return f"QR verificados (dos lectores): {len(targets)-len(bad)}/{len(targets)}" + (f" | FALLAN: {bad}" if bad else "")
G.verify_qr = _verify_qr
