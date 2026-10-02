# -*- coding: utf-8 -*-
"""
Asistente AUDITA-PIMS: identidad e instrucciones (03-asistente) + conocimiento
recuperado por RAG + modelo de lenguaje local.

El modelo nunca calcula: recibe en el bloque CONTEXTO los resultados que ya
produjo evidencia.py (hashes, integridad, cobertura) y los fragmentos que
recupero FAISS, y solo clasifica, valora y redacta.
"""

import json
import os
import re

import llm_local

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_INSTRUCCIONES = os.path.join(RAIZ, "03-asistente", "instrucciones_sistema.md")
RUTA_PLANTILLA = os.path.join(RAIZ, "02-skill", "evidencia-auditoria-pims", "assets",
                              "plantilla_hallazgo.md")


def _instrucciones():
    with open(RUTA_INSTRUCCIONES, encoding="utf-8") as f:
        texto = f.read()
    # Lo que va antes de la primera regla horizontal es una nota para el grupo.
    return texto.split("\n---\n", 1)[-1].strip()


def _bloque_contexto(fragmentos, resumen=None):
    lineas = ["CONTEXTO (unica fuente de verdad; si algo no esta aqui, dilo):"]
    for f in fragmentos:
        lineas.append("[%s | %s]\n%s" % (f["fuente"], f["tipo"], f["texto"]))
    if resumen:   # al final, mas cerca de la pregunta
        lineas.append("[Estado del expediente calculado por evidencia.py - cifras exactas]\n"
                      + resumen)
    return "\n\n".join(lineas)


# Controles criticos segun criterios_evidencia.md (seccion 2).
CRITICOS = {"5.2", "6.1.2", "6.1.3", "9.2", "9.3", "A.1.2.6", "A.1.3.7", "A.3.11", "A.3.12"}


def resumen_expediente(cobertura, integridad, evidencias=()):
    """Texto compacto con las cifras que el modelo puede citar."""
    c = cobertura["conteo_estados"]
    estado_ev = {i: k for k, ids in integridad["resultados"].items() for i in ids}
    malas = integridad["resultados"]["ALTERADA"] + integridad["resultados"]["FALTANTE"]
    alerta = ""
    if malas or integridad["problemas_cadena"]:
        afectados = sorted({f["ref"] for f in cobertura["controles"]
                            if set(f["evidencias"]) & set(malas)})
        alerta = ("ALERTA DE INTEGRIDAD: %s no conserva(n) su hash registrado%s; los controles "
                  "%s quedan Comprometidos." % (
                      ", ".join(malas) or "la cadena de custodia",
                      "" if not integridad["problemas_cadena"] else " y la cadena esta rota",
                      ", ".join(afectados) or "afectados"))
    partes = ([alerta] if alerta else []) + [
        "Fecha de corte %s, rol %s, vigencia %d dias." % (
            cobertura["fecha_corte"], cobertura["rol"], cobertura["vigencia_dias"]),
        "Evidencias: %d. Integridad: OK %d, ALTERADAS %s, FALTANTES %s. Cadena de custodia: %s." % (
            cobertura["total_evidencias"], len(integridad["resultados"]["OK"]),
            ", ".join(integridad["resultados"]["ALTERADA"]) or "ninguna",
            ", ".join(integridad["resultados"]["FALTANTE"]) or "ninguna",
            "integra" if not integridad["problemas_cadena"] else
            "ROTA (" + "; ".join(integridad["problemas_cadena"]) + ")"),
        "Cobertura automatica: %.1f %% (%d de %d controles aplicables)." % (
            cobertura["porcentaje_cobertura"], c["Cubierto"], cobertura["controles_aplicables"]),
        "Estados: " + ", ".join("%s %d" % (k, v) for k, v in c.items()) + ".",
        "Evidencias registradas (ID [integridad] titulo -> controles que respalda):",
    ]
    for ev in evidencias:
        partes.append("- %s [%s] %s (%s) -> %s" % (
            ev["id"], estado_ev.get(ev["id"], "OK"), ev["titulo"], ev["fecha_documento"],
            ", ".join(ev["controles"])))
    criticos = []
    for estado in ("Sin evidencia", "Comprometida", "Desactualizada", "Parcial"):
        refs = [f["ref"] for f in cobertura["controles"]
                if f["estado"] == estado and f["ref"] in CRITICOS]
        if refs:
            criticos.append("%s: %s" % (estado, ", ".join(refs)))
    partes.append("Controles CRITICOS no cubiertos (lista exacta, no anadas otros): "
                  + ("; ".join(criticos) or "ninguno") + ".")
    partes.append("Controles por estado (entre parentesis, las evidencias ligadas):")
    for estado in ("Cubierto", "Parcial", "Desactualizada", "Comprometida", "Sin evidencia",
                   "No aplica"):
        refs = ["%s%s" % (f["ref"], "(" + ",".join(f["evidencias"]) + ")" if f["evidencias"] else "")
                for f in cobertura["controles"] if f["estado"] == estado]
        if refs:
            partes.append("- %s: %s" % (estado, " ".join(refs)))
    return "\n".join(partes)


# --------------------------------------------------------------------------
def responder(rag, mensaje, historial, resumen):
    fragmentos = rag.buscar(mensaje, k=6)
    # Si la pregunta cita evidencias por su ID, se adjunta su texto completo.
    for ev_id in sorted(set(re.findall(r"EV-\d{4}", mensaje))):
        ya = {f["texto"] for f in fragmentos}
        fragmentos.extend(dict(f, similitud=None) for f in rag.fragmentos
                          if f["ref"] == ev_id and f["texto"] not in ya)
    mensajes = [{"role": "system", "content": _instrucciones()}]
    for turno in historial[-6:]:
        if turno.get("role") in ("user", "assistant"):
            mensajes.append({"role": turno["role"], "content": turno["content"]})
    aviso = ""
    if "ALERTA DE INTEGRIDAD" in (resumen or ""):
        aviso = ("\n\nIMPORTANTE: hay una ALERTA DE INTEGRIDAD en el estado del expediente. "
                 "Si la pregunta trata del expediente, la auditoria o el cumplimiento, empieza "
                 "tu respuesta con esa alerta, copiandola.")
    mensajes.append({"role": "user", "content": _bloque_contexto(fragmentos, resumen) + aviso
                     + "\n\nPREGUNTA DEL USUARIO:\n" + mensaje})
    respuesta = llm_local.conversar(mensajes, temperatura=0.1)
    return respuesta, [{"fuente": f["fuente"], "similitud": f["similitud"]} for f in fragmentos]


def sugerir_clasificacion(rag, catalogo, nombre_archivo, texto):
    """Propone control(es), tipo, titulo y fecha para una evidencia nueva."""
    muestra = (texto or "")[:3000]
    consulta = nombre_archivo + "\n" + muestra[:1500]
    candidatos = rag.buscar(consulta, k=6, tipos=["control"])
    refs_validas = {c["ref"] for c in catalogo}
    from evidencia_api import TIPOS
    # Catalogo completo (33 lineas cortas); el RAG solo ordena las pistas.
    lista = "\n".join("- %s: %s" % (c["ref"], c["titulo"]) for c in catalogo)
    pistas = ", ".join("%s (%.2f)" % (c["ref"], c["similitud"]) for c in candidatos)
    instruccion = (
        "Clasifica la evidencia de auditoria. Primero razona en 'justificacion' (una frase) "
        "que requisito demuestra el documento; despues elige en 'controles' entre 1 y 3 "
        "referencias del CATALOGO cuyo titulo corresponda a esa justificacion (las PISTAS "
        "son los controles mas parecidos por busqueda semantica, pero pueden fallar). "
        "Elige el tipo entre %s, un titulo breve en espanol y la fecha del documento "
        "(AAAA-MM-DD) si aparece en el texto; si no aparece, null. Responde solo JSON con "
        "las claves, en este orden: justificacion, controles (lista), tipo, titulo, "
        "fecha_documento." % ", ".join(TIPOS))
    mensajes = [
        {"role": "system", "content": _instrucciones()},
        {"role": "user", "content": "%s\n\nCATALOGO:\n%s\n\nPISTAS (similitud): %s\n\n"
                                    "ARCHIVO: %s\nCONTENIDO:\n%s" % (
                                        instruccion, lista, pistas, nombre_archivo,
                                        muestra or "(archivo no textual)")},
    ]
    try:
        datos = json.loads(llm_local.conversar(mensajes, temperatura=0, formato_json=True))
    except (ValueError, llm_local.ErrorModelo):
        datos = {}
    controles = [c for c in datos.get("controles", []) if c in refs_validas]
    # Coherencia: si la justificacion nombra candidatos que no eligio, prevalecen esos.
    nombrados = [c["ref"] for c in catalogo
                 if re.search(r"(?<![\w.])%s(?![\w.]*\d)" % re.escape(c["ref"]),
                              datos.get("justificacion", ""))]
    if nombrados and not set(nombrados) & set(controles):
        controles = nombrados[:3]
    if not controles and candidatos:
        controles = [candidatos[0]["ref"]]
    fecha = datos.get("fecha_documento")
    if not (isinstance(fecha, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", fecha)):
        fecha = None
    return {
        "controles": controles,
        "tipo": datos.get("tipo") if datos.get("tipo") in TIPOS else "registro",
        "titulo": datos.get("titulo") or os.path.splitext(nombre_archivo)[0],
        "fecha_documento": fecha,
        "justificacion": datos.get("justificacion", ""),
        "candidatos": [{"ref": c["ref"], "similitud": c["similitud"]} for c in candidatos],
    }


def clasificacion_propuesta(fila):
    """Regla de criterios_evidencia.md, seccion 2 (correspondencia con la matriz)."""
    if fila["estado"] == "Comprometida":
        return "No conformidad mayor (hasta que se explique la alteracion)"
    if fila["estado"] == "Sin evidencia":
        if fila["grupo"] == "clausula" or fila["ref"] in CRITICOS:
            return "No conformidad mayor"
        return "No conformidad menor"
    if fila["estado"] == "Desactualizada":
        return "No conformidad menor"
    return "No conformidad menor u observacion, segun cuanto falte"


def redactar_hallazgo(rag, fila, resumen):
    """Hallazgo preliminar de un control no cubierto, con la plantilla de la skill."""
    with open(RUTA_PLANTILLA, encoding="utf-8") as f:
        plantilla = f.read()
    consulta = "%s %s %s" % (fila["ref"], fila["titulo"], fila["nota"])
    fragmentos = rag.buscar(consulta, k=5)
    for ev_id in fila["evidencias"]:
        fragmentos.extend(f for f in rag.fragmentos if f["ref"] == ev_id)
    datos_fijos = (
        "Control: %s - %s\nEstado en la matriz: %s\nObservacion de la matriz: %s\n"
        "Clasificacion propuesta (regla de criterios_evidencia.md): %s\n"
        "Evidencias revisadas: %s" % (
            fila["ref"], fila["titulo"], fila["estado"], fila["nota"] or "-",
            clasificacion_propuesta(fila), ", ".join(fila["evidencias"]) or "ninguna"))
    instruccion = (
        "Redacta el hallazgo PRELIMINAR rellenando la plantilla. Copia tal cual los DATOS "
        "FIJOS en la tabla (no cambies la clasificacion ni las evidencias). Redacta tu el "
        "criterio, la condicion, la causa, el efecto y la recomendacion usando solo el "
        "contexto. Reglas: (1) menciona unicamente las evidencias de 'Evidencias revisadas'; "
        "no cites otras. (2) Si una de ellas esta ALTERADA, dilo en la condicion. (3) La causa "
        "no se deduce: escribe 'Por determinar con el responsable del proceso' salvo que el "
        "contexto la diga. (4) Nunca recomiendes modificar o corregir una evidencia archivada: "
        "se aporta y registra una evidencia nueva. (5) Usa H-01 como numero.\n\nDATOS FIJOS:\n%s\n\nPLANTILLA:\n%s"
        % (datos_fijos, plantilla))
    mensajes = [{"role": "system", "content": _instrucciones()},
                {"role": "user", "content": _bloque_contexto(fragmentos, resumen)
                 + "\n\n" + instruccion}]
    return llm_local.conversar(mensajes, temperatura=0.2)
