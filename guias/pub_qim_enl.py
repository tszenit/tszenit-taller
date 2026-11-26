"""Publica las guías de Enlace químico (nivelación de la I1) de Química para Ingeniería."""
import json, os, re, base64, shutil, pathlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
G = pathlib.Path("/home/claude/zenit/guias"); REPO = pathlib.Path("/home/claude/tszenit.github.io"); CODE = pathlib.Path("/home/claude/zenit/web/apps_script/Code.gs")
NEW = ["TSZ-QIM-ENL-N1", "TSZ-QIM-ENL-A1"]
info = {}
for c in NEW:
    spec = json.load(open(G / "out" / f"{c}.json"))
    mc = [q for q in spec["preguntas"] if not q.get("desarrollo")]
    info[c] = {"t": spec["titulo"], "claves": "".join(q["clave"] for q in mc), "q": [[5, re.sub(r"<[^>]+>", "", q["contenido"]), 0] for q in mc]}
    pdf = G / "out" / c / f"{c}.pdf"
    dst = REPO / "soluciones" / c
    if dst.exists(): shutil.rmtree(dst)
    shutil.copytree(G / "out" / c / "web" / c, dst)
    assert len(list(dst.glob("*.pdf"))) == len(spec["preguntas"])
    key = AESGCM.generate_key(256); iv = os.urandom(12)
    (REPO / "tienda/g" / f"{c}.bin").write_bytes(iv + AESGCM(key).encrypt(iv, pdf.read_bytes(), None))
    info[c]["k"] = base64.b64encode(key).decode()
    for f in (pdf, G / "out" / c / f"Soluciones-{c}.pdf"): shutil.copy(f, G / "entrega" / f.name)
# Code.gs
s = CODE.read_text()
def upsert(block, entries):
    global s
    i = s.index(f"const {block} = {{"); j = s.index("\n};", i); body = s[i:j]
    for k in entries: body = re.sub(rf'\n"{k}": .*,', "", body)
    anchor = re.search(r'^"TSZ-QIM-EX-S1": .*,$', body, re.M); assert anchor, block
    body = body[:anchor.end()] + "".join(f'\n"{k}": {json.dumps(v, ensure_ascii=False)},' for k, v in entries.items()) + body[anchor.end():]
    s = s[:i] + body + s[j:]
upsert("CLAVES", {c: info[c]["claves"] for c in NEW}); upsert("TITULOS", {c: info[c]["t"] for c in NEW}); upsert("LLAVES", {c: info[c]["k"] for c in NEW})
m = re.search(r'const PQIM_G = \{"I1": (\[[^\]]*\])', s); I1 = json.loads(m.group(1))
I1 = NEW + [c for c in I1 if c not in NEW]
s = s[:m.start(1)] + json.dumps(I1) + s[m.end(1):]
CODE.write_text(s)
# tienda
p = REPO / "index.html"; h = p.read_text()
m = re.search(r'("TSZ-PQIM-I1": \{[^{}]*?"guias": )(\[[^\]]*\])', h); assert m
g = json.loads(m.group(2)); g = NEW + [c for c in g if c not in NEW]
h = h[:m.start(2)] + json.dumps(g) + h[m.end(2):]
h = h.replace('"tem": ["Nivelación: estequiometría, reactivo limitante y disoluciones"', '"tem": ["Nivelación: enlace químico, estequiometría, reactivo limitante y disoluciones"')
h = h.replace("20 guías en PDF (básica y avanzada ★ de cada tema) e I1 simulada", "22 guías en PDF (básica y avanzada ★ de cada tema, con enlace químico) e I1 simulada")
p.write_text(h)
# aula
p = REPO / "universidad/quimica/index.html"; L = p.read_text().split("\n")
for n, ln in enumerate(L):
    if ln.startswith("const A = "):
        A = json.loads(ln[len("const A = "):].rstrip(";")); mat = next(x for x in A["mats"] if x["id"] == "I1")
        mat["ejes"] = [e for e in mat["ejes"] if "TSZ-QIM-ENL-N1" not in e["guias"]]
        mat["ejes"].insert(0, {"id": "UNI-QIM", "nombre": "Nivelación · Enlace químico", "desc": "Guía básica y avanzada ★: tipos de enlace, Lewis, carga formal, resonancia, VSEPR, hibridación y energía reticular.", "guias": NEW})
        L[n] = "const A = " + json.dumps(A, ensure_ascii=False) + ";"
    if ln.startswith("const GUIAS = "):
        GU = json.loads(ln[len("const GUIAS = "):].rstrip(";"))
        for c in NEW: GU[c] = {"t": info[c]["t"], "n": len(info[c]["q"]), "q": info[c]["q"]}
        L[n] = "const GUIAS = " + json.dumps(GU, ensure_ascii=False) + ";"
p.write_text("\n".join(L))
for c in NEW:
    b = (REPO / "tienda/g" / f"{c}.bin").read_bytes()
    assert AESGCM(base64.b64decode(info[c]["k"])).decrypt(b[:12], b[12:], None) == (G / "out" / c / f"{c}.pdf").read_bytes()
print("OK", NEW, [info[c]["claves"] for c in NEW])
