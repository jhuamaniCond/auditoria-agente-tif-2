# -*- coding: utf-8 -*-
"""
AUDITA-PIMS - aplicacion web local del Agente de Evidencia y Auditoria.

    python app.py            # http://127.0.0.1:5000

Backend Flask. La parte determinista (hash, cadena de custodia, cobertura) es
el mismo evidencia.py de la skill; el asistente usa un LLM local (Ollama) con
RAG sobre FAISS y embeddings locales. Nada sale de la maquina.

Cada organizacion auditada es un proyecto (proyectos.py) con su propio
expediente e indice de evidencias. Toda peticion indica su proyecto con la
cabecera X-Proyecto (o ?proyecto= en enlaces a archivos).
"""

import datetime as dt
import os
import tempfile
import uuid

from flask import Flask, jsonify, render_template, request, send_file

import asistente
import grafo
import llm_local
import norma
import revisiones
from evidencia_api import (CATALOGO_POR_DEFECTO, TIPOS, ErrorEvidencia, comprobar_cadena,
                           estado_integridad, evaluar_cobertura, leer_catalogo, leer_indice,
                           registrar_evidencia, verificar_expediente)
from proyectos import ErrorProyecto, Proyectos
from rag import Conocimiento, leer_texto

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
DATOS = os.environ.get("AUDITA_DATOS", os.path.join(AQUI, "datos"))
PENDIENTES = os.path.join(tempfile.gettempdir(), "audita_pims_subidas")
SKILL = os.path.join(RAIZ, "02-skill", "evidencia-auditoria-pims")
CONOCIMIENTO = [
    os.path.join(SKILL, "references", "criterios_evidencia.md"),
    os.path.join(SKILL, "assets", "plantilla_hallazgo.md"),
    os.path.join(SKILL, "SKILL.md"),
    os.path.join(RAIZ, "03-asistente", "glosario_pims.md"),
]
LIMITE_VISOR = 300000               # caracteres que muestra el visor de evidencias
EXTENSIONES = {".md", ".txt", ".csv", ".json", ".log", ".pdf", ".docx", ".xlsx", ".png", ".jpg"}

os.makedirs(DATOS, exist_ok=True)
os.makedirs(PENDIENTES, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
CATALOGO = leer_catalogo(CATALOGO_POR_DEFECTO)
CONOCIMIENTO_RAG = Conocimiento(CONOCIMIENTO, CATALOGO, DATOS)   # comun a todos
PROYECTOS = Proyectos(DATOS, CONOCIMIENTO_RAG)


def _proyecto():
    """Proyecto de la peticion (cabecera X-Proyecto, ?proyecto= o campo del JSON)."""
    id_ = request.headers.get("X-Proyecto") or request.args.get("proyecto")
    if not id_ and request.is_json:
        id_ = (request.get_json(silent=True) or {}).get("proyecto")
    p = PROYECTOS.obtener(id_)
    if not p:
        raise ErrorProyecto("Elige o crea un proyecto antes de continuar")
    return p


@app.errorhandler(ErrorProyecto)
def _error_proyecto(e):
    return _error(str(e))


def _parametros_cobertura(fuente, p):
    rol = fuente.get("rol") or p.rol
    vigencia = int(fuente.get("vigencia", 365))
    fecha = fuente.get("fecha") or dt.date.today().isoformat()
    return rol, vigencia, dt.date.fromisoformat(fecha)


def _integridad_sin_registrar(p):
    """Como verificar_expediente, pero sin anotar en la cadena (para consultas)."""
    indice = leer_indice(p.expediente)
    resultados = {"OK": [], "ALTERADA": [], "FALTANTE": []}
    for ev in indice["evidencias"]:
        resultados[estado_integridad(p.expediente, ev)].append(ev["id"])
    problemas = comprobar_cadena(p.expediente, indice)
    return {"total": len(indice["evidencias"]), "resultados": resultados,
            "problemas_cadena": problemas,
            "integro": not (resultados["ALTERADA"] or resultados["FALTANTE"] or problemas)}


def _resumen(fuente, p):
    rol, vigencia, fecha = _parametros_cobertura(fuente, p)
    cob = evaluar_cobertura(p.expediente, CATALOGO, rol, vigencia, fecha)
    evidencias = leer_indice(p.expediente)["evidencias"]
    revisiones.aplicar(cob, p.expediente, evidencias)
    organizacion = ("Organizacion auditada (proyecto activo): %s%s. Todo el expediente de "
                    "abajo es de esta organizacion; no tienes datos de ninguna otra." % (
                        p.nombre, " - " + p.descripcion if p.descripcion else ""))
    return cob, organizacion + "\n" + asistente.resumen_expediente(
        cob, _integridad_sin_registrar(p), evidencias)


def _error(mensaje, codigo=400):
    return jsonify({"error": mensaje}), codigo


# --------------------------------------------------------------------------
@app.route("/")
def inicio():
    return render_template("index.html", tipos=TIPOS)


@app.route("/api/proyectos")
def api_proyectos():
    return jsonify([p.publico() for p in PROYECTOS.listar()])


@app.route("/api/proyectos", methods=["POST"])
def api_crear_proyecto():
    d = request.get_json(force=True)
    refs = {c["ref"] for c in CATALOGO}
    excluidos = [e for e in d.get("excluidos", []) if e.get("ref") in refs]
    p = PROYECTOS.crear(d.get("nombre"), d.get("rol", "responsable"), d.get("descripcion", ""),
                        excluidos)
    return jsonify(p.publico())


@app.route("/api/estado")
def api_estado():
    p = _proyecto()
    indice = leer_indice(p.expediente)
    integridad = _integridad_sin_registrar(p)
    estado_ev = {}
    for clave, ids in integridad["resultados"].items():
        for i in ids:
            estado_ev[i] = clave
    for ev in indice["evidencias"]:
        ev["integridad"] = estado_ev.get(ev["id"], "OK")
    try:
        rag = p.preparar_rag()
        info_rag = {"fragmentos": len(rag.fragmentos), "evidencias": len(rag.evidencias.fragmentos),
                    "norma": sum(f["tipo"] == "norma" for f in CONOCIMIENTO_RAG.fragmentos)}
    except llm_local.ErrorModelo:
        info_rag = {"fragmentos": 0, "evidencias": 0, "norma": 0}
    return jsonify({"proyecto": p.publico(), "modelo": llm_local.estado(),
                    "evidencias": indice["evidencias"], "integridad": integridad, "rag": info_rag})


@app.route("/api/catalogo")
def api_catalogo():
    return jsonify(CATALOGO)


def _evidencia(p, ev_id):
    """Registro de una evidencia y la ruta de su archivo dentro del expediente."""
    ev = next((e for e in leer_indice(p.expediente)["evidencias"] if e["id"] == ev_id), None)
    if not ev:
        return None, None
    ruta = os.path.realpath(os.path.join(p.expediente, ev["archivo"]))
    if not ruta.startswith(os.path.realpath(p.expediente) + os.sep):
        return None, None
    return ev, ruta


@app.route("/api/evidencia/<ev_id>")
def api_evidencia(ev_id):
    """Contenido de una evidencia archivada, en solo lectura (no toca la cadena)."""
    p = _proyecto()
    ev, ruta = _evidencia(p, ev_id)
    if not ev:
        return _error("Evidencia no encontrada", 404)
    existe = os.path.exists(ruta)
    texto = leer_texto(ruta, limite=LIMITE_VISOR + 1) if existe else ""
    return jsonify(dict(ev, integridad=estado_integridad(p.expediente, ev),
                        formato=os.path.splitext(ruta)[1].lower().lstrip("."),
                        texto=texto[:LIMITE_VISOR], truncado=len(texto) > LIMITE_VISOR,
                        existe=existe))


@app.route("/api/evidencia/<ev_id>/archivo")
def api_evidencia_archivo(ev_id):
    """El archivo original (PDF, imagen...) para verlo o descargarlo."""
    ev, ruta = _evidencia(_proyecto(), ev_id)
    if not ev or not os.path.exists(ruta):
        return _error("Archivo no encontrado", 404)
    return send_file(ruta, download_name=os.path.basename(ruta),
                     as_attachment=request.args.get("descargar") == "1")


@app.route("/api/norma/<ref>")
def api_norma(ref):
    """Texto de ISO/IEC 27701:2025 (ISOS/texto) para un control: requisito y guia."""
    secciones = norma.para_control(ref)
    if not secciones:
        return _error("No hay texto de la norma para %s en ISOS/texto "
                      "(ejecuta python extraer_norma.py)" % ref, 404)
    return jsonify({"ref": ref, "secciones": [
        {"ref": s["ref"], "titulo": s["titulo"], "cita": norma.cita(s), "texto": s["texto"]}
        for s in secciones]})


@app.route("/api/cobertura")
def api_cobertura():
    try:
        cob, _ = _resumen(request.args, _proyecto())
    except (ValueError, KeyError) as e:
        if isinstance(e, ErrorProyecto):
            raise
        return _error(str(e))
    return jsonify(cob)


@app.route("/api/verificar", methods=["POST"])
def api_verificar():
    p = _proyecto()
    with p.bloqueo:
        return jsonify(verificar_expediente(p.expediente, "auditor (web)"))


@app.route("/api/sugerir", methods=["POST"])
def api_sugerir():
    p = _proyecto()
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
        sugerencia = asistente.sugerir_clasificacion(p.preparar_rag(), CATALOGO, nombre,
                                                     leer_texto(ruta))
    except llm_local.ErrorModelo as e:
        return _error(str(e), 503)
    sugerencia.update({"token": token, "nombre": nombre})
    return jsonify(sugerencia)


@app.route("/api/registrar", methods=["POST"])
def api_registrar():
    p = _proyecto()
    d = request.get_json(force=True)
    token, nombre = d.get("token", ""), os.path.basename(d.get("nombre", ""))
    ruta = os.path.join(PENDIENTES, token + "_" + nombre)
    if not token.isalnum() or not os.path.isfile(ruta):
        return _error("La subida expiro; vuelve a adjuntar el archivo")
    try:
        rag = p.preparar_rag()
        with p.bloqueo:
            ev = registrar_evidencia(
                p.expediente, ruta, d.get("controles", []), d.get("tipo", ""),
                d.get("titulo", "").strip() or nombre, d.get("responsable", "").strip()
                or "auditor (web)", d.get("fuente", ""), d.get("fecha_documento") or None,
                nombre_original=nombre)
            rag.agregar_evidencia(ev)
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
    p = _proyecto()
    d = request.get_json(force=True)
    mensaje = (d.get("mensaje") or "").strip()
    if not mensaje:
        return _error("Escribe una pregunta")
    try:
        _, resumen = _resumen(d, p)
        respuesta, fuentes = asistente.responder(p.preparar_rag(), mensaje,
                                                 d.get("historial", []), resumen)
    except llm_local.ErrorModelo as e:
        return _error(str(e), 503)
    return jsonify({"respuesta": respuesta, "fuentes": fuentes,
                    "nodos": grafo.nodos_de_fuentes(fuentes, [c["ref"] for c in CATALOGO])})


@app.route("/api/grafo")
def api_grafo():
    """Grafo de conocimiento del agente en el proyecto activo (pestana Grafo)."""
    p = _proyecto()
    try:
        cob, _ = _resumen(request.args, p)
    except (ValueError, KeyError) as e:
        return _error(str(e))
    integridad = {}
    for clave, ids in _integridad_sin_registrar(p)["resultados"].items():
        for i in ids:
            integridad[i] = clave
    return jsonify(grafo.construir(CATALOGO, CONOCIMIENTO_RAG, p, cob,
                                   leer_indice(p.expediente)["evidencias"], integridad))


@app.route("/api/hallazgo", methods=["POST"])
def api_hallazgo():
    p = _proyecto()
    d = request.get_json(force=True)
    cob, resumen = _resumen(d, p)
    fila = next((f for f in cob["controles"] if f["ref"] == d.get("ref")), None)
    if not fila:
        return _error("Control no encontrado")
    if fila["estado"] in ("Cubierto", "No aplica"):
        return _error("El control %s esta %s: no genera hallazgo" % (fila["ref"], fila["estado"]))
    try:
        texto = asistente.redactar_hallazgo(p.preparar_rag(), fila, resumen)
    except llm_local.ErrorModelo as e:
        return _error(str(e), 503)
    return jsonify({"ref": fila["ref"], "hallazgo": texto})


@app.route("/api/pertinencia", methods=["POST"])
def api_pertinencia():
    """La IA lee las evidencias de un control y propone si lo demuestran (paso 4)."""
    p = _proyecto()
    d = request.get_json(force=True)
    cob, _ = _resumen(d, p)
    fila = next((f for f in cob["controles"] if f["ref"] == d.get("ref")), None)
    if not fila:
        return _error("Control no encontrado")
    if fila["estado"] not in revisiones.EVALUABLES:
        return _error("El control %s esta %s: no hay evidencia valida que revisar"
                      % (fila["ref"], fila["estado"]))
    control = next(c for c in CATALOGO if c["ref"] == fila["ref"])
    indice = leer_indice(p.expediente)["evidencias"]
    leidas = [dict(ev, texto=leer_texto(os.path.join(p.expediente, ev["archivo"]),
                                        limite=200000))
              for ev in indice if ev["id"] in fila["evidencias"]]
    try:
        propuesta = asistente.evaluar_pertinencia(control, fila, leidas)
    except llm_local.ErrorModelo as e:
        return _error(str(e), 503)
    with p.bloqueo:
        rev = revisiones.guardar_propuesta(p.expediente, fila["ref"], propuesta, indice,
                                           fila["evidencias"], llm_local.MODELO_CHAT)
    return jsonify(rev)


@app.route("/api/pertinencia/decision", methods=["POST"])
def api_pertinencia_decision():
    """El auditor acepta o rechaza la propuesta; queda anotado en la cadena de custodia."""
    p = _proyecto()
    d = request.get_json(force=True)
    if d.get("decision") not in ("aceptada", "rechazada"):
        return _error("La decision debe ser 'aceptada' o 'rechazada'")
    cob, _ = _resumen(d, p)
    fila = next((f for f in cob["controles"] if f["ref"] == d.get("ref")), {})
    if not fila.get("revision", {}).get("vigente"):
        return _error("Las evidencias del control cambiaron: vuelve a evaluarlo con la IA")
    try:
        with p.bloqueo:
            rev = revisiones.decidir(p.expediente, d.get("ref", ""), d["decision"],
                                     (d.get("auditor") or "").strip() or "auditor (web)",
                                     (d.get("comentario") or "").strip())
    except ValueError as e:
        return _error(str(e))
    return jsonify(rev)


def preparar():
    """Construye o carga la base de conocimiento comun antes de atender peticiones."""
    try:
        print("Conocimiento:", CONOCIMIENTO_RAG.construir(), "-",
              len(CONOCIMIENTO_RAG.fragmentos), "fragmentos")
        for p in PROYECTOS.listar():
            print("Proyecto %s: indice de evidencias %s" % (p.id, p.rag.construir()))
            p._rag_listo = True
    except llm_local.ErrorModelo as e:
        print("AVISO:", e)


if __name__ == "__main__":
    preparar()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
