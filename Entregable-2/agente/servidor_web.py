# -*- coding: utf-8 -*-
"""
Servidor web del Agente autonomo (Entregable 2).

    python servidor_web.py          # http://127.0.0.1:5000  (PORT para cambiarlo)

Sirve en un solo proceso la aplicacion del Entregable 1 (en /) y el panel del
agente autonomo (en /agente) con su API JSON (/api/agente/...). No modifica
ningun archivo del Entregable 1: registra un Blueprint sobre su Flask
(nucleo.app_e1.app) e inyecta en la portada un enlace flotante al panel.
"""

import datetime as dt
import inspect
import json
import os
import re
import threading
import uuid

from flask import Blueprint, jsonify, render_template, request

import nucleo
import herramientas

AQUI = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(AQUI, "web")
BITACORAS = {
    "decisiones": os.path.join(nucleo.DATOS, "bitacora_decisiones.jsonl"),
    "mcp": os.path.join(nucleo.DATOS, "bitacora_mcp.jsonl"),
    "eventos": os.path.join(nucleo.DATOS, "eventos.jsonl"),
}
TIPOS_EJECUCION = ("auditoria_interna", "incidente", "bandeja")
EXTENSIONES = nucleo.app_e1.EXTENSIONES
CON_IA = {"clasificar", "buscar", "evaluar_pertinencia", "redactar_hallazgo", "preguntar"}


# ----------------------------------------------------------------------------
# Modulos del orquestador (los escribe otro componente del Entregable 2). Si aun
# no existen se usa un sustituto en memoria SOLO para poder probar el panel.
try:
    import orquestador
    ORQUESTADOR_REAL = True
except ImportError:
    ORQUESTADOR_REAL = False

    class _OrquestadorProvisional:
        """Sustituto temporal del orquestador: mismo contrato, estado en memoria."""

        NODOS = [("integridad", "Verificar integridad del expediente"),
                 ("cobertura", "Calcular matriz de cobertura"),
                 ("hallazgos", "Redactar hallazgos preliminares"),
                 ("pertinencia", "Evaluar pertinencia de evidencias"),
                 ("aprobacion", "Aprobacion del auditor (HITL)"),
                 ("informe", "Generar informe de auditoria"),
                 ("plan_accion", "Plan de accion")]

        def __init__(self):
            self._ej = {}
            self._lock = threading.Lock()

        @staticmethod
        def _ahora():
            return dt.datetime.now().astimezone().isoformat(timespec="seconds")

        def iniciar(self, tipo, proyecto="unsa", parametros=None):
            if tipo not in TIPOS_EJECUCION:
                raise ValueError("Tipo de ejecucion no valido: %s" % tipo)
            nodos = self.NODOS if tipo == "auditoria_interna" else [
                ("recibir", "Recibir notificacion"), ("analizar", "Analizar impacto en el PIMS"),
                ("registrar", "Registrar en bitacora")]
            e = {"id": uuid.uuid4().hex[:12], "tipo": tipo, "proyecto": proyecto,
                 "parametros": parametros or {}, "estado": "en_curso", "creado": self._ahora(),
                 "actualizado": self._ahora(), "paso_actual": nodos[0][0],
                 "pasos": [{"nodo": n, "titulo": t, "estado": "pendiente", "inicio": None,
                            "fin": None, "resumen": ""} for n, t in nodos],
                 "aprobacion": None, "resultado": None, "error": None}
            self._ej[e["id"]] = e
            threading.Thread(target=self._correr, args=(e,), daemon=True).start()
            return json.loads(json.dumps(e))

        def _paso(self, e, nodo, estado, resumen=""):
            p = next(x for x in e["pasos"] if x["nodo"] == nodo)
            p["estado"] = estado
            if estado == "en_curso":
                p["inicio"] = self._ahora()
                e["paso_actual"] = nodo
            else:
                p["fin"] = self._ahora()
            if resumen:
                p["resumen"] = resumen
            e["actualizado"] = self._ahora()

        def _correr(self, e):
            try:
                if e["tipo"] != "auditoria_interna":
                    for p in e["pasos"]:
                        self._paso(e, p["nodo"], "en_curso")
                        self._paso(e, p["nodo"], "ok", "Simulado (orquestador provisional)")
                    e["estado"], e["resultado"] = "completada", {"informe": None, "plan_accion": []}
                    return
                par = e["parametros"]
                rapido = bool(par.get("modo_rapido", True))
                self._paso(e, "integridad", "en_curso")
                est = herramientas.estado_expediente(e["proyecto"])
                integ = est["integridad"]
                self._paso(e, "integridad", "ok", "%s evidencias, %s" % (
                    integ["total"], "integro" if integ["integro"] else "CON FALLOS"))
                self._paso(e, "cobertura", "en_curso")
                cob = herramientas.matriz_cobertura(e["proyecto"], par.get("rol"),
                                                    int(par.get("vigencia_dias", 365)))
                self._paso(e, "cobertura", "ok", "Cobertura %s%%" % cob["porcentaje_cobertura"])
                self._paso(e, "hallazgos", "en_curso")
                pend = [f for f in cob["controles"] if f["estado"] not in ("Cubierto", "No aplica")]
                hall = []
                for i, f in enumerate(pend):
                    texto = f.get("nota") or "Control %s en estado %s." % (f["ref"], f["estado"])
                    if not rapido and i < int(par.get("max_hallazgos", 3)):
                        try:
                            texto = herramientas.redactar_hallazgo(f["ref"], e["proyecto"])["hallazgo"]
                        except Exception as ex:  # noqa: BLE001
                            texto += " (IA no disponible: %s)" % ex
                    hall.append({"ref": f["ref"], "estado": f["estado"], "texto": texto})
                self._paso(e, "hallazgos", "ok", "%d hallazgos" % len(hall))
                self._paso(e, "pertinencia", "en_curso")
                props = []
                if rapido:
                    self._paso(e, "pertinencia", "omitido", "Modo rapido: sin IA")
                else:
                    evals = [f for f in cob["controles"] if f["estado"] in ("Cubierto", "Parcial")]
                    for f in evals[:int(par.get("max_pertinencia", 2))]:
                        try:
                            r = herramientas.evaluar_pertinencia(f["ref"], e["proyecto"])
                            props.append({"ref": f["ref"], "veredicto": r.get("veredicto"),
                                          "justificacion": r.get("justificacion", "")})
                        except Exception:  # noqa: BLE001
                            pass
                    self._paso(e, "pertinencia", "ok", "%d propuestas" % len(props))
                self._paso(e, "aprobacion", "en_curso")
                e["aprobacion"] = {"pendiente": True, "pregunta": "Revisa los hallazgos y "
                                   "propuestas preliminares y aprueba o rechaza el informe.",
                                   "hallazgos": hall, "propuestas": props}
                e["estado"] = "esperando_aprobacion"
                e["actualizado"] = self._ahora()
            except Exception as ex:  # noqa: BLE001
                e["estado"], e["error"] = "error", str(ex)

        def obtener(self, id_):
            e = self._ej.get(id_)
            return json.loads(json.dumps(e)) if e else None

        def listar(self, proyecto=None):
            return sorted((self.obtener(i) for i, e in self._ej.items()
                           if proyecto in (None, e["proyecto"])),
                          key=lambda x: x["creado"], reverse=True)

        def aprobar(self, id_, decision, auditor, comentario="", decisiones_controles=None):
            with self._lock:
                e = self._ej.get(id_)
                if not e or e["estado"] != "esperando_aprobacion":
                    raise ValueError("La ejecucion no espera aprobacion")
                e["aprobacion"]["pendiente"] = False
                if decision == "rechazada":
                    self._paso(e, "aprobacion", "error", "Rechazada por %s" % auditor)
                    e["estado"] = "rechazada"
                    return self.obtener(id_)
                self._paso(e, "aprobacion", "ok", "Aprobada por %s" % auditor)
                self._paso(e, "informe", "en_curso")
                hall = {h["ref"]: h["texto"] for h in e["aprobacion"]["hallazgos"]}
                inf = herramientas.generar_informe(e["proyecto"], hall, auditor, comentario)
                self._paso(e, "informe", "ok", os.path.basename(inf["ruta"]))
                self._paso(e, "plan_accion", "en_curso")
                plan = [{"ref": h["ref"], "accion": "Subsanar: " + h["estado"],
                         "responsable": "Responsable del PIMS", "prioridad":
                         "Alta" if h["estado"] in ("Sin evidencia", "Comprometida") else "Media",
                         "plazo_dias": 30} for h in e["aprobacion"]["hallazgos"]]
                self._paso(e, "plan_accion", "ok", "%d acciones" % len(plan))
                e["resultado"] = {"informe": inf, "plan_accion": plan}
                e["estado"] = "completada"
                return self.obtener(id_)

    orquestador = _OrquestadorProvisional()

try:
    import coordinacion
except ImportError:
    coordinacion = None

try:
    import bandeja
except ImportError:
    bandeja = None


# ----------------------------------------------------------------------------
bp = Blueprint("agente", __name__, template_folder=WEB, static_folder=WEB,
               static_url_path="/agente/static")


def _error(mensaje, codigo=400):
    return jsonify({"error": mensaje}), codigo


def _json():
    return request.get_json(silent=True) or {}


def _publica(e):
    """Anade a la ejecucion el nombre del informe (para pedirlo con /api/agente/informe)."""
    if not e:
        return e
    inf = (e.get("resultado") or {}).get("informe")
    ruta = inf.get("ruta") if isinstance(inf, dict) else inf
    if isinstance(ruta, str) and ruta.lower().endswith(".md"):
        e["informe_nombre"] = os.path.basename(ruta)
    return e


@bp.route("/agente")
def panel():
    return render_template("agente.html", real=ORQUESTADOR_REAL)


@bp.route("/api/agente/ejecuciones")
def api_listar():
    return jsonify([_publica(e) for e in orquestador.listar(request.args.get("proyecto"))])


@bp.route("/api/agente/ejecuciones", methods=["POST"])
def api_iniciar():
    d = _json()
    tipo = d.get("tipo")
    if tipo not in TIPOS_EJECUCION:
        return _error("Tipo no valido (usa %s)" % ", ".join(TIPOS_EJECUCION))
    parametros = d.get("parametros") or {}
    if not isinstance(parametros, dict):
        return _error("parametros debe ser un objeto")
    try:
        e = orquestador.iniciar(tipo, d.get("proyecto") or "unsa", parametros)
    except (nucleo.ErrorAgente, ValueError, KeyError) as ex:
        return _error(str(ex))
    return jsonify(_publica(e)), 202


@bp.route("/api/agente/ejecuciones/<id_>")
def api_obtener(id_):
    e = orquestador.obtener(id_)
    return jsonify(_publica(e)) if e else _error("Ejecucion no encontrada", 404)


@bp.route("/api/agente/ejecuciones/<id_>/aprobar", methods=["POST"])
def api_aprobar(id_):
    d = _json()
    if d.get("decision") not in ("aprobada", "rechazada"):
        return _error("La decision debe ser 'aprobada' o 'rechazada'")
    auditor = (d.get("auditor") or "").strip()
    if not auditor:
        return _error("Indica el nombre del auditor que valida")
    dc = d.get("decisiones_controles") or {}
    if not isinstance(dc, dict) or any(v not in ("aceptada", "rechazada") for v in dc.values()):
        return _error("decisiones_controles: {ref: 'aceptada'|'rechazada'}")
    if not orquestador.obtener(id_):
        return _error("Ejecucion no encontrada", 404)
    try:
        e = orquestador.aprobar(id_, d["decision"], auditor, (d.get("comentario") or "").strip(),
                                decisiones_controles=dc)
    except (nucleo.ErrorAgente, ValueError, KeyError) as ex:
        return _error(str(ex))
    return jsonify(_publica(e))


@bp.route("/api/agente/incidente", methods=["POST"])
def api_incidente():
    descripcion = (_json().get("descripcion") or "").strip()
    if not descripcion:
        return _error("Describe el incidente")
    try:
        if coordinacion is not None:
            r = coordinacion.simular_agente_incidentes(descripcion)
        else:   # sin coordinacion.py: se lanza directamente el flujo de incidente
            r = orquestador.iniciar("incidente", "unsa", {"descripcion": descripcion})
    except (nucleo.ErrorAgente, ValueError, KeyError) as ex:
        return _error(str(ex))
    return jsonify(_publica(r) if isinstance(r, dict) and "pasos" in r else r), 202


def _nombre_seguro(nombre):
    nombre = os.path.basename((nombre or "").replace("\\", "/")).strip()
    nombre = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", nombre)
    return nombre.lstrip(".")


@bp.route("/api/agente/bandeja", methods=["POST"])
def api_subir_bandeja():
    archivos = request.files.getlist("archivo")
    if not archivos or not any(a.filename for a in archivos):
        return _error("Adjunta un archivo")
    guardados = []
    for a in archivos:
        nombre = _nombre_seguro(a.filename)
        base, ext = os.path.splitext(nombre)
        if not base or ext.lower() not in EXTENSIONES:
            return _error("Formato no admitido: %s (usa %s)" % (
                nombre or a.filename, ", ".join(sorted(EXTENSIONES))))
        destino = os.path.join(nucleo.BANDEJA, nombre)
        if os.path.exists(destino):
            nombre = "%s_%s%s" % (base, dt.datetime.now().strftime("%Y%m%d%H%M%S"), ext)
            destino = os.path.join(nucleo.BANDEJA, nombre)
        a.save(destino)
        guardados.append(nombre)
    return jsonify({"guardados": guardados, "carpeta": nucleo.BANDEJA})


@bp.route("/api/agente/bandeja")
def api_listar_bandeja():
    raiz = nucleo.BANDEJA
    filas = []
    for actual, carpetas, archivos in os.walk(raiz):
        rel = os.path.relpath(actual, raiz)
        if rel.count(os.sep) >= 1 and rel != ".":
            carpetas[:] = []
        for n in archivos:
            ruta = os.path.join(actual, n)
            st = os.stat(ruta)
            filas.append({"nombre": n, "carpeta": "" if rel == "." else rel.replace(os.sep, "/"),
                          "bytes": st.st_size, "modificado": dt.datetime.fromtimestamp(
                              st.st_mtime).astimezone().isoformat(timespec="seconds")})
    filas.sort(key=lambda f: f["modificado"], reverse=True)
    return jsonify({"carpeta": raiz, "archivos": filas,
                    "automatizacion": bandeja is not None})


def _ultimas_lineas(ruta, n=100):
    if not os.path.isfile(ruta):
        return []
    with open(ruta, encoding="utf-8", errors="replace") as f:
        lineas = [x for x in f.read().splitlines() if x.strip()][-n:]
    salida = []
    for x in lineas:
        try:
            salida.append(json.loads(x))
        except ValueError:
            salida.append({"linea": x})
    return salida[::-1]     # lo mas reciente primero


@bp.route("/api/agente/bitacora")
def api_bitacora():
    tipo = request.args.get("tipo", "decisiones")
    if tipo not in BITACORAS:
        return _error("tipo: decisiones | mcp | eventos")
    return jsonify({"tipo": tipo, "registros": _ultimas_lineas(BITACORAS[tipo])})


@bp.route("/api/agente/informe/<nombre>")
def api_informe(nombre):
    if nombre != os.path.basename(nombre) or not nombre.lower().endswith(".md"):
        return _error("Nombre de informe no valido", 404)
    raiz = os.path.realpath(nucleo.SALIDAS)
    ruta = os.path.realpath(os.path.join(raiz, nombre))
    if not ruta.startswith(raiz + os.sep) or not os.path.isfile(ruta):
        return _error("Informe no encontrado", 404)
    with open(ruta, encoding="utf-8", errors="replace") as f:
        return jsonify({"nombre": nombre, "contenido": f.read()})


@bp.route("/api/agente/herramientas")
def api_herramientas():
    salida = []
    for nombre, fn in herramientas.HERRAMIENTAS.items():
        try:
            firma = str(inspect.signature(fn))
        except (TypeError, ValueError):
            firma = "(...)"
        salida.append({"nombre": nombre, "firma": firma, "doc": inspect.getdoc(fn) or "",
                       "ia": nombre in CON_IA})
    return jsonify(salida)


@bp.route("/api/agente/resumen")
def api_resumen():
    try:
        p = nucleo.proyecto("unsa")
        cob = herramientas.matriz_cobertura("unsa")
        integ = nucleo.app_e1._integridad_sin_registrar(p)
        n_ev = len(nucleo.leer_indice(p.expediente)["evidencias"])
    except (nucleo.ErrorAgente, ValueError, KeyError) as ex:
        return _error(str(ex), 500)
    return jsonify({"proyecto": p.publico(), "porcentaje_cobertura": cob["porcentaje_cobertura"],
                    "controles_aplicables": cob["controles_aplicables"],
                    "conteo_estados": cob["conteo_estados"], "rol": cob["rol"],
                    "fecha_corte": cob["fecha_corte"], "integridad": integ, "evidencias": n_ev,
                    "orquestador_real": ORQUESTADOR_REAL})


# ------------------------------------------------- enlace al panel desde la portada
BOTON_AGENTE = (
    '<a href="/agente" id="enlace-agente-autonomo" style="position:fixed;right:20px;bottom:20px;'
    'z-index:50;background:#1f4e5f;color:#fff;padding:10px 16px;border-radius:99px;'
    'font:600 14px/1.2 \'Segoe UI\',system-ui,sans-serif;text-decoration:none;'
    'box-shadow:0 6px 18px rgba(0,0,0,.22)">Agente aut&oacute;nomo &rarr;</a>')


@bp.after_app_request
def _inyectar_enlace(resp):
    if (request.path == "/" and request.method == "GET" and resp.status_code == 200
            and resp.mimetype == "text/html" and not resp.direct_passthrough):
        html = resp.get_data(as_text=True)
        i = html.lower().rfind("</body>")
        if i != -1 and "enlace-agente-autonomo" not in html:
            resp.set_data(html[:i] + BOTON_AGENTE + html[i:])
    return resp


nucleo.app_e1.app.register_blueprint(bp)
app = nucleo.app_e1.app


if __name__ == "__main__":
    nucleo.preparar()
    if bandeja is not None and hasattr(bandeja, "iniciar_automatizacion"):
        bandeja.iniciar_automatizacion()
    if not ORQUESTADOR_REAL:
        print("AVISO: orquestador.py no encontrado; se usa un sustituto provisional en memoria")
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False, threaded=True)
