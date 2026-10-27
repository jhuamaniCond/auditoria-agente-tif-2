# -*- coding: utf-8 -*-
"""
Orquestador del Agente de Evidencia y Auditoria (capa de gobernanza del PIMS).

Encadena las herramientas de herramientas.py en grafos de LangGraph con una
puerta de aprobacion humana (HITL, ``interrupt``) antes de cualquier salida
que comprometa a la organizacion: el informe de auditoria interna (9.2), el
informe de un incidente (A.3.12) o el registro de evidencias de la bandeja.

Grafos (tipo de ejecucion):

  auditoria_interna  planificar -> verificar_integridad -[alterada]-> alerta_integridad
                     -> matriz_cobertura -> evaluar_pertinencia -> priorizar
                     -> redactar_hallazgos -> aprobacion_auditor (HITL)
                     -[aprobada]-> generar_informe -> plan_accion -> FIN
                     -[rechazada]-> FIN
  incidente          recibir_evento -> registrar_incidente -> verificar_integridad
                     -> buscar_relacionadas -> aprobacion_dpo (HITL)
                     -[aprobada]-> informe_incidente -> FIN
  bandeja            tomar_archivos -[vacia]-> FIN
                     -> clasificar -> aprobacion_bandeja (HITL ligera)
                     -> registrar -> mover -> FIN   (rechazada: -> mover)

API publica (la usa la web y la linea de comandos):

    iniciar(tipo, proyecto="unsa", parametros=None) -> dict
    obtener(id) -> dict | None
    listar(proyecto=None) -> list[dict]
    aprobar(id, decision, auditor, comentario="", decisiones_controles=None) -> dict

parametros (todos opcionales):
    modo_rapido      True: ninguna llamada al LLM ni a embeddings (textos deterministas)
    max_pertinencia  controles Cubierto/Parcial que evalua la IA (3)
    max_hallazgos    hallazgos que redacta la IA; el resto es determinista (3)
    alcance, rol, vigencia_dias, fecha_corte, periodo ("AAAA-MM-DD/AAAA-MM-DD")
    evento / descripcion            (incidente)
    archivos, auto_registrar        (bandeja)

Cada ejecucion se guarda en datos/ejecuciones/<id>.json tras cada paso; el
estado del grafo vive en el checkpointer de LangGraph (SqliteSaver en
datos/ejecuciones/checkpoints.sqlite) para reanudar tras la aprobacion aunque
el proceso se haya reiniciado. Toda decision del agente y del humano queda en
datos/bitacora_decisiones.jsonl (registro de decisiones).
"""

import datetime as dt
import json
import os
import random
import re
import shutil
import string
import threading
import time
import traceback
import unicodedata
from typing import Annotated, TypedDict

import nucleo
import herramientas
from nucleo import CATALOGO, ErrorAgente, asistente, leer_indice, leer_texto, revisiones

from langgraph.errors import GraphBubbleUp
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

MOTOR = "LangGraph"
BITACORA = os.path.join(nucleo.DATOS, "bitacora_decisiones.jsonl")
INSTANTANEAS = os.path.join(nucleo.EJECUCIONES, "_estado")
INCIDENTES = os.path.join(nucleo.SALIDAS, "incidentes")
for _c in (INSTANTANEAS, INCIDENTES):
    os.makedirs(_c, exist_ok=True)

ESTADOS_ABIERTOS = ("en_curso", "esperando_aprobacion")
REFS = {c["ref"]: c for c in CATALOGO}
ACTOR = herramientas.RESPONSABLE           # "agente-evidencia"


def _ahora():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


# =====================================================================
# Checkpointer (SqliteSaver si esta instalado; si no, memoria + JSON)
# =====================================================================
def _crear_checkpointer():
    try:
        import sqlite3
        from langgraph.checkpoint.sqlite import SqliteSaver
        con = sqlite3.connect(os.path.join(nucleo.EJECUCIONES, "checkpoints.sqlite"),
                              check_same_thread=False)
        return SqliteSaver(con), "SqliteSaver"
    except ImportError:
        from langgraph.checkpoint.memory import InMemorySaver
        return InMemorySaver(), "MemorySaver"


CHECKPOINTER, TIPO_CHECKPOINTER = _crear_checkpointer()


# =====================================================================
# Bitacora de decisiones (capa de gobernanza)
# =====================================================================
_CANDADO_BITACORA = threading.Lock()


def registrar_decision(ejecucion, nodo, decision, actor=ACTOR, humano=False, detalle=None,
                       tipo=None, proyecto=None):
    """Anade una linea a la bitacora JSONL (append-only)."""
    linea = {"fecha": _ahora(), "ejecucion": ejecucion, "flujo": tipo, "proyecto": proyecto,
             "nodo": nodo, "actor": actor, "origen": "humano" if humano else "agente",
             "decision": decision, "detalle": detalle or {}}
    with _CANDADO_BITACORA:
        with open(BITACORA, "a", encoding="utf-8") as f:
            f.write(json.dumps(linea, ensure_ascii=False, default=str) + "\n")
    return linea


def leer_bitacora(ejecucion=None, n=500):
    if not os.path.exists(BITACORA):
        return []
    with open(BITACORA, encoding="utf-8") as f:
        lineas = [json.loads(x) for x in f if x.strip()]
    if ejecucion:
        lineas = [x for x in lineas if x.get("ejecucion") == ejecucion]
    return lineas[-n:]


def _decidir(estado, nodo, decision, **detalle):
    return registrar_decision(estado["ejecucion"], nodo, decision, detalle=detalle,
                              tipo=estado.get("tipo"), proyecto=estado["proyecto"])


def _publicar(tipo, **datos):
    """Evento al bus de coordinacion (si existe); nunca rompe el flujo."""
    try:
        import coordinacion
        return coordinacion.publicar(dict(datos, tipo=tipo, origen=ACTOR))
    except Exception:                        # noqa: BLE001
        return None


# =====================================================================
# Persistencia de ejecuciones
# =====================================================================
_CANDADO = threading.RLock()
_HILOS = {}


def _ruta(id_):
    if not id_ or not re.fullmatch(r"[A-Za-z0-9-]{1,80}", str(id_)):
        raise ErrorAgente("Identificador de ejecucion no valido: %r" % (id_,))
    return os.path.join(nucleo.EJECUCIONES, id_ + ".json")


def _escribir_json(ruta, datos):
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2, default=str)
    for intento in range(10):               # Windows: el lector puede tenerlo abierto
        try:
            os.replace(tmp, ruta)
            return
        except PermissionError:
            time.sleep(0.05 * (intento + 1))
    os.replace(tmp, ruta)


def _guardar(ej):
    ej["actualizado"] = _ahora()
    with _CANDADO:
        _escribir_json(_ruta(ej["id"]), ej)


def obtener(id_):
    """Ejecucion por id (dict JSON) o None."""
    try:
        ruta = _ruta(id_)
    except ErrorAgente:
        return None
    if not os.path.exists(ruta):
        return None
    for intento in range(5):
        try:
            with open(ruta, encoding="utf-8") as f:
                return json.load(f)
        except (ValueError, PermissionError):
            time.sleep(0.05 * (intento + 1))
    return None


def listar(proyecto=None):
    """Ejecuciones (mas recientes primero), opcionalmente de un proyecto."""
    salida = []
    for nombre in os.listdir(nucleo.EJECUCIONES):
        if not nombre.endswith(".json") or nombre.startswith("_"):
            continue
        ej = obtener(nombre[:-5])
        if ej and (proyecto is None or ej.get("proyecto") == proyecto):
            salida.append(ej)
    salida.sort(key=lambda e: (e.get("creado", ""), e.get("id", "")), reverse=True)
    return salida


def _modificar(id_, fn):
    with _CANDADO:
        ej = obtener(id_)
        if ej is None:
            return None
        fn(ej)
        _guardar(ej)
        return ej


def _marcar_paso(id_, nodo, estado, resumen=None, resultado=None):
    def fn(ej):
        for p in ej["pasos"]:
            if p["nodo"] != nodo:
                continue
            p["estado"] = estado
            if estado == "en_curso":
                p["inicio"] = p.get("inicio") or _ahora()
                ej["paso_actual"] = nodo
            else:
                p["fin"] = _ahora()
                p["inicio"] = p.get("inicio") or p["fin"]
            if resumen is not None:
                p["resumen"] = resumen
        if resultado:
            ej["resultado"] = dict(ej.get("resultado") or {}, **resultado)
    _modificar(id_, fn)


def _guardar_instantanea(estado):
    _escribir_json(os.path.join(INSTANTANEAS, estado["ejecucion"] + ".json"), estado)


def _leer_instantanea(id_):
    ruta = os.path.join(INSTANTANEAS, id_ + ".json")
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


# =====================================================================
# Estado del grafo
# =====================================================================
def _fusionar(a, b):
    r = dict(a or {})
    r.update(b or {})
    return r


class Estado(TypedDict, total=False):
    ejecucion: str
    tipo: str
    proyecto: str
    parametros: dict
    resultado: Annotated[dict, _fusionar]
    estado_final: str
    respuesta: dict                 # decision humana en la puerta HITL
    # auditoria interna
    plan: dict
    integridad: dict
    cobertura: dict
    propuestas: list
    hallazgos: list
    hallazgos_finales: list
    # incidente
    evento: dict
    evidencia: dict
    relacionadas: list
    controles_incidente: list
    # bandeja
    archivos: list
    clasificaciones: list
    decisiones_archivos: dict
    registradas: list


def _rapido(estado):
    return bool((estado.get("parametros") or {}).get("modo_rapido"))


def _entero(estado, clave, defecto):
    try:
        return max(0, int((estado.get("parametros") or {}).get(clave, defecto)))
    except (TypeError, ValueError):
        return defecto


def _nodo(nombre, fn):
    """Envuelve un nodo: marca el paso en la ejecucion y guarda el JSON tras cada paso."""
    def envoltura(estado):
        id_ = estado["ejecucion"]
        _marcar_paso(id_, nombre, "en_curso")
        try:
            salida = fn(estado) or {}
        except GraphBubbleUp:               # interrupt() de la puerta HITL: no es error
            raise
        except Exception as e:              # noqa: BLE001
            _marcar_paso(id_, nombre, "error", resumen="%s: %s" % (type(e).__name__, e))
            raise
        resumen = salida.pop("_resumen", "")
        omitido = salida.pop("_omitido", False)
        _marcar_paso(id_, nombre, "omitido" if omitido else "ok", resumen,
                     salida.get("resultado"))
        return salida
    envoltura.__name__ = nombre
    return envoltura


# =====================================================================
# Utilidades deterministas
# =====================================================================
ESTADO_PESO = {"Comprometida": 40, "Sin evidencia": 30, "Desactualizada": 20, "Parcial": 10}
PLAZO_POR_NIVEL = {3: 30, 2: 60, 1: 90}

CAUSA = {
    "Comprometida": "El archivo registrado ya no coincide con su SHA-256 o la cadena de custodia "
                    "presenta roturas: posible modificacion posterior al registro.",
    "Sin evidencia": "No se ha documentado o no se ha aportado al expediente la evidencia del "
                     "control.",
    "Desactualizada": "La evidencia existe pero no se ha revisado ni reaprobado dentro del "
                      "periodo de vigencia.",
    "Parcial": "La evidencia aportada no alcanza el minimo requerido o no cubre todos los "
               "elementos esperados.",
}
RECOMENDACION = {
    "Comprometida": "Investigar la alteracion, recuperar el original desde su fuente, registrarlo "
                    "de nuevo y documentar la causa en el registro de no conformidades (10.2).",
    "Sin evidencia": "Elaborar, aprobar y registrar en el expediente la evidencia esperada.",
    "Desactualizada": "Revisar, reaprobar y registrar la version vigente del documento.",
    "Parcial": "Completar la evidencia faltante y registrarla en el expediente.",
}


def _nivel(clasificacion):
    c = clasificacion.lower()
    if "mayor" in c:
        return 3
    if "observacion" in c:
        return 1
    return 2


def _texto_determinista(fila, clasificacion=None):
    control = REFS.get(fila["ref"], {})
    clasificacion = clasificacion or asistente.clasificacion_propuesta(fila)
    nota = fila.get("nota") or ""
    criterio = "ISO/IEC 27701:2025, %s - %s." % (fila["ref"], fila.get("titulo", ""))
    if control.get("evidencia_esperada") and not nota.startswith("Se espera"):
        criterio += " Evidencia esperada: %s." % control["evidencia_esperada"]
    efecto = ("Riesgo de incumplimiento de la Ley N.o 29733 y de no conformidad en la auditoria "
              "de certificacion" if fila["ref"] in asistente.CRITICOS or fila.get("grupo") ==
              "clausula" else "Debilita la capacidad de demostrar el control ante el auditor externo")
    return "\n".join([
        "**Clasificacion propuesta:** %s" % clasificacion,
        "- **Criterio:** %s" % criterio,
        "- **Condicion:** El control esta en estado \"%s\". %s" % (fila["estado"], nota),
        "- **Causa (preliminar):** %s" % CAUSA.get(fila["estado"], "Por determinar con el area."),
        "- **Efecto:** %s." % efecto,
        "- **Recomendacion:** %s" % RECOMENDACION.get(fila["estado"], "Analizar con el area."),
        "",
        "_Texto determinista generado desde la matriz de cobertura (sin IA); "
        "requiere validacion del auditor._"])


def _responsable(ref):
    if ref in ("A.3.11", "A.3.12", "A.3.14"):
        return "Oficina de Tecnologias de la Informacion (seguridad / equipo de respuesta)"
    if ref in ("7.2", "7.3", "A.3.17"):
        return "Unidad de Recursos Humanos con el Oficial de Privacidad"
    if ref == "A.3.18":
        return "Unidad de Recursos Humanos y Oficina de Asesoria Juridica"
    if ref.startswith("A.1"):
        return "Oficial de Datos Personales (DPO)"
    if ref.startswith("A.2"):
        return "Oficina de Abastecimiento y Oficina de Asesoria Juridica"
    if ref in ("5.1", "9.3", "7.1"):
        return "Alta direccion (Rectorado) con el Oficial de Privacidad"
    if ref.startswith("9."):
        return "Auditor interno y Responsable del PIMS"
    return "Responsable del PIMS (Oficial de Privacidad)"


def _accion(h):
    control = REFS.get(h["ref"], {})
    esperada = control.get("evidencia_esperada", "la evidencia esperada")
    if h["estado"] == "Comprometida":
        return ("Investigar la alteracion o ausencia de %s, recuperar el original de su fuente, "
                "registrarlo de nuevo y abrir no conformidad (10.2)." % (
                    ", ".join(h.get("evidencias") or []) or "las evidencias"))
    if h["estado"] == "Sin evidencia":
        return "Elaborar, aprobar y registrar: %s." % esperada
    if h["estado"] == "Desactualizada":
        return "Revisar y reaprobar el documento vigente y registrarlo (%s)." % esperada
    return "Completar la evidencia: %s" % (h.get("nota") or esperada)


def _plan_accion(hallazgos, desde=None):
    desde = desde or dt.date.today()
    plan = []
    for h in hallazgos:
        dias = 7 if h["estado"] == "Comprometida" else PLAZO_POR_NIVEL.get(h.get("nivel", 2), 60)
        plan.append({"ref": h["ref"], "titulo": h.get("titulo", ""), "estado": h["estado"],
                     "clasificacion": h.get("clasificacion", ""), "prioridad": h.get("orden"),
                     "accion": _accion(h), "responsable": _responsable(h["ref"]),
                     "plazo_dias": dias,
                     "fecha_limite": (desde + dt.timedelta(days=dias)).isoformat(),
                     "verificacion": "Nueva auditoria con el agente: el control debe quedar "
                                     "Cubierto con evidencia integra y vigente."})
    return plan


def _filas(cob):
    claves = ("ref", "grupo", "titulo", "estado", "evidencias", "nota")
    salida = []
    for f in cob["controles"]:
        fila = {k: f.get(k) for k in claves}
        if f.get("revision"):
            r = f["revision"]
            fila["revision"] = {"veredicto": r.get("veredicto"), "decision": r.get("decision"),
                                "vigente": r.get("vigente")}
        salida.append(fila)
    return salida


def _registrar(estado, ruta, controles, tipo, titulo, fuente="", fecha=None):
    """Registra evidencia. En modo rapido no indexa en el RAG (sin embeddings): el indice
    FAISS del proyecto se reconstruye solo la proxima vez que se use (huella distinta)."""
    proyecto = estado["proyecto"]
    if not _rapido(estado):
        return herramientas.registrar(ruta, controles, tipo, titulo, proyecto=proyecto,
                                      fuente=fuente, fecha_documento=fecha)
    if tipo not in nucleo.TIPOS:
        raise ErrorAgente("Tipo no valido: %s" % tipo)
    p = nucleo.proyecto(proyecto)
    with p.bloqueo:
        ev = nucleo.registrar_evidencia(p.expediente, ruta, list(controles), tipo, titulo,
                                        ACTOR, fuente, fecha,
                                        nombre_original=os.path.basename(ruta))
        p._rag_listo = False
    return dict(ev, indexado_rag=False)


def _publico(ev):
    return {k: ev.get(k) for k in ("id", "titulo", "tipo", "controles", "sha256",
                                   "fecha_documento", "archivo", "indexado_rag") if k in ev}


# =====================================================================
# Grafo 1: auditoria interna (9.2)
# =====================================================================
def n_planificar(estado):
    par = estado.get("parametros") or {}
    p = nucleo.proyecto(estado["proyecto"])
    rol = par.get("rol") or p.rol
    if rol not in ("responsable", "encargado", "ambos"):
        raise ErrorAgente("Rol no valido: %s" % rol)
    vigencia = int(par.get("vigencia_dias") or 365)
    corte = par.get("fecha_corte") or dt.date.today().isoformat()
    periodo = par.get("periodo")
    if isinstance(periodo, str) and "/" in periodo:
        ini, fin = [dt.date.fromisoformat(x.strip()) for x in periodo.split("/", 1)]
        corte, vigencia = fin.isoformat(), max(1, (fin - ini).days)
    elif periodo:
        vigencia = int(periodo)
    dt.date.fromisoformat(corte)
    plan = {
        "organizacion": p.nombre,
        "objetivo": "Determinar si el PIMS es conforme con los requisitos de la organizacion y "
                    "de la norma, y si se implementa y mantiene eficazmente (clausula 9.2).",
        "alcance": par.get("alcance") or "PIMS completo segun ISO/IEC 27701:2025 (clausulas "
                                         "4 a 10 y Anexo A segun el rol)",
        "criterios": "ISO/IEC 27701:2025; criterios de evidencia del Entregable 1; Ley N.o 29733",
        "rol": rol, "vigencia_dias": vigencia, "fecha_corte": corte,
        "evidencias_en_expediente": len(leer_indice(p.expediente)["evidencias"]),
        "modo": "rapido (sin IA)" if _rapido(estado) else "con IA local (%s)" %
                nucleo.llm_local.MODELO_CHAT,
        "max_pertinencia": _entero(estado, "max_pertinencia", 3),
        "max_hallazgos": _entero(estado, "max_hallazgos", 3),
        "solicitado_por": par.get("solicitado_por") or "orquestador",
    }
    _decidir(estado, "planificar", "plan de auditoria definido", **plan)
    return {"plan": plan, "resultado": {"plan": plan},
            "_resumen": "Alcance: %s. Rol %s, corte %s, vigencia %d dias, %d evidencias." % (
                plan["alcance"], rol, corte, vigencia, plan["evidencias_en_expediente"])}


def n_verificar_integridad(estado):
    r = herramientas.verificar_integridad(estado["proyecto"])
    res = r["resultados"]
    resumen = "%d evidencias: OK %d, alteradas %d, faltantes %d; cadena %s." % (
        r["total"], len(res["OK"]), len(res["ALTERADA"]), len(res["FALTANTE"]),
        "integra" if not r["problemas_cadena"] else "ROTA (%d problemas)" % len(r["problemas_cadena"]))
    _decidir(estado, "verificar_integridad", "integro" if r["integro"] else "integridad fallida",
             alteradas=res["ALTERADA"], faltantes=res["FALTANTE"],
             problemas_cadena=r["problemas_cadena"])
    if estado.get("tipo") == "auditoria_interna" and r["integro"]:
        _marcar_paso(estado["ejecucion"], "alerta_integridad", "omitido",
                     "Expediente integro: no hay alerta.")
    if estado.get("tipo") == "incidente" and not r["integro"]:
        _publicar("integridad.alterada", proyecto=estado["proyecto"],
                  ejecucion=estado["ejecucion"], alteradas=res["ALTERADA"],
                  faltantes=res["FALTANTE"], problemas_cadena=r["problemas_cadena"])
    return {"integridad": r, "resultado": {"integridad": {"integro": r["integro"],
                                                          "resultados": res,
                                                          "problemas_cadena": r["problemas_cadena"]}},
            "_resumen": resumen}


def n_alerta_integridad(estado):
    r = estado["integridad"]
    alerta = {"nivel": "critica", "proyecto": estado["proyecto"],
              "alteradas": r["resultados"]["ALTERADA"], "faltantes": r["resultados"]["FALTANTE"],
              "problemas_cadena": r["problemas_cadena"],
              "mensaje": "Integridad del expediente comprometida: las evidencias afectadas se "
                         "marcan como Comprometidas en la matriz y la auditoria continua."}
    _publicar("integridad.alterada", ejecucion=estado["ejecucion"], **alerta)
    _decidir(estado, "alerta_integridad", "alerta emitida y auditoria continua", **alerta)
    return {"resultado": {"alertas": [alerta]},
            "_resumen": "ALERTA: alteradas %s, faltantes %s, cadena %s. Se continua marcandolas "
                        "como Comprometidas." % (alerta["alteradas"] or "-",
                                                 alerta["faltantes"] or "-",
                                                 "rota" if alerta["problemas_cadena"] else "integra")}


def n_matriz_cobertura(estado):
    plan = estado["plan"]
    cob = herramientas.matriz_cobertura(estado["proyecto"], plan["rol"], plan["vigencia_dias"],
                                        plan["fecha_corte"])
    compacta = {k: cob[k] for k in ("norma", "fecha_corte", "rol", "vigencia_dias",
                                    "total_evidencias", "controles_evaluados",
                                    "controles_aplicables", "porcentaje_cobertura",
                                    "conteo_estados")}
    compacta["controles"] = _filas(cob)
    _decidir(estado, "matriz_cobertura", "cobertura %s%%" % cob["porcentaje_cobertura"],
             conteo=cob["conteo_estados"])
    return {"cobertura": compacta,
            "resultado": {"cobertura": {k: v for k, v in compacta.items() if k != "controles"}},
            "_resumen": "Cobertura %s%% (%d de %d aplicables cubiertos). %s" % (
                cob["porcentaje_cobertura"], cob["conteo_estados"]["Cubierto"],
                cob["controles_aplicables"],
                ", ".join("%s %d" % (k, v) for k, v in cob["conteo_estados"].items() if v))}


def _pertinencia_determinista(proyecto, fila):
    p = nucleo.proyecto(proyecto)
    veredicto = "cumple" if fila["estado"] == "Cubierto" else "cumple_parcialmente"
    propuesta = {
        "veredicto": veredicto,
        "justificacion": "Modo rapido (sin IA): veredicto derivado del estado automatico "
                         "\"%s\" con %d evidencia(s) integra(s) (%s). El auditor debe leer el "
                         "contenido antes de aceptarlo." % (fila["estado"], len(fila["evidencias"]),
                                                             ", ".join(fila["evidencias"])),
        "citas": [], "falta": "" if veredicto == "cumple" else (fila.get("nota") or ""),
        "truncadas": False}
    with p.bloqueo:
        indice = leer_indice(p.expediente)["evidencias"]
        return revisiones.guardar_propuesta(p.expediente, fila["ref"], propuesta, indice,
                                            fila["evidencias"], "determinista (modo_rapido)")


def n_evaluar_pertinencia(estado):
    maximo = _entero(estado, "max_pertinencia", 3)
    filas = [f for f in estado["cobertura"]["controles"] if f["estado"] in revisiones.EVALUABLES]
    # Primero los que no tienen una revision vigente ya decidida, luego criticos y Parciales.
    filas.sort(key=lambda f: (bool(f.get("revision") and f["revision"].get("vigente")
                                   and f["revision"].get("decision")),
                              f["ref"] not in asistente.CRITICOS, f["estado"] != "Parcial"))
    elegidas = filas[:maximo]
    if not elegidas:
        return {"propuestas": [], "_omitido": True,
                "_resumen": "No hay controles Cubierto/Parcial que evaluar (o max_pertinencia=0)."}
    propuestas, errores = [], []
    for f in elegidas:
        try:
            if _rapido(estado):
                rev, origen = _pertinencia_determinista(estado["proyecto"], f), "determinista"
            else:
                rev, origen = herramientas.evaluar_pertinencia(f["ref"], estado["proyecto"]), "ia"
        except Exception as e:              # noqa: BLE001
            errores.append({"ref": f["ref"], "error": str(e)})
            _decidir(estado, "evaluar_pertinencia", "error al evaluar", ref=f["ref"], error=str(e))
            continue
        prop = {"ref": f["ref"], "estado": f["estado"], "veredicto": rev["veredicto"],
                "justificacion": rev.get("justificacion", ""), "falta": rev.get("falta", ""),
                "citas": rev.get("citas", []), "origen": origen}
        propuestas.append(prop)
        _decidir(estado, "evaluar_pertinencia", "propuesta %s" % rev["veredicto"], ref=f["ref"],
                 origen=origen, modelo=rev.get("modelo"))
    return {"propuestas": propuestas,
            "resultado": {"propuestas_pertinencia": propuestas, "errores_pertinencia": errores},
            "_resumen": "%d de %d controles evaluables revisados (%s): %s%s" % (
                len(propuestas), len(filas), "determinista" if _rapido(estado) else "IA",
                ", ".join("%s=%s" % (x["ref"], x["veredicto"]) for x in propuestas) or "-",
                "; errores en %s" % ", ".join(e["ref"] for e in errores) if errores else "")}


def _priorizar_filas(filas):
    hallazgos = []
    for f in filas:
        if f["estado"] in ("Cubierto", "No aplica"):
            continue
        clas = asistente.clasificacion_propuesta(f)
        nivel = _nivel(clas)
        puntos = (nivel * 100 + ESTADO_PESO.get(f["estado"], 0)
                  + (5 if f["ref"] in asistente.CRITICOS else 0)
                  + (3 if f.get("grupo") == "clausula" else 0))
        hallazgos.append(dict(f, clasificacion=clas, nivel=nivel, puntos=puntos))
    hallazgos.sort(key=lambda h: -h["puntos"])
    for i, h in enumerate(hallazgos, 1):
        h["orden"] = i
    return hallazgos


def n_priorizar(estado):
    hallazgos = _priorizar_filas(estado["cobertura"]["controles"])
    mayores = sum(1 for h in hallazgos if h["nivel"] == 3)
    _decidir(estado, "priorizar", "hallazgos priorizados",
             orden=[(h["ref"], h["estado"], h["puntos"]) for h in hallazgos])
    return {"hallazgos": hallazgos,
            "_resumen": "%d hallazgos (%d no conformidades mayores). Primeros: %s" % (
                len(hallazgos), mayores,
                ", ".join("%s (%s)" % (h["ref"], h["estado"]) for h in hallazgos[:5]) or "-")}


def n_redactar_hallazgos(estado):
    maximo = _entero(estado, "max_hallazgos", 3)
    salida, con_ia = [], 0
    for h in estado["hallazgos"]:
        h = dict(h)
        if h["orden"] <= maximo and not _rapido(estado):
            try:
                h["texto"] = herramientas.redactar_hallazgo(h["ref"], estado["proyecto"])["hallazgo"]
                h["origen"] = "ia"
                con_ia += 1
            except Exception as e:          # noqa: BLE001
                h["texto"], h["origen"] = _texto_determinista(h, h["clasificacion"]), \
                    "determinista (fallo IA: %s)" % e
        else:
            h["texto"], h["origen"] = _texto_determinista(h, h["clasificacion"]), "determinista"
        salida.append(h)
        _decidir(estado, "redactar_hallazgos", "hallazgo redactado", ref=h["ref"],
                 origen=h["origen"])
    return {"hallazgos": salida,
            "_resumen": "%d hallazgos redactados: %d con IA, %d deterministas." % (
                len(salida), con_ia, len(salida) - con_ia)}


def _respuesta_hitl(estado, nodo, payload):
    """Puerta HITL comun: guarda instantanea, interrumpe y registra la decision humana."""
    _guardar_instantanea(estado)
    resp = interrupt(payload)
    resp = dict(resp or {})
    registrar_decision(estado["ejecucion"], nodo, "decision humana: %s" % resp.get("decision"),
                       actor=resp.get("auditor") or "auditor", humano=True,
                       detalle={"comentario": resp.get("comentario", ""),
                                "decisiones_controles": resp.get("decisiones_controles") or {}},
                       tipo=estado.get("tipo"), proyecto=estado["proyecto"])
    return resp


def n_aprobacion_auditor(estado):
    hallazgos = estado.get("hallazgos") or []
    payload = {
        "pregunta": "Revise los %d hallazgos preliminares y las %d propuestas de pertinencia. "
                    "Apruebe para emitir el informe de auditoria interna (9.2) o rechace para "
                    "cerrar sin informe." % (len(hallazgos), len(estado.get("propuestas") or [])),
        "rol_aprobador": "auditor interno",
        "hallazgos": [{"ref": h["ref"], "estado": h["estado"], "texto": h["texto"],
                       "clasificacion": h["clasificacion"], "origen": h["origen"],
                       "orden": h["orden"]} for h in hallazgos],
        "propuestas": [{"ref": x["ref"], "veredicto": x["veredicto"],
                        "justificacion": x["justificacion"], "falta": x.get("falta", ""),
                        "origen": x["origen"]} for x in estado.get("propuestas") or []],
    }
    resp = _respuesta_hitl(estado, "aprobacion_auditor", payload)
    auditor = resp.get("auditor") or "auditor"
    decisiones = []
    for ref, d in (resp.get("decisiones_controles") or {}).items():
        try:
            herramientas.decidir_pertinencia(ref, d, auditor, resp.get("comentario", ""),
                                             estado["proyecto"])
            decisiones.append({"ref": ref, "decision": d})
        except Exception as e:              # noqa: BLE001
            decisiones.append({"ref": ref, "decision": d, "error": str(e)})
    rechazada = resp.get("decision") != "aprobada"
    aprob = {"decision": resp.get("decision"), "auditor": auditor,
             "comentario": resp.get("comentario", ""), "fecha": _ahora()}
    return {"respuesta": resp, "estado_final": "rechazada" if rechazada else "en_curso",
            "resultado": {"aprobacion": aprob, "decisiones_pertinencia": decisiones},
            "_resumen": "%s por %s. Propuestas decididas: %s" % (
                "Rechazada" if rechazada else "Aprobada", auditor,
                ", ".join("%s=%s" % (x["ref"], x["decision"]) for x in decisiones) or "ninguna")}


def n_generar_informe(estado):
    resp = estado["respuesta"]
    proyecto = estado["proyecto"]
    textos = {h["ref"]: h["texto"] for h in estado.get("hallazgos") or []}
    # Tras las decisiones del auditor puede haber controles degradados (Cubierto -> Parcial).
    cob = herramientas.matriz_cobertura(proyecto)
    finales = _priorizar_filas(_filas(cob))
    previos = {h["ref"]: h for h in estado.get("hallazgos") or []}
    for h in finales:
        if h["ref"] not in textos:
            textos[h["ref"]] = _texto_determinista(h, h["clasificacion"])
        h["texto"] = textos[h["ref"]]
        h["origen"] = previos.get(h["ref"], {}).get("origen", "determinista (tras revision)")
    inf = herramientas.generar_informe(proyecto, textos, aprobado_por=resp.get("auditor"),
                                       comentario=resp.get("comentario", ""))
    plan = estado.get("plan") or {}
    lin = ["## 6. Plan de la auditoria", "",
           "- Objetivo: %s" % plan.get("objetivo", ""),
           "- Alcance: %s" % plan.get("alcance", ""),
           "- Criterios: %s" % plan.get("criterios", ""),
           "- Rol: %s | Fecha de corte: %s | Vigencia: %s dias | Modo: %s" % (
               plan.get("rol"), plan.get("fecha_corte"), plan.get("vigencia_dias"),
               plan.get("modo")), "",
           "## 7. Revision de pertinencia (propuesta del agente y decision del auditor)", ""]
    decisiones = {d["ref"]: d["decision"] for d in
                  (estado.get("resultado") or {}).get("decisiones_pertinencia", [])}
    if estado.get("propuestas"):
        lin += ["| Control | Veredicto propuesto | Origen | Decision del auditor |",
                "|---|---|---|---|"]
        for x in estado["propuestas"]:
            lin.append("| %s | %s | %s | %s |" % (x["ref"], x["veredicto"], x["origen"],
                                                  decisiones.get(x["ref"], "sin decision")))
    else:
        lin.append("Sin propuestas de pertinencia en esta ejecucion.")
    with open(inf["ruta"], "a", encoding="utf-8") as f:
        f.write("\n" + "\n".join(lin) + "\n")
    _decidir(estado, "generar_informe", "informe emitido", ruta=inf["ruta"],
             aprobado_por=resp.get("auditor"))
    return {"hallazgos_finales": finales,
            "resultado": {"informe": inf["ruta"], "controles_con_hallazgo":
                          inf["controles_con_hallazgo"]},
            "_resumen": "Informe validado por %s: %s (%d controles con hallazgo)." % (
                resp.get("auditor"), os.path.basename(inf["ruta"]),
                inf["controles_con_hallazgo"])}


def n_plan_accion(estado):
    plan = _plan_accion(estado.get("hallazgos_finales") or estado.get("hallazgos") or [])
    ruta = (estado.get("resultado") or {}).get("informe")
    if ruta:
        lin = ["## 8. Plan de accion correctiva (propuesto por el agente)", "",
               "| # | Control | Estado | Accion | Responsable sugerido | Plazo | Fecha limite |",
               "|---|---|---|---|---|---|---|"]
        for a in plan:
            lin.append("| %s | %s | %s | %s | %s | %d dias | %s |" % (
                a["prioridad"], a["ref"], a["estado"], a["accion"], a["responsable"],
                a["plazo_dias"], a["fecha_limite"]))
        lin += ["", "## 9. Trazabilidad", "",
                "- Ejecucion del orquestador: `%s` (%s, checkpointer %s)" % (
                    estado["ejecucion"], MOTOR, TIPO_CHECKPOINTER),
                "- Registro de decisiones: `datos/bitacora_decisiones.jsonl`",
                "- Cadena de custodia del expediente: `expediente/cadena_custodia.jsonl`"]
        with open(ruta, "a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(lin) + "\n")
    _decidir(estado, "plan_accion", "plan de accion propuesto", acciones=len(plan))
    _publicar("auditoria.completada", proyecto=estado["proyecto"], ejecucion=estado["ejecucion"],
              informe=ruta, hallazgos=len(plan))
    return {"estado_final": "completada", "resultado": {"plan_accion": plan},
            "_resumen": "%d acciones correctivas con responsable y plazo." % len(plan)}


# =====================================================================
# Grafo 2: incidente (evento del Agente de Incidentes y Brechas)
# =====================================================================
def n_recibir_evento(estado):
    par = estado.get("parametros") or {}
    ev = dict(par.get("evento") or {})
    inc = dict(ev.get("incidente") or ev)
    if par.get("descripcion") and not inc.get("descripcion"):
        inc["descripcion"] = par["descripcion"]
    if not inc.get("descripcion"):
        raise ErrorAgente("El evento de incidente no trae descripcion")
    inc.setdefault("id", "INC-%s" % dt.datetime.now().strftime("%Y%m%d%H%M%S"))
    inc.setdefault("titulo", inc["descripcion"][:90])
    inc.setdefault("severidad", "media")
    inc.setdefault("deteccion", {"fecha": _ahora(), "fuente": ev.get("origen") or "manual"})
    normal = {"evento_id": ev.get("id"), "origen": ev.get("origen") or "manual",
              "recibido": _ahora(), "incidente": inc}
    _decidir(estado, "recibir_evento", "evento de incidente aceptado", incidente=inc["id"],
             origen=normal["origen"], severidad=inc["severidad"])
    return {"evento": normal, "resultado": {"incidente": inc},
            "_resumen": "%s (%s, severidad %s) desde %s." % (inc["id"], inc["titulo"],
                                                             inc["severidad"], normal["origen"])}


def _reporte_incidente_md(evento):
    inc = evento["incidente"]
    det = inc.get("deteccion") or {}
    lin = ["# Reporte de incidente de seguridad con datos personales - %s" % inc["id"], "",
           "- Titulo: %s" % inc["titulo"],
           "- Origen del reporte: %s (evento %s)" % (evento["origen"], evento.get("evento_id")),
           "- Fecha de deteccion: %s" % det.get("fecha", ""),
           "- Fuente de deteccion: %s" % det.get("fuente", ""),
           "- Severidad: %s" % inc.get("severidad"),
           "- Banco de datos afectado: %s" % inc.get("banco_datos", "por determinar"),
           "- Categorias de PII: %s" % ", ".join(inc.get("categorias_pii") or ["por determinar"]),
           "- Titulares afectados (estimado): %s" % inc.get("titulares_afectados_estimados",
                                                            "por determinar"),
           "", "## Descripcion", "", inc["descripcion"], ""]
    if det.get("indicadores"):
        lin += ["## Indicadores", ""] + ["- %s" % x for x in det["indicadores"]] + [""]
    if inc.get("acciones_inmediatas"):
        lin += ["## Acciones inmediatas", ""] + ["- %s" % x for x in inc["acciones_inmediatas"]] + [""]
    lin += ["## Base legal", "", inc.get("base_legal") or "Ley N.o 29733 y su Reglamento.", "",
            "_Recibido por el Agente de Evidencia y Auditoria el %s._" % evento["recibido"]]
    return "\n".join(lin) + "\n"


def n_registrar_incidente(estado):
    evento = estado["evento"]
    inc = evento["incidente"]
    controles = [r for r in ("A.3.11", "A.3.12") if r in REFS]
    if not controles:
        raise ErrorAgente("El catalogo no tiene A.3.11/A.3.12 para registrar el incidente")
    nombre = re.sub(r"[^A-Za-z0-9_-]+", "_", inc["id"]) + "_reporte.md"
    ruta = os.path.join(INCIDENTES, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(_reporte_incidente_md(evento))
    fecha = str((inc.get("deteccion") or {}).get("fecha") or "")[:10] or None
    try:
        dt.date.fromisoformat(fecha)
    except (TypeError, ValueError):
        fecha = None
    ev = _registrar(estado, ruta, controles, "registro", "Reporte de incidente %s: %s" % (
        inc["id"], inc["titulo"][:80]), "Agente de Incidentes y Brechas (evento %s)" %
        evento.get("evento_id"), fecha)
    _decidir(estado, "registrar_incidente", "incidente registrado como evidencia",
             evidencia=ev["id"], sha256=ev["sha256"], controles=controles)
    return {"evidencia": _publico(ev), "controles_incidente": controles,
            "resultado": {"evidencia": _publico(ev), "reporte": ruta},
            "_resumen": "%s registrada (tipo registro, controles %s, SHA-256 %s...)." % (
                ev["id"], ", ".join(controles), ev["sha256"][:16])}


def n_buscar_relacionadas(estado):
    inc = estado["evento"]["incidente"]
    p = nucleo.proyecto(estado["proyecto"])
    propia = estado["evidencia"]["id"]
    if _rapido(estado):
        claves = {"A.3.11", "A.3.12", "A.3.14", "A.1.2.9", "A.1.2.6", "A.3.17"}
        palabras = _palabras(inc["descripcion"] + " " + inc.get("banco_datos", ""))
        rel = []
        for ev in leer_indice(p.expediente)["evidencias"]:
            if ev["id"] == propia:
                continue
            comun = claves & set(ev["controles"])
            pal = palabras & _palabras(ev["titulo"])
            if comun or len(pal) >= 2:
                rel.append({"fuente": ev["id"], "titulo": ev["titulo"],
                            "controles": ev["controles"], "motivo": "controles %s" % (
                                ", ".join(sorted(comun))) if comun else "palabras: %s" %
                            ", ".join(sorted(pal)), "similitud": None})
        metodo = "determinista (controles y palabras clave)"
    else:
        rel = []
        for fr in herramientas.buscar(inc["descripcion"], estado["proyecto"], k=8):
            if fr.get("fuente") == propia:
                continue
            rel.append({"fuente": fr.get("fuente"), "tipo": fr.get("tipo"),
                        "similitud": fr.get("similitud"),
                        "extracto": (fr.get("texto") or "")[:240]})
        metodo = "RAG semantico (FAISS + nomic-embed-text)"
    cob = herramientas.matriz_cobertura(estado["proyecto"])
    controles = [{"ref": f["ref"], "titulo": f["titulo"], "estado": f["estado"],
                  "nota": f["nota"], "evidencias": f["evidencias"]}
                 for f in cob["controles"] if f["ref"] in ("A.3.11", "A.3.12", "A.3.14")]
    _decidir(estado, "buscar_relacionadas", "evidencias relacionadas", metodo=metodo,
             encontradas=[r["fuente"] for r in rel])
    return {"relacionadas": rel,
            "resultado": {"relacionadas": rel, "controles_incidente": controles},
            "_resumen": "%d evidencias/fragmentos relacionados (%s). %s" % (
                len(rel), metodo, "; ".join("%s %s" % (c["ref"], c["estado"]) for c in controles))}


def n_aprobacion_dpo(estado):
    inc = estado["evento"]["incidente"]
    controles = (estado.get("resultado") or {}).get("controles_incidente") or []
    hallazgos = []
    for c in controles:
        texto = ("%s - %s: %s. %s" % (c["ref"], c["titulo"], c["estado"], c["nota"] or "")).strip()
        if c["ref"] == "A.3.11" and c["estado"] != "Cubierto":
            texto += (" El incidente se gestiona sin un procedimiento de incidentes con PII "
                      "vigente en el expediente.")
        hallazgos.append({"ref": c["ref"], "estado": c["estado"], "texto": texto})
    payload = {
        "pregunta": "El DPO debe confirmar el registro del incidente %s (severidad %s) y la "
                    "emision del informe del incidente, que sirve de base para la notificacion "
                    "a la Autoridad Nacional de Proteccion de Datos Personales y a los titulares."
                    % (inc["id"], inc.get("severidad")),
        "rol_aprobador": "DPO (Oficial de Datos Personales)",
        "incidente": inc, "evidencia": estado["evidencia"],
        "hallazgos": hallazgos,
        "propuestas": [{"ref": inc["id"], "veredicto": "notificar" if inc.get(
            "requiere_notificacion", inc.get("severidad") in ("alta", "critica")) else
            "registrar_sin_notificar",
            "justificacion": "Severidad %s; %s titulares estimados; PII: %s." % (
                inc.get("severidad"), inc.get("titulares_afectados_estimados", "?"),
                ", ".join(inc.get("categorias_pii") or ["por determinar"]))}],
    }
    resp = _respuesta_hitl(estado, "aprobacion_dpo", payload)
    rechazada = resp.get("decision") != "aprobada"
    aprob = {"decision": resp.get("decision"), "auditor": resp.get("auditor"),
             "comentario": resp.get("comentario", ""), "fecha": _ahora(),
             "decisiones_controles": resp.get("decisiones_controles") or {}}
    return {"respuesta": resp, "estado_final": "rechazada" if rechazada else "en_curso",
            "resultado": {"aprobacion": aprob},
            "_resumen": "%s por %s." % ("Rechazada" if rechazada else "Confirmada",
                                        resp.get("auditor"))}


def n_informe_incidente(estado):
    ev, inc = estado["evento"], estado["evento"]["incidente"]
    resp, evid = estado["respuesta"], estado["evidencia"]
    res = estado.get("resultado") or {}
    integ = res.get("integridad") or {}
    notificar = (resp.get("decisiones_controles") or {}).get(inc["id"], "aceptada") == "aceptada"
    plan = [
        {"accion": "Contencion: mantener bloqueada la cuenta/vector y preservar los logs de "
                   "acceso como evidencia (A.3.14).", "responsable": _responsable("A.3.12"),
         "plazo_horas": 4},
        {"accion": "Determinar PII y titulares afectados con el inventario de tratamientos "
                   "(A.1.2.9).", "responsable": _responsable("A.1.2.9"), "plazo_horas": 24},
        {"accion": "Notificar a la Autoridad Nacional de Proteccion de Datos Personales "
                   "(plazo de referencia 48 h desde la deteccion; verificar con el Reglamento "
                   "vigente de la Ley N.o 29733)." if notificar else
                   "Registrar la decision de no notificar con su justificacion.",
         "responsable": "Oficial de Datos Personales (DPO)", "plazo_horas": 48},
        {"accion": "Comunicar a los titulares afectados medidas de proteccion recomendadas.",
         "responsable": "Oficial de Datos Personales (DPO) y Oficina de Imagen Institucional",
         "plazo_horas": 72},
        {"accion": "Analisis de causa raiz y no conformidad con accion correctiva (10.2); "
                   "registrar el cierre como evidencia de A.3.12.",
         "responsable": _responsable("10.2"), "plazo_horas": 240},
    ]
    ahora = dt.datetime.now()
    lin = ["# Informe del incidente %s - %s" % (inc["id"], nucleo.proyecto(estado["proyecto"]).nombre),
           "", "Norma: ISO/IEC 27701:2025 (A.3.11, A.3.12, A.3.14). Generado por el Agente de "
           "Evidencia y Auditoria el %s." % ahora.strftime("%Y-%m-%d %H:%M"), "",
           "**Confirmado por el DPO:** %s. %s" % (resp.get("auditor"), resp.get("comentario", "")),
           "", "## 1. Incidente", "", "- %s" % inc["titulo"],
           "- Severidad: %s | Origen: %s | Detectado: %s" % (
               inc.get("severidad"), ev["origen"], (inc.get("deteccion") or {}).get("fecha")),
           "- Banco de datos: %s" % inc.get("banco_datos", "por determinar"),
           "- Titulares afectados (estimado): %s" % inc.get("titulares_afectados_estimados", "?"),
           "", inc["descripcion"], "",
           "## 2. Evidencia registrada (cadena de custodia)", "",
           "- %s - %s" % (evid["id"], evid["titulo"]),
           "- Controles: %s | SHA-256: `%s`" % (", ".join(evid["controles"]), evid["sha256"]),
           "- Integridad del expediente tras el registro: %s" % (
               "integro" if integ.get("integro") else "ALERTA (ver bitacora)"),
           "", "## 3. Estado de los controles de incidentes", ""]
    for c in res.get("controles_incidente") or []:
        lin.append("- %s %s: **%s** %s" % (c["ref"], c["titulo"], c["estado"], c["nota"] or ""))
    lin += ["", "## 4. Evidencias relacionadas", ""]
    for r in estado.get("relacionadas") or []:
        lin.append("- %s %s" % (r["fuente"], r.get("titulo") or r.get("extracto", "")[:120]))
    if not estado.get("relacionadas"):
        lin.append("- Ninguna evidencia relacionada en el expediente.")
    lin += ["", "## 5. Plan de respuesta", "", "| Accion | Responsable | Plazo |", "|---|---|---|"]
    for a in plan:
        lin.append("| %s | %s | %d h |" % (a["accion"], a["responsable"], a["plazo_horas"]))
    lin += ["", "## 6. Trazabilidad", "", "- Ejecucion `%s`, evento `%s`" % (
        estado["ejecucion"], ev.get("evento_id")),
        "- Registro de decisiones: `datos/bitacora_decisiones.jsonl`"]
    ruta = os.path.join(nucleo.SALIDAS, "informe_incidente_%s_%s_%s.md" % (
        estado["proyecto"], re.sub(r"[^A-Za-z0-9-]+", "_", inc["id"]),
        ahora.strftime("%Y%m%d_%H%M%S")))
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(lin) + "\n")
    _decidir(estado, "informe_incidente", "informe del incidente emitido", ruta=ruta,
             notificar=notificar)
    _publicar("incidente.documentado", proyecto=estado["proyecto"], ejecucion=estado["ejecucion"],
              incidente=inc["id"], evidencia=evid["id"], informe=ruta, notificar=notificar)
    return {"estado_final": "completada", "resultado": {"informe": ruta, "plan_accion": plan},
            "_resumen": "Informe %s; %d acciones de respuesta." % (os.path.basename(ruta),
                                                                     len(plan))}


# =====================================================================
# Grafo 3: bandeja de entrada (automatizacion)
# =====================================================================
IGNORAR = (".tmp", ".part", ".crdownload", ".lock")
VACIAS = {"para", "como", "este", "esta", "estos", "estas", "entre", "sobre", "segun", "desde",
          "cada", "todo", "todos", "donde", "cuando", "debe", "deben", "sera", "puede", "tiene",
          "with", "that", "from", "this", "pims", "datos", "personales", "informacion", "unsa",
          "universidad", "nacional", "agustin", "arequipa"}


def _palabras(texto):
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode("ascii")
    return {w for w in re.findall(r"[a-z]{4,}", t.lower()) if w not in VACIAS}


def _clasificar_determinista(ruta):
    nombre = os.path.basename(ruta)
    texto = leer_texto(ruta, limite=4000)
    base = os.path.splitext(nombre)[0]
    pal = _palabras(base.replace("_", " ").replace("-", " ") + " " + texto[:3000])
    puntos = []
    for c in CATALOGO:
        comun = pal & _palabras(c["titulo"] + " " + c["evidencia_esperada"])
        if comun:
            puntos.append((len(comun), c["ref"], sorted(comun)))
    puntos.sort(key=lambda x: -x[0])
    elegidos = [x for x in puntos if x[0] >= 2][:2] or puntos[:1]
    bajo = (base + " " + texto[:500]).lower()
    tipo = "registro"
    for clave, t in (("politica", "politica"), ("procedimiento", "procedimiento"),
                     ("acta", "acta"), ("contrato", "contrato"), ("convenio", "contrato"),
                     ("informe", "informe"), ("log", "log"), ("config", "configuracion")):
        if clave in unicodedata.normalize("NFKD", bajo).encode("ascii", "ignore").decode():
            tipo = t
            break
    if nombre.lower().endswith((".png", ".jpg", ".jpeg")):
        tipo = "captura"
    fecha = re.search(r"\b(20\d\d-\d\d-\d\d)\b", texto)
    return {"controles": [x[1] for x in elegidos], "tipo": tipo,
            "titulo": re.sub(r"[_-]+", " ", base).strip().capitalize() or nombre,
            "fecha_documento": fecha.group(1) if fecha else None,
            "justificacion": "Modo rapido (sin IA): coincidencia de palabras con %s" % (
                "; ".join("%s (%s)" % (x[1], ", ".join(x[2][:4])) for x in elegidos) or
                "ningun control"),
            "candidatos": [{"ref": x[1], "similitud": x[0]} for x in puntos[:5]]}


def _en_proceso(estado):
    return os.path.join(nucleo.BANDEJA, "en_proceso", estado["ejecucion"])


def n_tomar_archivos(estado):
    par = estado.get("parametros") or {}
    nombres = par.get("archivos")
    if not nombres:
        nombres = sorted(n for n in os.listdir(nucleo.BANDEJA)
                         if os.path.isfile(os.path.join(nucleo.BANDEJA, n))
                         and not n.startswith((".", "~$")) and not n.lower().endswith(IGNORAR))
    destino = _en_proceso(estado)
    tomados = []
    for n in nombres:
        n = os.path.basename(n)
        origen = os.path.join(nucleo.BANDEJA, n)
        if not os.path.isfile(origen):
            continue
        os.makedirs(destino, exist_ok=True)
        try:
            os.replace(origen, os.path.join(destino, n))     # reclama el archivo
        except OSError:
            continue
        tomados.append({"archivo": n, "ruta": os.path.join(destino, n)})
    _decidir(estado, "tomar_archivos", "archivos tomados de la bandeja",
             archivos=[t["archivo"] for t in tomados])
    if not tomados:
        return {"archivos": [], "estado_final": "completada",
                "resultado": {"archivos": [], "registradas": []},
                "_resumen": "Bandeja vacia: nada que procesar."}
    return {"archivos": tomados, "resultado": {"archivos": [t["archivo"] for t in tomados]},
            "_resumen": "%d archivo(s): %s" % (len(tomados), ", ".join(t["archivo"] for t in tomados))}


def n_clasificar(estado):
    salida = []
    for a in estado["archivos"]:
        try:
            if _rapido(estado):
                c, origen = _clasificar_determinista(a["ruta"]), "determinista"
            else:
                c, origen = herramientas.clasificar(a["ruta"], estado["proyecto"]), "ia"
        except Exception as e:              # noqa: BLE001
            c, origen = dict(_clasificar_determinista(a["ruta"])), "determinista (fallo IA: %s)" % e
        item = dict(a, controles=c["controles"], tipo=c["tipo"], titulo=c["titulo"],
                    fecha_documento=c.get("fecha_documento"),
                    justificacion=c.get("justificacion", ""), origen=origen)
        salida.append(item)
        _decidir(estado, "clasificar", "propuesta de clasificacion", archivo=a["archivo"],
                 controles=item["controles"], tipo=item["tipo"], origen=origen)
    return {"clasificaciones": salida,
            "resultado": {"clasificaciones": [{k: v for k, v in x.items() if k != "ruta"}
                                              for x in salida]},
            "_resumen": "; ".join("%s -> %s (%s)" % (x["archivo"], ", ".join(x["controles"]) or
                                                      "sin control", x["tipo"]) for x in salida)}


def n_aprobacion_bandeja(estado):
    auto = bool((estado.get("parametros") or {}).get("auto_registrar"))
    decisiones = {}
    if auto:
        for c in estado["clasificaciones"]:
            if c["controles"]:
                decisiones[c["archivo"]] = "aceptada"
        if decisiones:
            _decidir(estado, "aprobacion_bandeja", "registro automatico (auto_registrar)",
                     archivos=sorted(decisiones))
    pendientes = [c for c in estado["clasificaciones"] if c["archivo"] not in decisiones]
    if not pendientes:
        return {"decisiones_archivos": decisiones, "estado_final": "en_curso",
                "resultado": {"aprobacion": {"decision": "aprobada", "auditor": "auto_registrar",
                                             "fecha": _ahora()}},
                "_resumen": "Sin HITL: auto_registrar acepto %d propuesta(s)." % len(decisiones)}
    payload = {
        "pregunta": "Confirme el registro en el expediente de %d archivo(s) de la bandeja con "
                    "la clasificacion propuesta (puede aceptar o rechazar cada uno)." %
                    len(pendientes),
        "rol_aprobador": "auditor interno / responsable de evidencias",
        "hallazgos": [],
        "propuestas": [{"ref": c["archivo"], "veredicto": "registrar como %s en %s" % (
            c["tipo"], ", ".join(c["controles"]) or "(sin control)"),
            "justificacion": c["justificacion"], "controles": c["controles"], "tipo": c["tipo"],
            "titulo": c["titulo"], "origen": c["origen"]} for c in pendientes],
    }
    resp = _respuesta_hitl(estado, "aprobacion_bandeja", payload)
    aprobada = resp.get("decision") == "aprobada"
    elegidas = resp.get("decisiones_controles") or {}
    for c in pendientes:
        d = elegidas.get(c["archivo"]) or ("aceptada" if aprobada else "rechazada")
        if not aprobada or not c["controles"]:
            d = "rechazada" if not c["controles"] or not aprobada else d
        decisiones[c["archivo"]] = d
    return {"respuesta": resp, "decisiones_archivos": decisiones,
            "estado_final": "en_curso" if aprobada else "rechazada",
            "resultado": {"aprobacion": {"decision": resp.get("decision"),
                                         "auditor": resp.get("auditor"),
                                         "comentario": resp.get("comentario", ""),
                                         "fecha": _ahora(), "decisiones": decisiones}},
            "_resumen": "%s por %s: %s" % ("Aprobada" if aprobada else "Rechazada",
                                           resp.get("auditor"),
                                           ", ".join("%s=%s" % kv for kv in decisiones.items()))}


def n_registrar(estado):
    registradas, errores = [], []
    for c in estado["clasificaciones"]:
        if estado["decisiones_archivos"].get(c["archivo"]) != "aceptada":
            continue
        try:
            ev = _registrar(estado, c["ruta"], c["controles"], c["tipo"], c["titulo"],
                            "Bandeja de entrada (%s)" % c["archivo"], c.get("fecha_documento"))
            registradas.append(dict(_publico(ev), archivo=c["archivo"]))
            _decidir(estado, "registrar", "evidencia registrada", archivo=c["archivo"],
                     evidencia=ev["id"], sha256=ev["sha256"])
        except Exception as e:              # noqa: BLE001
            errores.append({"archivo": c["archivo"], "error": str(e)})
            _decidir(estado, "registrar", "error al registrar", archivo=c["archivo"], error=str(e))
    return {"registradas": registradas,
            "resultado": {"registradas": registradas, "errores_registro": errores},
            "_resumen": "%d registrada(s)%s." % (len(registradas), ", %d error(es)" % len(errores)
                                                 if errores else "")}


def n_mover(estado):
    ok = {r["archivo"] for r in estado.get("registradas") or []}
    movidos = []
    for c in estado.get("clasificaciones") or estado.get("archivos") or []:
        sub = "procesados" if c["archivo"] in ok else "rechazados"
        carpeta = os.path.join(nucleo.BANDEJA, sub)
        os.makedirs(carpeta, exist_ok=True)
        destino = os.path.join(carpeta, c["archivo"])
        base, ext = os.path.splitext(c["archivo"])
        n = 2
        while os.path.exists(destino):
            destino = os.path.join(carpeta, "%s_%d%s" % (base, n, ext))
            n += 1
        if os.path.exists(c["ruta"]):
            shutil.move(c["ruta"], destino)
            movidos.append({"archivo": c["archivo"], "destino": os.path.relpath(
                destino, nucleo.BANDEJA)})
    shutil.rmtree(_en_proceso(estado), ignore_errors=True)
    _decidir(estado, "mover", "archivos movidos", movidos=movidos)
    final = estado.get("estado_final") if estado.get("estado_final") == "rechazada" else "completada"
    for r in estado.get("registradas") or []:
        _publicar("evidencia.registrada", proyecto=estado["proyecto"],
                  ejecucion=estado["ejecucion"], evidencia=r["id"], archivo=r["archivo"])
    return {"estado_final": final, "resultado": {"movidos": movidos},
            "_resumen": ", ".join("%s -> %s" % (m["archivo"], m["destino"]) for m in movidos)
                        or "Nada que mover."}


# =====================================================================
# Construccion de los grafos
# =====================================================================
PASOS = {
    "auditoria_interna": [
        ("planificar", "Planificar (alcance, rol, periodo)", n_planificar),
        ("verificar_integridad", "Verificar integridad (SHA-256 y cadena de custodia)",
         n_verificar_integridad),
        ("alerta_integridad", "Alerta de integridad", n_alerta_integridad),
        ("matriz_cobertura", "Matriz de cobertura", n_matriz_cobertura),
        ("evaluar_pertinencia", "Evaluar pertinencia de la evidencia", n_evaluar_pertinencia),
        ("priorizar", "Priorizar hallazgos", n_priorizar),
        ("redactar_hallazgos", "Redactar hallazgos", n_redactar_hallazgos),
        ("aprobacion_auditor", "Aprobacion del auditor (HITL)", n_aprobacion_auditor),
        ("generar_informe", "Generar informe de auditoria", n_generar_informe),
        ("plan_accion", "Plan de accion correctiva", n_plan_accion),
    ],
    "incidente": [
        ("recibir_evento", "Recibir evento del Agente de Incidentes", n_recibir_evento),
        ("registrar_incidente", "Registrar reporte como evidencia (A.3.11/A.3.12)",
         n_registrar_incidente),
        ("verificar_integridad", "Verificar integridad", n_verificar_integridad),
        ("buscar_relacionadas", "Buscar evidencias relacionadas", n_buscar_relacionadas),
        ("aprobacion_dpo", "Confirmacion del DPO (HITL)", n_aprobacion_dpo),
        ("informe_incidente", "Informe del incidente", n_informe_incidente),
    ],
    "bandeja": [
        ("tomar_archivos", "Tomar archivos nuevos de la bandeja", n_tomar_archivos),
        ("clasificar", "Clasificar (controles, tipo, titulo)", n_clasificar),
        ("aprobacion_bandeja", "Confirmacion del registro (HITL ligera)", n_aprobacion_bandeja),
        ("registrar", "Registrar en el expediente", n_registrar),
        ("mover", "Mover a procesados", n_mover),
    ],
}
TIPOS = tuple(PASOS)
NODO_ANTES_DE_HITL = {"auditoria_interna": "redactar_hallazgos",
                      "incidente": "buscar_relacionadas", "bandeja": "clasificar"}


def _si_aprobada(siguiente):
    def ruta(estado):
        return END if estado.get("estado_final") == "rechazada" else siguiente
    return ruta


def _construir(tipo):
    g = StateGraph(Estado)
    for nombre, _titulo, fn in PASOS[tipo]:
        g.add_node(nombre, _nodo(nombre, fn))
    if tipo == "auditoria_interna":
        g.add_edge(START, "planificar")
        g.add_edge("planificar", "verificar_integridad")
        g.add_conditional_edges(
            "verificar_integridad",
            lambda s: "matriz_cobertura" if s["integridad"]["integro"] else "alerta_integridad",
            ["alerta_integridad", "matriz_cobertura"])
        g.add_edge("alerta_integridad", "matriz_cobertura")
        g.add_edge("matriz_cobertura", "evaluar_pertinencia")
        g.add_edge("evaluar_pertinencia", "priorizar")
        g.add_edge("priorizar", "redactar_hallazgos")
        g.add_edge("redactar_hallazgos", "aprobacion_auditor")
        g.add_conditional_edges("aprobacion_auditor", _si_aprobada("generar_informe"),
                                ["generar_informe", END])
        g.add_edge("generar_informe", "plan_accion")
        g.add_edge("plan_accion", END)
    elif tipo == "incidente":
        g.add_edge(START, "recibir_evento")
        g.add_edge("recibir_evento", "registrar_incidente")
        g.add_edge("registrar_incidente", "verificar_integridad")
        g.add_edge("verificar_integridad", "buscar_relacionadas")
        g.add_edge("buscar_relacionadas", "aprobacion_dpo")
        g.add_conditional_edges("aprobacion_dpo", _si_aprobada("informe_incidente"),
                                ["informe_incidente", END])
        g.add_edge("informe_incidente", END)
    else:
        g.add_edge(START, "tomar_archivos")
        g.add_conditional_edges("tomar_archivos",
                                lambda s: "clasificar" if s.get("archivos") else END,
                                ["clasificar", END])
        g.add_edge("clasificar", "aprobacion_bandeja")
        g.add_conditional_edges("aprobacion_bandeja",
                                lambda s: "mover" if s.get("estado_final") == "rechazada"
                                else "registrar", ["registrar", "mover"])
        g.add_edge("registrar", "mover")
        g.add_edge("mover", END)
    return g.compile(checkpointer=CHECKPOINTER)


GRAFOS = {t: _construir(t) for t in TIPOS}


def diagrama(tipo):
    """Diagrama Mermaid del grafo (para la web y la documentacion)."""
    return GRAFOS[tipo].get_graph().draw_mermaid()


def describir(tipo):
    """Nodos y aristas del grafo compilado."""
    g = GRAFOS[tipo].get_graph()
    return {"tipo": tipo, "motor": MOTOR, "checkpointer": TIPO_CHECKPOINTER,
            "nodos": [n for n in g.nodes],
            "aristas": [{"origen": e.source, "destino": e.target, "condicional": e.conditional}
                        for e in g.edges]}


# =====================================================================
# Ejecucion en segundo plano
# =====================================================================
def _config(id_):
    return {"configurable": {"thread_id": id_}}


def _cerrar(ej, estado, error=None):
    ej["estado"] = estado
    ej["paso_actual"] = None
    if error:
        ej["error"] = error
    for p in ej["pasos"]:
        if p["estado"] in ("pendiente", "en_curso"):
            p["estado"] = "omitido" if not error or p["estado"] == "pendiente" else "error"


def _ejecutar(id_, tipo, entrada):
    grafo = GRAFOS[tipo]
    config = _config(id_)
    try:
        grafo.invoke(entrada, config)
        snap = grafo.get_state(config)
        interrupciones = [i for t in snap.tasks for i in (t.interrupts or ())]
        if interrupciones:
            payload = interrupciones[0].value

            def fn(ej):
                ej["estado"] = "esperando_aprobacion"
                ej["aprobacion"] = dict(payload, pendiente=True, solicitada=_ahora())
                for p in ej["pasos"]:
                    if p["nodo"] == ej.get("paso_actual"):
                        p["resumen"] = "Esperando decision humana (%s)." % payload.get(
                            "rol_aprobador", "auditor")
            _modificar(id_, fn)
            registrar_decision(id_, snap.next[0] if snap.next else None,
                               "aprobacion humana solicitada", tipo=tipo,
                               proyecto=snap.values.get("proyecto"),
                               detalle={"pregunta": payload.get("pregunta")})
            _publicar("aprobacion.requerida", ejecucion=id_, flujo=tipo,
                      proyecto=snap.values.get("proyecto"), pregunta=payload.get("pregunta"))
            return
        valores = snap.values
        final = valores.get("estado_final")
        final = final if final in ("completada", "rechazada") else "completada"

        def fin(ej):
            ej["resultado"] = dict(ej.get("resultado") or {}, **(valores.get("resultado") or {}))
            _cerrar(ej, final)
        _modificar(id_, fin)
        registrar_decision(id_, None, "ejecucion %s" % final, tipo=tipo,
                           proyecto=valores.get("proyecto"))
    except Exception as e:                  # noqa: BLE001
        mensaje = "%s: %s" % (type(e).__name__, e)
        _modificar(id_, lambda ej: _cerrar(ej, "error", mensaje))
        registrar_decision(id_, None, "ejecucion con error", tipo=tipo,
                           proyecto=(obtener(id_) or {}).get("proyecto"),
                           detalle={"error": mensaje, "traza": traceback.format_exc()[-2000:]})
    finally:
        _HILOS.pop(id_, None)


def _lanzar(id_, objetivo, *args):
    hilo = threading.Thread(target=objetivo, args=args, name="orquestador-%s" % id_, daemon=True)
    _HILOS[id_] = hilo
    hilo.start()
    return hilo


def _nuevo_id(tipo):
    pref = {"auditoria_interna": "AUD", "incidente": "INC", "bandeja": "BAN"}[tipo]
    return "%s-%s-%s" % (pref, dt.datetime.now().strftime("%Y%m%d-%H%M%S"),
                         "".join(random.choices(string.ascii_lowercase + string.digits, k=4)))


def iniciar(tipo, proyecto="unsa", parametros=None):
    """Lanza una ejecucion del grafo `tipo` en un hilo de fondo y la devuelve."""
    if tipo not in PASOS:
        raise ErrorAgente("Tipo de ejecucion no valido: %s (usa %s)" % (tipo, ", ".join(TIPOS)))
    proyecto = proyecto or "unsa"
    nucleo.proyecto(proyecto)               # valida (y crea 'unsa' si falta)
    parametros = json.loads(json.dumps(parametros or {}, default=str))
    ahora = _ahora()
    ej = {"id": _nuevo_id(tipo), "tipo": tipo, "proyecto": proyecto, "parametros": parametros,
          "estado": "en_curso", "creado": ahora, "actualizado": ahora, "paso_actual": None,
          "pasos": [{"nodo": n, "titulo": t, "estado": "pendiente", "inicio": None, "fin": None,
                     "resumen": ""} for n, t, _ in PASOS[tipo]],
          "aprobacion": None, "resultado": {}, "error": None,
          "motor": "%s + %s" % (MOTOR, TIPO_CHECKPOINTER)}
    _guardar(ej)
    registrar_decision(ej["id"], None, "ejecucion iniciada", tipo=tipo, proyecto=proyecto,
                       actor=parametros.get("solicitado_por") or ACTOR,
                       detalle={"parametros": parametros})
    entrada = {"ejecucion": ej["id"], "tipo": tipo, "proyecto": proyecto,
               "parametros": parametros, "resultado": {}}
    _lanzar(ej["id"], _ejecutar, ej["id"], tipo, entrada)
    return ej


def _reanudar(id_, tipo, respuesta):
    grafo = GRAFOS[tipo]
    config = _config(id_)
    try:
        snap = grafo.get_state(config)
        if not snap.next:
            # Checkpoint perdido (MemorySaver tras un reinicio): se reconstruye desde la
            # instantanea JSON y se vuelve a llegar a la puerta HITL sin repetir pasos.
            inst = _leer_instantanea(id_)
            if not inst:
                raise ErrorAgente("No hay estado guardado para reanudar %s" % id_)
            grafo.update_state(config, inst, as_node=NODO_ANTES_DE_HITL[tipo])
            grafo.invoke(None, config)
    except Exception as e:                  # noqa: BLE001
        _modificar(id_, lambda ej: _cerrar(ej, "error", "%s: %s" % (type(e).__name__, e)))
        _HILOS.pop(id_, None)
        return
    _ejecutar(id_, tipo, Command(resume=respuesta))


def aprobar(id_, decision, auditor, comentario="", decisiones_controles=None):
    """Decision humana en la puerta HITL. decision: 'aprobada' | 'rechazada';
    decisiones_controles: {ref: 'aceptada' | 'rechazada'} sobre las propuestas."""
    if decision not in ("aprobada", "rechazada"):
        raise ErrorAgente("Decision no valida: %s (usa aprobada o rechazada)" % decision)
    auditor = (auditor or "").strip()
    if not auditor:
        raise ErrorAgente("Indica el nombre del auditor que decide")
    decisiones_controles = dict(decisiones_controles or {})
    with _CANDADO:
        ej = obtener(id_)
        if ej is None:
            raise ErrorAgente("No existe la ejecucion %s" % id_)
        if ej["estado"] != "esperando_aprobacion":
            raise ErrorAgente("La ejecucion %s no espera aprobacion (estado %s)" % (
                id_, ej["estado"]))
        refs = {p["ref"] for p in (ej.get("aprobacion") or {}).get("propuestas") or []}
        for ref, d in decisiones_controles.items():
            if d not in ("aceptada", "rechazada"):
                raise ErrorAgente("Decision no valida para %s: %s" % (ref, d))
            if ref not in refs:
                raise ErrorAgente("%s no esta entre las propuestas de esta ejecucion" % ref)
        respuesta = {"decision": decision, "auditor": auditor, "comentario": comentario or "",
                     "decisiones_controles": decisiones_controles}
        ej["estado"] = "en_curso"
        ej["aprobacion"] = dict(ej["aprobacion"], pendiente=False,
                                respuesta=dict(respuesta, fecha=_ahora()))
        _guardar(ej)
    _lanzar(id_, _reanudar, id_, ej["tipo"], respuesta)
    return ej


def esperar(id_, timeout=None, intervalo=0.5):
    """Bloquea hasta que la ejecucion salga de 'en_curso' (util en CLI y pruebas)."""
    limite = time.time() + timeout if timeout else None
    while True:
        ej = obtener(id_)
        if ej is None or ej["estado"] != "en_curso":
            return ej
        if limite and time.time() > limite:
            return ej
        time.sleep(intervalo)


if __name__ == "__main__":
    for t in TIPOS:
        print("== %s ==" % t)
        print(diagrama(t))
