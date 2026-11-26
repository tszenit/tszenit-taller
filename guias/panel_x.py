"""Lee o reescribe el bloque BLOB_X del panel (guías y material que solo ve el creador).
Cifrado: PBKDF2-SHA256 (310 000 iteraciones) con TOKEN = ADMIN_TOKEN de Code.gs; formato base64(sal16 | iv12 | AES-GCM).
Contenido: {"xejes": [...], "gk": {guía: llave}, "guias": {guía: {...}}, "mat": {id: nombre}, "mk": {id: llave}}.
Uso:  python3 panel_x.py leer  > X.json
      python3 panel_x.py escribir X.json      (reemplaza BLOB_X en panel/index.html)"""
import sys, re, json, os, base64, pathlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
PANEL = pathlib.Path("/home/claude/tszenit.github.io/panel/index.html")
CODE = pathlib.Path("/home/claude/zenit/web/apps_script/Code.gs")
TOKEN = re.search(r'const ADMIN_TOKEN = "([0-9a-f]+)"', CODE.read_text()).group(1)
def kdf(salt): return PBKDF2HMAC(hashes.SHA256(), 32, salt, 310000).derive(TOKEN.encode())
def leer():
    b = base64.b64decode(re.search(r'const BLOB_X = "([^"]+)"', PANEL.read_text()).group(1))
    return json.loads(AESGCM(kdf(b[:16])).decrypt(b[16:28], b[28:], None))
def escribir(X):
    salt, iv = os.urandom(16), os.urandom(12)
    blob = base64.b64encode(salt + iv + AESGCM(kdf(salt)).encrypt(iv, json.dumps(X, ensure_ascii=False).encode(), None)).decode()
    h = PANEL.read_text(); h2 = re.sub(r'const BLOB_X = "[^"]+"', f'const BLOB_X = "{blob}"', h, count=1)
    assert h2 != h; PANEL.write_text(h2); assert leer() == X
if __name__ == "__main__":
    if sys.argv[1] == "leer": print(json.dumps(leer(), ensure_ascii=False, indent=1))
    else: escribir(json.load(open(sys.argv[2])))
