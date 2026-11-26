"""Publica una prueba simulada (o guía) nueva de Química para Ingeniería en una sección del plan.
Uso: python3 pub_qim_sim.py CODIGO SECCION "Nombre del eje" "Descripción" [despues_de]"""
import json, os, re, sys, base64, shutil, pathlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
G = pathlib.Path("/home/claude/zenit/guias"); REPO = pathlib.Path("/home/claude/tszenit.github.io"); CODE = pathlib.Path("/home/claude/zenit/web/apps_script/Code.gs")
c, SEC, NOM, DESC = sys.argv[1:5]
spec = json.load(open(G / "out" / f"{c}.json"))
mc = [q for q in spec["preguntas"] if not q.get("desarrollo")]
info = {"t": spec["titulo"], "claves": "".join(q["clave"] for q in mc), "q": [[5, re.sub(r"<[^>]+>", "", q["contenido"]), 0] for q in mc]}
pdf = G / "out" / c / f"{c}.pdf"
dst = REPO / "soluciones" / c
if dst.exists(): shutil.rmtree(dst)
shutil.copytree(G / "out" / c / "web" / c, dst)
assert len(list(dst.glob("*.pdf"))) == len(spec["preguntas"])
key = AESGCM.generate_key(256); iv = os.urandom(12)
(REPO / "tienda/g" / f"{c}.bin").write_bytes(iv + AESGCM(key).encrypt(iv, pdf.read_bytes(), None))
k64 = base64.b64encode(key).decode()
for f in (pdf, G / "out" / c / f"Soluciones-{c}.pdf"): shutil.copy(f, G / "entrega" / f.name)
s = CODE.read_text()
def upsert(block, val):
    global s
    i = s.index(f"const {block} = {{"); j = s.index("\n};", i); body = s[i:j]
    body = re.sub(rf'\n"{c}": .*,', "", body)
    a = re.search(r'^"TSZ-QIM-EX-S1": .*,$', body, re.M); assert a
    body = body[:a.end()] + f'\n"{c}": {json.dumps(val, ensure_ascii=False)},' + body[a.end():]
    s = s[:i] + body + s[j:]
upsert("CLAVES", info["claves"]); upsert("TITULOS", info["t"]); upsert("LLAVES", k64)
m = re.search(r'const PQIM_G = (\{.*?\});', s); PG = json.loads(m.group(1))
if c not in PG[SEC]: PG[SEC].append(c)
s = s[:m.start(1)] + json.dumps(PG) + s[m.end(1):]
CODE.write_text(s)
p = REPO / "index.html"; h = p.read_text()
m = re.search(r'("TSZ-PQIM-' + SEC + r'": \{[^{}]*?"guias": )(\[[^\]]*\])', h); g = json.loads(m.group(2))
if c not in g: g.append(c)
h = h[:m.start(2)] + json.dumps(g) + h[m.end(2):]; p.write_text(h)
p = REPO / "universidad/quimica/index.html"; L = p.read_text().split("\n")
for n, ln in enumerate(L):
    if ln.startswith("const A = "):
        A = json.loads(ln[len("const A = "):].rstrip(";")); mat = next(x for x in A["mats"] if x["id"] == SEC)
        mat["ejes"] = [e for e in mat["ejes"] if c not in e["guias"]] + [{"id": "UNI-QIM", "nombre": NOM, "desc": DESC, "guias": [c]}]
        L[n] = "const A = " + json.dumps(A, ensure_ascii=False) + ";"
    if ln.startswith("const GUIAS = "):
        GU = json.loads(ln[len("const GUIAS = "):].rstrip(";")); GU[c] = {"t": info["t"], "n": len(info["q"]), "q": info["q"]}
        L[n] = "const GUIAS = " + json.dumps(GU, ensure_ascii=False) + ";"
p.write_text("\n".join(L))
b = (REPO / "tienda/g" / f"{c}.bin").read_bytes()
assert AESGCM(key).decrypt(b[:12], b[12:], None) == pdf.read_bytes()
print("OK", c, info["claves"])
