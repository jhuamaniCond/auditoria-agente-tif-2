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

# ---------------------------------------------------------------- almacenamiento
# PIMS_BACKEND=postgres (por defecto): expediente, custodia, revisiones, proyectos,
# ejecuciones, eventos y bitacoras viven en PostgreSQL (carpeta BD/ del repositorio).
# PIMS_BACKEND=archivos: modo anterior con JSON/JSONL en Entregable-2/datos.
# Los archivos de evidencia y los indices FAISS siguen en disco en ambos modos.
BD = os.path.join(REPO, "BD")
BACKEND = os.environ.get("PIMS_BACKEND", "postgres").strip().lower()
ALMACEN = None
if BACKEND == "postgres":
    if BD not in sys.path:
        sys.path.insert(0, BD)
    import evidencia_api  # noqa: E402,F401  (pone scripts/ de la skill en sys.path)
    import evidencia  # noqa: E402
    try:
        from almacen_pg import AlmacenPG  # noqa: E402
        ALMACEN = AlmacenPG()
    except Exception as _e:  # noqa: BLE001
        raise RuntimeError(
            "No se pudo usar PostgreSQL (%s: %s). Levante la BD con 'docker compose up -d' en BD/ "
            "y cargue el catalogo (BD/README.md), o use PIMS_BACKEND=archivos."
            % (type(_e).__name__, _e)) from _e
    evidencia.ALMACEN = ALMACEN
elif BACKEND != "archivos":
    raise RuntimeError("PIMS_BACKEND debe ser 'postgres' o 'archivos', no %r" % BACKEND)

import app as app_e1  # noqa: E402  (Flask app del Entregable 1, con todo cargado)
import asistente  # noqa: E402,F401
import llm_local  # noqa: E402,F401
import revisiones  # noqa: E402,F401
from evidencia_api import (TIPOS, ErrorEvidencia, leer_indice,  # noqa: E402,F401
                           registrar_evidencia, verificar_expediente)
import rag  # noqa: E402
from rag import leer_texto  # noqa: E402,F401

# El texto de los documentos sale de PostgreSQL (tablas documentos / documento_paginas, cargadas
# con BD/cargar_documentos.py, OCR incluido): el agente deja de leer los PDF. Si el archivo no
# esta cargado en la BD, se usa el lector de archivos del Entregable 1 (solo formatos de texto).
_leer_texto_archivo = rag.leer_texto
_SHA_ARCHIVO = {}


def _leer_texto_bd(ruta, limite=20000):
    if ALMACEN is not None and os.path.isfile(ruta):
        marca = (ruta, os.path.getmtime(ruta))
        sha = _SHA_ARCHIVO.get(marca)
        if sha is None:
            import hashlib
            with open(ruta, "rb") as f:
                sha = _SHA_ARCHIVO[marca] = hashlib.sha256(f.read()).hexdigest()
        texto = ALMACEN.texto_documento(sha, limite)
        if texto:
            return texto
    return _leer_texto_archivo(ruta, limite)


# Con texto real cada documento da decenas de fragmentos: se mandan a Ollama en lotes pequenos
# (una sola peticion con todos hacia caer el modelo de embeddings en una laptop sin GPU).
_embeber_original = llm_local.embeber


def _embeber_por_lotes(textos, lote=6):
    vectores = []
    for i in range(0, len(textos), lote):
        vectores.extend(_embeber_original(textos[i:i + lote]))
    return vectores


llm_local.embeber = _embeber_por_lotes
rag.leer_texto = leer_texto = _leer_texto_bd
app_e1.leer_texto = _leer_texto_bd

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
    return PROYECTOS.crear(UNSA["nombre"], UNSA["rol"], UNSA["descripcion"], id_="unsa")


def proyecto(id_="unsa"):
    if id_ == "unsa":
        return asegurar_unsa()
    p = PROYECTOS.obtener(id_)
    if not p:
        raise ErrorAgente("No existe el proyecto %r" % id_)
    return p


def vaciar_datos():
    """Borra todo lo que el agente guarda sobre las organizaciones auditadas y deja el proyecto
    'unsa' vacio. Conserva el catalogo de la norma y de GESTITEL, `documentos_unsa/` (originales
    descargados) y el codigo. Devuelve un resumen de lo que se borro."""
    import shutil
    resumen = {"filas": ALMACEN.vaciar_datos() if ALMACEN is not None else {}, "carpetas": []}
    destinos = [os.path.join(DATOS, "proyectos"), SALIDAS, BANDEJA, EJECUCIONES]
    if ALMACEN is None:     # modo archivos: tambien las bitacoras JSONL
        for n in ("bitacora_decisiones.jsonl", "bitacora_mcp.jsonl", "eventos.jsonl"):
            ruta = os.path.join(DATOS, n)
            if os.path.isfile(ruta):
                os.remove(ruta)
    for carpeta in destinos:
        if not os.path.isdir(carpeta):
            continue
        for nombre in os.listdir(carpeta):
            ruta = os.path.join(carpeta, nombre)
            if carpeta == EJECUCIONES and ALMACEN is None and nombre.startswith("checkpoints"):
                continue    # lo mantiene abierto SqliteSaver
            try:
                shutil.rmtree(ruta) if os.path.isdir(ruta) else os.remove(ruta)
                resumen["carpetas"].append(os.path.relpath(ruta, DATOS).replace(os.sep, "/"))
            except OSError:
                pass        # archivo abierto por otro proceso: se deja
    for carpeta in destinos + [os.path.join(EJECUCIONES, "_estado"), os.path.join(SALIDAS, "incidentes")]:
        os.makedirs(carpeta, exist_ok=True)
    with PROYECTOS._candado:
        PROYECTOS._cache.clear()
    asegurar_unsa()
    return resumen


def preparar():
    """Carga los indices RAG (conocimiento comun y evidencias de cada proyecto)."""
    asegurar_unsa()
    app_e1.preparar()
