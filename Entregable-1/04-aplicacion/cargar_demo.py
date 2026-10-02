# -*- coding: utf-8 -*-
"""
Carga en la aplicacion el expediente del caso de estudio ClinData S.A.C.
(8 evidencias, EV-0007 alterada a proposito, SoA con A.1.5.4 excluido).

    python cargar_demo.py

Reemplaza datos/expediente. Ejecuta antes ../02-skill/.../assets/demo/ejecutar_demo.py
si quieres regenerar el expediente de origen.
"""

import os
import shutil

AQUI = os.path.dirname(os.path.abspath(__file__))
ORIGEN = os.path.join(os.path.dirname(AQUI), "02-skill", "evidencia-auditoria-pims",
                      "assets", "demo", "expediente")
DESTINO = os.path.join(AQUI, "datos", "expediente")

if __name__ == "__main__":
    if not os.path.isdir(ORIGEN):
        raise SystemExit("No existe %s: ejecuta primero ejecutar_demo.py" % ORIGEN)
    shutil.rmtree(DESTINO, ignore_errors=True)
    shutil.copytree(ORIGEN, DESTINO)
    for nombre in ("indice.faiss", "indice_meta.json"):
        ruta = os.path.join(AQUI, "datos", nombre)
        if os.path.exists(ruta):
            os.remove(ruta)
    print("Expediente de ClinData S.A.C. cargado en %s" % DESTINO)
