#!/usr/bin/env python3
"""TS Zenit — generador de ensayos PAES imprimibles.

Uso:
  python3 gen_paes.py spec.json salida/

Siempre genera  salida/Soluciones-<codigo>.pdf  (una pregunta por página).
Con "carpeta_soluciones" genera salida/web/<codigo>/pNN-<hash>.pdf (un PDF por pregunta, para
publicar) y salida/<codigo>.pdf con un QR por pregunta apuntando a su PDF.
Con "url_soluciones" (enlace único, p. ej. Drive) los QR apuntan a <enlace>#page=K.

Matemáticas: LaTeX entre \\( ... \\) (en línea) o \\[ ... \\] (destacado). El signo $ queda libre para pesos.
Dependencias: matplotlib, reportlab (QR), playwright (Chromium), pypdfium2, pypdf; opencv opcional (verificación).
"""
import hashlib, html, json, math, re, sys, pathlib, os, secrets
# Sal secreta de los nombres de los PDF de solución: nunca se escribe en el repositorio.
# Sin TSZ_SAL, cada ejecución usa una sal aleatoria (los nombres cambian, pero el QR y el archivo siempre coinciden).
SAL = os.environ.get("TSZ_SAL") or secrets.token_hex(16)
from collections import Counter

LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 100" role="img" aria-label="TS Zenit"><g><path d="M10 86 A44 44 0 0 1 98 86" fill="none" stroke="#1B1F5E" stroke-width="6"/><rect x="33" y="70" width="9" height="16" rx="1.5" fill="#6C74C9"/><rect x="49.5" y="60" width="9" height="26" rx="1.5" fill="#3E4596"/><rect x="66" y="56" width="9" height="30" rx="1.5" fill="#1B1F5E"/><path d="M54 4 L58.6 19.4 L74 24 L58.6 28.6 L54 44 L49.4 28.6 L34 24 L49.4 19.4 Z" fill="#F5A524"/><rect x="2" y="86" width="104" height="4.5" rx="2.2" fill="#1B1F5E"/></g><text x="122" y="61" font-family="Poppins, Montserrat, 'TeX Gyre Adventor', 'DejaVu Sans', sans-serif" font-size="46" letter-spacing="2.5" fill="#1B1F5E"><tspan font-weight="500">TS</tspan><tspan font-weight="700" dx="10">ZENIT</tspan></text><text x="124" y="87" font-family="Poppins, Montserrat, 'TeX Gyre Adventor', 'DejaVu Sans', sans-serif" font-weight="600" font-size="14.5" letter-spacing="5.0" fill="#E08E0B">HAZLO REALIDAD</text></svg>"""

MARCA = "TS ZENIT · Hazlo realidad"
PRUEBAS = {
    "M1": "Competencia Matemática 1 (M1)",
    "M2": "Competencia Matemática 2 (M2)",
    "CIENCIAS": "Ciencias",
    "BIOLOGIA": "Ciencias · Biología",
    "QUIMICA": "Ciencias · Química",
    "FISICA": "Ciencias · Física",
}
LETRAS = "ABCDE"

# ---------- LaTeX -> SVG vectorial (matplotlib mathtext, sin red) ----------
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["mathtext.fontset"] = "cm"
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path as MPath

_FP = FontProperties(family="DejaVu Serif", size=10)

_TEX_SUBS = [(r"\\tfrac", r"\\frac"), (r"\\dfrac", r"\\frac"), (r"\\text\{", r"\\mathrm{"), (r"\\operatorname\{", r"\\mathrm{"),
             (r"\\left|\\right", ""), (r"\\,|\\;|\\!", r"\\ "), (r"\\le\b", r"\\leq"), (r"\\ge\b", r"\\geq")]

def _textpath(tex, size):
    try:
        return TextPath((0, 0), f"${tex}$", size=size, prop=_FP)
    except Exception:
        t2 = tex
        for a, b in _TEX_SUBS:
            t2 = re.sub(a, b, t2)
        return TextPath((0, 0), f"${t2}$", size=size, prop=_FP)

def tex_svg(tex, display=False, scale=1.0):
    size = 10.0
    try:
        tp = _textpath(tex, size)
    except Exception:
        print(f"AVISO LaTeX no soportado, se muestra como texto: {tex}", file=sys.stderr)
        return f'<code class="tex-err">{html.escape(tex)}</code>'

    ext = tp.get_extents()
    pad = 0.6
    x0, x1 = min(0, ext.x0) - pad, ext.x1 + pad
    y0, y1 = min(ext.y0, -2.2) - pad, max(ext.y1, 7.2) + pad
    d, verts, codes = [], tp.vertices, tp.codes
    i = 0
    while i < len(verts):
        c = codes[i]
        if c == MPath.MOVETO:
            d.append(f"M{verts[i][0]:.2f} {-verts[i][1]:.2f}"); i += 1
        elif c == MPath.LINETO:
            d.append(f"L{verts[i][0]:.2f} {-verts[i][1]:.2f}"); i += 1
        elif c == MPath.CURVE3:
            d.append(f"Q{verts[i][0]:.2f} {-verts[i][1]:.2f} {verts[i+1][0]:.2f} {-verts[i+1][1]:.2f}"); i += 2
        elif c == MPath.CURVE4:
            d.append("C" + " ".join(f"{verts[i+k][0]:.2f} {-verts[i+k][1]:.2f}" for k in range(3))); i += 3
        elif c == MPath.CLOSEPOLY:
            d.append("Z"); i += 1
        else:
            i += 1
    w, h = x1 - x0, y1 - y0
    em = 1.0 / size * 1.12 * scale
    style = f"width:{w*em:.3f}em;height:{h*em:.3f}em;vertical-align:{y0*em:.3f}em"
    svg = (f'<svg class="tex" xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.2f} {-y1:.2f} {w:.2f} {h:.2f}" '
           f'style="{style}" role="img" aria-label="{html.escape(tex)}"><path d="{"".join(d)}" fill="currentColor"/></svg>')
    return f'<div class="texd">{svg}</div>' if display else svg

def render_math(s):
    if not s:
        return ""
    s = re.sub(r"\\\[(.+?)\\\]", lambda m: tex_svg(m.group(1).strip(), True, 1.15), s, flags=re.S)
    s = re.sub(r"\\\((.+?)\\\)", lambda m: tex_svg(m.group(1).strip()), s, flags=re.S)
    return s

# ---------- QR (reportlab, sin red) ----------
def qr_matrix(url):
    from reportlab.graphics.barcode import qrencoder
    q = qrencoder.QRCode(None, qrencoder.QRErrorCorrectLevel.M)
    q.addData(url); q.make()
    return [[bool(v) for v in row] for row in q.modules]

def qr_svg(url):
    m = qr_matrix(url); n = len(m); b = 4
    rects = []
    for r in range(n):
        c = 0
        while c < n:
            if m[r][c]:
                s = c
                while c < n and m[r][c]:
                    c += 1
                rects.append(f"M{s+b} {r+b}h{c-s}v1h{-(c-s)}z")
            else:
                c += 1
    t = n + 2 * b
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {t} {t}" shape-rendering="crispEdges">'
            f'<rect width="{t}" height="{t}" fill="#fff"/><path d="{"".join(rects)}" fill="#000"/></svg>')

# ---------- helpers ----------
def esc(s):
    return html.escape(str(s or ""))

def alt_layout(alts):
    # Formato PAES: siempre una alternativa debajo de la otra (A, B, C, D en una columna).
    tall = " tall" if any(("frac" in a) or ("sqrt" in a) or ("<svg" in a) for a in alts) else ""
    return "alts" + tall

def page_url(base, page):
    return f"{base.split('#')[0]}#page={page}"

def nombre_prueba(spec):
    return PRUEBAS.get(spec["prueba"].upper(), spec["prueba"])

def codigo(spec):
    return spec.get("codigo") or "ensayo"

# ---------- CSS de impresión (común) ----------
BASE_CSS = r"""
@page { size: Letter; margin: 16mm 17mm 18mm 17mm; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin: 0; background: #fff; color: #111; font-family: 'Source Serif 4', Lora, 'TeX Gyre Pagella', 'DejaVu Serif', serif; font-size: 10.6pt; line-height: 1.42; }
header.portada { display: grid; grid-template-columns: 64mm 1fr; gap: 8mm; align-items: center; padding-bottom: 4mm; border-bottom: 2.2pt solid #1B1F5E; }
header.portada svg { width: 64mm; height: auto; display: block; }
.meta { text-align: right; }
.meta .prueba { font: 600 8.5pt Poppins, 'DejaVu Sans', sans-serif; letter-spacing: .14em; text-transform: uppercase; color: #E08E0B; }
.meta h1 { font: 700 17pt/1.15 Poppins, 'DejaVu Sans', sans-serif; color: #1B1F5E; margin: 1mm 0 1.2mm; }
.meta .det { font: 400 8.6pt Poppins, 'DejaVu Sans', sans-serif; color: #444; }
.mini { display: grid; grid-template-columns: 42mm 1fr; align-items: end; border-bottom: 1.2pt solid #1B1F5E; padding-bottom: 2.5mm; margin-bottom: 4mm; }
.mini svg { width: 42mm; height: auto; }
.mini div { text-align: right; font: 400 8.4pt Poppins, 'DejaVu Sans', sans-serif; color: #444; }
.pagebreak { break-before: page; }
.alts { list-style: none; margin: 1.8mm 0 0; padding: 0; display: grid; grid-template-columns: 1fr; gap: 1.6mm; }
.alts.tall { row-gap: 3.2mm; }
.alts.g2 { grid-template-columns: 1fr 1fr; column-gap: 6mm; }
.alts.g4 { grid-template-columns: repeat(4, 1fr); column-gap: 4mm; }
.alts li { display: grid; grid-template-columns: 6.5mm 1fr; align-items: center; }
.alts li b { font-family: Poppins, 'DejaVu Sans', sans-serif; font-weight: 600; }
table.enun { border-collapse: collapse; margin: 1.5mm 0; font-size: 9.4pt; }
table.enun td, table.enun th { border: .6pt solid #333; padding: 1mm 2.5mm; text-align: center; }
.texd { text-align: center; margin: 1.5mm 0; }
svg.tex { display: inline-block; overflow: visible; }
.fig { margin: 1.5mm 0 2mm; text-align: center; }
.fig svg, .fig img { max-width: 100%; height: auto; }
.fuente { font: italic 7.6pt 'DejaVu Sans', sans-serif; color: #555; margin-top: 1.2mm; }
h2.sec { font: 700 13pt Poppins, 'DejaVu Sans', sans-serif; color: #1B1F5E; margin: 0 0 3mm; }
"""

ENSAYO_CSS = r"""
.instr { margin: 4.5mm 0 3mm; border: .8pt solid #1B1F5E; padding: 3mm 4mm; font-size: 9.2pt; }
.instr b.t { font: 600 8.6pt Poppins, 'DejaVu Sans', sans-serif; letter-spacing: .1em; text-transform: uppercase; color: #1B1F5E; display: block; margin-bottom: 1mm; }
.instr ol { margin: 0; padding-left: 5mm; }
.repaso { margin: 0 0 3mm; border: .8pt solid #E08E0B; background: #FFF6E6; padding: 3mm 4mm; font-size: 9.6pt; break-inside: avoid; }
.repaso b.t { font: 600 8.6pt Poppins, 'DejaVu Sans', sans-serif; letter-spacing: .1em; text-transform: uppercase; color: #E08E0B; display: block; margin-bottom: 1mm; }
.repaso p { margin: 0 0 1.4mm; }
.diag { margin: 4mm 0 0; }
.dtop { display: grid; grid-template-columns: 52mm 1fr; gap: 6mm; align-items: center; margin-bottom: 3mm; }
.score { border: 1pt solid #1B1F5E; padding: 3mm 4mm; text-align: center; }
.score b { display: block; font: 700 20pt Poppins, 'DejaVu Sans', sans-serif; color: #1B1F5E; }
.score span { font: 8.4pt 'DejaVu Sans', sans-serif; color: #444; }
table.dejes { width: 100%; border-collapse: collapse; font: 8.8pt 'DejaVu Sans', sans-serif; }
table.dejes td { padding: 1.2mm 2mm; border-bottom: .4pt solid #ccc; }
table.dejes td.bar { width: 45%; }
table.dejes td.bar i { display: block; height: 3mm; background: #E08E0B; border-radius: 1mm; min-width: 1mm; }
table.dejes td.c, table.derr td.c { text-align: center; font-weight: 700; white-space: nowrap; }
.dcom { font-size: 10pt; margin: 2mm 0 3mm; }
h3.dh { font: 600 8.6pt Poppins, 'DejaVu Sans', sans-serif; letter-spacing: .1em; text-transform: uppercase; color: #E08E0B; margin: 4mm 0 2mm; }
table.derr { width: 100%; border-collapse: collapse; font: 8.8pt/1.35 'DejaVu Sans', sans-serif; }
table.derr th { background: #1B1F5E; color: #fff; font: 600 8pt Poppins, 'DejaVu Sans', sans-serif; text-align: left; padding: 1.4mm 2mm; }
table.derr td { border-bottom: .4pt solid #bbb; padding: 1.4mm 2mm; vertical-align: top; }
table.derr tr { break-inside: avoid; }
ol.dpri { margin: 0; padding-left: 5mm; font-size: 10pt; }
.ficha { display: grid; grid-template-columns: 1fr 1fr; gap: 1.6mm 6mm; margin: 4mm 0 0; padding: 3mm 4mm; border: .7pt solid #1B1F5E; font-size: 9.4pt; }
.ficha div { display: grid; grid-template-columns: 30mm 1fr; }
.ficha div:first-child { grid-column: 1 / -1; }
.ficha b { font: 600 8.2pt Poppins, 'DejaVu Sans', sans-serif; color: #1B1F5E; text-transform: uppercase; letter-spacing: .06em; }
section.bq, h2.bt, .prop { break-after: avoid; page-break-after: avoid; }
h2.bt { font: 700 12.5pt Poppins, 'DejaVu Sans', sans-serif; color: #1B1F5E; margin: 6mm 0 1.5mm; padding-bottom: 1.2mm; border-bottom: 1pt solid #E08E0B; }
.prop { font-size: 9.6pt; color: #444; font-style: italic; margin: 0 0 1mm; }
section.texto p { margin: 0 0 1.6mm; }
.ejemplo { border: .7pt solid #ccd; padding: 0 4mm 3mm; margin: 2mm 0; break-inside: avoid; }
.ejemplo .enun { margin: 1mm 0 2mm; }
.ejx { font-size: 9.6pt; margin: 1.6mm 0 0; }
.lista ul, .lista ol { margin: 1mm 0; padding-left: 6mm; }
.lista.checklist ul { list-style: none; padding-left: 0; }
.lista.checklist li::before { content: "☐  "; font-size: 11pt; }
.lista li { margin: 0 0 1.4mm; }
.q .tag { font: 600 6.4pt Poppins, 'DejaVu Sans', sans-serif; color: #E08E0B; letter-spacing: .04em; margin-top: 1mm; text-transform: uppercase; }
.datos { margin: 0 0 2mm; border: .6pt dashed #777; padding: 2mm 4mm; font-size: 9pt; }
.q { display: grid; grid-template-columns: 9mm 1fr 21mm; column-gap: 3mm; padding: 3.6mm 0 3.8mm; border-bottom: .4pt solid #bbb; break-inside: avoid; }
.q .num { font: 700 11pt Poppins, 'DejaVu Sans', sans-serif; color: #1B1F5E; }
.q .body { min-width: 0; }
.q .body p { margin: 0 0 1.6mm; }
.qr { text-align: center; padding-top: .5mm; }
.qr svg { width: 19mm; height: 19mm; display: block; margin: 0 auto; }
.qr span { display: block; font: 600 6.2pt/1.25 Poppins, 'DejaVu Sans', sans-serif; letter-spacing: .05em; text-transform: uppercase; color: #1B1F5E; margin-top: .6mm; }
.fin { text-align: center; font: 600 9pt Poppins, 'DejaVu Sans', sans-serif; letter-spacing: .2em; margin-top: 6mm; color: #1B1F5E; }
h2.solu { font-family: 'TeX Gyre Chorus', 'URW Chancery L', 'Z003', cursive; font-weight: 400; font-size: 46pt; text-align: center; margin: 2mm 0 6mm; color: #000; line-height: 1; }
table.clav { width: 82%; margin: 0 auto; border-collapse: collapse; table-layout: fixed; }
table.clav td { border: .9pt solid #000; text-align: center; font-family: 'TeX Gyre Chorus', 'URW Chancery L', 'Z003', cursive; font-size: 21pt; line-height: 1; padding: 0; }
table.clav td.vacia { border: none; }
table.pauta { width: 100%; border-collapse: collapse; font: 8.6pt/1.3 'DejaVu Sans', sans-serif; }
table.pauta th { background: #1B1F5E; color: #fff; font: 600 8pt Poppins, 'DejaVu Sans', sans-serif; letter-spacing: .04em; text-align: left; padding: 1.6mm 2mm; }
table.pauta td { border-bottom: .4pt solid #bbb; padding: 1.3mm 2mm; vertical-align: top; }
table.pauta td.c { text-align: center; font-weight: 700; }
table.pauta tr { break-inside: avoid; }
.resumen { display: grid; grid-template-columns: repeat(auto-fit, minmax(38mm, 1fr)); gap: 3mm; margin: 0 0 5mm; }
.resumen div { border: .7pt solid #1B1F5E; padding: 2mm 3mm; font: 8.4pt 'DejaVu Sans', sans-serif; }
.resumen b { display: block; font: 700 15pt Poppins, 'DejaVu Sans', sans-serif; color: #1B1F5E; }
.hoja { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.2mm 6mm; font: 9pt Poppins, 'DejaVu Sans', sans-serif; }
.hoja div { display: flex; align-items: center; gap: 1.6mm; }
.hoja div b { width: 7mm; text-align: right; }
.hoja i { width: 4.6mm; height: 4.6mm; border: .8pt solid #000; border-radius: 50%; display: inline-grid; place-items: center; font: normal 6.2pt Poppins, 'DejaVu Sans', sans-serif; }
.campos { display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 5mm; margin-bottom: 5mm; font: 9pt Poppins, 'DejaVu Sans', sans-serif; }
.campos span { border-bottom: .8pt solid #000; padding-bottom: 5mm; display: block; }
"""

SOL_CSS = r"""
.sol + .sol { break-before: page; }
.solh { display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1.4pt solid #1B1F5E; padding-bottom: 2mm; margin-bottom: 3.5mm; }
.solh h2 { font: 700 14pt Poppins, 'DejaVu Sans', sans-serif; color: #1B1F5E; margin: 0; }
.solh span { font: 500 8.2pt Poppins, 'DejaVu Sans', sans-serif; color: #555; text-transform: uppercase; letter-spacing: .06em; text-align: right; }
.enun p { margin: 0 0 1.6mm; }
.alts li.ok { outline: 1pt solid #1F7A4D; background: #E7F4EC; border-radius: 1.2mm; padding: .6mm 1mm; }
.alts li.ok b { color: #1F7A4D; }
.clave { margin: 4mm 0 1mm; font: 700 10.5pt Poppins, 'DejaVu Sans', sans-serif; color: #1F7A4D; }
h3 { font: 600 8.4pt Poppins, 'DejaVu Sans', sans-serif; letter-spacing: .12em; text-transform: uppercase; color: #E08E0B; margin: 5mm 0 2mm; }
ol.pasos { list-style: none; margin: 0; padding: 0; counter-reset: p; display: grid; gap: 2.6mm; }
ol.pasos li { counter-increment: p; display: grid; grid-template-columns: 8mm 1fr; break-inside: avoid; }
ol.pasos li::before { content: counter(p); width: 5.6mm; height: 5.6mm; border-radius: 50%; background: #1B1F5E; color: #fff; font: 700 8pt Poppins, 'DejaVu Sans', sans-serif; display: grid; place-items: center; margin-top: .4mm; }
ol.pasos strong { font: 600 9.8pt Poppins, 'DejaVu Sans', sans-serif; color: #1B1F5E; }
ul.dis { list-style: none; margin: 0; padding: 0; display: grid; gap: 1.6mm; }
ul.dis li { display: grid; grid-template-columns: 8mm 1fr; break-inside: avoid; }
ul.dis b { font: 700 9.6pt Poppins, 'DejaVu Sans', sans-serif; color: #A3352B; }
.idea { margin-top: 5mm; border: .8pt solid #E08E0B; background: #FFF6E6; padding: 3mm 4mm; break-inside: avoid; }
.idea strong { font: 700 9.4pt Poppins, 'DejaVu Sans', sans-serif; color: #1B1F5E; }
"""

FOOTER = ('<div style="width:100%;font:7pt DejaVu Sans,sans-serif;color:#555;padding:0 17mm;display:flex;justify-content:space-between">'
          '<span>{left}</span><span>{code}Página <span class="pageNumber"></span> de <span class="totalPages"></span></span></div>')

def doc_html(css, body):
    return f'<!doctype html><html lang="es"><head><meta charset="utf-8"><style>{BASE_CSS}{css}</style></head><body>{body}</body></html>'

def render_pdf(doc, pdf_path, spec, left, title):
    from playwright.sync_api import sync_playwright
    code = esc(codigo(spec)) + " · "
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page()
        pg.set_content(doc, wait_until="load")
        pg.pdf(path=str(pdf_path), format="Letter", print_background=True, prefer_css_page_size=True,
               display_header_footer=True, header_template="<span></span>",
               footer_template=FOOTER.replace("{left}", left).replace("{code}", code))
        b.close()
    # Metadatos del PDF con la marca
    from pypdf import PdfReader, PdfWriter
    w = PdfWriter(clone_from=PdfReader(str(pdf_path)))
    w.add_metadata({"/Title": title, "/Author": "TS Zenit", "/Creator": "TS Zenit", "/Producer": "TS Zenit",
                    "/Subject": f"{nombre_prueba(spec)} · {MARCA}"})
    with open(pdf_path, "wb") as f:
        w.write(f)

def header(spec, det):
    return (f'<header class="portada">{LOGO_SVG}<div class="meta"><div class="prueba">{esc(nombre_prueba(spec))}</div>'
            f'<h1>{esc(spec["titulo"])}</h1><div class="det">{det}</div></div></header>')

def mini(spec, extra=""):
    return f'<div class="mini">{LOGO_SVG}<div>{esc(spec["titulo"])}{extra}<br>{esc(nombre_prueba(spec))}</div></div>'

def alts_html(q, marcar=False):
    items = "".join(f'<li class="{"ok" if marcar and LETRAS[i]==q["clave"] else ""}"><b>{LETRAS[i]})</b><span>{render_math(a)}</span></li>'
                    for i, a in enumerate(q["alternativas"]))
    return f'<ol class="{alt_layout(q["alternativas"])}">{items}</ol>'

# ---------- Retroalimentación (guías de refuerzo) ----------
def diagnostico_html(d):
    filas = "".join(
        f'<tr><td>{esc(e["eje"])}</td><td class="bar"><i style="width:{100*e["correctas"]/max(e["total"],1):.0f}%"></i></td>'
        f'<td class="c">{e["correctas"]}/{e["total"]}</td></tr>' for e in d.get("por_eje", []))
    errores = "".join(
        f'<tr><td class="c">{e["n"]}</td><td class="c">{esc(e.get("marco") or "—")}</td><td class="c">{esc(e["clave"])}</td>'
        f'<td>{render_math(e.get("diagnostico",""))}</td></tr>' for e in d.get("errores", []))
    prior = "".join(f"<li>{render_math(p)}</li>" for p in d.get("prioridades", []))
    quien = " · ".join(x for x in [esc(d.get("alumno")), ("Guía " + esc(d["guia_origen"])) if d.get("guia_origen") else ""] if x)
    return (f'<section class="diag"><h2 class="sec">Retroalimentación</h2>'
            f'<div class="dtop"><div class="score"><b>{esc(d.get("puntaje",""))}</b><span>{quien}</span></div>'
            f'<table class="dejes"><tbody>{filas}</tbody></table></div>'
            + (f'<p class="dcom">{render_math(d["comentario"])}</p>' if d.get("comentario") else "")
            + (f'<h3 class="dh">Tus errores, uno por uno</h3><table class="derr"><thead><tr><th>N°</th><th>Marcaste</th><th>Correcta</th>'
               f'<th>Qué pasó y cómo corregirlo</th></tr></thead><tbody>{errores}</tbody></table>' if errores else "")
            + (f'<h3 class="dh">Prioridades para esta guía</h3><ol class="dpri">{prior}</ol>' if prior else "")
            + '</section>')

# ---------- Exigencia: dificultad y habilidades PAES ----------
HABILIDADES = {
    "MAT": ["Resolver problemas", "Modelar", "Representar", "Argumentar"],
    "CIE": ["Observar y plantear preguntas", "Planificar y conducir una investigación",
            "Procesar y analizar la evidencia", "Evaluar", "Comunicar"],
}
EX_NOM = {"estandar": "estándar", "avanzada": "avanzada", "refuerzo": "refuerzo"}
DIF_PUNTOS = {"facil": 1, "media": 2, "dificil": 3, "muy_dificil": 4}
# (máx. fácil, mín. difícil + muy difícil, mín. muy difícil, mín. por cada habilidad PAES de matemática)
METAS = {
    ("MAT1", "estandar"): (0.15, 0.35, 0.00, 0.15),
    ("MAT1", "avanzada"): (0.00, 0.60, 0.20, 0.20),
    ("MAT2", "estandar"): (0.10, 0.50, 0.15, 0.20),
    ("MAT2", "avanzada"): (0.00, 0.75, 0.35, 0.20),
    ("CIE", "estandar"): (0.15, 0.35, 0.00, 0.00),
    ("CIE", "avanzada"): (0.00, 0.60, 0.20, 0.00),
    ("refuerzo", ""): (0.00, 0.60, 0.20, 0.15),
}

def _norm(s):
    import unicodedata
    s = "".join(c for c in unicodedata.normalize("NFD", str(s or "")) if unicodedata.category(c) != "Mn")
    return re.sub(r"[\s_]+", " ", s.lower()).strip()

def area(prueba):
    p = str(prueba or "").upper()
    return "MAT1" if p == "M1" else "MAT2" if p == "M2" else "CIE"

def dificultad_norm(d):
    if d in (None, ""):
        return None
    d = _norm(d)
    return {"facil": "facil", "baja": "facil", "media": "media", "intermedia": "media", "dificil": "dificil", "alta": "dificil",
            "muy dificil": "muy_dificil", "muy alta": "muy_dificil"}.get(d, "?")

def habilidades_de(prueba):
    return HABILIDADES["CIE" if area(prueba) == "CIE" else "MAT"]

def habilidad_canonica(h, prueba):
    for c in habilidades_de(prueba):
        if _norm(h) == _norm(c) or _norm(c).startswith(_norm(h) or "\0"):
            return c
    return h or "—"

def nivel_exigencia(spec):
    if any(q.get("debilidad") for q in spec["preguntas"]):
        return "refuerzo"
    return "avanzada" if _norm(spec.get("exigencia")).startswith("avanzad") else "estandar"

def revisar_exigencia(spec):
    """Distribución de dificultad y de habilidades PAES frente a las metas de la sección 3b de la skill."""
    pregs, prueba = spec["preguntas"], spec.get("prueba")
    n, ex, ar = len(pregs), nivel_exigencia(spec), area(prueba)
    mx_f, mn_h, mn_mh, mn_hab = METAS[("refuerzo", "")] if ex == "refuerzo" else METAS[(ar, ex)]
    avisos = []
    difs = Counter(dificultad_norm(q.get("dificultad")) for q in pregs)
    if difs.get(None):
        avisos.append(f"{difs[None]} {'pregunta' if difs[None] == 1 else 'preguntas'} sin 'dificultad' (facil, media, dificil o muy_dificil).")
    if difs.get("?"):
        avisos.append(f"{difs['?']} con una 'dificultad' no reconocida (usa facil, media, dificil o muy_dificil).")
    f, h, mh = difs["facil"], difs["dificil"] + difs["muy_dificil"], difs["muy_dificil"]
    if f > math.floor(mx_f * n + 1e-9):
        avisos.append(f"Demasiadas fáciles para exigencia {EX_NOM[ex]}: {f} de {n} (máximo {math.floor(mx_f * n + 1e-9)}).")
    if h < math.ceil(mn_h * n - 1e-9):
        avisos.append(f"Faltan preguntas difíciles para exigencia {EX_NOM[ex]}: {h} de {n} difíciles o muy difíciles (mínimo {math.ceil(mn_h * n - 1e-9)}).")
    if mh < math.ceil(mn_mh * n - 1e-9):
        avisos.append(f"Faltan muy difíciles para exigencia {EX_NOM[ex]}: {mh} de {n} (mínimo {math.ceil(mn_mh * n - 1e-9)}).")
    habs = Counter(habilidad_canonica(q.get("habilidad"), prueba) for q in pregs)
    if ar != "CIE":
        need = math.ceil(mn_hab * n - 1e-9)
        for hb in HABILIDADES["MAT"]:
            if not habs.get(hb):
                avisos.append(f"Falta la habilidad PAES '{hb}': ninguna pregunta la trabaja.")
            elif habs[hb] < need:
                avisos.append(f"Poca presencia de '{hb}': {habs[hb]} de {n} (mínimo {need}).")
    elif n >= 10 and sum(1 for hb in HABILIDADES["CIE"] if habs.get(hb)) < 3:
        avisos.append("Ciencias: trabaja al menos 3 de las 5 habilidades científicas.")
    resumen = (f"{EX_NOM[ex]} · fácil {f} · media {difs['media']} · difícil {difs['dificil']} · muy difícil {mh} | "
               + " · ".join(f"{k} {v}" for k, v in habs.items()))
    return resumen, avisos

# ---------- 1) PDF de soluciones ----------
def build_solutions_html(spec):
    return doc_html(SOL_CSS, solutions_sections(spec))

def solutions_sections(spec):
    pregs = spec["preguntas"]
    out = []
    for k, q in enumerate(pregs, 1):
        s = q.get("solucion", {})
        fig = f'<div class="fig">{q["figura"]}</div>' if q.get("figura") else ""
        fuente = f'<div class="fuente">{esc(q["fuente"])}</div>' if q.get("fuente") else ""
        pasos = "".join(f'<li><div><strong>{render_math(p.get("t",""))}</strong><div>{render_math(p.get("d",""))}</div></div></li>' for p in s.get("pasos", []))
        dis = "".join(f'<li><b>{L})</b><span>{render_math(t)}</span></li>' for L, t in sorted(s.get("distractores", {}).items()))
        etiqueta = esc(q.get("eje")) + (" · " + esc(q.get("contenido")) if q.get("contenido") else "")
        out.append(f'<section class="sol" id="p{k}">{mini(spec, " · Solucionario")}<div class="solh"><h2>Solución de la pregunta {k}</h2><span>{etiqueta}</span></div>'
                   f'<div class="enun">{render_math(q["enunciado"])}{fig}</div>{alts_html(q, True)}{fuente}'
                   f'<p class="clave">Respuesta correcta: {q["clave"]}</p><h3>Paso a paso</h3><ol class="pasos">{pasos}</ol>'
                   + (f'<h3>¿Por qué no las otras?</h3><ul class="dis">{dis}</ul>' if dis else "")
                   + (f'<div class="idea"><strong>Idea clave.</strong> {render_math(s["idea"])}</div>' if s.get("idea") else "")
                   + '</section>')
    return "".join(out)

def solution_pages(pdf_path, n):
    """Página (1-indexada) donde empieza la solución de cada pregunta."""
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(pdf_path))
    pages = {}
    for i in range(len(doc)):
        txt = doc[i].get_textpage().get_text_range()
        for m in re.finditer(r"Solución\s+de\s+la\s+pregunta\s+(\d+)", txt):
            pages.setdefault(int(m.group(1)), i + 1)
    missing = [k for k in range(1, n + 1) if k not in pages]
    assert not missing, f"No encontré la página de las soluciones: {missing}"
    return pages

# ---------- Bloques de guías de refuerzo ----------
def ficha_html(f):
    filas = [("Objetivo", f.get("objetivo")), ("Habilidades", " · ".join(f.get("habilidades", []))),
             ("Nivel", f.get("nivel")), ("Tiempo estimado", f.get("tiempo"))]
    return '<section class="ficha">' + "".join(f'<div><b>{k}</b><span>{render_math(esc(v) if k != "Objetivo" else v)}</span></div>' for k, v in filas if v) + '</section>'

def bloque_html(b, spec):
    t = b.get("tipo", "texto")
    tit = f'<h2 class="bt">{esc(b.get("titulo",""))}</h2>' if b.get("titulo") else ""
    prop = f'<p class="prop">{render_math(b["proposito"])}</p>' if b.get("proposito") else ""
    brk = ' pagebreak' if b.get("salto") else ''
    if t == "ejemplo":
        pasos = "".join(f'<li><div><strong>{render_math(p.get("t",""))}</strong><div>{render_math(p.get("d",""))}</div></div></li>' for p in b.get("pasos", []))
        extra = "".join(f'<p class="ejx"><b>{lab}.</b> {render_math(b[key])}</p>' for key, lab in
                        [("por_que", "Por qué funciona"), ("errores", "Errores habituales"), ("comprobacion", "Comprobación")] if b.get(key))
        return (f'<section class="ejemplo{brk}">{tit}{prop}<div class="enun">{render_math(b.get("enunciado",""))}</div>'
                f'<ol class="pasos">{pasos}</ol>{extra}</section>')
    if t in ("checklist", "recomendaciones"):
        tag = "ul" if t == "checklist" else "ol"
        items = "".join(f'<li>{render_math(i)}</li>' for i in b.get("items", []))
        return f'<section class="lista {t}{brk}">{tit}{prop}<{tag}>{items}</{tag}></section>'
    if t == "preguntas":
        return f'<section class="bq{brk}">{tit}{prop}</section>'
    return f'<section class="texto{brk}">{tit}{prop}{render_math(b.get("html",""))}</section>'

# ---------- 2) PDF del ensayo ----------
def build_ensayo_html(spec, targets, labels):
    pregs = spec["preguntas"]
    cuentas = sorted({len(q["alternativas"]) for q in pregs})
    n_alt = max(cuentas)
    tiempo = spec.get("tiempo_min")
    det = (f'{len(pregs)} preguntas' + (' · Nivel avanzado' if nivel_exigencia(spec) == 'avanzada' else '')
           + (f' · {tiempo} minutos' if tiempo else '') + f' · Código {esc(codigo(spec))}')
    guia = spec.get("tipo", "ensayo").lower().startswith("gu")
    instr = spec.get("instrucciones") or [
        (f"{'Esta guía' if guia else 'Esta prueba'} consta de {len(pregs)} preguntas. Cada pregunta tiene {n_alt} opciones, señaladas con las letras {', '.join(LETRAS[:n_alt-1])} y {LETRAS[n_alt-1]}, de las cuales solo una es correcta."
         if len(cuentas) == 1 else
         f"{'Esta guía' if guia else 'Esta prueba'} consta de {len(pregs)} preguntas. Hay preguntas de 4 opciones (A, B, C y D) y de 5 opciones (A, B, C, D y E); en cada una, solo una es correcta."),
        "Marca tus respuestas en la hoja de respuestas al final del cuadernillo.",
        "Las figuras que aparecen son solo indicativas.",
        "Cada pregunta tiene un código QR: escanéalo después de responder para ver su solución paso a paso.",
    ]
    out = [header(spec, det)]
    if spec.get("ficha"):
        out.append(ficha_html(spec["ficha"]))
    if spec.get("diagnostico"):
        out.append(diagnostico_html(spec["diagnostico"]))
        out.append(f'<div class="pagebreak">{mini(spec)}</div>')
    out.append('<section class="instr"><b class="t">Instrucciones</b><ol>' + "".join(f"<li>{render_math(i)}</li>" for i in instr) + '</ol></section>')
    if spec.get("repaso"):
        out.append(f'<section class="repaso"><b class="t">Repaso</b>{render_math(spec["repaso"])}</section>')
    if spec.get("datos"):
        out.append(f'<section class="datos">{render_math(spec["datos"])}</section>')
    def pregunta_html(k, q):
        fig = f'<div class="fig">{q["figura"]}</div>' if q.get("figura") else ""
        fuente = f'<div class="fuente">{esc(q["fuente"])}</div>' if q.get("fuente") else ""
        qr = f'<div class="qr">{qr_svg(targets[k])}<span>{labels[k]}</span></div>'
        tag = f'<div class="tag">Nivel {esc(q["nivel"])}</div>' if q.get("nivel") else ""
        return (f'<article class="q"><div class="num">{k}.{tag}</div><div class="body">{render_math(q["enunciado"])}{fig}'
                f'{alts_html(q)}{fuente}</div>{qr}</article>')
    if spec.get("bloques"):
        k = 0
        for b in spec["bloques"]:
            out.append(bloque_html(b, spec))
            if b.get("tipo") == "preguntas":
                for q in b["preguntas"]:
                    k += 1
                    out.append(pregunta_html(k, q))
    else:
        for k, q in enumerate(pregs, 1):
            out.append(pregunta_html(k, q))
    out.append(f'<div class="fin">{"FIN DE LA GUÍA" if guia else "FIN DEL ENSAYO"}</div>')
    for b in spec.get("cierre", []):
        out.append(bloque_html(b, spec))
    if spec.get("hoja_respuestas", True):
        out.append(f'<section class="pagebreak">{mini(spec, " · Código " + esc(codigo(spec)))}<h2 class="sec">Hoja de respuestas</h2>'
                   '<div class="campos"><span>Nombre</span><span>Curso</span><span>Fecha</span></div><div class="hoja">')
        for k in range(1, len(pregs) + 1):
            out.append(f'<div><b>{k}</b>' + "".join(f'<i>{L}</i>' for L in LETRAS[:len(pregs[k-1]["alternativas"])]) + '</div>')
        out.append('</div></section>')
    rows = math.ceil(len(pregs) / 4)
    rh = min(13.0, 205.0 / max(rows, 1))
    out.append(f'<section class="pagebreak">{mini(spec)}<h2 class="solu">Solucionario</h2><table class="clav">')
    for r in range(rows):
        out.append(f'<tr style="height:{rh:.1f}mm">')
        for c in range(4):
            k = c * rows + r + 1
            out.append(f'<td>{k} {pregs[k-1]["clave"]}</td>' if k <= len(pregs) else '<td class="vacia"></td>')
        out.append('</tr>')
    out.append('</table></section>')
    ejes = Counter(q.get("eje", "—") for q in pregs)
    claves = Counter(q["clave"] for q in pregs)
    traz = any(q.get("nivel") or q.get("debilidad") for q in pregs)
    con_dif = any(q.get("dificultad") for q in pregs)
    NOM_DIF = {"facil": "Fácil", "media": "Media", "dificil": "Difícil", "muy_dificil": "Muy difícil"}
    out.append(f'<section class="pagebreak">{mini(spec)}<h2 class="sec">Pauta de corrección</h2><div class="resumen">'
               + "".join(f'<div><b>{v}</b>{esc(e)}</div>' for e, v in ejes.items())
               + f'<div><b>{" · ".join(f"{L}{claves.get(L,0)}" for L in LETRAS[:n_alt])}</b>Distribución de claves</div></div>'
               '<table class="pauta"><thead><tr><th>N°</th><th>Clave</th><th>Eje</th><th>Contenido evaluado</th><th>Habilidad</th>'
               + ('<th>Dificultad</th>' if con_dif else '') + ('<th>Nivel · Debilidad</th>' if traz else '') + '<th>Origen</th></tr></thead><tbody>')
    for k, q in enumerate(pregs, 1):
        nd = " · ".join(x for x in [q.get("nivel", ""), q.get("debilidad", "")] if x)
        out.append(f'<tr><td class="c">{k}</td><td class="c">{q["clave"]}</td><td>{esc(q.get("eje"))}</td>'
                   f'<td>{esc(q.get("contenido"))}</td><td>{esc(q.get("habilidad"))}</td>'
                   + (f'<td>{esc(NOM_DIF.get(dificultad_norm(q.get("dificultad")), q.get("dificultad") or "—"))}</td>' if con_dif else '')
                   + (f'<td>{esc(nd)}</td>' if traz else '') + f'<td>{esc(q.get("origen","Original"))}</td></tr>')
    out.append('</tbody></table></section>')
    if spec.get("incluir_solucionario"):
        out.append(f'<div class="pagebreak"></div>' + solutions_sections(spec))
    return doc_html(ENSAYO_CSS + SOL_CSS, "".join(out))

def snapshots(pdf, outdir, prefijo):
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(pdf))
    for i in range(len(doc)):
        doc[i].render(scale=2.2).to_pil().save(outdir / f"{prefijo}_{i+1:02d}.png")
    return len(doc)

def verify_qr(targets):
    try:
        import cv2, numpy as np
    except Exception:
        return "sin OpenCV: QR no verificados"
    det, bad = cv2.QRCodeDetector(), []
    for k, target in targets.items():
        m = np.array(qr_matrix(target), dtype=np.uint8)
        img = cv2.resize(np.pad((1 - m) * 255, 4, constant_values=255).astype(np.uint8), None, fx=10, fy=10,
                         interpolation=cv2.INTER_NEAREST)
        if det.detectAndDecode(img)[0] != target:
            bad.append(k)
    return f"QR verificados: {len(targets)-len(bad)}/{len(targets)}" + (f" | FALLAN: {bad}" if bad else "")

def main():
    spec_path, outdir = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if spec.get("bloques") and not spec.get("preguntas"):
        spec["preguntas"] = [q for b in spec["bloques"] if b.get("tipo") == "preguntas" for q in b["preguntas"]]
    for k, q in enumerate(spec["preguntas"], 1):
        m = len(q["alternativas"])
        assert m in (4, 5), f"Pregunta {k}: tiene {m} alternativas (deben ser 4 o 5)"
        assert q["clave"] in LETRAS[:m], f"Pregunta {k}: clave inválida {q['clave']}"
    resumen, avisos = revisar_exigencia(spec)
    print("Exigencia:", resumen)
    for a in avisos:
        print("AVISO exigencia:", a)
    cod = codigo(spec)
    sol_name = f"Soluciones-{cod}.pdf"
    sol_pdf = outdir / sol_name
    render_pdf(build_solutions_html(spec), sol_pdf, spec, MARCA + " — solucionario", f"Soluciones {cod} · TS Zenit")
    pages = solution_pages(sol_pdf, len(spec["preguntas"]))
    print(f"Soluciones: {sol_pdf} ({snapshots(sol_pdf, outdir, 'sol')} págs.)")
    n = len(spec["preguntas"])
    targets, labels = {}, {}
    if spec.get("carpeta_soluciones"):
        # Carpeta propia (p. ej. GitHub Pages): un PDF por pregunta, abre directo en cualquier navegador.
        from pypdf import PdfReader, PdfWriter
        base = spec["carpeta_soluciones"].rstrip("/") + "/" + cod
        web = outdir / "web" / cod
        web.mkdir(parents=True, exist_ok=True)
        reader = PdfReader(str(sol_pdf))
        total = len(reader.pages)
        for k in range(1, n + 1):
            fin = (pages[k + 1] - 1) if k < n else total
            w = PdfWriter()
            for pg in range(pages[k] - 1, fin):
                w.add_page(reader.pages[pg])
            w.add_metadata({"/Title": f"Solución pregunta {k} · {cod} · TS Zenit", "/Author": "TS Zenit",
                            "/Creator": "TS Zenit", "/Producer": "TS Zenit",
                            # Ficha completa de la pregunta (para corregir y diagnosticar después sin el spec original)
                            "/TSZPregunta": json.dumps({"codigo": cod, "n": k, **{c: v for c, v in spec["preguntas"][k - 1].items() if c != "figura"}}, ensure_ascii=False)})
            nombre = f"p{k:02d}-{hashlib.sha256(f'{cod}-{k}-{SAL}'.encode()).hexdigest()[:8]}.pdf"
            with open(web / nombre, "wb") as f:
                w.write(f)
            targets[k], labels[k] = f"{base}/{nombre}", "Solución"
        print(f"Carpeta para subir: {outdir / 'web'}  →  {spec['carpeta_soluciones'].rstrip('/')}/")
    elif spec.get("url_soluciones"):
        # Enlace único (Drive, Dropbox…): mismo PDF para todos, con la página escrita bajo el QR.
        for k in range(1, n + 1):
            targets[k], labels[k] = page_url(spec["url_soluciones"], pages[k]), f"Solución<br>pág. {pages[k]}"
    else:
        print("Sin carpeta_soluciones ni url_soluciones: solo se generó el solucionario.")
        return
    ens_pdf = outdir / f"{cod}.pdf"
    render_pdf(build_ensayo_html(spec, targets, labels), ens_pdf, spec, MARCA + " — material de práctica, no oficial", f"{spec['titulo']} · TS Zenit")
    print(f"Ensayo: {ens_pdf} ({snapshots(ens_pdf, outdir, 'ensayo')} págs.)")
    print(f"QR 1 → {targets[1]} | " + verify_qr(targets))

if __name__ == "__main__":
    main()
