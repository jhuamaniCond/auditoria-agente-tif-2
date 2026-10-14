# -*- coding: utf-8 -*-
"""
Grafo de conocimiento de AUDITA-PIMS: lo que el agente sabe en este momento y
como se relaciona, para la pestana "Grafo de conocimiento".

Nodos
  agente      AUDITA-PIMS
  fuente      cada fuente indexada en el RAG comun (norma, catalogo, criterios...)
  grupo       clausulas 4-10, A.1 responsable, A.2 encargado, A.3 ambos
  control     cada control del catalogo, con su estado de cobertura en el proyecto
  proyecto    la organizacion auditada activa
  evidencia   cada evidencia del expediente, con su integridad

Aristas
  conoce / audita     agente -> fuente / proyecto
  organiza / define   catalogo -> grupo / norma -> grupo
  incluye             grupo -> control
  remite              control -> control que su texto normativo cita (ISOS/texto)
  semejanza           control <-> sus vecinos mas cercanos en el indice FAISS
                      (embeddings nomic-embed-text): asi "relaciona" el agente
  aporta / respalda   proyecto -> evidencia / evidencia -> control
"""

import os
import re

import numpy as np

import norma

VECINOS = 2                 # vecinos semanticos por control
GRUPOS = {
    "clausula": "Cláusulas 4–10 (sistema de gestión)",
    "A.1": "A.1 · Responsable del tratamiento",
    "A.2": "A.2 · Encargado del tratamiento",
    "A.3": "A.3 · Responsable y encargado",
}
FUENTES = {
    "controles_27701.json": "Catálogo de controles",
    "criterios_evidencia.md": "Criterios de evidencia",
    "plantilla_hallazgo.md": "Plantilla de hallazgo",
    "SKILL.md": "Reglas de la skill",
    "glosario_pims.md": "Glosario PIMS",
}
_REF = re.compile(r"(?<![\w.])((?:[AB]\.)?\d{1,2}(?:\.\d{1,2})+)(?!\w)")


def ref_de_catalogo(ref, refs):
    """Control del catalogo al que pertenece una referencia de la norma
    (B.1.3.7 -> A.1.3.7, 9.2.1 -> 9.2), o None."""
    if ref.startswith("B."):
        ref = "A." + ref[2:]
    if ref in refs:
        return ref
    if ref.startswith("A."):
        return None
    padres = [r for r in refs if not r.startswith("A.") and ref.startswith(r + ".")]
    return max(padres, key=len) if padres else None


def _remisiones(refs):
    """{ref: [refs del catalogo que cita su texto normativo]}."""
    salida = {}
    for ref in refs:
        texto = " ".join(s["texto"] for s in norma.para_control(ref))
        citadas = {ref_de_catalogo(r, refs) for r in _REF.findall(texto)}
        salida[ref] = sorted(r for r in citadas if r and r != ref)
    return salida


def _semejanzas(conocimiento):
    """[(ref_a, ref_b, similitud)] entre controles, desde los vectores FAISS."""
    if conocimiento.indice is None:
        return []
    pos = [(i, f["ref"]) for i, f in enumerate(conocimiento.fragmentos) if f["tipo"] == "control"]
    if len(pos) < 2:
        return []
    vectores = np.vstack([conocimiento.indice.reconstruct(i) for i, _ in pos])
    sim = vectores @ vectores.T
    np.fill_diagonal(sim, -1)
    pares = {}
    for a, (_, ref) in enumerate(pos):
        for b in np.argsort(-sim[a])[:VECINOS]:
            clave = tuple(sorted((ref, pos[b][1])))
            pares[clave] = max(pares.get(clave, 0), float(sim[a, b]))
    return [(a, b, round(s, 3)) for (a, b), s in sorted(pares.items())]


def construir(catalogo, conocimiento, proyecto, cobertura, evidencias, integridad):
    """{"nodos": [...], "aristas": [...], "resumen": {...}} para la interfaz."""
    nodos, aristas = [], []

    def nodo(id_, tipo, etiqueta, **datos):
        nodos.append(dict(datos, id=id_, tipo=tipo, etiqueta=etiqueta))

    def arista(origen, destino, tipo, **datos):
        aristas.append(dict(datos, origen=origen, destino=destino, tipo=tipo))

    # Fragmentos por fuente: se cuentan sobre lo que se indexaria (no hace falta Ollama).
    frags = conocimiento._fragmentos()
    indexado = bool(conocimiento.fragmentos)
    por_fuente = {}
    for f in frags:
        clave = "norma" if f["tipo"] == "norma" else f["fuente"]
        por_fuente[clave] = por_fuente.get(clave, 0) + 1

    nodo("agente", "agente", "AUDITA-PIMS",
         detalle="Agente de evidencia y auditoría. Responde con lo que recupera de FAISS "
                 "(conocimiento común + evidencias de este proyecto).")
    normas = sorted({os.path.splitext(os.path.basename(r))[0] for r in norma.rutas()})
    nodo("src:norma", "fuente", "ISO/IEC 27701:2025", fragmentos=por_fuente.get("norma", 0),
         detalle="Texto oficial de %s (ISOS/texto), por cláusula, control del Anexo A y "
                 "guía del Anexo B." % (", ".join(normas) or "la norma"))
    arista("agente", "src:norma", "conoce")
    for archivo, nombre in FUENTES.items():
        nodo("src:" + archivo, "fuente", nombre, archivo=archivo,
             fragmentos=por_fuente.get(archivo, 0))
        arista("agente", "src:" + archivo, "conoce")

    for g, nombre in GRUPOS.items():
        nodo("grp:" + g, "grupo", nombre, grupo=g)
        arista("src:controles_27701.json", "grp:" + g, "organiza")
        arista("src:norma", "grp:" + g, "define")

    filas = {f["ref"]: f for f in cobertura["controles"]}
    refs = [c["ref"] for c in catalogo]
    for c in catalogo:
        fila = filas.get(c["ref"])
        nodo("ctl:" + c["ref"], "control", c["ref"], titulo=c["titulo"], grupo=c["grupo"],
             evidencia_esperada=c["evidencia_esperada"], minimo=c["minimo"],
             estado=fila["estado"] if fila else "Fuera del rol",
             nota=fila["nota"] if fila else "No se evalúa con el rol del proyecto",
             norma=[norma.cita(s) for s in norma.para_control(c["ref"]) if s["texto"]])
        arista("grp:" + c["grupo"], "ctl:" + c["ref"], "incluye")
    for ref, citadas in _remisiones(refs).items():
        for otra in citadas:
            arista("ctl:" + ref, "ctl:" + otra, "remite")
    for a, b, s in _semejanzas(conocimiento):
        arista("ctl:" + a, "ctl:" + b, "semejanza", similitud=s)

    nodo("prj:" + proyecto.id, "proyecto", proyecto.nombre, rol=proyecto.rol,
         detalle=proyecto.descripcion, cobertura=cobertura["porcentaje_cobertura"])
    arista("agente", "prj:" + proyecto.id, "audita")
    for ev in evidencias:
        nodo("ev:" + ev["id"], "evidencia", ev["id"], titulo=ev["titulo"], tipo_doc=ev["tipo"],
             fecha=ev["fecha_documento"], integridad=integridad.get(ev["id"], "OK"),
             sha256=ev["sha256"])
        arista("prj:" + proyecto.id, "ev:" + ev["id"], "aporta")
        for ref in ev["controles"]:
            if ref in refs:
                arista("ev:" + ev["id"], "ctl:" + ref, "respalda")

    return {"nodos": nodos, "aristas": aristas, "resumen": {
        "indexado": indexado, "fragmentos_conocimiento": len(frags),
        "fragmentos_norma": por_fuente.get("norma", 0), "controles": len(catalogo),
        "evidencias": len(evidencias), "cobertura": cobertura["porcentaje_cobertura"],
        "semejanzas": sum(a["tipo"] == "semejanza" for a in aristas),
        "remisiones": sum(a["tipo"] == "remite" for a in aristas)}}


def nodos_de_fuentes(fuentes, refs):
    """IDs de nodo que tocan los fragmentos recuperados en una respuesta del chat."""
    ids = set()
    for f in fuentes:
        tipo, ref = f.get("tipo"), f.get("ref") or ""
        if tipo == "control":
            ids.update(("ctl:" + ref, "src:controles_27701.json"))
        elif tipo == "norma":
            ids.add("src:norma")
            control = ref_de_catalogo(ref, refs)
            if control:
                ids.add("ctl:" + control)
        elif tipo == "evidencia":
            ids.add("ev:" + ref)
        elif tipo == "conocimiento":
            ids.add("src:" + f.get("fuente", ""))
    return sorted(ids)
