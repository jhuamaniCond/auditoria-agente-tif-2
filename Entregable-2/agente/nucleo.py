# -*- coding: utf-8 -*-
"""
Nucleo del Agente de Evidencia y Auditoria (Entregable 2).

Reutiliza sin copiar la aplicacion del Entregable 1 (04-aplicacion): el mismo
evidencia.py de la skill, el mismo RAG (FAISS + nomic-embed-text) y el mismo
asistente (LLM local en Ollama). Lo unico propio es la carpeta de datos del
Entregable 2 (Entregable-2/datos), donde vive el expediente de la UNSA.

Todo modulo del Entregable 2 importa este primero:

    import nucleo
    p = nucleo.proyecto("unsa")
"""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ENTREGABLE2 = os.path.dirname(AQUI)
REPO = os.path.dirname(ENTREGABLE2)
APP_E1 = os.path.join(REPO, "Entregable-1", "04-aplicacion")
DATOS = os.path.join(ENTREGABLE2, "datos")
DOCUMENTOS_UNSA = os.path.join(DATOS, "documentos_unsa")     # descargas originales
BANDEJA = os.path.join(DATOS, "bandeja_entrada")              # automatizacion
SALIDAS = os.path.join(DATOS, "salidas")                      # informes generados
EJECUCIONES = os.path.join(DATOS, "ejecuciones")              # estado del orquestador

# La app del Entregable 1 lee AUDITA_DATOS al importarse: debe fijarse antes.
os.environ.setdefault("AUDITA_DATOS", DATOS)
if APP_E1 not in sys.path:
    sys.path.insert(0, APP_E1)

for _c in (DATOS, DOCUMENTOS_UNSA, BANDEJA, SALIDAS, EJECUCIONES):
    os.makedirs(_c, exist_ok=True)

import app as app_e1  # noqa: E402  (Flask app del Entregable 1, con todo cargado)
import asistente  # noqa: E402,F401
import llm_local  # noqa: E402,F401
import revisiones  # noqa: E402,F401
from evidencia_api import (TIPOS, ErrorEvidencia, leer_indice,  # noqa: E402,F401
                           registrar_evidencia, verificar_expediente)
from rag import leer_texto  # noqa: E402,F401

CATALOGO = app_e1.CATALOGO
PROYECTOS = app_e1.PROYECTOS
CONOCIMIENTO_RAG = app_e1.CONOCIMIENTO_RAG

UNSA = {
    "nombre": "Universidad Nacional de San Agustin de Arequipa (UNSA)",
    "rol": "responsable",
    "descripcion": ("Universidad publica peruana. Responsable del tratamiento de datos "
                    "personales de estudiantes, postulantes, docentes, administrativos, "
                    "egresados y proveedores (Ley N.o 29733)."),
}


class ErrorAgente(RuntimeError):
    """Error que el agente comunica al usuario tal cual."""


def asegurar_unsa():
    """Crea el proyecto 'unsa' del Entregable 2 si aun no existe."""
    p = PROYECTOS.obtener("unsa")
    if p:
        return p
    creado = PROYECTOS.crear(UNSA["nombre"], UNSA["rol"], UNSA["descripcion"])
    if creado.id != "unsa":     # el slug sale del nombre; se fija el id corto
        os.rename(creado.carpeta, os.path.join(PROYECTOS.carpeta, "unsa"))
        import json
        ruta = os.path.join(PROYECTOS.carpeta, "unsa", "proyecto.json")
        with open(ruta, encoding="utf-8") as f:
            datos = json.load(f)
        datos["id"] = "unsa"
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        PROYECTOS._cache.clear()
    return PROYECTOS.obtener("unsa")


def proyecto(id_="unsa"):
    if id_ == "unsa":
        return asegurar_unsa()
    p = PROYECTOS.obtener(id_)
    if not p:
        raise ErrorAgente("No existe el proyecto %r" % id_)
    return p


def preparar():
    """Carga los indices RAG (conocimiento comun y evidencias de cada proyecto)."""
    asegurar_unsa()
    app_e1.preparar()
