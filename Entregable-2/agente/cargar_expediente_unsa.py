# -*- coding: utf-8 -*-
"""
Registra en el expediente del proyecto `unsa` los documentos oficiales que ya tienen controles
asignados (docs-unsa/fuentes.json, con su justificacion).

    python cargar_expediente_unsa.py

Cada documento queda como evidencia (SHA-256, cadena de custodia, indexado). Si su texto ya esta
en la tabla `documentos` (BD/cargar_documentos.py), el indexado y el analisis usan ese texto.
Es idempotente: un archivo con el mismo SHA-256 ya registrado se omite.
"""

import hashlib
import json
import os

import nucleo
import herramientas

RESPONSABLE = "Grupo 6 (carga inicial)"


def main():
    nucleo.preparar()
    carpeta = os.path.join(nucleo.REPO, "docs-unsa")
    fuentes = json.load(open(os.path.join(carpeta, "fuentes.json"), encoding="utf-8"))
    ya = {e["sha256"] for e in herramientas.estado_expediente("unsa")["evidencias"]}
    nuevas = 0
    for f in fuentes:
        if not f.get("controles"):
            print("omitido (sin controles asignados): %s" % f["archivo"])
            continue
        ruta = os.path.join(carpeta, f["archivo"])
        sha = hashlib.sha256(open(ruta, "rb").read()).hexdigest()
        if sha in ya:
            print("ya registrado: %s" % f["archivo"])
            continue
        ev = herramientas.registrar(ruta, f["controles"], f["tipo"], f["titulo"], "unsa", RESPONSABLE,
                                    f.get("url_origen") or "", f.get("fecha_documento"))
        nuevas += 1
        print("%s  %s  controles %s" % (ev["id"], f["archivo"], ", ".join(ev["controles"])))
    print("Evidencias nuevas: %d" % nuevas)


if __name__ == "__main__":
    main()
