# -*- coding: utf-8 -*-
"""
Herramientas del Agente de Evidencia y Auditoria.

Es el contrato comun del Entregable 2: el servidor MCP (servidor_mcp.py) las
publica como tools, el orquestador (orquestador.py) las encadena y la web las
muestra. Cada herramienta recibe y devuelve solo tipos JSON (dict, list, str,
int, bool) para que valgan igual por MCP, por HTTP o desde Python.

Deterministas (sin IA):  listar_proyectos, estado_expediente, registrar,
                         verificar_integridad, matriz_cobertura, generar_informe
Con IA local (Ollama):   clasificar, buscar, evaluar_pertinencia,
                         redactar_hallazgo, preguntar
"""

import datetime as dt
import json
import os

import nucleo
from nucleo import CATALOGO, ErrorAgente, asistente, leer_indice, leer_texto, llm_local, revisiones

RESPONSABLE = "agente-evidencia"

_preparado = False


def _asegurar_preparado():
    global _preparado
    if not _preparado:
        nucleo.preparar()
        _preparado = True


def _p(proyecto):
    return nucleo.proyecto(proyecto or "unsa")


def _resumen(p, rol=None, vigencia=365, fecha=None):
    fuente = {"vigencia": vigencia}
    if rol:
        fuente["rol"] = rol
    if fecha:
        fuente["fecha"] = fecha
    return nucleo.app_e1._resumen(fuente, p)


def _fila(p, ref, **kw):
    cob, resumen = _resumen(p, **kw)
    fila = next((f for f in cob["controles"] if f["ref"] == ref), None)
    if not fila:
        raise ErrorAgente("Control no encontrado en la matriz: %s" % ref)
    return fila, resumen


# ---------------------------------------------------------------- deterministas

def listar_proyectos():
    """Organizaciones auditadas disponibles."""
    nucleo.asegurar_unsa()
    return [p.publico() for p in nucleo.PROYECTOS.listar()]


def estado_expediente(proyecto="unsa"):
    """Evidencias registradas e integridad (sin anotar en la cadena de custodia)."""
    p = _p(proyecto)
    return {"proyecto": p.publico(),
            "evidencias": leer_indice(p.expediente)["evidencias"],
            "integridad": nucleo.app_e1._integridad_sin_registrar(p)}


def registrar(ruta_archivo, controles, tipo, titulo, proyecto="unsa", responsable=RESPONSABLE,
              fuente="", fecha_documento=None):
    """Copia el archivo al expediente con SHA-256, cadena de custodia e indexado RAG."""
    p = _p(proyecto)
    if tipo not in nucleo.TIPOS:
        raise ErrorAgente("Tipo no valido: %s (usa %s)" % (tipo, ", ".join(nucleo.TIPOS)))
    rag = p.preparar_rag()
    with p.bloqueo:
        ev = nucleo.registrar_evidencia(p.expediente, ruta_archivo, list(controles), tipo,
                                        titulo, responsable, fuente, fecha_documento,
                                        nombre_original=os.path.basename(ruta_archivo))
        rag.agregar_evidencia(ev)
    return ev


def verificar_integridad(proyecto="unsa", responsable=RESPONSABLE):
    """Recalcula hashes y comprueba la cadena; deja constancia en la cadena."""
    p = _p(proyecto)
    with p.bloqueo:
        return nucleo.verificar_expediente(p.expediente, responsable)


def matriz_cobertura(proyecto="unsa", rol=None, vigencia_dias=365, fecha_corte=None):
    """Estado por control (Cubierto, Parcial, Sin evidencia...) y % de cobertura."""
    cob, _ = _resumen(_p(proyecto), rol, vigencia_dias, fecha_corte)
    return cob


def generar_informe(proyecto="unsa", hallazgos=None, aprobado_por=None, comentario=""):
    """Escribe el informe de auditoria en Markdown en datos/salidas y devuelve su ruta.

    hallazgos: {ref: texto} ya redactados (si faltan, se listan sin redactar)."""
    p = _p(proyecto)
    cob = matriz_cobertura(proyecto)
    integ = nucleo.app_e1._integridad_sin_registrar(p)
    evid = leer_indice(p.expediente)["evidencias"]
    hallazgos = hallazgos or {}
    ahora = dt.datetime.now().astimezone()
    lin = ["# Informe de auditoria interna del PIMS - %s" % p.nombre, "",
           "Norma: ISO/IEC 27701:2025 (clausula 9.2). Generado por el Agente de Evidencia y "
           "Auditoria el %s." % ahora.strftime("%Y-%m-%d %H:%M"), ""]
    if aprobado_por:
        lin += ["**Validado por el auditor:** %s. %s" % (aprobado_por, comentario or ""), ""]
    else:
        lin += ["**PRELIMINAR - requiere validacion del auditor.**", ""]
    lin += ["## 1. Integridad del expediente", ""]
    if integ["integro"]:
        lin.append("Expediente integro: %d evidencias con hash coincidente y cadena de "
                   "custodia sin roturas." % integ["total"])
    else:
        lin.append("ALERTA DE INTEGRIDAD: alteradas %s, faltantes %s, problemas de cadena %s." % (
            integ["resultados"]["ALTERADA"], integ["resultados"]["FALTANTE"],
            integ["problemas_cadena"]))
    lin += ["", "## 2. Resumen de cobertura", ""]
    lin.append("- Cobertura: %s%% de %s controles aplicables (rol %s, corte %s)" % (
        cob["porcentaje_cobertura"], cob["controles_aplicables"], cob["rol"], cob["fecha_corte"]))
    for k, v in cob["conteo_estados"].items():
        lin.append("- %s: %s" % (k, v))
    lin += ["", "## 3. Evidencias analizadas", "", "| ID | Titulo | Tipo | Controles | SHA-256 |",
            "|---|---|---|---|---|"]
    for ev in evid:
        lin.append("| %s | %s | %s | %s | `%s...` |" % (ev["id"], ev["titulo"], ev["tipo"],
                                                    ", ".join(ev["controles"]), ev["sha256"][:16]))
    lin += ["", "## 4. Matriz de cobertura", "", "| Control | Titulo | Estado | Evidencias |",
            "|---|---|---|---|"]
    for f in cob["controles"]:
        lin.append("| %s | %s | %s | %s |" % (f["ref"], f["titulo"], f["estado"],
                                              ", ".join(f.get("evidencias", [])) or "-"))
    lin += ["", "## 5. Hallazgos", ""]
    pendientes = [f for f in cob["controles"] if f["estado"] not in ("Cubierto", "No aplica")]
    for f in pendientes:
        lin += ["### %s - %s (%s)" % (f["ref"], f["titulo"], f["estado"]), "",
                hallazgos.get(f["ref"]) or "_Hallazgo sin redactar: %s_" % f.get("nota", ""), ""]
    ruta = os.path.join(nucleo.SALIDAS, "informe_auditoria_%s_%s.md" % (
        p.id, ahora.strftime("%Y%m%d_%H%M%S")))
    with open(ruta, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lin) + "\n")
    return {"ruta": ruta, "controles_con_hallazgo": len(pendientes)}


# ---------------------------------------------------------------- con IA local

def clasificar(ruta_archivo, proyecto="unsa"):
    """Propone controles, tipo, titulo y fecha para un archivo nuevo (no registra)."""
    _asegurar_preparado()
    p = _p(proyecto)
    return asistente.sugerir_clasificacion(p.preparar_rag(), CATALOGO,
                                           os.path.basename(ruta_archivo),
                                           leer_texto(ruta_archivo))


def buscar(consulta, proyecto="unsa", k=6):
    """Busqueda semantica en la norma, el conocimiento y las evidencias del proyecto."""
    _asegurar_preparado()
    return _p(proyecto).preparar_rag().buscar(consulta, k=k)


def evaluar_pertinencia(ref, proyecto="unsa"):
    """La IA lee las evidencias del control y propone cumple / parcial / no cumple."""
    _asegurar_preparado()
    p = _p(proyecto)
    fila, _ = _fila(p, ref)
    if fila["estado"] not in revisiones.EVALUABLES:
        raise ErrorAgente("El control %s esta %s: no hay evidencia que evaluar" % (ref, fila["estado"]))
    control = next(c for c in CATALOGO if c["ref"] == ref)
    indice = leer_indice(p.expediente)["evidencias"]
    leidas = [dict(ev, texto=leer_texto(os.path.join(p.expediente, ev["archivo"]), limite=200000))
              for ev in indice if ev["id"] in fila["evidencias"]]
    propuesta = asistente.evaluar_pertinencia(control, fila, leidas)
    with p.bloqueo:
        return revisiones.guardar_propuesta(p.expediente, ref, propuesta, indice,
                                            fila["evidencias"], llm_local.MODELO_CHAT)


def decidir_pertinencia(ref, decision, auditor, comentario="", proyecto="unsa"):
    """Decision humana sobre una propuesta de pertinencia ('aceptada' o 'rechazada')."""
    p = _p(proyecto)
    with p.bloqueo:
        return revisiones.decidir(p.expediente, ref, decision, auditor, comentario)


def redactar_hallazgo(ref, proyecto="unsa"):
    """Hallazgo preliminar (criterio-condicion-causa-efecto-recomendacion)."""
    _asegurar_preparado()
    p = _p(proyecto)
    fila, resumen = _fila(p, ref)
    if fila["estado"] in ("Cubierto", "No aplica"):
        raise ErrorAgente("El control %s esta %s: no genera hallazgo" % (ref, fila["estado"]))
    return {"ref": ref, "estado": fila["estado"],
            "hallazgo": asistente.redactar_hallazgo(p.preparar_rag(), fila, resumen)}


def preguntar(mensaje, proyecto="unsa", historial=None):
    """Pregunta libre al asistente AUDITA-PIMS sobre el expediente o la norma."""
    _asegurar_preparado()
    p = _p(proyecto)
    _, resumen = _resumen(p)
    respuesta, fuentes = asistente.responder(p.preparar_rag(), mensaje, historial or [], resumen)
    return {"respuesta": respuesta, "fuentes": fuentes}


# Metadatos para publicar las herramientas (MCP, panel web, documentacion).
HERRAMIENTAS = {
    "listar_proyectos": listar_proyectos,
    "estado_expediente": estado_expediente,
    "registrar": registrar,
    "verificar_integridad": verificar_integridad,
    "matriz_cobertura": matriz_cobertura,
    "generar_informe": generar_informe,
    "clasificar": clasificar,
    "buscar": buscar,
    "evaluar_pertinencia": evaluar_pertinencia,
    "decidir_pertinencia": decidir_pertinencia,
    "redactar_hallazgo": redactar_hallazgo,
    "preguntar": preguntar,
}


if __name__ == "__main__":
    print(json.dumps(listar_proyectos(), ensure_ascii=False, indent=2))
