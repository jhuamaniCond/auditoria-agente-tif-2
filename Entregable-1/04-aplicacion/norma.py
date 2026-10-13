# -*- coding: utf-8 -*-
"""
Texto de las normas de ISOS/texto/ (generado con extraer_norma.py a partir de
los PDF de ISOS/pdf/).

Cada archivo .md tiene una seccion "## <ref> <titulo>" por clausula, control del
Anexo A y guia del Anexo B. Este modulo las separa para dos usos:
  - el RAG las indexa como fragmentos de tipo "norma";
  - la app y el asistente piden el texto exacto de un control del catalogo:
    requisito (clausula o Anexo A) + guia de implementacion (Anexo B).
"""

import glob
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_TEXTO = os.path.join(RAIZ, "ISOS", "texto")

_ENCABEZADO = re.compile(r"^## ((?:[A-F]\.)?\d+(?:\.\d+)*)\s*(.*)$")
_PAGINA = re.compile(r"^_Pagina (\d+) del PDF")


def rutas():
    return sorted(glob.glob(os.path.join(CARPETA_TEXTO, "*.md")))


def _leer(ruta):
    norma = os.path.splitext(os.path.basename(ruta))[0]
    secciones, actual = [], None
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            linea = linea.rstrip("\n")
            m = _ENCABEZADO.match(linea)
            if m or linea.startswith("# "):
                actual = None
                if m:
                    actual = {"norma": norma, "ref": m.group(1), "titulo": m.group(2).strip(),
                              "pagina": None, "lineas": []}
                    secciones.append(actual)
                continue
            if actual is None:
                continue
            p = _PAGINA.match(linea)
            if p and actual["pagina"] is None:
                actual["pagina"] = int(p.group(1))
            else:
                actual["lineas"].append(linea)
    for s in secciones:
        s["texto"] = re.sub(r"\n{3,}", "\n\n", "\n".join(s.pop("lineas"))).strip()
    return secciones


_CACHE = {}


def secciones():
    """Todas las secciones de todas las normas de ISOS/texto (se releen si cambian)."""
    clave = tuple((r, os.path.getmtime(r)) for r in rutas())
    if _CACHE.get("clave") != clave:
        _CACHE["clave"] = clave
        _CACHE["secciones"] = [s for r in rutas() for s in _leer(r)]
    return _CACHE["secciones"]


def cita(s):
    """'ISO 27701-2025 §B.1.3.7 (p. 33)'"""
    return "%s §%s%s" % (s["norma"], s["ref"], " (p. %d)" % s["pagina"] if s["pagina"] else "")


def para_control(ref):
    """Secciones de la norma que corresponden a un control del catalogo.

    Clausula (p. ej. 9.2): la seccion y sus subapartados (9.2.1, 9.2.2).
    Control del Anexo A (p. ej. A.1.3.7): el requisito A.1.3.7 y su guia B.1.3.7.
    """
    todas = [s for s in secciones() if s["texto"]]
    if ref.startswith("A."):
        guia = "B." + ref[2:]
        return [s for s in todas if s["ref"] == ref] + [s for s in todas if s["ref"] == guia]
    return [s for s in todas if s["ref"] == ref or s["ref"].startswith(ref + ".")]


def texto_control(ref, limite=3500):
    """Texto normativo de un control, listo para el prompt (recortado a `limite`)."""
    partes = []
    for s in para_control(ref):
        partes.append("[%s] %s %s\n%s" % (cita(s), s["ref"], s["titulo"], s["texto"]))
    texto = "\n\n".join(partes)
    if len(texto) > limite:
        texto = texto[:limite].rsplit("\n", 1)[0] + "\n[... texto de la norma recortado]"
    return texto
