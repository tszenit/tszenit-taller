#!/usr/bin/env python3
"""TS Zenit — análisis de resultados, diagnóstico y control de calidad del refuerzo.

Subcomandos (todos escriben JSON legible y un resumen en pantalla):
  analizar   resultados.json  salida/            -> salida/analisis.json   (estadística con denominadores)
  excluidas  carpeta_pdfs  "1,3,7"  salida.json  -> registro de preguntas falladas extraído de los PDF por pregunta
  validar    diagnostico.json  refuerzo_spec.json -> trazabilidad + originalidad + coherencia (sale con código 1 si falla)
  informe    diagnostico.json  salida/            -> Informe PDF docente, panel docente HTML y tutor HTML por alumno
  comparar   analisis_v1.json  analisis_v2.json  [mapa.json] -> cambios entre versiones de una guía

Requiere gen_paes.py en la misma carpeta (reutiliza logo, estilos, LaTeX y render a PDF).
"""
SAL_INF = __import__('os').environ.get('TSZ_SAL_INF') or __import__('secrets').token_hex(16)  # sal secreta de los enlaces de informes
import difflib, html, json, math, re, sys, unicodedata, pathlib, hashlib
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gen_paes as G

LETRAS = "ABCDE"
VACIAS = {"", "-", "—", "o", "O", None}

def leer(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))

def escribir(p, obj):
    pathlib.Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")

def pct(a, b):
    return None if not b else round(100.0 * a / b, 1)

def fmt_pct(x):
    return "—" if x is None else f"{x:.1f} %".replace(".", ",")

# ======================================================================
# 1) ANALIZAR
# ======================================================================
def normaliza_resp(r):
    if isinstance(r, str):
        r = r.strip().upper()
    if r in VACIAS:
        return "OMIT"
    if r in ("?", "DUDOSA"):
        return "DUDOSA"
    if r in ("*", "MULTIPLE", "MÚLTIPLE") or (isinstance(r, str) and len(r) > 1):
        return "MULTIPLE"
    return r

def analizar(res):
    P = res["preguntas"]; E = res.get("estudiantes", [])
    nP, nE = len(P), len(E)
    avisos = []
    con_clave = [q for q in P if q.get("clave")]
    if not con_clave:
        avisos.append("SIN PAUTA: no hay respuestas correctas; solo se informa la distribución de respuestas. No se puede calcular logro ni diagnosticar errores.")
    elif len(con_clave) < nP:
        avisos.append(f"PAUTA INCOMPLETA: {nP-len(con_clave)} de {nP} preguntas sin clave; quedan fuera del logro.")
    if not res.get("pauta_oficial", True):
        avisos.append("La pauta no es oficial (inferida o reconstruida): toda conclusión de logro es provisional.")
    if nE == 0:
        avisos.append("No hay respuestas de estudiantes.")
    elif nE == 1:
        avisos.append("Resultado individual (N = 1): no se calculan índices de dificultad ni discriminación de las preguntas.")
    elif nE < 5:
        avisos.append(f"Muestra muy pequeña (N = {nE}): las conclusiones sobre el grupo y sobre la calidad de las preguntas son inestables.")
    elif nE < 10:
        avisos.append(f"Muestra pequeña (N = {nE}): la discriminación se calcula solo como orientación.")

    # --- respuestas normalizadas
    R = []
    for e in E:
        rs = e["respuestas"]
        if isinstance(rs, str):
            rs = list(rs)
        rs = [normaliza_resp(x) for x in rs]
        if len(rs) != nP:
            avisos.append(f"{e.get('id')}: tiene {len(rs)} respuestas y la guía tiene {nP} preguntas; se completan como omitidas o se recortan.")
            rs = (rs + ["OMIT"] * nP)[:nP]
        for i, x in enumerate(rs):
            if x not in ("OMIT", "DUDOSA", "MULTIPLE") and x not in LETRAS[:P[i].get("n_alt", 4)]:
                avisos.append(f"{e.get('id')}, pregunta {P[i]['n']}: respuesta '{x}' no existe en esa pregunta; se trata como inválida.")
                rs[i] = "INVALIDA"
        R.append(rs)

    def estado(i, x):
        clave = P[i].get("clave")
        if x == "OMIT": return "omitida"
        if x in ("DUDOSA", "MULTIPLE", "INVALIDA"): return "no_valida"
        if not clave: return "sin_clave"
        return "correcta" if x == clave else "incorrecta"

    # --- por estudiante
    por_est = []
    for e, rs in zip(E, R):
        det = []
        c = inc = om = nv = 0
        for i, x in enumerate(rs):
            st = estado(i, x)
            c += st == "correcta"; inc += st == "incorrecta"; om += st == "omitida"; nv += st == "no_valida"
            det.append({"n": P[i]["n"], "marcada": None if x in ("OMIT",) else x, "clave": P[i].get("clave"), "estado": st})
        base = len(con_clave)
        ejes = defaultdict(lambda: [0, 0])
        habs = defaultdict(lambda: [0, 0])
        for i, d in enumerate(det):
            if not P[i].get("clave"): continue
            for dic, key in ((ejes, P[i].get("eje", "—")), (habs, P[i].get("habilidad", "—"))):
                dic[key][1] += 1
                dic[key][0] += d["estado"] == "correcta"
        por_est.append({
            "id": e.get("id"), "nombre": e.get("nombre"),
            "correctas": c, "incorrectas": inc, "omitidas": om, "no_validas": nv,
            "base": base, "logro_pct": pct(c, base),
            "denominador": f"{c} correctas de {base} preguntas con clave",
            "por_eje": {k: {"correctas": v[0], "total": v[1], "pct": pct(*v)} for k, v in ejes.items()},
            "por_habilidad": {k: {"correctas": v[0], "total": v[1], "pct": pct(*v)} for k, v in habs.items()},
            "detalle": det,
        })

    # --- por pregunta
    tot = [pe["correctas"] for pe in por_est]
    por_preg = []
    for i, q in enumerate(P):
        col = [rs[i] for rs in R]
        dist = Counter(x for x in col)
        letras = LETRAS[:q.get("n_alt", 4)]
        clave = q.get("clave")
        item = {"n": q["n"], "clave": clave, "eje": q.get("eje"), "contenido": q.get("contenido"),
                "habilidad": q.get("habilidad"), "dificultad_estimada": q.get("dificultad"), "tipo": q.get("tipo"),
                "N": nE, "distribucion": {L: dist.get(L, 0) for L in letras},
                "omitidas": dist.get("OMIT", 0), "no_validas": dist.get("DUDOSA", 0) + dist.get("MULTIPLE", 0) + dist.get("INVALIDA", 0),
                "flags": []}
        if clave and nE:
            corr = dist.get(clave, 0)
            item["correctas"] = corr
            item["p"] = round(corr / nE, 3)
            item["pct_estudiantes_correctos"] = pct(corr, nE)
            item["denominador"] = f"{corr} de {nE} estudiantes respondieron correctamente"
            dis = {L: n for L, n in item["distribucion"].items() if L != clave}
            if dis and max(dis.values()) > 0:
                top = max(dis, key=dis.get)
                item["distractor_mas_elegido"] = {"letra": top, "n": dis[top], "pct": pct(dis[top], nE)}
            if nE >= 5:
                if item["p"] < 0.2: item["flags"].append("muy_dificil")
                if item["p"] > 0.9: item["flags"].append("muy_facil")
                if item["p"] < 1.0 / len(letras) and nE >= 8: item["flags"].append("bajo_el_azar")
            if nE >= 5:
                # grupos alto/bajo según puntaje total sin el ítem
                resto = [t - (1 if R[j][i] == clave else 0) for j, t in enumerate(tot)]
                orden = sorted(range(nE), key=lambda j: resto[j])
                g = max(1, round(nE * (0.27 if nE >= 10 else 0.5)))
                bajo, alto = orden[:g], orden[-g:]
                pa = sum(R[j][i] == clave for j in alto) / g
                pb = sum(R[j][i] == clave for j in bajo) / g
                item["discriminacion_D"] = round(pa - pb, 2)
                item["grupos"] = f"alto y bajo de {g} estudiantes cada uno (por puntaje sin esta pregunta)"
                alto_dist = Counter(R[j][i] for j in alto)
                rival = [L for L in letras if L != clave and alto_dist.get(L, 0) > alto_dist.get(clave, 0)]
                if rival:
                    item["flags"].append("posible_clave_erronea_o_ambigua")
                    item["rival_en_grupo_alto"] = rival
                if nE >= 10:
                    if item["discriminacion_D"] < 0.1: item["flags"].append("discrimina_poco")
                    if item["discriminacion_D"] < 0: item["flags"].append("discriminacion_negativa")
                    muertos = [L for L in letras if L != clave and item["distribucion"][L] == 0]
                    if muertos: item["distractores_sin_eleccion"] = muertos
                # punto biserial
                xs = [1 if R[j][i] == clave else 0 for j in range(nE)]
                if 0 < sum(xs) < nE:
                    m1 = sum(r for r, x in zip(resto, xs) if x) / sum(xs)
                    m0 = sum(r for r, x in zip(resto, xs) if not x) / (nE - sum(xs))
                    mu = sum(resto) / nE
                    sd = math.sqrt(sum((r - mu) ** 2 for r in resto) / nE)
                    if sd > 0:
                        pp = sum(xs) / nE
                        item["r_pbis"] = round((m1 - m0) / sd * math.sqrt(pp * (1 - pp)), 2)
        if item["omitidas"] and nE and item["omitidas"] / nE >= 0.3:
            item["flags"].append("muchas_omisiones")
        por_preg.append(item)

    # --- agregados grupales (denominador = estudiantes × preguntas de la categoría)
    def agregado(campo):
        out = {}
        grupos = defaultdict(list)
        for i, q in enumerate(P):
            if q.get("clave") and q.get(campo):
                grupos[q[campo]].append(i)
        for k, idx in grupos.items():
            corr = sum(R[j][i] == P[i]["clave"] for i in idx for j in range(nE))
            den = len(idx) * nE
            out[k] = {"preguntas": [P[i]["n"] for i in idx], "correctas": corr, "respuestas": den, "pct": pct(corr, den),
                      "denominador": f"{corr} correctas de {den} respuestas ({len(idx)} {'pregunta' if len(idx) == 1 else 'preguntas'} × {nE} {'estudiante' if nE == 1 else 'estudiantes'})"}
        return out

    grupo = None
    if nE:
        tot_c = sum(pe["correctas"] for pe in por_est); tot_i = sum(pe["incorrectas"] for pe in por_est)
        tot_o = sum(pe["omitidas"] for pe in por_est); tot_nv = sum(pe["no_validas"] for pe in por_est); den = len(con_clave) * nE
        logros = [pe["logro_pct"] for pe in por_est if pe["logro_pct"] is not None]
        grupo = {"respuestas_con_clave": den, "correctas": tot_c, "incorrectas": tot_i, "omitidas": tot_o,
                 "no_validas": tot_nv, "pct_correctas": pct(tot_c, den), "pct_incorrectas": pct(tot_i, den), "pct_omitidas": pct(tot_o, den), "pct_no_validas": pct(tot_nv, den),
                 "denominador": f"porcentajes sobre {den} respuestas ({len(con_clave)} preguntas con clave × {nE} {'estudiante' if nE == 1 else 'estudiantes'})",
                 "logro_promedio_pct": round(sum(logros) / len(logros), 1) if logros else None,
                 "logro_min_pct": min(logros) if logros else None, "logro_max_pct": max(logros) if logros else None,
                 "por_eje": agregado("eje"), "por_habilidad": agregado("habilidad"), "por_contenido": agregado("contenido"),
                 "por_dificultad": agregado("dificultad"), "por_tipo": agregado("tipo")}
    return {"codigo": res.get("codigo"), "titulo": res.get("titulo"), "prueba": res.get("prueba"),
            "n_preguntas": nP, "n_con_clave": len(con_clave), "n_estudiantes": nE,
            "pauta_oficial": res.get("pauta_oficial", True), "avisos": avisos,
            "grupo": grupo, "por_estudiante": por_est, "por_pregunta": por_preg}

def imprimir_analisis(a):
    print(f"\n# Análisis {a.get('codigo')} · {a['n_preguntas']} preguntas ({a['n_con_clave']} con clave) · {a['n_estudiantes']} {'estudiante' if a['n_estudiantes'] == 1 else 'estudiantes'}")
    for w in a["avisos"]:
        print("AVISO:", w)
    if a["grupo"]:
        g = a["grupo"]
        print(f"\nGrupo: {fmt_pct(g['pct_correctas'])} correctas · {fmt_pct(g['pct_incorrectas'])} incorrectas · {fmt_pct(g['pct_omitidas'])} omitidas"
              + (f" · {fmt_pct(g['pct_no_validas'])} no válidas (dudosas, múltiples o inexistentes)" if g.get('no_validas') else "") + f" — {g['denominador']}")
        print(f"Logro por estudiante: promedio {fmt_pct(g['logro_promedio_pct'])}, mín {fmt_pct(g['logro_min_pct'])}, máx {fmt_pct(g['logro_max_pct'])}")
        for nombre in ("por_eje", "por_habilidad"):
            if g[nombre]:
                print(f"\n{nombre.replace('_', ' ').capitalize()}:")
                for k, v in sorted(g[nombre].items(), key=lambda kv: kv[1]["pct"] or 0):
                    print(f"  {fmt_pct(v['pct']):>8}  {k}  ({v['denominador']})")
    print("\n| N° | Clave | % correctos | Distribución | Distractor + elegido | D | r_pb | Alertas |")
    print("|---|---|---|---|---|---|---|---|")
    for q in a["por_pregunta"]:
        dist = " ".join(f"{L}:{n}" for L, n in q["distribucion"].items()) + (f" om:{q['omitidas']}" if q["omitidas"] else "") + (f" nv:{q['no_validas']}" if q["no_validas"] else "")
        dm = q.get("distractor_mas_elegido")
        print(f"| {q['n']} | {q.get('clave') or '—'} | {fmt_pct(q.get('pct_estudiantes_correctos'))} | {dist} | "
              f"{(dm['letra'] + ' (' + str(dm['n']) + ')') if dm else '—'} | {q.get('discriminacion_D', '—')} | {q.get('r_pbis', '—')} | {', '.join(q['flags']) or '—'} |")
    print("\n| Estudiante | Correctas | Incorrectas | Omitidas | No válidas | Logro |")
    print("|---|---|---|---|---|---|")
    for e in a["por_estudiante"]:
        if not e["base"]:
            print(f"| {e['nombre'] or e['id']} | — | — | {e['omitidas']} | {e['no_validas']} | sin pauta |"); continue
        print(f"| {e['nombre'] or e['id']} | {e['correctas']} | {e['incorrectas']} | {e['omitidas']} | {e['no_validas']} | {fmt_pct(e['logro_pct'])} ({e['denominador']}) |")

# ======================================================================
# 2) REGISTRO DE EXCLUSIÓN (desde los PDF por pregunta publicados)
# ======================================================================
def excluidas_desde_pdfs(carpeta, numeros):
    import pypdfium2 as pdfium
    carpeta = pathlib.Path(carpeta)
    out = []
    for n in numeros:
        files = sorted(carpeta.glob(f"p{n:02d}-*.pdf")) or sorted(carpeta.glob(f"p{n:02d}.pdf"))
        if not files:
            out.append({"n": n, "texto": None, "aviso": "No se encontró el PDF de esta pregunta: la comprobación de duplicados queda incompleta."})
            continue
        from pypdf import PdfReader
        meta = (PdfReader(str(files[0])).metadata or {}).get("/TSZPregunta")
        if meta:
            q = json.loads(meta)
            out.append({"n": n, "texto": q.get("enunciado", "") + " " + " ".join(q.get("alternativas", [])), "clave": q.get("clave"),
                        "habilidad": q.get("habilidad"), "contenido": q.get("contenido"), "eje": q.get("eje"),
                        "distractores": q.get("solucion", {}).get("distractores"), "fuente": files[0].name, "origen_texto": "ficha"})
            continue
        doc = pdfium.PdfDocument(str(files[0]))
        txt = "\n".join(doc[i].get_textpage().get_text_range() for i in range(len(doc)))
        m = re.search(r"Solución\s+de\s+la\s+pregunta\s+\d+(.*?)Respuesta\s+correcta:\s*([A-E])", txt, re.S)
        cuerpo = m.group(1) if m else txt
        out.append({"n": n, "texto": cuerpo.strip(), "clave": m.group(2) if m else None, "fuente": files[0].name, "origen_texto": "pdf",
                    "aviso": "Texto extraído del PDF: las fórmulas no se recuperan, la comparación es menos precisa."})
    return out

# ======================================================================
# 3) VALIDAR: trazabilidad, originalidad y coherencia del refuerzo
# ======================================================================
def _sin_tildes(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def normaliza_texto(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = html.unescape(s)
    s = re.sub(r"\\(dfrac|frac|sqrt|cdot|left|right|text|mathrm|quad|,|;)", " ", s)
    s = _sin_tildes(s.lower())
    s = re.sub(r"\d+([.,]\d+)?", " # ", s)
    s = re.sub(r"[^a-z#ñ ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

STOP = set("de la el los las un una y o a en que se por con del al es su para como cual cuales siguiente siguientes lo".split())

def tokens(s):
    return [t for t in normaliza_texto(s).split() if t not in STOP and (len(t) > 2 or t == "#")]

def similitud(a, b):
    na, nb = normaliza_texto(a), normaliza_texto(b)
    ta, tb = set(tokens(a)), set(tokens(b))
    jac = len(ta & tb) / len(ta | tb) if ta | tb else 0.0
    ratio = difflib.SequenceMatcher(None, na, nb).ratio()
    return {"jaccard": round(jac, 2), "secuencia": round(ratio, 2), "esqueleto_identico": bool(na) and na == nb}

def texto_pregunta(q):
    return (q.get("enunciado", "") or "") + " " + " ".join(q.get("alternativas", []))

def veredicto(s):
    if s["esqueleto_identico"] or s["secuencia"] >= 0.80 or s["jaccard"] >= 0.70:
        return "FALLA"
    if s["secuencia"] >= 0.60 or s["jaccard"] >= 0.50:
        return "REVISAR"
    return "OK"

def validar(diag, ref):
    pregs = ref.get("preguntas") or [q for b in ref.get("bloques", []) if b.get("tipo") == "preguntas" for q in b["preguntas"]]
    fallas, revisar, notas = [], [], []
    a = diag.get("analisis")
    if a is not None and not isinstance(a, dict):
        try:
            a = leer(a)
        except Exception:
            a = None
            notas.append("No se pudo leer analisis.json: no se comprobó la cantidad de preguntas del original, su dificultad ni la cobertura del tutor.")
    excl = diag.get("excluidas", [])
    if not excl:
        notas.append("No hay registro de preguntas excluidas: no se puede comprobar la ausencia de copias.")
    if any(not e.get("texto") for e in excl):
        notas.append("Algunas preguntas excluidas no tienen texto: la comprobación de duplicados no es exhaustiva.")
    orig = []
    for k, q in enumerate(pregs, 1):
        t = texto_pregunta(q)
        for e in excl:
            if not e.get("texto"): continue
            s = similitud(t, e["texto"]); v = veredicto(s)
            if v != "OK":
                (fallas if v == "FALLA" else revisar).append(f"Ejercicio {k} vs pregunta original {e['n']}: {v} {s}")
            orig.append({"ejercicio": k, "original": e["n"], **s, "veredicto": v})
        for j, q2 in enumerate(pregs[:k - 1], 1):
            s = similitud(t, texto_pregunta(q2))
            if veredicto(s) == "FALLA":
                revisar.append(f"Ejercicios {j} y {k} son casi iguales entre sí {s}")
    # ejercicios nuevos del tutor (práctica y transferencia) frente a las preguntas falladas
    for al in diag.get("tutor_alumnos", []):
        for t in al.get("errores", []):
            for rol in ("practica", "transferencia"):
                ej = t.get("tutor", {}).get(rol)
                if not ej: 
                    fallas.append(f"Tutor {al['id']}, pregunta {t['n']}: falta el ejercicio de {rol}.")
                    continue
                if ej.get("clave") not in LETRAS[:len(ej.get("alternativas", []))]:
                    fallas.append(f"Tutor {al['id']}, pregunta {t['n']}: el ejercicio de {rol} tiene clave inválida.")
                for e in excl:
                    if not e.get("texto"): continue
                    s = similitud(texto_pregunta(ej), e["texto"]); v = veredicto(s)
                    if v != "OK":
                        (fallas if v == "FALLA" else revisar).append(f"Tutor {al['id']}, {rol} de la pregunta {t['n']} vs original {e['n']}: {v} {s}")
            pasos = t.get("tutor", {}).get("pasos", [])
            for i, p in enumerate(pasos, 1):
                if not (0 <= p.get("correcta", -1) < len(p.get("opciones", []))):
                    fallas.append(f"Tutor {al['id']}, pregunta {t['n']}, paso {i}: índice 'correcta' fuera de rango.")
            c = t.get("tutor", {}).get("comprobacion", {})
            if c and not (0 <= c.get("correcta", -1) < len(c.get("opciones", []))):
                fallas.append(f"Tutor {al['id']}, pregunta {t['n']}: comprobación con 'correcta' fuera de rango.")
            refl = t.get("tutor", {}).get("reflexion", {})
            hips = t.get("tutor", {}).get("hipotesis", {})
            for o in refl.get("opciones", []):
                if o.get("lleva_a") not in hips:
                    fallas.append(f"Tutor {al['id']}, pregunta {t['n']}: la opción de reflexión '{o.get('texto')}' lleva a una hipótesis inexistente.")
    # ejemplos resueltos que anticipan ejercicios
    for b in ref.get("bloques", []):
        if b.get("tipo") == "ejemplo":
            for k, q in enumerate(pregs, 1):
                s = similitud(b.get("enunciado", ""), q.get("enunciado", ""))
                if s["secuencia"] >= 0.75 or s["esqueleto_identico"]:
                    revisar.append(f"El ejemplo resuelto '{b.get('titulo')}' anticipa el ejercicio {k} {s}")
    # trazabilidad
    debs = {d["id"]: d for d in diag.get("mapa_debilidades", [])}
    usados = Counter()
    for k, q in enumerate(pregs, 1):
        d = q.get("debilidad")
        ids = d if isinstance(d, list) else ([d] if d else [])
        if not ids:
            fallas.append(f"Ejercicio {k}: no está vinculado a ninguna debilidad (campo 'debilidad').")
        for i in ids:
            if i not in debs:
                fallas.append(f"Ejercicio {k}: la debilidad '{i}' no existe en el mapa del diagnóstico.")
            usados[i] += 1
        if not q.get("solucion", {}).get("pasos"):
            fallas.append(f"Ejercicio {k}: no tiene solución paso a paso.")
        if q.get("clave") not in LETRAS[:len(q.get("alternativas", []))]:
            fallas.append(f"Ejercicio {k}: clave inválida.")
        if q.get("rol") not in ("intervencion", "transferencia", "prerrequisito", "mantencion"):
            revisar.append(f"Ejercicio {k}: falta 'rol' (prerrequisito, intervencion, transferencia o mantencion).")
    for i, d in debs.items():
        if d.get("prioridad") in ("critica", "alta") and not usados[i] and not d.get("sin_intervencion_porque"):
            fallas.append(f"Debilidad {i} ({d.get('prioridad')}) no tiene ejercicios ni una justificación para no intervenir.")
        if d.get("pregunta_defectuosa") and usados[i]:
            revisar.append(f"Debilidad {i} se basa en una pregunta posiblemente defectuosa: confirma que el refuerzo no culpa al alumno de un error de la guía.")
    if pregs and not any(q.get("rol") == "transferencia" for q in pregs):
        fallas.append("No hay ejercicios de transferencia (rol 'transferencia').")
    # cantidad: la misma del material original (un ensayo de 40 -> refuerzo de 40), salvo pedido explícito (n_preguntas_objetivo)
    if "n_preguntas_objetivo" in ref:
        objetivo, origen_n = ref["n_preguntas_objetivo"], "cantidad pedida por el usuario"
    elif a and a.get("n_preguntas"):
        objetivo, origen_n = a["n_preguntas"], "las mismas preguntas que el material original"
    else:
        objetivo, origen_n = 30, "valor por defecto, porque no se pudo leer el análisis del original"
    if len(pregs) != objetivo:
        fallas.append(f"La guía de refuerzo tiene {len(pregs)} ejercicios y deben ser {objetivo} ({origen_n}).")
    # exigencia: el refuerzo debe ser claramente más exigente que el material original
    niveles = Counter(str(q.get("nivel", "")).upper() for q in pregs)
    if niveles.get("A"):
        fallas.append(f"Hay {niveles['A']} ejercicios de nivel A: el refuerzo debe ser más exigente que el original (niveles B a E, con B como máximo el 10 %).")
    max_b = max(1, math.floor(0.10 * len(pregs)))
    if niveles.get("B", 0) > max_b:
        fallas.append(f"Hay {niveles['B']} ejercicios de nivel B y el máximo es {max_b} (10 %): sube su exigencia.")
    if pregs and niveles.get("D", 0) + niveles.get("E", 0) < math.ceil(0.40 * len(pregs)):
        fallas.append(f"Solo {niveles.get('D', 0) + niveles.get('E', 0)} ejercicios de nivel D o E; deben ser al menos {math.ceil(0.40 * len(pregs))} (40 %).")
    difs = [G.dificultad_norm(q.get("dificultad")) for q in pregs]
    sin_dif = [k for k, x in enumerate(difs, 1) if x in (None, "?")]
    if sin_dif:
        fallas.append(f"Ejercicios sin 'dificultad' válida (media, dificil o muy_dificil): {', '.join(map(str, sin_dif))}.")
    if "facil" in difs:
        fallas.append(f"Hay {difs.count('facil')} ejercicios fáciles: el refuerzo no lleva preguntas fáciles.")
    if pregs:
        duras = sum(x in ("dificil", "muy_dificil") for x in difs)
        if duras < math.ceil(0.60 * len(pregs)):
            fallas.append(f"Solo {duras} de {len(pregs)} ejercicios son difíciles o muy difíciles; deben ser al menos {math.ceil(0.60 * len(pregs))} (60 %).")
        if difs.count("muy_dificil") < math.ceil(0.20 * len(pregs)):
            fallas.append(f"Solo {difs.count('muy_dificil')} ejercicios muy difíciles; deben ser al menos {math.ceil(0.20 * len(pregs))} (20 %).")
        orig_d = [G.DIF_PUNTOS.get(G.dificultad_norm(q.get("dificultad_estimada"))) for q in (a or {}).get("por_pregunta", [])]
        orig_d = [x for x in orig_d if x]
        ref_d = [G.DIF_PUNTOS[x] for x in difs if x in G.DIF_PUNTOS]
        if orig_d and ref_d:
            mo, mr = sum(orig_d) / len(orig_d), sum(ref_d) / len(ref_d)
            meta = min(mo + 0.5, 3.5) if mo < 3.5 else mo
            if mr + 1e-9 < meta:
                fallas.append(f"Dificultad media del refuerzo {mr:.2f} y del original {mo:.2f} (fácil 1 … muy difícil 4): debe llegar al menos a {meta:.2f}.")
        elif not orig_d:
            notas.append("El material original no trae 'dificultad' estimada: no se comparó la exigencia del refuerzo con la del original.")
    # habilidades PAES: el refuerzo trabaja todas (en matemática, cada una al menos el 15 %)
    prueba = diag.get("prueba") or ref.get("prueba") or (a or {}).get("prueba")
    habs = Counter(G.habilidad_canonica(q.get("habilidad"), prueba) for q in pregs)
    if G.area(prueba) != "CIE":
        need = math.ceil(0.15 * len(pregs))
        for hb in G.HABILIDADES["MAT"]:
            if not habs.get(hb):
                fallas.append(f"Ningún ejercicio trabaja la habilidad PAES '{hb}': el refuerzo debe trabajar las cuatro.")
            elif habs[hb] < need:
                revisar.append(f"'{hb}' aparece en {habs[hb]} ejercicios (sugerido: al menos {need}, 15 %).")
    elif sum(1 for hb in G.HABILIDADES["CIE"] if habs.get(hb)) < 3:
        revisar.append("Ciencias: el refuerzo trabaja menos de 3 de las 5 habilidades científicas.")
    # tutor: cada respuesta incorrecta del alumno debe tener su recorrido
    if diag.get("tutor_alumnos"):
        if a:
            for al in diag["tutor_alumnos"]:
                est = next((e for e in a["por_estudiante"] if e["id"] == al["id"]), None)
                if not est:
                    fallas.append(f"Tutor {al['id']}: ese estudiante no está en el análisis.")
                    continue
                incorrectas = [x["n"] for x in est["detalle"] if x["estado"] == "incorrecta"]
                cubiertas = {t["n"] for t in al.get("errores", [])}
                faltan = [n for n in incorrectas if n not in cubiertas]
                if faltan:
                    fallas.append(f"Tutor {al['id']}: faltan recorridos para las respuestas incorrectas {', '.join(map(str, faltan))} (debe cubrir las {len(incorrectas)}).")
    return {"ok": not fallas, "fallas": fallas, "revisar": revisar, "notas": notas,
            "originalidad": orig, "ejercicios_por_debilidad": dict(usados), "n_ejercicios": len(pregs),
            "por_habilidad": dict(habs), "por_dificultad": dict(Counter(difs)), "por_nivel": dict(niveles)}

# ======================================================================
# 4) INFORME: PDF docente + panel docente HTML + tutor HTML del alumno
# ======================================================================
INF_CSS = r"""
.sec2 { break-before: page; }
h2.h { font: 700 14pt Poppins, 'DejaVu Sans', sans-serif; color: #1B1F5E; margin: 0 0 2.5mm; padding-bottom: 1.4mm; border-bottom: 1.4pt solid #E08E0B; }
h3.h { font: 600 10.5pt Poppins, 'DejaVu Sans', sans-serif; color: #1B1F5E; margin: 4mm 0 1.5mm; }
p.l { margin: 0 0 2mm; } .nota { font-size: 8.6pt; color: #555; }
table.t { width: 100%; border-collapse: collapse; font: 8.4pt/1.3 'DejaVu Sans', sans-serif; margin: 1mm 0 3mm; }
table.t th { background: #1B1F5E; color: #fff; font: 600 7.8pt Poppins, 'DejaVu Sans', sans-serif; text-align: left; padding: 1.4mm 1.8mm; }
table.t td { border-bottom: .4pt solid #bbb; padding: 1.2mm 1.8mm; vertical-align: top; } table.t tr { break-inside: avoid; }
td.n { text-align: center; white-space: nowrap; font-variant-numeric: tabular-nums; }
.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 3mm; margin: 2mm 0 4mm; }
.kpis div { border: .8pt solid #1B1F5E; padding: 2.4mm 3mm; font: 8pt 'DejaVu Sans', sans-serif; color: #444; }
.kpis b { display: block; font: 700 15pt Poppins, 'DejaVu Sans', sans-serif; color: #1B1F5E; }
.bar { display: inline-block; height: 2.6mm; background: #E08E0B; border-radius: .8mm; vertical-align: middle; }
.bar.bg { background: #E7E8F2; width: 24mm; position: relative; } .bar.bg i { position: absolute; left: 0; top: 0; bottom: 0; background: #1B1F5E; border-radius: .8mm; }
.pill { display: inline-block; font: 600 7pt Poppins, 'DejaVu Sans', sans-serif; padding: .3mm 1.8mm; border-radius: 3mm; border: .6pt solid; }
.p-critica { color: #A3352B; } .p-alta { color: #C8641A; } .p-media { color: #8A6D00; } .p-baja { color: #1F7A4D; }
.hip { border-left: 2pt solid #E08E0B; padding-left: 3mm; margin: 1mm 0 2mm; font-size: 9.2pt; }
.card { border: .7pt solid #ccd; padding: 2.5mm 3.5mm; margin: 0 0 3mm; break-inside: avoid; }
.card h4 { font: 600 10pt Poppins, 'DejaVu Sans', sans-serif; margin: 0 0 1.2mm; color: #1B1F5E; }
dl.g { display: grid; grid-template-columns: 34mm 1fr; gap: 1mm 3mm; margin: 0; font-size: 9pt; } dl.g dt { font-weight: 700; color: #333; } dl.g dd { margin: 0; }
"""

def pill(nivel):
    return f'<span class="pill p-{G.esc(nivel)}">{G.esc(str(nivel).capitalize())}</span>' if nivel else ""

def barra(p):
    if p is None: return "—"
    return f'<span style="white-space:nowrap"><span class="bar bg"><i style="width:{p:.0f}%"></i></span> {fmt_pct(p)}</span>'

def tabla(cols, filas):
    return ('<table class="t"><thead><tr>' + "".join(f"<th>{c}</th>" for c in cols) + "</tr></thead><tbody>"
            + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in f) + "</tr>" for f in filas) + "</tbody></table>")

def M(s):
    return G.render_math(s or "")

def informe_pdf_html(d, a):
    spec = {"prueba": d.get("prueba") or a.get("prueba") or "", "titulo": "Informe de diagnóstico · " + (d.get("titulo") or a.get("titulo") or ""), "codigo": d.get("codigo_informe")}
    g = a.get("grupo") or {}
    individual = a["n_estudiantes"] == 1
    out = [G.header(spec, f"Guía {G.esc(a.get('codigo'))} · {a['n_estudiantes']} {'estudiante' if individual else 'estudiantes'} · {a['n_preguntas']} preguntas")]
    r = d.get("resumen", {})
    out.append('<h2 class="h" style="margin-top:5mm">1. Resumen ejecutivo</h2>')
    out.append('<div class="kpis">'
               f'<div><b>{fmt_pct(g.get("pct_correctas"))}</b>respuestas correctas</div>'
               f'<div><b>{fmt_pct(g.get("pct_incorrectas"))}</b>incorrectas</div>'
               f'<div><b>{fmt_pct(g.get("pct_omitidas"))}</b>omitidas</div>'
               f'<div><b>{a["n_estudiantes"]}</b>{"estudiante" if individual else "estudiantes"}</div></div>')
    out.append(f'<p class="nota">Base: {G.esc(g.get("denominador", ""))}.</p>')
    for lab, key in [("Estado general", "estado"), ("Debilidades principales", "debilidades"), ("Errores más preocupantes", "errores_preocupantes"),
                     ("Lo que funciona en la guía", "funciona_bien"), ("Cambios de mayor beneficio", "cambios_clave"), ("Prioridades inmediatas", "prioridades_inmediatas")]:
        v = r.get(key)
        if not v: continue
        out.append(f'<h3 class="h">{lab}</h3>' + (f'<ul>{"".join(f"<li>{M(x)}</li>" for x in v)}</ul>' if isinstance(v, list) else f'<p class="l">{M(v)}</p>'))
    if a["avisos"] or d.get("limitaciones"):
        out.append('<h3 class="h">Límites de los datos</h3><ul>' + "".join(f"<li>{G.esc(w)}</li>" for w in a["avisos"]) + "".join(f"<li>{M(w)}</li>" for w in d.get("limitaciones", [])) + "</ul>")

    out.append('<section class="sec2"><h2 class="h">2. Análisis cuantitativo</h2>')
    for nombre, tit in (("por_eje", "Rendimiento por eje"), ("por_habilidad", "Rendimiento por habilidad"), ("por_contenido", "Rendimiento por contenido"), ("por_dificultad", "Rendimiento por dificultad estimada"), ("por_tipo", "Rendimiento por tipo de pregunta")):
        dd = g.get(nombre) or {}
        if dd:
            out.append(f'<h3 class="h">{tit}</h3>' + tabla(["Categoría", "Preguntas", "Logro", "Base"],
                [[G.esc(k), ", ".join(map(str, v["preguntas"])), barra(v["pct"]), G.esc(v["denominador"])] for k, v in sorted(dd.items(), key=lambda kv: kv[1]["pct"] or 0)]))
    filas = []
    for q in a["por_pregunta"]:
        dist = " ".join(f"{('<b>' + L + '</b>') if L == q.get('clave') else L}:{n}" for L, n in q["distribucion"].items()) + (f" · om:{q['omitidas']}" if q["omitidas"] else "")
        filas.append([str(q["n"]), q.get("clave") or "—", fmt_pct(q.get("pct_estudiantes_correctos")), dist, str(q.get("discriminacion_D", "—")), G.esc(", ".join(q["flags"]) or "—")])
    out.append('<h3 class="h">Por pregunta</h3>' + tabla(["N°", "Clave", "% estudiantes correctos", "Elecciones (clave en negrita)", "D", "Alertas"], filas))
    out.append('<p class="nota">"% estudiantes correctos" = estudiantes que acertaron esa pregunta / total de estudiantes. No es el porcentaje de preguntas correctas de un estudiante. D = proporción de aciertos del grupo alto − grupo bajo (se calcula desde N = 5; es orientativo bajo N = 10).</p>')
    if not individual:
        out.append('<h3 class="h">Por estudiante</h3>' + tabla(["Estudiante", "Correctas", "Incorrectas", "Omitidas", "Logro"],
            [[G.esc(e["nombre"] or e["id"]), str(e["correctas"]), str(e["incorrectas"]), str(e["omitidas"]), barra(e["logro_pct"])] for e in a["por_estudiante"]]))
    out.append('</section>')

    out.append('<section class="sec2"><h2 class="h">3. Diagnóstico por pregunta</h2>')
    for q in d.get("preguntas", []):
        dg = q.get("diag", {})
        hips = "".join(f'<div class="hip"><b>Hipótesis ({G.esc(h.get("confianza", "?"))}):</b> {M(h.get("causa"))}<br><span class="nota">Evidencia: {M(h.get("evidencia"))}</span></div>' for h in dg.get("hipotesis", []))
        filas = [("Evalúa", dg.get("evalua")), ("Prerrequisitos", dg.get("prerrequisitos")), ("Procedimiento esperado", dg.get("procedimiento")),
                 ("Error observado", dg.get("error_observado")), ("Falta para confirmar", dg.get("falta_info")), ("Intervención", dg.get("intervencion")),
                 ("Decisión sobre la pregunta", dg.get("decision_pregunta"))]
        out.append(f'<div class="card"><h4>Pregunta {q["n"]} · {G.esc(q.get("habilidad") or "")} · {G.esc(q.get("contenido") or "")}</h4><dl class="g">'
                   + "".join(f"<dt>{k}</dt><dd>{M(v)}</dd>" for k, v in filas if v) + "</dl>" + hips + "</div>")
    out.append('</section>')

    out.append('<section class="sec2"><h2 class="h">4. Mapa de debilidades y patrones</h2>')
    out.append(tabla(["ID", "Categoría", "Debilidad", "Evidencia", "Estado", "Prioridad"],
        [[G.esc(x["id"]), G.esc(x.get("categoria")), M(x.get("descripcion")), G.esc(", ".join(f"P{n}" for n in x.get("evidencia", []))), G.esc(x.get("estado")), pill(x.get("prioridad"))] for x in d.get("mapa_debilidades", [])]))
    if d.get("patrones"):
        out.append('<h3 class="h">Patrones de error</h3><ul>' + "".join(f"<li>{M(p)}</li>" for p in d["patrones"]) + "</ul>")
    out.append('</section>')

    cg = d.get("calidad_guia", {})
    if cg:
        out.append('<section class="sec2"><h2 class="h">5. Calidad de la guía original</h2>')
        for key, tit in (("conceptual", "Calidad conceptual"), ("enunciados", "Enunciados"), ("alternativas", "Alternativas"), ("pedagogica", "Calidad pedagógica"), ("evaluacion", "Calidad de la evaluación"), ("sin_datos", "No evaluable con estos datos")):
            if cg.get(key):
                out.append(f'<h3 class="h">{tit}</h3><ul>' + "".join(f"<li>{M(x)}</li>" for x in cg[key]) + "</ul>")
        out.append('</section>')

    out.append('<section class="sec2"><h2 class="h">6. Prioridades</h2>')
    if d.get("metodo_prioridad"):
        out.append(f'<p class="nota">{M(d["metodo_prioridad"])}</p>')
    out.append(tabla(["ID", "Problema", "Tipo", "Frecuencia", "Gravedad", "Importancia PAES", "Evidencia", "Riesgo de pregunta defectuosa", "Nivel", "Por qué"],
        [[G.esc(p.get("id")), M(p.get("problema")), G.esc(p.get("tipo")), G.esc(p.get("frecuencia")), G.esc(p.get("gravedad")), G.esc(p.get("importancia_paes")), G.esc(p.get("evidencia")), G.esc(p.get("riesgo_pregunta")), pill(p.get("nivel")), M(p.get("porque"))] for p in d.get("prioridades", [])]))
    out.append('<h2 class="h" style="margin-top:6mm">7. Plan de mejora de la guía</h2>')
    for cat, tit in (("inmediato", "Cambios inmediatos"), ("siguiente_version", "Para la siguiente versión"), ("opcional", "Mejoras opcionales"), ("conservar", "Conservar")):
        items = [p for p in d.get("plan_mejora", []) if p.get("categoria") == cat]
        if items:
            out.append(f'<h3 class="h">{tit}</h3>' + tabla(["Problema", "Evidencia", "Cambio recomendado", "Justificación", "Resultado esperado", "Cómo comprobarlo", "Prioridad"],
                [[M(p.get("problema")), M(p.get("evidencia")), M(p.get("cambio")) + (f'<br><i>Ejemplo:</i> {M(p["ejemplo"])}' if p.get("ejemplo") else ""), M(p.get("justificacion")), M(p.get("resultado_esperado")), M(p.get("verificacion")), pill(p.get("prioridad"))] for p in items]))
    out.append('</section>')

    out.append('<section class="sec2"><h2 class="h">8. Trazabilidad error → refuerzo</h2>')
    out.append(tabla(["ID", "Pregunta original", "Error observado", "Habilidad", "Diagnóstico", "Prioridad", "Intervención", "Ejercicios de refuerzo", "Criterio de dominio"],
        [[G.esc(t.get("id")), G.esc(t.get("pregunta")), M(t.get("error")), G.esc(t.get("habilidad")), M(t.get("diagnostico")), pill(t.get("prioridad")), M(t.get("intervencion")), G.esc(", ".join(map(str, t.get("ejercicios", [])))), M(t.get("criterio"))] for t in d.get("trazabilidad", [])]))
    c = d.get("conclusiones", {})
    preguntas_c = ["¿Qué reforzar primero?", "¿Qué errores corregir antes?", "¿Qué partes de la guía revisar?", "¿Qué preguntas conservar?",
                   "¿Qué preguntas modificar o reemplazar?", "¿Qué contenidos faltan evaluar?", "¿Qué debe incluir la siguiente versión?", "¿Qué información mejoraría el diagnóstico?"]
    if c:
        out.append('<h2 class="h" style="margin-top:6mm">9. Conclusiones</h2><dl class="g">' + "".join(f"<dt>{q}</dt><dd>{M(c.get(str(i + 1)) or c.get(i + 1) or '—')}</dd>" for i, q in enumerate(preguntas_c)) + "</dl>")
    qc = d.get("control_calidad")
    if qc:
        out.append('<h3 class="h">Control de calidad realizado</h3><ul>' + "".join(f"<li>{M(x)}</li>" for x in qc) + "</ul>")
    out.append('<p class="nota" style="margin-top:4mm">Las hipótesis sobre la causa de un error son interpretaciones a partir de las respuestas; no reemplazan una conversación con el estudiante ni la revisión de un docente.</p></section>')
    return G.doc_html(G.ENSAYO_CSS + INF_CSS, "".join(out)), spec

# ---------- HTML compartido ----------
WEB_CSS = r"""
:root{--bg:#F6F7FB;--card:#fff;--ink:#14183A;--muted:#5B6177;--line:#DDE1EC;--navy:#1B1F5E;--acc:#E08E0B;--ok:#1F7A4D;--okbg:#E7F4EC;--bad:#A3352B;--badbg:#FBECEA;--warn:#8A6D00}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 'Source Serif 4',Georgia,serif}
.wrap{max-width:860px;margin:0 auto;padding:18px max(16px,env(safe-area-inset-right,0px)) 64px max(16px,env(safe-area-inset-left,0px))}
header.top{display:flex;flex-wrap:wrap;gap:10px 20px;align-items:center;justify-content:space-between;border-bottom:2px solid var(--navy);padding-bottom:12px}
header.top svg{width:190px;height:auto;display:block}
h1,h2,h3,.ui,button,.tab{font-family:Poppins,'Segoe UI',system-ui,sans-serif}
h1{font-size:1.25rem;margin:0}h2{font-size:1.1rem;margin:28px 0 10px;color:var(--navy)}h3{font-size:1rem;margin:0 0 6px}
.muted{color:var(--muted)}.small{font-size:.86rem}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:12px 0}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px}.kpi b{display:block;font:700 1.5rem Poppins,system-ui,sans-serif;color:var(--navy)}
.row{display:grid;grid-template-columns:minmax(0,1fr) 120px auto;gap:10px;align-items:center;padding:7px 0;border-bottom:1px solid var(--line)}
.meter{height:10px;background:#E7E8F2;border-radius:6px;overflow:hidden}.meter i{display:block;height:100%;background:var(--navy)}
.meter.lo i{background:var(--acc)}
button,.btn{font-size:.92rem;font-weight:600;border-radius:10px;border:1px solid var(--navy);background:var(--navy);color:#fff;padding:10px 14px;min-height:44px;cursor:pointer}
button.ghost{background:transparent;color:var(--navy)}button:disabled{opacity:.5;cursor:default}
button:focus-visible,.opt:focus-visible{outline:3px solid var(--acc);outline-offset:2px}
.btns{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.opt{display:grid;grid-template-columns:30px 1fr;gap:6px;width:100%;text-align:left;background:var(--card);color:var(--ink);border:1px solid var(--line);font:inherit;font-weight:400;padding:10px 12px;border-radius:10px;margin:6px 0;min-height:44px}
.opt b{font-family:Poppins,system-ui,sans-serif}.opt.ok{background:var(--okbg);border-color:var(--ok)}.opt.no{background:var(--badbg);border-color:var(--bad)}
.opt.mine{box-shadow:inset 4px 0 0 var(--bad)}.opt.key{box-shadow:inset 4px 0 0 var(--ok)}
.fb{border-radius:10px;padding:10px 12px;margin:8px 0;font-size:.95rem}.fb.ok{background:var(--okbg)}.fb.no{background:var(--badbg)}.fb.info{background:#FFF6E6;border:1px solid #F2D29B}
.tagline{display:inline-block;font:600 .72rem Poppins,system-ui,sans-serif;letter-spacing:.06em;text-transform:uppercase;color:var(--acc)}
.chip{display:inline-block;font:600 .74rem Poppins,system-ui,sans-serif;padding:3px 9px;border-radius:99px;border:1px solid var(--line);color:var(--muted)}
.chip.ok{color:var(--ok);border-color:var(--ok)}.chip.w{color:var(--warn);border-color:#D9C36A}
.steps{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 12px}.steps span{font:600 .72rem Poppins,system-ui,sans-serif;padding:3px 8px;border-radius:99px;background:#E7E8F2;color:var(--muted)}.steps span.on{background:var(--navy);color:#fff}.steps span.done{background:var(--okbg);color:var(--ok)}
.enun p{margin:0 0 8px}.enun{overflow-x:auto}svg.tex{display:inline-block;overflow:visible}.texd{text-align:center;margin:8px 0;overflow-x:auto}
.tabs{display:flex;flex-wrap:wrap;gap:6px;margin:16px 0}.tab{border:1px solid var(--line);background:var(--card);color:var(--muted);border-radius:99px;padding:8px 14px;font-size:.88rem;font-weight:600;cursor:pointer;min-height:40px}.tab[aria-selected=true]{background:var(--navy);color:#fff;border-color:var(--navy)}
table{width:100%;border-collapse:collapse;font-size:.88rem}th{text-align:left;font:600 .78rem Poppins,system-ui,sans-serif;color:var(--muted);border-bottom:2px solid var(--line);padding:8px 6px}td{border-bottom:1px solid var(--line);padding:8px 6px;vertical-align:top}
.tw{overflow-x:auto}tr.click{cursor:pointer}tr.click:hover{background:#F0F2FA}
select{font:inherit;padding:8px;border-radius:8px;border:1px solid var(--line);min-height:40px;max-width:100%}
@media (max-width:560px){.row{grid-template-columns:minmax(0,1fr) 70px auto}}
.chip{white-space:nowrap}
@media (prefers-reduced-motion:no-preference){html{scroll-behavior:smooth}}
"""

def pagina(titulo, cuerpo, datos, js):
    return ("<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">"
            f"<meta name=\"robots\" content=\"noindex,nofollow\"><title>{G.esc(titulo)}</title>"
            "<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\"><link rel=\"stylesheet\" href=\"https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Source+Serif+4:wght@400;600&display=swap\">"
            f"<style>{WEB_CSS}</style></head><body><div class=\"wrap\">{cuerpo}</div>"
            f"<script>const DATA={json.dumps(datos, ensure_ascii=False)};</script><script>{js}</script></body></html>")

def precompila(obj):
    """Convierte LaTeX \\(..\\) a SVG en todos los textos para el navegador."""
    if isinstance(obj, str):
        return G.render_math(obj)
    if isinstance(obj, list):
        return [precompila(x) for x in obj]
    if isinstance(obj, dict):
        return {k: (v if k in ("id", "clave", "lleva_a", "correcta", "estado", "prioridad", "n") else precompila(v)) for k, v in obj.items()}
    return obj

# ---------- Panel docente ----------
PANEL_JS = r"""
const $=s=>document.querySelector(s);const fmt=x=>x==null?'—':(x.toFixed(1).replace('.',',')+' %');
function meter(p){return `<div class="meter ${p!=null&&p<60?'lo':''}"><i style="width:${p||0}%"></i></div>`}
const A=DATA.analisis,D=DATA.diag;let tab='resumen',filtro={eje:'',hab:''};
function tabs(){const t=[['resumen','Resumen'],['preguntas','Preguntas'],['debilidades','Debilidades'],['calidad','Calidad de la guía'],['plan','Plan de mejora'],['traza','Trazabilidad']];
 $('#tabs').innerHTML=t.map(([k,l])=>`<button class="tab" role="tab" aria-selected="${k===tab}" data-t="${k}">${l}</button>`).join('')}
function vResumen(){const g=A.grupo||{};let h=`<div class="kpis"><div class="kpi"><b>${fmt(g.pct_correctas)}</b>correctas</div><div class="kpi"><b>${fmt(g.pct_incorrectas)}</b>incorrectas</div><div class="kpi"><b>${fmt(g.pct_omitidas)}</b>omitidas</div><div class="kpi"><b>${A.n_estudiantes}</b>estudiantes</div></div><p class="small muted">Base: ${g.denominador||''}</p>`;
 if(A.avisos.length)h+=`<div class="fb info">${A.avisos.join('<br>')}</div>`;
 h+=`<div class="card"><h3>Estado general</h3><p>${D.resumen?.estado||'—'}</p></div>`;
 for(const [k,t] of [['por_eje','Por eje'],['por_habilidad','Por habilidad (toca una para ver sus preguntas)']]){const o=g[k]||{};if(!Object.keys(o).length)continue;
  h+=`<h2>${t}</h2><div class="card">`+Object.entries(o).sort((a,b)=>(a[1].pct||0)-(b[1].pct||0)).map(([n,v])=>`<div class="row click" data-${k==='por_eje'?'eje':'hab'}="${n}" style="cursor:pointer"><span>${n}</span>${meter(v.pct)}<span class="small">${fmt(v.pct)}</span></div>`).join('')+`</div>`}
 return h}
function vPreguntas(){const ejes=[...new Set(A.por_pregunta.map(q=>q.eje).filter(Boolean))],habs=[...new Set(A.por_pregunta.map(q=>q.habilidad).filter(Boolean))];
 let h=`<div class="btns"><select id="fe" aria-label="Filtrar por eje"><option value="">Todos los ejes</option>${ejes.map(e=>`<option ${e===filtro.eje?'selected':''}>${e}</option>`).join('')}</select><select id="fh" aria-label="Filtrar por habilidad"><option value="">Todas las habilidades</option>${habs.map(e=>`<option ${e===filtro.hab?'selected':''}>${e}</option>`).join('')}</select></div>`;
 const qs=A.por_pregunta.filter(q=>(!filtro.eje||q.eje===filtro.eje)&&(!filtro.hab||q.habilidad===filtro.hab));
 h+=`<div class="tw"><table><thead><tr><th>N°</th><th>Contenido</th><th>% correctos</th><th>Distractor + elegido</th><th>Alertas</th></tr></thead><tbody>`+qs.map(q=>`<tr class="click" data-q="${q.n}"><td>${q.n}</td><td>${q.contenido||''}<div class="small muted">${q.habilidad||''}</div></td><td>${fmt(q.pct_estudiantes_correctos)}</td><td>${q.distractor_mas_elegido?q.distractor_mas_elegido.letra+' ('+q.distractor_mas_elegido.n+')':'—'}</td><td>${q.flags.map(f=>`<span class="chip w">${f.replaceAll('_',' ')}</span>`).join(' ')||'—'}</td></tr>`).join('')+`</tbody></table></div><div id="det"></div>`;return h}
function detalle(n){const q=A.por_pregunta.find(x=>x.n==n),d=(D.preguntas||[]).find(x=>x.n==n)||{},dg=d.diag||{};const tot=Math.max(1,q.N);
 let h=`<div class="card"><h3>Pregunta ${n} · clave ${q.clave||'—'}</h3>${d.enunciado?`<div class="enun">${d.enunciado}</div>`:''}<h3 style="margin-top:12px">Elecciones</h3>`+Object.entries(q.distribucion).map(([L,c])=>`<div class="row"><span>${L}${L===q.clave?' (clave)':''}</span>${meter(100*c/tot)}<span class="small">${c}</span></div>`).join('');
 for(const [k,l] of [['evalua','Evalúa'],['error_observado','Error observado'],['intervencion','Intervención'],['decision_pregunta','Decisión']]) if(dg[k])h+=`<p><b>${l}:</b> ${dg[k]}</p>`;
 (dg.hipotesis||[]).forEach(x=>h+=`<div class="fb info"><b>Hipótesis (${x.confianza||'?'}):</b> ${x.causa}<div class="small">Evidencia: ${x.evidencia||'—'}</div></div>`);
 const t=(D.trazabilidad||[]).filter(t=>String(t.pregunta).split(/[ ,]+/).includes(String(n)));if(t.length)h+=`<p><b>Refuerzo vinculado:</b> ${t.map(x=>x.id+' → ejercicios '+(x.ejercicios||[]).join(', ')).join('; ')}</p>`;
 $('#det').innerHTML=h+'</div>';$('#det').scrollIntoView()}
function lista(arr,f){return arr&&arr.length?arr.map(f).join(''):'<p class="muted">Sin datos.</p>'}
function vDeb(){return lista(D.mapa_debilidades,x=>`<div class="card"><span class="chip">${x.id}</span> <span class="chip">${x.categoria||''}</span> <span class="chip ${x.prioridad==='critica'||x.prioridad==='alta'?'w':''}">${x.prioridad||''}</span><p>${x.descripcion}</p><p class="small muted">Evidencia: ${(x.evidencia||[]).map(n=>'P'+n).join(', ')} · ${x.estado||''}</p></div>`)+(D.patrones?.length?`<h2>Patrones</h2><div class="card"><ul>${D.patrones.map(p=>`<li>${p}</li>`).join('')}</ul></div>`:'')}
function vCal(){const c=D.calidad_guia||{};return Object.entries({conceptual:'Conceptual',enunciados:'Enunciados',alternativas:'Alternativas',pedagogica:'Pedagógica',evaluacion:'Evaluación',sin_datos:'Sin datos suficientes'}).filter(([k])=>c[k]?.length).map(([k,l])=>`<div class="card"><h3>${l}</h3><ul>${c[k].map(x=>`<li>${x}</li>`).join('')}</ul></div>`).join('')||'<p class="muted">Sin evaluación.</p>'}
function vPlan(){return lista(D.plan_mejora,p=>`<div class="card"><span class="chip">${(p.categoria||'').replace('_',' ')}</span> <span class="chip w">${p.prioridad||''}</span><p><b>${p.problema}</b></p><p>${p.cambio}</p><p class="small muted">Evidencia: ${p.evidencia||'—'} · Cómo comprobarlo: ${p.verificacion||'—'}</p></div>`)}
function vTraza(){return `<div class="tw"><table><thead><tr><th>ID</th><th>Pregunta</th><th>Error</th><th>Intervención</th><th>Ejercicios</th><th>Criterio</th></tr></thead><tbody>${(D.trazabilidad||[]).map(t=>`<tr><td>${t.id}</td><td>${t.pregunta}</td><td>${t.error}</td><td>${t.intervencion}</td><td>${(t.ejercicios||[]).join(', ')}</td><td>${t.criterio||''}</td></tr>`).join('')}</tbody></table></div>`}
function render(){tabs();const v={resumen:vResumen,preguntas:vPreguntas,debilidades:vDeb,calidad:vCal,plan:vPlan,traza:vTraza}[tab]();$('#view').innerHTML=v}
document.addEventListener('click',e=>{const t=e.target.closest('[data-t]');if(t){tab=t.dataset.t;render();return}
 const r=e.target.closest('[data-hab],[data-eje]');if(r){filtro={eje:r.dataset.eje||'',hab:r.dataset.hab||''};tab='preguntas';render();return}
 const q=e.target.closest('[data-q]');if(q)detalle(q.dataset.q)});
document.addEventListener('change',e=>{if(e.target.id==='fe'){filtro.eje=e.target.value;render()}if(e.target.id==='fh'){filtro.hab=e.target.value;render()}});
render();
"""

def panel_html(d, a):
    cuerpo = (f'<header class="top">{G.LOGO_SVG}<div><span class="tagline">Panel docente · uso interno</span><h1>{G.esc(d.get("titulo") or a.get("titulo") or "")}</h1>'
              f'<div class="small muted">Guía {G.esc(a.get("codigo"))} · {a["n_estudiantes"]} {"estudiante" if a["n_estudiantes"] == 1 else "estudiantes"}</div></div></header>'
              '<nav class="tabs" id="tabs" role="tablist" aria-label="Secciones"></nav><main id="view"></main>')
    return pagina(f"Panel {a.get('codigo')}", cuerpo, {"analisis": a, "diag": precompila(d)}, PANEL_JS)

# ---------- Tutor del estudiante ----------
TUTOR_JS = r"""
const $=s=>document.querySelector(s);const T=DATA;const KEY='tsz-tutor-'+T.clave_local;
let S={};try{S=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){S={}}
function save(){try{localStorage.setItem(KEY,JSON.stringify(S))}catch(e){}}
const ETAPAS=['Tu razonamiento','Qué pasó','Resolución guiada','Comprobación','Práctica nueva','Transferencia'];
function st(n){return S[n]||(S[n]={etapa:0,hip:null,paso:0,pistas:0,comp:null,prac:{},log:[]})}
function opts(list,name,cls=''){return list.map((o,i)=>`<button class="opt ${cls}" data-${name}="${i}"><b>${String.fromCharCode(65+i)})</b><span>${o.texto??o}</span></button>`).join('')}
function head(e,s){return `<div class="steps">${ETAPAS.map((x,i)=>`<span class="${i===s.etapa?'on':i<s.etapa?'done':''}">${i+1}. ${x}</span>`).join('')}</div>`}
function original(e){return `<div class="enun">${e.enunciado}</div>`+e.alternativas.map((a,i)=>{const L='ABCDE'[i];const c=L===e.marcada?'mine':L===e.clave?'key':'';return `<div class="opt ${c}" aria-disabled="true"><b>${L})</b><span>${a}${L===e.marcada?' <span class="chip">tu respuesta</span>':''}${L===e.clave&&T.mostrar_clave?' <span class="chip ok">correcta</span>':''}</span></div>`}).join('')}
function render(n){const e=T.errores.find(x=>x.n==n),s=st(n),box=$('#e'+n);let h=head(e,s);const tu=e.tutor;
 if(s.etapa===0){h+=original(e)+`<p class="ui"><b>${tu.reflexion.pregunta}</b></p>`+opts(tu.reflexion.opciones,'ref')}
 else if(s.etapa===1){const hp=tu.hipotesis[s.hip]||{};if(hp.siguiente&&!s.hip2){h+=`<p class="ui"><b>${hp.siguiente.pregunta}</b></p>`+opts(hp.siguiente.opciones,'ref2')}else{const H=tu.hipotesis[s.hip2||s.hip]||hp;
  h+=`<div class="fb info"><span class="tagline">${H.confirmada?'Lo que pasó':'Lo más probable, según lo que respondiste'}</span>`;
  for(const [k,l] of [['que_fallo','Qué parte falló'],['por_que_parece','Por qué parece razonable'],['concepto','Lo que necesitas tener claro'],['diferencia','La diferencia clave'],['senal','Señal para la próxima vez']]) if(H[k])h+=`<p><b>${l}.</b> ${H[k]}</p>`;
  h+=`</div><div class="btns"><button data-go="2">Resolverla paso a paso</button><button class="ghost" data-sol="1">Ver la solución completa</button></div>`}}
 else if(s.etapa===2){const p=tu.pasos[s.paso];if(!p){s.etapa=3;save();return render(n)}
  h+=`<p class="small muted">Paso ${s.paso+1} de ${tu.pasos.length}</p>${p.contexto?`<p>${p.contexto}</p>`:''}<p class="ui"><b>${p.pregunta}</b></p>`+opts(p.opciones,'paso');
  for(let i=0;i<s.pistas&&i<(p.pistas||[]).length;i++)h+=`<div class="fb info"><b>Pista ${i+1}.</b> ${p.pistas[i]}</div>`;
  h+=`<div id="fb${n}"></div><div class="btns">${(p.pistas||[]).length>s.pistas?`<button class="ghost" data-pista="1">Dame una pista</button>`:''}<button class="ghost" data-sol="1">Ver la solución completa</button></div>`}
 else if(s.etapa===3){if(s.versol)h+=`<div class="card"><span class="tagline">Solución completa</span><div>${tu.solucion_completa}</div></div>`;
  const c=tu.comprobacion;h+=`<p class="ui"><b>Comprueba que lo entendiste:</b> ${c.pregunta}</p>`+opts(c.opciones,'comp')+`<div id="fb${n}"></div>`}
 else if(s.etapa===4||s.etapa===5){const ej=s.etapa===4?tu.practica:tu.transferencia;const k=s.etapa===4?'p':'t';
  h+=`<span class="tagline">${s.etapa===4?'Ejercicio nuevo':'Problema de transferencia'}</span><div class="enun">${ej.enunciado}</div>`+opts(ej.alternativas,'ej')+`<div id="fb${n}"></div>`}
 else{const p=s.prac||{};h+=`<div class="fb ${p.t?'ok':'info'}">${p.t?'Resolviste el problema de transferencia. Es una buena señal; confírmalo con la guía de refuerzo antes de darlo por dominado.':'Completaste el recorrido. Esta habilidad todavía necesita práctica: sigue con los ejercicios de la guía de refuerzo marcados para ella.'}</div><div class="btns"><button class="ghost" data-reset="1">Volver a empezar este error</button></div>`}
 box.innerHTML=h;progreso()}
function feedback(n,ok,txt){const f=$('#fb'+n);if(f)f.innerHTML=`<div class="fb ${ok?'ok':'no'}">${txt}</div>`}
document.addEventListener('click',ev=>{const b=ev.target.closest('button');if(!b)return;const box=b.closest('[data-err]');
 if(b.dataset.abrir){const n=b.dataset.abrir;$('#e'+n).hidden=false;render(n);b.hidden=true;return}
 if(!box)return;const n=box.dataset.err,e=T.errores.find(x=>x.n==n),s=st(n),tu=e.tutor;
 if(b.dataset.ref!==undefined){s.hip=tu.reflexion.opciones[+b.dataset.ref].lleva_a;s.hip2=null;s.etapa=1;s.log.push('razonamiento:'+s.hip)}
 else if(b.dataset.ref2!==undefined){s.hip2=tu.hipotesis[s.hip].siguiente.opciones[+b.dataset.ref2].lleva_a;s.log.push('razonamiento2:'+s.hip2)}
 else if(b.dataset.go){s.etapa=+b.dataset.go;s.paso=0;s.pistas=0}
 else if(b.dataset.sol){s.versol=true;s.etapa=3;s.log.push('pidio_solucion')}
 else if(b.dataset.pista){s.pistas++;s.log.push('pista')}
 else if(b.dataset.paso!==undefined){const p=tu.pasos[s.paso],i=+b.dataset.paso;if(i===p.correcta){s.paso++;s.pistas=0;save();render(n);const f=$('#fb'+n);if(f&&p.feedback_ok)f.innerHTML=`<div class="fb ok">${p.feedback_ok}</div>`;return}
  save();return feedback(n,false,(p.feedback&&p.feedback[i])||'Revisa este paso. Puedes pedir una pista.')}
 else if(b.dataset.comp!==undefined){const c=tu.comprobacion,i=+b.dataset.comp;if(i===c.correcta){s.comp=true;s.etapa=4;save();render(n);return}
  s.comp=false;save();return feedback(n,false,c.feedback_no||c.explicacion_alternativa||'Todavía no. Lee de nuevo la idea clave e inténtalo otra vez.')}
 else if(b.dataset.ej!==undefined){const ej=s.etapa===4?tu.practica:tu.transferencia,i=+b.dataset.ej,L='ABCDE'[i],k=s.etapa===4?'p':'t';const ok=L===ej.clave;
  if(s.prac[k]===undefined)s.prac[k]=ok;s.log.push((k==='p'?'practica:':'transferencia:')+(ok?'ok':'no'));
  if(ok){feedback(n,true,ej.explicacion+'<div class="btns"><button data-go="'+(s.etapa+1)+'">Continuar</button></div>');save();progreso();return}
  save();return feedback(n,false,(ej.feedback&&ej.feedback[L])||'Esa no es. Revisa la señal que aprendiste e inténtalo de nuevo.')}
 else if(b.dataset.reset){delete S[n]}
 save();render(n)});
function estadoHab(){const m={};for(const e of T.errores){const s=S[e.n]||{};const k=e.habilidad||'General';m[k]=m[k]||{n:0,trab:0,t:0};m[k].n++;if(s.etapa>=4)m[k].trab++;if(s.prac&&s.prac.t)m[k].t++}return m}
function progreso(){const m=estadoHab();$('#prog').innerHTML=Object.entries(m).map(([k,v])=>`<div class="row"><span>${k}</span><div class="meter"><i style="width:${100*(v.trab+v.t)/(2*v.n)}%"></i></div><span class="small">${v.t?'<span class="chip ok">en consolidación</span>':v.trab?'<span class="chip w">trabajada</span>':'<span class="chip">pendiente</span>'}</span></div>`).join('')}
function resumen(){const m=estadoHab();let t=`Progreso TS Zenit · ${T.titulo}\n${T.alumno?'Alumno: '+T.alumno+'\n':''}`;for(const e of T.errores){const s=S[e.n]||{};t+=`\nPregunta ${e.n} (${e.habilidad||''}): etapa ${Math.min((s.etapa||0)+1,7)} de 7`+(s.prac?` · práctica: ${s.prac.p===undefined?'—':s.prac.p?'correcta':'incorrecta'} · transferencia: ${s.prac.t===undefined?'—':s.prac.t?'correcta':'incorrecta'}`:'')+(s.log&&s.log.length?`\n  registro: ${s.log.join(', ')}`:'')}return t}
$('#exp').addEventListener('click',async()=>{const t=resumen();try{await navigator.clipboard.writeText(t);$('#expmsg').textContent='Resumen copiado. Pégalo en un correo o mensaje para tu profesor.'}catch(e){const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();$('#expmsg').textContent='Selecciona y copia el texto.'}});
$('#dl').addEventListener('click',()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([resumen()],{type:'text/plain'}));a.download='progreso-'+T.codigo+'.txt';a.click()});
progreso();
"""

def tutor_html(d, a, alumno):
    est = next(e for e in a["por_estudiante"] if e["id"] == alumno["id"])
    errores = []
    for t in alumno.get("errores", []):
        q = next(x for x in d["preguntas"] if x["n"] == t["n"])
        det = next(x for x in est["detalle"] if x["n"] == t["n"])
        errores.append(precompila({"n": t["n"], "enunciado": q.get("enunciado", ""), "alternativas": q.get("alternativas", []),
                                   "marcada": det["marcada"], "clave": det["clave"], "habilidad": q.get("habilidad"),
                                   "tutor": t["tutor"]}))
    habs = est["por_habilidad"]
    domina = [k for k, v in habs.items() if v["pct"] is not None and v["pct"] >= 75]
    reforzar = [k for k, v in habs.items() if v["pct"] is not None and v["pct"] < 75]
    nombre = alumno.get("nombre_visible") or ""
    datos = {"clave_local": hashlib.sha256((a.get("codigo", "") + alumno["id"]).encode()).hexdigest()[:10],
             "codigo": a.get("codigo"), "titulo": d.get("titulo") or a.get("titulo"), "alumno": nombre,
             "mostrar_clave": alumno.get("mostrar_clave", True), "errores": errores}
    prueba = d.get("prueba") or a.get("prueba")
    canon = {}
    for k, v in habs.items():
        canon[G.habilidad_canonica(k, prueba)] = v
    orden = G.habilidades_de(prueba) + [k for k in canon if k not in G.habilidades_de(prueba)]
    filas = "".join(
        (f'<div class="row"><span>{G.esc(k)}</span><div class="meter {"lo" if (canon[k]["pct"] or 0) < 75 else ""}"><i style="width:{canon[k]["pct"] or 0}%"></i></div><span class="small">{canon[k]["correctas"]}/{canon[k]["total"]}</span></div>'
         if k in canon else
         f'<div class="row"><span>{G.esc(k)}</span><div class="meter"><i style="width:0%"></i></div><span class="small"><span class="chip">sin preguntas</span></span></div>')
        for k in orden)
    no_evaluadas = [k for k in G.habilidades_de(prueba) if k not in canon]
    lista_err = "".join(
        f'<div class="card" data-err="{e["n"]}"><h3>Pregunta {e["n"]}</h3><div class="small muted">{G.esc(e.get("habilidad") or "")}</div>'
        f'<div class="btns"><button data-abrir="{e["n"]}">Analizar mi error</button></div><div id="e{e["n"]}" hidden></div></div>' for e in errores)
    cuerpo = (f'<header class="top">{G.LOGO_SVG}<div><span class="tagline">Tu informe · {G.esc(a.get("codigo"))}</span><h1>{G.esc(datos["titulo"])}</h1>'
              f'<div class="small muted">{("Hola, " + G.esc(nombre) + ". ") if nombre else ""}Aquí puedes entender cada error y practicar con ejercicios nuevos.</div></div></header>'
              f'<div class="kpis" style="margin-top:16px"><div class="kpi"><b>{est["correctas"]} de {est["base"]}</b>respuestas correctas</div>'
              f'<div class="kpi"><b>{est["incorrectas"]}</b>para trabajar</div><div class="kpi"><b>{est["omitidas"]}</b>sin responder</div></div>'
              f'<h2>Tus habilidades en esta guía</h2><div class="card">{filas}<p class="small muted">Se basa en {est["base"]} preguntas; con pocas preguntas por habilidad, tómalo como una orientación.'
              + (f' Esta guía no tuvo preguntas de {G.esc(", ".join(no_evaluadas))}' + ('; tu guía de refuerzo sí las trabaja.' if G.area(prueba) != "CIE" else '.') if no_evaluadas else '')
              + '</p></div>'
              + (f'<div class="card"><b>Lo que ya muestras:</b> {G.esc(", ".join(domina))}</div>' if domina else "")
              + (f'<div class="card"><b>Para reforzar:</b> {G.esc(", ".join(reforzar))}</div>' if reforzar else "")
              + "".join(f'<div class="card">{M(p)}</div>' for p in alumno.get("mensajes", []))
              + f'<h2>Trabaja tus errores</h2><p class="small muted">Primero te preguntamos cómo lo pensaste; después ves qué pasó, la resuelves paso a paso, compruebas que lo entendiste y practicas con un ejercicio nuevo.</p>{lista_err}'
              + '<h2>Tu progreso</h2><div class="card" id="prog"></div>'
              + '<div class="btns"><button class="ghost" id="exp">Copiar resumen de mi progreso</button><button class="ghost" id="dl">Descargar resumen</button></div><p class="small muted" id="expmsg">Tu progreso se guarda solo en este navegador.</p>'
              + (f'<h2>Siguiente paso</h2><div class="card">{M(alumno["siguiente_paso"])}</div>' if alumno.get("siguiente_paso") else ""))
    return pagina(f"Informe {a.get('codigo')}", cuerpo, datos, TUTOR_JS)

def informe(d, a, outdir):
    outdir = pathlib.Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    doc, spec = informe_pdf_html(d, a)
    cod = d.get("codigo_informe") or f"INF-{a.get('codigo')}"
    pdf = outdir / f"{cod}.pdf"
    G.render_pdf(doc, pdf, spec, G.MARCA + " — informe de diagnóstico", f"Informe {cod} · TS Zenit")
    G.snapshots(pdf, outdir, "inf")
    (outdir / f"panel-{cod}.html").write_text(panel_html(d, a), encoding="utf-8")
    hechos = [str(pdf), str(outdir / f"panel-{cod}.html")]
    for al in d.get("tutor_alumnos", []):
        token = hashlib.sha256(f"{cod}-{al['id']}-{SAL_INF}".encode()).hexdigest()[:10]
        carpeta = outdir / "web" / "informes" / token
        carpeta.mkdir(parents=True, exist_ok=True)
        (carpeta / "index.html").write_text(tutor_html(d, a, al), encoding="utf-8")
        hechos.append(str(carpeta / "index.html"))
        # correo para el alumno, con el enlace donde quedará publicado el tutor
        enlace = f"{d.get('sitio', 'https://tszenit.cl').rstrip('/')}/informes/{token}/"
        n_ej = d.get("n_ejercicios_refuerzo") or a.get("n_preguntas") or 30
        n_err = len(al.get("errores", []))
        correo = (f"Asunto: Tu guía de refuerzo personalizada · TS Zenit\n\n"
                  f"Hola {al.get('nombre_visible') or ''}:\n"
                  f"Te adjunto tu guía de refuerzo personalizada ({n_ej} {'ejercicio' if n_ej == 1 else 'ejercicios'}, cada uno con un QR a su solución).\n"
                  + ("Además, aquí puedes revisar tu error paso a paso, con pistas y ejercicios nuevos: \n" if n_err == 1 else
                     f"Además, aquí puedes revisar tus {n_err} errores uno por uno, con pistas y ejercicios nuevos: \n")
                  + f"{enlace}\n"
                  f"Tu avance queda guardado en el navegador que uses.\n"
                  f"TS Zenit · Hazlo realidad\n")
        (outdir / f"correo-{al['id']}.txt").write_text(correo, encoding="utf-8")
        hechos.append(f"{outdir / ('correo-' + al['id'] + '.txt')}  (enlace: {enlace})")
    return hechos

# ======================================================================
# 5) COMPARAR VERSIONES
# ======================================================================
def comparar(a1, a2, mapa=None):
    mapa = mapa or {str(q["n"]): q["n"] for q in a1["por_pregunta"]}
    filas, avisos = [], []
    if a1["n_estudiantes"] < 5 or a2["n_estudiantes"] < 5:
        avisos.append("Alguna versión tiene menos de 5 estudiantes: las diferencias pueden deberse al azar.")
    avisos.append("Una mejora observada no prueba que la causa sea el cambio de la guía: compara también grupos, condiciones de aplicación y conocimientos previos.")
    for n1, n2 in mapa.items():
        q1 = next((q for q in a1["por_pregunta"] if str(q["n"]) == str(n1)), None)
        q2 = next((q for q in a2["por_pregunta"] if str(q["n"]) == str(n2)), None)
        if not q1 or not q2: continue
        d1, d2 = q1.get("distractor_mas_elegido"), q2.get("distractor_mas_elegido")
        filas.append({"v1": n1, "v2": n2, "pct_v1": q1.get("pct_estudiantes_correctos"), "pct_v2": q2.get("pct_estudiantes_correctos"),
                      "cambio_pp": None if q1.get("pct_estudiantes_correctos") is None or q2.get("pct_estudiantes_correctos") is None else round(q2["pct_estudiantes_correctos"] - q1["pct_estudiantes_correctos"], 1),
                      "distractor_v1": d1 and d1["letra"], "distractor_v2": d2 and d2["letra"],
                      "persiste_distractor": bool(d1 and d2 and d1["letra"] == d2["letra"] and (d2["pct"] or 0) >= 20),
                      "alertas_v1": q1["flags"], "alertas_v2": q2["flags"]})
    return {"avisos": avisos, "filas": filas}

# ======================================================================
def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "analizar":
        a = analizar(leer(sys.argv[2])); out = pathlib.Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
        escribir(out / "analisis.json", a); imprimir_analisis(a); print(f"\n→ {out / 'analisis.json'}")
    elif cmd == "excluidas":
        nums = [int(x) for x in sys.argv[3].split(",") if x.strip()]
        r = excluidas_desde_pdfs(sys.argv[2], nums); escribir(sys.argv[4], r)
        print(f"{sum(1 for x in r if x.get('texto'))} de {len(r)} preguntas extraídas → {sys.argv[4]}")
    elif cmd == "validar":
        v = validar(leer(sys.argv[2]), leer(sys.argv[3]))
        print(f"Ejercicios: {v['n_ejercicios']} · por debilidad: {v['ejercicios_por_debilidad']}")
        for k in ("fallas", "revisar", "notas"):
            for x in v[k]: print(k.upper()[:-1] if k != "notas" else "NOTA", "·", x)
        print("RESULTADO:", "OK" if v["ok"] else "NO APTO — corrige las fallas antes de entregar")
        sys.exit(0 if v["ok"] else 1)
    elif cmd == "informe":
        d = leer(sys.argv[2]); a = d.get("analisis") if isinstance(d.get("analisis"), dict) else leer(d["analisis"])
        for x in informe(d, a, sys.argv[3]): print("→", x)
    elif cmd == "comparar":
        r = comparar(leer(sys.argv[2]), leer(sys.argv[3]), leer(sys.argv[4]) if len(sys.argv) > 4 else None)
        for w in r["avisos"]: print("AVISO:", w)
        print("| v1 | v2 | % v1 | % v2 | Cambio (pp) | Distractor v1 → v2 | Persiste |"); print("|---|---|---|---|---|---|---|")
        for f in r["filas"]:
            print(f"| {f['v1']} | {f['v2']} | {fmt_pct(f['pct_v1'])} | {fmt_pct(f['pct_v2'])} | {f['cambio_pp']} | {f['distractor_v1']} → {f['distractor_v2']} | {'sí' if f['persiste_distractor'] else 'no'} |")
    else:
        print(__doc__); sys.exit(1)

if __name__ == "__main__":
    main()
