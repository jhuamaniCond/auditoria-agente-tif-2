# -*- coding: utf-8 -*-
"""
Genera los documentos PIMS de los otros equipos del PIMS (Agentes 1, 2, 3, 5, 6, 7, 8 y la alta
dirección) para que la lista maestra PIMS-RG-01 quede completa en la implementación simulada.

    python Entregable-3/scripts/generar_documentos_otros_grupos.py

Salida: Entregable-3/documentos-pims/otros-grupos/ (.docx) y otros-grupos/anexos/ (.xlsx).

Los elabora el Grupo 6 con apoyo de IA, en coordinación con los demás equipos (Mensaje 2). Usan
las plantillas del docente cuando existen (Metodología de riesgos, Apéndice 3, Plan de
tratamiento, Plan de capacitación); los demás se construyen sobre la plantilla de
procedimiento para mantener el formato común. Cada documento lleva la nota de simulación y
pasa el control documental de PIMS-PR-01. La salida es determinista (mismo contenido, mismo
SHA-256), así que volver a generar no crea versiones nuevas en la base de datos.
"""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
E3 = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(E3, "agente"))
sys.path.insert(0, AQUI)

import docs_direccion  # noqa: E402
import docs_riesgos_controles  # noqa: E402
import docs_titulares_terceros  # noqa: E402


def main():
    rutas = docs_direccion.generar() + docs_riesgos_controles.generar() + docs_titulares_terceros.generar()
    for r in rutas:
        print("generado:", os.path.relpath(r, E3))


if __name__ == "__main__":
    main()
