# TS Zenit · Taller

Herramientas para generar el material de TS Zenit (guías y ensayos PAES, guías y simulacros universitarios, apuntes interactivos, apuntes a mano y slides) y publicarlo en el sitio **https://tszenit.cl** (repositorio `tszenit/tszenit.github.io`).

Este repositorio es **público**. Por eso aquí solo hay código y plantillas:

- No hay contenido de guías ni de apuntes. Los archivos `guias/q_*.py`, `qim/c_*.py` y `pre/c_*.py` quedan fuera.
- No hay llaves: `keys.json` y `web/apps_script/Code.gs` quedan fuera.
- No hay sales: los nombres de los PDF de solución y de los informes usan las variables `TSZ_SAL` y `TSZ_SAL_INF`. Si no están definidas, se usa una sal aleatoria por ejecución.

## Preparar una sesión nueva

```bash
git clone https://github.com/tszenit/tszenit-taller /home/claude/zenit
git clone https://github.com/tszenit/tszenit.github.io /home/claude/tszenit.github.io
cd /home/claude/zenit/tools && npm install           # KaTeX (con mhchem) para los apuntes
pip install --break-system-packages reportlab pypdf pypdfium2 cryptography opencv-contrib-python-headless pymupdf
mkdir -p /home/claude/zenit/web/apps_script /home/claude/zenit/guias/entrega
```

- Las rutas de los scripts suponen exactamente esas dos carpetas.
- Playwright y Chromium ya vienen instalados en el entorno. No hay que reinstalarlos.
- Las fuentes Poppins y Lora vienen del sistema.
- **Code.gs:** el usuario lo pega en el chat, desde su Apps Script. Se guarda en `/home/claude/zenit/web/apps_script/Code.gs`. Nunca se sube a ningún repositorio.

## Estructura

| Carpeta | Qué hay |
|---|---|
| `guias/gen_paes.py` | Motor principal. Toma un spec JSON (formato en la skill TS Zenit) y produce `out/<código>/<código>.pdf`, `Soluciones-<código>.pdf` y `web/<código>/pNN-<hash>.pdf` (un PDF por pregunta, el destino de cada QR). Incluye logo, estilos, LaTeX→MathML, QR y verificación de QR. |
| `guias/pre_guia.py`, `guias/qim_guia.py` | Guías universitarias (Precálculo, Química para Ingeniería): `Q(...)` alternativas A–E, `D(...)` desarrollo, `build(spec, "out", claves(seed[, n]))`. Guía = 20 + 3 desarrollo. Simulada = 8 + 4 desarrollo (68 pts). |
| `guias/pub_qim_sim.py`, `guias/pub_qim_enl.py` | Ejemplos de publicación. Hacen esto: copiar las soluciones al sitio, cifrar el PDF (AES-GCM, llave nueva) en `tienda/g/<código>.bin`, insertar CLAVES/TITULOS/LLAVES en Code.gs, y actualizar el plan, el aula y la tienda. |
| `guias/panel_x.py` | Lee y reescribe `BLOB_X` del panel del creador (guías privadas y material), usando el `ADMIN_TOKEN` de Code.gs. |
| `guias/zenit_resultados.py` | Modo diagnóstico: análisis de resultados, informe docente, tutor por alumno y validación de la guía de refuerzo. |
| `qim/`, `pre/` | Generador de material (`gen.py I1 I2 EX`): apunte interactivo (AP), slides (SL) y apuntes a mano (AM). El contenido va en `c_<id>.py`, con el lenguaje `TEMA/SUB/P/EQ/TBL/EX/TRAP/KEY/TOOL/MINI/FIG/UL/SL/C`. Las herramientas interactivas están en `tools.js`. |

## Reglas de publicación (resumen)

1. **QR:** apuntan a `https://tszenit.cl/soluciones/<código>/pNN-<hash>.pdf`.
2. **Llaves:** nunca van en el sitio. Viven solo en Code.gs (LLAVES y MATERIAL) o en `BLOB_X` del panel (material privado).
3. **Al cambiar Code.gs:** hay que entregarle al usuario el archivo completo para copiar (una página con botón «Copiar código», enviada como archivo y no como artifact publicado, porque contiene ADMIN_TOKEN). Él lo pega en Apps Script y crea una nueva versión en Implementar → Administrar implementaciones → ✏️.
4. **Antes de subir:**
   - Revisar las claves con Python.
   - Revisar que los QR decodifiquen la URL correcta, con OpenCV.
   - Revisar que cada `.bin` descifre igual al PDF.
   - Mirar las páginas renderizadas.
5. **Commits:** con autor `TS Zenit <tszenit@users.noreply.github.com>`.
