# -*- coding: utf-8 -*-
"""Importa la parte determinista de la skill (scripts/evidencia.py) para que la
aplicacion web use exactamente el mismo codigo que la linea de comandos."""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(RAIZ, "02-skill", "evidencia-auditoria-pims")
sys.path.insert(0, os.path.join(SKILL, "scripts"))

from evidencia import (  # noqa: E402,F401
    CATALOGO_POR_DEFECTO, ORDEN_ESTADOS, TIPOS, ErrorEvidencia, ahora, anotar_custodia,
    comprobar_cadena, estado_integridad, evaluar_cobertura, leer_catalogo, leer_indice,
    registrar_evidencia, verificar_expediente)
