# -*- coding: utf-8 -*-
"""
AUDITA-PIMS - aplicacion web local del Agente de Evidencia y Auditoria.

    python app.py            # http://127.0.0.1:5000

Backend Flask. La parte determinista (hash, cadena de custodia, cobertura) es
el mismo evidencia.py de la skill; el asistente usa un LLM local (Ollama) con
RAG sobre FAISS y embeddings locales. Nada sale de la maquina.
"""

import datetime as dt
import os
import tempfile
import threading
import uuid

from flask import Flask, jsonify, render_template, request

import asistente
import llm_local
from evidencia_api import (CATALOGO_POR_DEFECTO, TIPOS, ErrorEvidencia, comprobar_cadena,
                           estado_integridad, evaluar_cobertura, leer_catalogo, leer_indice,
                           registrar_evidencia, verificar_expediente)
from rag import IndiceRAG, leer_texto

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
DATOS = os.environ.get("AUDITA_DATOS", os.path.join(AQUI, "datos"))
EXPEDIENTE = os.path.join(DATOS, "expediente")
PENDIENTES = os.path.join(tempfile.gettempdir(), "audita_pims_subidas")
SKILL = os.path.join(RAIZ, "02-skill", "evidencia-auditoria-pims")
CONOCIMIENTO = [
    os.path.join(SKILL, "references", "criterios_evidencia.md"),
    os.path.join(SKILL, "assets", "plantilla_hallazgo.md"),
    os.path.join(SKILL, "SKILL.md"),
    os.path.join(RAIZ, "03-asistente", "glosario_pims.md"),
]
EXTENSIONES = {".md", ".txt", ".csv", ".json", ".log", ".pdf", ".docx", ".xlsx", ".png", ".jpg"}

os.makedirs(EXPEDIENTE, exist_ok=True)
os.makedirs(PENDIENTES, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
CATALOGO = leer_catalogo(CATALOGO_POR_DEFECTO)
RAG = IndiceRAG(CONOCIMIENTO, CATALOGO, EXPEDIENTE, DATOS)
_bloqueo = threading.Lock()          # el expediente se escribe de uno en uno


def _parametros_cobertura(fuente):
    rol = fuente.get("rol", "responsable")
    vigencia = int(fuente.get("vigencia", 365))
    fecha = fuente.get("fecha") or dt.date.today().isoformat()
    return rol, vigencia, dt.date.fromisoformat(fecha)


def _integridad_sin_registrar():
    """Como verificar_expediente, pero sin anotar en la cadena (para consultas)."""
    indice = leer_indice(EXPEDIENTE)
    resultados = {"OK": [], "ALTERADA": [], "FALTANTE": []}
    for ev in indice["evidencias"]:
        resultados[estado_integridad(EXPEDIENTE, ev)].append(ev["id"])
    problemas = comprobar_cadena(EXPEDIENTE, indice)
    return {"total": len(indice["evidencias"]), "resultados": resultados,
            "problemas_cadena": problemas,
            "integro": not (resultados["ALTERADA"] or resultados["FALTANTE"] or problemas)}


def _resumen(fuente):
    rol, vigencia, fecha = _parametros_cobertura(fuente)
    cob = evaluar_cobertura(EXPEDIENTE, CATALOGO, rol, vigencia, fecha)
    evidencias = leer_indice(EXPEDIENTE)["evidencias"]
    return cob, asistente.resumen_expediente(cob, _integridad_sin_registrar(), evidencias)


def _error(mensaje, codigo=400):
    return jsonify({"error": mensaje}), codigo


# --------------------------------------------------------------------------
@app.route("/")
def inicio():
    return render_template("index.html", tipos=TIPOS)


@app.route("/api/estado")
def api_estado():
    indice = leer_indice(EXPEDIENTE)
    integridad = _integridad_sin_registrar()
    estado_ev = {}
    for clave, ids in integridad["resultados"].items():
        for i in ids:
            estado_ev[i] = clave
    for ev in indice["evidencias"]:
        ev["integridad"] = estado_ev.get(ev["id"], "OK")
    return jsonify({"modelo": llm_local.estado(), "evidencias": indice["evidencias"],
                    "integridad": integridad,
                    "rag": {"fragmentos": len(RAG.fragmentos)}})


@app.route("/api/catalogo")
def api_catalogo():
    return jsonify(CATALOGO)


@app.route("/api/cobertura")
def api_cobertura():
    try:
        cob, _ = _resumen(request.args)
    except ValueError as e:
        return _error(str(e))
    return jsonify(cob)


@app.route("/api/verificar", methods=["POST"])
def api_verificar():
    with _bloqueo:
        return jsonify(verificar_expediente(EXPEDIENTE, "auditor (web)"))


@app.route("/api/sugerir", methods=["POST"])
def api_sugerir():
    archivo = request.files.get("archivo")
    if not archivo or not archivo.filename:
        return _error("Adjunta un archivo")
    nombre = os.path.basename(archivo.filename)
    if os.path.splitext(nombre)[1].lower() not in EXTENSIONES:
        return _error("Formato no admitido: %s" % nombre)
    token = uuid.uuid4().hex
    ruta = os.path.join(PENDIENTES, token + "_" + nombre)
    archivo.save(ruta)
    try:
        sugerencia = asistente.sugerir_clasificacion(RAG, CATALOGO, nombre, leer_texto(ruta))
    except llm_local.ErrorModelo as e:
        return _error(str(e), 503)
    sugerencia.update({"token": token, "nombre": nombre})
    return jsonify(sugerencia)


@app.route("/api/registrar", methods=["POST"])
def api_registrar():
    d = request.get_json(force=True)
    token, nombre = d.get("token", ""), os.path.basename(d.get("nombre", ""))
    ruta = os.path.join(PENDIENTES, token + "_" + nombre)
    if not token.isalnum() or not os.path.isfile(ruta):
        return _error("La subida expiro; vuelve a adjuntar el archivo")
    try:
        with _bloqueo:
            ev = registrar_evidencia(
                EXPEDIENTE, ruta, d.get("controles", []), d.get("tipo", ""),
                d.get("titulo", "").strip() or nombre, d.get("responsable", "").strip()
                or "auditor (web)", d.get("fuente", ""), d.get("fecha_documento") or None,
                nombre_original=nombre)
            RAG.agregar_evidencia(ev)
    except ErrorEvidencia as e:
        return _error(str(e))
    except llm_local.ErrorModelo as e:
        return _error("Evidencia registrada, pero no indexada: %s" % e, 503)
    finally:
        if os.path.exists(ruta):
            os.remove(ruta)
    return jsonify(ev)


@app.route("/api/chat", methods=["POST"])
def api_chat():
    d = request.get_json(force=True)
    mensaje = (d.get("mensaje") or "").strip()
    if not mensaje:
        return _error("Escribe una pregunta")
    try:
        _, resumen = _resumen(d)
        respuesta, fuentes = asistente.responder(RAG, mensaje, d.get("historial", []), resumen)
    except llm_local.ErrorModelo as e:
        return _error(str(e), 503)
    return jsonify({"respuesta": respuesta, "fuentes": fuentes})


@app.route("/api/hallazgo", methods=["POST"])
def api_hallazgo():
    d = request.get_json(force=True)
    cob, resumen = _resumen(d)
    fila = next((f for f in cob["controles"] if f["ref"] == d.get("ref")), None)
    if not fila:
        return _error("Control no encontrado")
    if fila["estado"] in ("Cubierto", "No aplica"):
        return _error("El control %s esta %s: no genera hallazgo" % (fila["ref"], fila["estado"]))
    try:
        texto = asistente.redactar_hallazgo(RAG, fila, resumen)
    except llm_local.ErrorModelo as e:
        return _error(str(e), 503)
    return jsonify({"ref": fila["ref"], "hallazgo": texto})


def preparar():
    """Construye o carga el indice RAG antes de atender peticiones."""
    try:
        print("Indice RAG:", RAG.construir(), "-", len(RAG.fragmentos), "fragmentos")
    except llm_local.ErrorModelo as e:
        print("AVISO:", e)


if __name__ == "__main__":
    preparar()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
