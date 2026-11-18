# -*- coding: utf-8 -*-
"""
Sube a la base de datos los documentos PIMS (.docx) de la UNSA.

    python Entregable-3/scripts/cargar_documentos_pims.py [carpeta ...] [--por "Nombre"]

Por defecto carga Entregable-3/documentos-pims/generados (los del Grupo 6) y
Entregable-3/documentos-pims/otros-grupos (los que entreguen los demas grupos). Para
cada .docx: lee la portada, verifica el control documental (PIMS-PR-01), lo guarda en
`documentos` / `documento_paginas` / `documentos_pims` y lo registra como evidencia del
expediente. Es idempotente (SHA-256): un archivo ya cargado no se repite.
"""

import argparse
import glob
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
E3 = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(E3, "agente"))

import documentos_pims  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("carpetas", nargs="*", default=[
        os.path.join(E3, "documentos-pims", "generados"),
        os.path.join(E3, "documentos-pims", "otros-grupos")])
    ap.add_argument("--por", default="Grupo 6 - Agente de Evidencia y Auditoria",
                    help="quien registra (queda en la bitacora)")
    ap.add_argument("--proyecto", default="unsa")
    a = ap.parse_args()
    n = documentos_pims.sincronizar_lista_maestra(a.proyecto)
    print("Lista maestra PIMS-RG-01 sincronizada en la BD: %d documentos esperados\n" % n)
    for carpeta in a.carpetas:
        archivos = sorted(f for f in glob.glob(os.path.join(carpeta, "**", "*.docx"), recursive=True)
                          if not os.path.basename(f).startswith("~$"))
        for ruta in archivos:
            try:
                d = documentos_pims.registrar(ruta, a.por, proyecto=a.proyecto)
            except Exception as e:  # noqa: BLE001
                print("ERROR %s: %s" % (os.path.basename(ruta), e))
                continue
            c = d["control"]
            print("%-12s v%-4s %-10s control=%-13s evidencia=%s%s" % (
                d["codigo"], d["version"], d["estado"], c["resultado"], d.get("evidencia_id"),
                " (ya estaba)" if d.get("ya_registrado") else ""))
    print("\nLista maestra PIMS-RG-01:")
    for f in documentos_pims.lista_maestra(a.proyecto):
        print("  %-12s %-10s %-36s %s" % (f["codigo"], f["situacion"], f["agente_autor"][:36], f["titulo"]))


if __name__ == "__main__":
    main()
