# -*- coding: utf-8 -*-
"""
Revision de pertinencia (paso 4 de la skill) en la aplicacion web.

evidencia.py dice si un control tiene evidencia integra, vigente y en numero
suficiente; esta revision dice si esa evidencia demuestra de verdad el control.
La IA propone un veredicto y el auditor lo acepta o lo rechaza (HITL).

Reglas:
  - Solo una propuesta ACEPTADA cambia la matriz.
  - Solo cambia hacia abajo: un control Cubierto cuya evidencia no lo demuestra
    pasa a Parcial. La IA nunca sube un control.
  - La revision vale para las evidencias que se leyeron: si se liga otra
    evidencia al control o cambia un hash, la revision deja de aplicarse.

Las revisiones se guardan en el expediente (revisiones_pertinencia.json) y cada
decision del auditor se anota en la cadena de custodia.
"""

import json
import os

from evidencia_api import ORDEN_ESTADOS, ahora, anotar_custodia

ARCHIVO = "revisiones_pertinencia.json"
VEREDICTOS = ("cumple", "cumple_parcialmente", "no_cumple")
EVALUABLES = ("Cubierto", "Parcial")


def leer(expediente):
    ruta = os.path.join(expediente, ARCHIVO)
    if not os.path.exists(ruta):
        return {}
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)["revisiones"]


def _guardar(expediente, revisiones):
    with open(os.path.join(expediente, ARCHIVO), "w", encoding="utf-8") as f:
        json.dump({"revisiones": revisiones}, f, ensure_ascii=False, indent=2)


def huellas(evidencias, ids):
    """{ID: sha256} de las evidencias leidas, para saber si la revision sigue vigente."""
    por_id = {ev["id"]: ev["sha256"] for ev in evidencias}
    return {i: por_id.get(i) for i in ids}


def guardar_propuesta(expediente, ref, propuesta, evidencias, ids, modelo):
    revisiones = leer(expediente)
    revisiones[ref] = dict(propuesta, ref=ref, huellas=huellas(evidencias, ids),
                           modelo=modelo, fecha_ia=ahora(), decision=None)
    _guardar(expediente, revisiones)
    return revisiones[ref]


def decidir(expediente, ref, decision, auditor, comentario):
    revisiones = leer(expediente)
    rev = revisiones.get(ref)
    if not rev:
        raise ValueError("No hay propuesta de la IA para %s" % ref)
    rev.update(decision=decision, auditor=auditor, comentario=comentario,
               fecha_decision=ahora())
    _guardar(expediente, revisiones)
    anotar_custodia(expediente, "REVISION_PERTINENCIA", auditor, control=ref,
                    decision=decision, veredicto_ia=rev["veredicto"],
                    evidencias=sorted(rev["huellas"]))
    return rev


def aplicar(cobertura, expediente, evidencias):
    """Adjunta la revision a cada fila y degrada los Cubierto rechazados por el auditor."""
    revisiones = leer(expediente)
    degradados = []
    for fila in cobertura["controles"]:
        rev = revisiones.get(fila["ref"])
        if not rev:
            continue
        vigente = rev["huellas"] == huellas(evidencias, fila["evidencias"])
        fila["revision"] = dict(rev, vigente=vigente)
        if (vigente and rev["decision"] == "aceptada" and rev["veredicto"] != "cumple"
                and fila["estado"] == "Cubierto"):
            fila["estado"] = "Parcial"
            fila["nota"] = "Revision de pertinencia aceptada por %s: %s" % (
                rev.get("auditor") or "el auditor", rev.get("falta") or rev["justificacion"])
            degradados.append(fila["ref"])

    conteo = {e: sum(1 for f in cobertura["controles"] if f["estado"] == e)
              for e in ORDEN_ESTADOS}
    aplicables = cobertura["controles_aplicables"]
    cobertura["porcentaje_automatico"] = cobertura["porcentaje_cobertura"]
    cobertura["porcentaje_cobertura"] = (round(100.0 * conteo["Cubierto"] / aplicables, 1)
                                         if aplicables else 0.0)
    cobertura["conteo_estados"] = conteo
    cobertura["degradados"] = degradados
    return cobertura
