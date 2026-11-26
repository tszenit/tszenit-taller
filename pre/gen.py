"""Generador de materiales del Plan Precálculo (TS Zenit).
Uso: python3 gen.py I1 [I2 I3 EX]  →  out/PRE-<ID>-{AP,SL,AM}.html (con la matemática ya en MathML)
El contenido vive en c_<id>.py como listas de bloques (ver funciones de este archivo)."""
import sys, re, html, json, subprocess, importlib, os
D = os.path.dirname(os.path.abspath(__file__))

# ---------------- DSL ----------------
def P(h): return ("p", h)
def EQ(tex, small=None): return ("eq", tex, small)
def MINI(*items): return ("mini", items)                 # (título, html)
def TBL(head, rows): return ("tbl", head, rows)
def EX(q, steps, ans=None, tipo=False, titulo=None): return ("ex", q, steps, ans, tipo, titulo)
def TRAP(h): return ("note", "trap", h)
def KEY(h, lab="Idea clave"): return ("note", "key", h, lab)
def TOOL(name): return ("tool", name)
def FIG(svg, cap=None): return ("fig", svg, cap)
def UL(*items): return ("ul", items)
def SUB(id, title, *blocks): return {"id": id, "t": title, "b": list(blocks)}
def TEMA(id, sym, nm, title, intro, subs, rep=None, preg=None):
    return {"id": id, "sym": sym, "nm": nm, "t": title, "intro": intro, "subs": subs, "rep": rep or [], "preg": preg or intro}
# slides
def SL(k, title, fx=None, small=None, cards=(), cols=None, box=None, tbl=None):
    return {"k": k, "t": title, "fx": fx, "small": small, "cards": list(cards), "cols": cols, "box": box, "tbl": tbl}
def C(h, p, a=False, n=None): return {"h": h, "p": p, "a": a, "n": n}

# matemática: $...$ en línea; los bloques EQ van como display
def m(s):
    s = s.replace("\\$", "\x00")
    return re.sub(r"\$(.+?)\$", lambda g: "⟦" + g.group(1) + "⟧", s).replace("\x00", "$")
def md(tex): return "⟪" + tex + "⟫"

def esc(s): return html.escape(s, quote=False)

TIPO_LAB = "Pregunta tipo interrogación"
# ---------------- AP: apunte interactivo ----------------
def ap_block(b, pfx):
    k = b[0]
    if k == "p": return "<p>" + m(b[1]) + "</p>"
    if k == "eq": return '<div class="eq">' + md(b[1]) + (("<small>" + m(b[2]) + "</small>") if b[2] else "") + "</div>"
    if k == "mini": return '<div class="two">' + "".join('<div class="mini"><h5>' + m(t) + "</h5><p>" + m(h) + "</p></div>" for t, h in b[1]) + "</div>"
    if k == "tbl": return '<div class="tw"><table class="tbl"><thead><tr>' + "".join("<th>" + m(x) + "</th>" for x in b[1]) + "</tr></thead><tbody>" + "".join("<tr>" + "".join("<td>" + m(c) + "</td>" for c in r) + "</tr>" for r in b[2]) + "</tbody></table></div>"
    if k == "ul": return '<ul class="plain">' + "".join("<li>" + m(x) + "</li>" for x in b[1]) + "</ul>"
    if k == "ex":
        _, q, steps, ans, tipo, tit = b
        lab = (tit or TIPO_LAB) if tipo else (tit or "Ejemplo")
        head = ('<span class="tag">' + lab + "</span>" if tipo else lab + ": ")
        body = '<ol class="pasos">' + "".join("<li>" + m(s) + "</li>" for s in steps) + "</ol>" if len(steps) > 1 else "<p>" + m(steps[0]) + "</p>"
        if ans: body += "<p><b>Respuesta:</b> " + m(ans) + "</p>"
        return '<div class="ex' + (" tipo" if tipo else "") + '"><p class="q">' + head + m(q) + "</p><details><summary>" + ("Ver resolución completa" if tipo else "Ver resolución") + "</summary>" + body + "</details></div>"
    if k == "note":
        lab = "Error típico" if b[1] == "trap" else (b[3] if len(b) > 3 else "Idea clave")
        return '<div class="note ' + b[1] + '"><span class="lab">' + lab + "</span><span>" + m(b[2]) + "</span></div>"
    if k == "tool": return '<div class="tool" data-tool="' + b[1] + '"></div>'
    if k == "fig": return '<figure class="fig">' + b[1] + (("<figcaption>" + m(b[2]) + "</figcaption>") if b[2] else "") + "</figure>"
    raise ValueError(k)

def build_ap(C_):
    global TIPO_LAB
    TIPO_LAB = "Pregunta tipo examen" if C_.ID == "EX" else "Pregunta tipo interrogación"
    pfx = "pre-" + C_.ID.lower() + "-"
    temas = C_.TEMAS; n = len(temas)
    ntools = sum(1 for t in temas for s in t["subs"] for b in s["b"] if b[0] == "tool")
    tiles = "".join('<button class="tile" role="tab" data-tab="%s" aria-selected="%s"><span class="z">%d</span><span class="sym">%s</span><span class="nm">%s</span><span class="pg"><span></span></span></button>' % (t["id"], "true" if i == 0 else "false", i + 1, esc(t["sym"]), esc(t["nm"])) for i, t in enumerate(temas))
    panels = []
    for i, t in enumerate(temas):
        h = ['<section class="panel" id="%s" role="tabpanel"%s>' % (t["id"], "" if i == 0 else " hidden"),
             '  <div class="phead"><span class="lab">Tema %d de %d · %s · %s</span><h2>%s</h2><p>%s</p></div>' % (i + 1, n, C_.ID if C_.ID != "EX" else "Examen", esc(C_.NOMBRE), esc(t["t"]), m(t["intro"]))]
        for s in t["subs"]:
            h.append('  <div class="sub" data-sub="%s%s"><div class="subh"><h3>%s</h3></div>%s</div>' % (pfx, s["id"], m(s["t"]), "".join(ap_block(b, pfx) for b in s["b"])))
        if t["rep"]:
            h.append('  <div class="sub" data-sub="%s%s-rep"><div class="subh"><h3>Autoevaluación rápida</h3></div><p class="muted">Responde mentalmente y luego abre cada respuesta.</p>%s</div>' % (pfx, t["id"], "".join('<div class="ex"><p class="q">' + m(q) + '</p><details><summary>Ver respuesta</summary><p>' + m(a) + "</p></details></div>" for q, a in t["rep"])))
        h.append('  <div class="tz-next"><b>Practica con las guías TS Zenit</b><span class="muted">%s</span></div>' % C_.GUIAS_TXT)
        h.append("</section>")
        panels.append("\n".join(h))
    temario = "".join("<li><b>%s:</b> %s</li>" % (esc(t["t"]), m(t["intro"])) for t in temas)
    out = open(D + "/ap_head.html").read().replace("{{TITLE}}", "%s · %s · Apunte Precálculo · TS Zenit" % ("Examen" if C_.ID == "EX" else C_.ID, C_.NOMBRE)) + "</head><body>\n" + open(D + "/ap_css.html").read() + CSS_AP_EXTRA
    out += '\n<header class="tz-top"><div class="wrap"><span class="tz-brand"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.5l2.6 6.3 6.8.5-5.2 4.4 1.6 6.6L12 16.8l-5.8 3.5 1.6-6.6-5.2-4.4 6.8-.5z" fill="currentColor"/></svg>TS Zenit <span>· Material Plan Precálculo</span></span><span class="tz-pill"><i></i>Exclusivo Plan Precálculo</span></div></header>\n'
    out += '<div class="wrap intro">\n  <div class="art" aria-hidden="true">%s</div>\n  <span class="lab">Precálculo · %s · %s · Stewart, Precálculo</span>\n  <h1>%s<em>%s</em></h1>\n  <p>%s</p>\n  <div class="stats"><span>Temas dominados <b id="stDom">0/0</b></span><span>Herramientas <b>%d</b></span><span>Temas <b>%d</b></span></div>\n  <details class="temario"><summary>Temario de la %s</summary><ol>%s</ol><p class="gu">Guías para practicar: %s</p></details>\n</div>\n' % (
        C_.ART, "Examen" if C_.ID == "EX" else C_.ID, esc(C_.NOMBRE), esc(C_.NOMBRE), "Examen" if C_.ID == "EX" else "Interrogación " + C_.ID[1], m(C_.LEAD), ntools, n, "prueba" if C_.ID == "EX" else C_.ID, temario, C_.GUIAS_B)
    out += '<nav class="bar" aria-label="Temas"><div class="wrap tiles" role="tablist">' + tiles + "</div></nav>\n<main class=\"wrap\">\n" + "".join(panels) + "\n</main>\n"
    out += '<footer class="wrap"><p>Basado en Stewart, Redlin y Watson, <i>Precálculo: matemáticas para el cálculo</i>, %s.</p><p class="tz-lic"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.5l2.6 6.3 6.8.5-5.2 4.4 1.6 6.6L12 16.8l-5.8 3.5 1.6-6.6-5.2-4.4 6.8-.5z" fill="currentColor"/></svg>Material exclusivo del Plan Precálculo de TS Zenit · Uso personal de {{LIC}} · Prohibida su copia o distribución.</p></footer>\n' % C_.CAPS
    out += "<script>" + open(D + "/ap_core.js").read() + open(D + "/tools.js").read() + "\n})();\n</script>\n<script>" + open(D + "/ap_page.js").read().replace("{{PFX}}", pfx) + "</script>\n</body></html>"
    return out, ntools

CSS_AP_EXTRA = """<style>
.fig{margin:0;display:grid;gap:.4rem;justify-items:center}.fig svg{max-width:100%;height:auto}.fig figcaption{font-size:.85rem;color:var(--muted);text-align:center}
.tbl td,.tbl th{white-space:normal}
.pasos li{margin:.25rem 0}
.tool .eq{display:block;text-align:center;line-height:1.7}
.sub>.tw .tbl td{font:400 .95rem/1.45 var(--body)}
.sub>.tw .tbl th{white-space:nowrap}
</style>"""

# ---------------- SL: slides ----------------
def build_sl(C_):
    secs = []
    secs.append('<section class="s cover" data-t="Portada">\n  <div class="art" aria-hidden="true">%s</div>\n  <div class="in"><p class="k">Plan Precálculo · %s</p><h1>%s<em>Lo esencial, en %d slides</em></h1><p class="lead">%s</p><div class="chips">%s</div></div>\n</section>' % (
        C_.ART, "Examen" if C_.ID == "EX" else "Interrogación " + C_.ID[1], esc(C_.NOMBRE), len(C_.SLIDES) + 2, m(C_.LEAD), "".join('<span class="chip">' + c + "</span>" for c in C_.CHIPS)))
    # panorama
    cards = "".join('<div class="card%s"><span class=n>%d</span><h3>%s</h3><p>%s</p></div>' % (" a" if i == len(C_.TEMAS) - 1 else "", i + 1, esc(t["nm"]), m(t["intro"])) for i, t in enumerate(C_.TEMAS))
    nc = 4 if len(C_.TEMAS) > 6 else 2 if len(C_.TEMAS) == 4 else 3
    secs.append('<section class="s" data-t="Qué entra">\n  <div class="in"><p class="k">Panorama</p><h2>Qué entra en %s</h2><div class="cols" style="--c:%d">%s</div></div>\n</section>' % ("el examen" if C_.ID == "EX" else "la " + C_.ID, nc, cards))
    for s in C_.SLIDES:
        body = ""
        if s["fx"]: body += '<div class="fx"><span>' + md(s["fx"]) + "</span>" + (("<small>" + m(s["small"]) + "</small>") if s["small"] else "") + "</div>"
        if s["tbl"]:
            hd, rows = s["tbl"]; body += '<div class="tw"><table><thead><tr>' + "".join("<th>" + m(x) + "</th>" for x in hd) + "</tr></thead><tbody>" + "".join("<tr>" + "".join("<td>" + m(c) + "</td>" for c in r) + "</tr>" for r in rows) + "</tbody></table></div>"
        if s["cards"]:
            nc = s["cols"] or min(3, len(s["cards"]))
            body += '<div class="cols" style="--c:%d">' % nc + "".join('<div class="card%s">%s<h3>%s</h3><p>%s</p></div>' % (" a" if c["a"] else "", ("<span class=n>%s</span>" % c["n"]) if c["n"] else "", m(c["h"]), m(c["p"])) for c in s["cards"]) + "</div>"
        if s["box"]:
            kind, lab, txt = s["box"]; body += '<div class="box %s"><p class="k">%s</p><p>%s</p></div>' % (kind, lab, m(txt))
        secs.append('<section class="s" data-t="%s">\n  <div class="in"><p class="k">%s</p><h2>%s</h2>%s</div>\n</section>' % (html.escape(re.sub(r"\$", "", s["t"])), esc(s["k"]), m(s["t"]), body))
    pre = open(D + "/sl_pre.html").read().replace("<title>I1 · Límites · Slides Cálculo 1 · TS Zenit</title>", "<title>%s · %s · Slides Precálculo · TS Zenit</title>" % ("Examen" if C_.ID == "EX" else C_.ID, C_.NOMBRE)).replace("· Slides I1 · Límites", "· Slides %s · %s" % ("Examen" if C_.ID == "EX" else C_.ID, C_.NOMBRE))
    post = open(D + "/sl_post.html").read().replace("Plan Cálculo 1", "Plan Precálculo").replace("Índice · I1 · Límites", "Índice · %s · %s" % ("Examen" if C_.ID == "EX" else C_.ID, C_.NOMBRE))
    return pre + "\n" + "\n".join(secs) + "\n" + post, len(secs)

# ---------------- AM: apuntes a mano ----------------
def am_block(b):
    k = b[0]
    if k == "p": return "<p>" + m(b[1]) + "</p>"
    if k == "eq": return '<div class="fx">' + md(b[1]) + (('<div class="fxs">' + m(b[2]) + "</div>") if b[2] else "") + "</div>"
    if k == "mini": return '<div class="grid g2">' + "".join('<div class="card"><h5>' + m(t) + "</h5><p>" + m(h) + "</p></div>" for t, h in b[1]) + "</div>"
    if k == "tbl": return "<table><thead><tr>" + "".join("<th>" + m(x) + "</th>" for x in b[1]) + "</tr></thead><tbody>" + "".join("<tr>" + "".join("<td>" + m(c) + "</td>" for c in r) + "</tr>" for r in b[2]) + "</tbody></table>"
    if k == "ul": return '<ul class="l">' + "".join("<li>" + m(x) + "</li>" for x in b[1]) + "</ul>"
    if k == "ex":
        _, q, steps, ans, tipo, tit = b
        t = (tit or "Pregunta tipo prueba") if tipo else "Ejemplo resuelto"
        body = "<ol>" + "".join("<li>" + m(s) + "</li>" for s in steps) + "</ol>" if len(steps) > 1 else "<p>" + m(steps[0]) + "</p>"
        return '<div class="ej"><span class="t">' + t + "</span><p>" + m(q) + "</p>" + body + (("<p><b>Respuesta:</b> <span class=\"r\">" + m(ans) + "</span></p>") if ans else "") + "</div>"
    if k == "note":
        if b[1] == "trap": return '<div class="box trampa"><span class="t">Ojo</span>' + m(b[2]) + "</div>"
        return '<div class="box regla"><span class="t">' + (b[3] if len(b) > 3 else "Idea clave") + "</span>" + m(b[2]) + "</div>"
    if k == "tool": return ""
    if k == "fig": return '<figure class="fig">' + b[1] + (("<figcaption>" + m(b[2]) + "</figcaption>") if b[2] else "") + "</figure>"
    raise ValueError(k)

PAL = [("#0f7a6c", "#eef7f5"), ("#6b3fd1", "#f3effc"), ("#c2461b", "#fcf1ec"), ("#a07a10", "#fbf6e7"), ("#1f5fa8", "#edf3fb"), ("#b0306a", "#fbeef4")]
def build_am(C_):
    letters = "ABCDEFGH"
    toc, units = [], []
    nej = 0
    for i, t in enumerate(C_.TEMAS):
        c, cl = PAL[i % len(PAL)]; L = letters[i]
        toc.append('<div class="u" style="--c:%s"><h3 style="color:%s">%s</h3><ul>%s%s</ul></div>' % (c, c, esc(t["t"]), "".join("<li><span>%s.%d</span>%s</li>" % (L, j + 1, re.sub(r"\$", "", s["t"])) for j, s in enumerate(t["subs"])), ("<li><span>%s.✓</span>Repaso rápido</li>" % L) if t["rep"] else ""))
        secs = []
        for j, s in enumerate(t["subs"]):
            nej += sum(1 for b in s["b"] if b[0] == "ex")
            secs.append('<section class="sec"><h3><span class="n">%s.%d</span>%s</h3>%s</section>' % (L, j + 1, m(s["t"]), "".join(am_block(b) for b in s["b"])))
        if t["rep"]:
            secs.append('<section class="sec"><h3><span class="n">%s.✓</span>Repaso rápido: %s</h3><p style="color:var(--soft)">Preguntas típicas de la prueba, con su respuesta.</p><div class="qa">%s</div></section>' % (L, esc(t["nm"]), "".join('<div class="card"><p>' + m(q) + '</p><p class="ans">' + m(a) + "</p></div>" for q, a in t["rep"])))
        units.append('<div class="unidad" style="--c:%s;--cl:%s"><div class="mono">TEMA %d · %s</div><h2>%s</h2><div class="preg">%s</div>%s</div>' % (c, cl, i + 1, "EXAMEN" if C_.ID == "EX" else C_.ID, esc(t["t"]), m(t["preg"]), "".join(secs)))
    pre = open(D + "/am_pre.html").read().replace("<title>Matemática M1 · Apuntes a mano · TS Zenit</title>", "<title>%s · %s · Apuntes a mano · Precálculo · TS Zenit</title>" % ("Examen" if C_.ID == "EX" else C_.ID, C_.NOMBRE))
    pre = pre.replace("</style></head>", CSS_AM_EXTRA + "</style></head>")
    body = '<main class="hoja"><div class="mono">PRECÁLCULO · %s · STEWART</div><h1 class="tit">Mis apuntes de <mark>%s</mark></h1><div class="uso"><h4>Cómo usar estos apuntes</h4><p>%s Cada tema trae definiciones, fórmulas, <b>ejemplos resueltos paso a paso</b>, los <b>errores que más puntos restan</b> y preguntas tipo prueba. Las respuestas aparecen en <span class="ans" style="font-size:16px">cursiva de color</span>. Al final de cada tema hay un <b>repaso rápido</b>.</p></div><div class="toc">%s</div>%s</main>\n<div class="pie">TS Zenit · Precálculo · %s · Apuntes a mano · Uso personal de {{LIC}}</div>\n</body></html>' % (
        "EXAMEN" if C_.ID == "EX" else "INTERROGACIÓN " + C_.ID[1], esc(C_.NOMBRE), m(C_.LEAD), "".join(toc), "".join(units), "Examen" if C_.ID == "EX" else C_.ID)
    return pre + body, nej

CSS_AM_EXTRA = """
.fx math{font-size:1.12em}.fx .fxs{font-family:Lora;font-size:13px;color:var(--soft);margin-top:2px}
.sec math{font-family:"STIX Two Math","Cambria Math","Latin Modern Math",math;color:var(--ink)}
.r math,.ans math{color:var(--c)}
"""

# ---------------- KaTeX ----------------
def katexify(htm):
    r = subprocess.run(["node", D + "/katexify.js"], input=htm.encode(), capture_output=True)
    if r.returncode: raise SystemExit(r.stderr.decode())
    sys.stderr.write(r.stderr.decode())
    return r.stdout.decode()

if __name__ == "__main__":
    for ID in sys.argv[1:]:
        C_ = importlib.import_module("c_" + ID.lower())
        ap, nt = build_ap(C_); sl, ns = build_sl(C_); am, ne = build_am(C_)
        for kind, h in (("AP", ap), ("SL", sl), ("AM", am)):
            out = katexify(h)
            assert "⟦" not in out and "⟪" not in out
            open(D + "/out/PRE-%s-%s.html" % (ID, kind), "w").write(out)
        print(ID, "herramientas:", nt, "· slides:", ns, "· ejemplos:", ne, "· temas:", len(C_.TEMAS))
