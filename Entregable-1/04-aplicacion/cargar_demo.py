# -*- coding: utf-8 -*-
"""
Carga en la aplicacion el proyecto del caso de estudio ClinData S.A.C.
(8 evidencias, EV-0007 alterada a proposito, SoA con A.1.5.4 excluido).

    python cargar_demo.py

Reemplaza datos/proyectos/clindata (los demas proyectos no se tocan). Ejecuta
antes ../02-skill/.../assets/demo/ejecutar_demo.py si quieres regenerar el
expediente de origen.
"""

import json
import os
import shutil

AQUI = os.path.dirname(os.path.abspath(__file__))
ORIGEN = os.path.join(os.path.dirname(AQUI), "02-skill", "evidencia-auditoria-pims",
                      "assets", "demo", "expediente")
DATOS = os.environ.get("AUDITA_DATOS", os.path.join(AQUI, "datos"))
PROYECTO = os.path.join(DATOS, "proyectos", "clindata")
FICHA = {
    "id": "clindata",
    "nombre": "ClinData S.A.C.",
    "rol": "responsable",
    "descripcion": "Caso de estudio: clínica con historia clínica electrónica y telemedicina",
    "creado": "2026-10-01T21:55:25-05:00",
}

if __name__ == "__main__":
    if not os.path.isdir(ORIGEN):
        raise SystemExit("No existe %s: ejecuta primero ejecutar_demo.py" % ORIGEN)
    shutil.rmtree(PROYECTO, ignore_errors=True)
    shutil.copytree(ORIGEN, os.path.join(PROYECTO, "expediente"))
    with open(os.path.join(PROYECTO, "proyecto.json"), "w", encoding="utf-8") as f:
        json.dump(FICHA, f, ensure_ascii=False, indent=2)
    print("Proyecto ClinData S.A.C. cargado en %s" % PROYECTO)
