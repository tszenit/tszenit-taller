"""Contenido privado de TS Zenit (fuentes de guías y apuntes), cifrado dentro del taller público.
La llave sale del ADMIN_TOKEN de Code.gs (PBKDF2-SHA256, 310 000 iteraciones): sin el Code.gs del usuario, el archivo es ilegible.
Uso:  python3 privado.py guardar   → empaqueta y cifra en privado/contenido.enc
      python3 privado.py abrir     → descifra y restaura los archivos en /home/claude/zenit"""
import sys, os, io, re, tarfile, pathlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
Z = pathlib.Path("/home/claude/zenit"); ENC = Z / "privado" / "contenido.enc"
CODE = Z / "web/apps_script/Code.gs"
PATRONES = ["guias/q_*.py", "guias/bin.py", "guias/cpo.py", "guias/cpx.py", "guias/gra.py", "guias/itr.py",
            "guias/out/*.json", "guias/formulario_*.py", "qim/c_*.py", "pre/c_*.py", "qim/keys.json", "pre/keys.json",
            "paes/*.json", "paes/*.py", "paes/run.sh", "paes/repl/**/*"]
def llave(sal):
    tok = re.search(r'const ADMIN_TOKEN = "([0-9a-f]+)"', CODE.read_text()).group(1)
    return PBKDF2HMAC(hashes.SHA256(), 32, sal, 310000).derive(tok.encode())
def guardar():
    buf = io.BytesIO(); n = 0
    with tarfile.open(fileobj=buf, mode="w:gz") as t:
        for p in PATRONES:
            for f in sorted(Z.glob(p)):
                if f.is_file(): t.add(f, arcname=str(f.relative_to(Z))); n += 1
    sal, iv = os.urandom(16), os.urandom(12)
    ENC.parent.mkdir(exist_ok=True); ENC.write_bytes(sal + iv + AESGCM(llave(sal)).encrypt(iv, buf.getvalue(), None))
    print(f"{n} archivos cifrados en {ENC} ({ENC.stat().st_size // 1024} KB)")
def abrir():
    b = ENC.read_bytes(); data = AESGCM(llave(b[:16])).decrypt(b[16:28], b[28:], None)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as t:
        t.extractall(Z, filter="data"); print(len(t.getnames()), "archivos restaurados en", Z)
if __name__ == "__main__":
    {"guardar": guardar, "abrir": abrir}[sys.argv[1]]()
