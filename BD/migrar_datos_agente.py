# -*- coding: utf-8 -*-
"""Migra los datos que el agente guardaba en archivos (Entregable-2/datos) a PostgreSQL.

Usa las mismas funciones de almacen_pg.py que el agente, asi lo migrado es identico
a lo que el agente escribe desde ahora. Idempotente: rehace los datos del proyecto.

  proyectos/<id>/proyecto.json + expediente/soa.csv   -> proyectos + soa_evaluaciones
  expediente/registro_evidencias.json                 -> evidencias + evidencia_requisito
  expediente/cadena_custodia.log                      -> cadena_custodia (hashes intactos)
  expediente/revisiones_pertinencia.json              -> revisiones_pertinencia
  ejecuciones/*.json y ejecuciones/_estado/*.json     -> ejecuciones, instantaneas
                                                         (+ auditorias/hallazgos/acciones)
  bitacora_decisiones.jsonl, eventos.jsonl, bitacora_mcp.jsonl -> sus tablas

Requiere haber ejecutado antes cargar_catalogo.py.
Uso:  python migrar_datos_agente.py [--datos RUTA] [--proyecto unsa]
"""

import argparse
import csv
import glob
import json
import os
import sys

from psycopg.types.json import Jsonb

from almacen_pg import AlmacenPG, _json

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "Entregable-2", "datos")


def leer_json(ruta, defecto=None):
    if not os.path.exists(ruta):
        return defecto
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def leer_jsonl(ruta):
    if not os.path.exists(ruta):
        return []
    with open(ruta, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datos", default=DATOS, help="carpeta datos/ del Entregable 2")
    ap.add_argument("--proyecto", default="unsa")
    args = ap.parse_args()

    base = os.path.join(args.datos, "proyectos", args.proyecto)
    exp = os.path.join(base, "expediente")
    ficha = leer_json(os.path.join(base, "proyecto.json"))
    if not ficha:
        sys.exit("No existe %s" % os.path.join(base, "proyecto.json"))

    almacen = AlmacenPG()
    almacen.borrar_proyecto(args.proyecto)

    # Proyecto (+ exclusiones de la SoA si existian)
    excluidos = []
    soa_csv = os.path.join(exp, "soa.csv")
    if os.path.exists(soa_csv):
        with open(soa_csv, encoding="utf-8", newline="") as f:
            excluidos = [{"ref": r["control_ref"], "justificacion": r.get("justificacion") or "Excluido"}
                         for r in csv.DictReader(f) if r["aplicable"].strip().lower() in ("no", "false", "0")]
    almacen.crear_proyecto(ficha, excluidos)

    # Expediente
    indice = leer_json(os.path.join(exp, "registro_evidencias.json"), {"evidencias": []})
    almacen.guardar_indice(exp, indice)
    custodia = leer_jsonl(os.path.join(exp, "cadena_custodia.log"))
    for linea in custodia:
        almacen.agregar_custodia(exp, linea)
    revs = leer_json(os.path.join(exp, "revisiones_pertinencia.json"), {"revisiones": {}})["revisiones"]
    almacen.guardar_revisiones(exp, revs)

    # Ejecuciones del orquestador (las completadas generan la auditoria en las tablas de GESTITEL)
    n_ej = 0
    for ruta in sorted(glob.glob(os.path.join(args.datos, "ejecuciones", "*.json"))):
        ej = leer_json(ruta)
        if ej.get("proyecto") == args.proyecto:
            almacen.guardar_ejecucion(ej)
            n_ej += 1
            inst = leer_json(os.path.join(args.datos, "ejecuciones", "_estado", ej["id"] + ".json"))
            if inst:
                almacen.guardar_instantanea(inst)

    # Bitacoras
    decisiones = [d for d in leer_jsonl(os.path.join(args.datos, "bitacora_decisiones.jsonl"))
                  if d.get("proyecto") in (None, args.proyecto)]
    for d in decisiones:
        almacen.guardar_decision(d)
    eventos = leer_jsonl(os.path.join(args.datos, "eventos.jsonl"))
    for ev in eventos:
        almacen.guardar_evento(ev)

    # Bitacora MCP: se copia tal cual (con sus hashes), sin volver a encadenar
    mcp = leer_jsonl(os.path.join(args.datos, "bitacora_mcp.jsonl"))
    with almacen.conexion().cursor() as cur:
        cur.execute("SELECT COALESCE(max(n), 0) AS n FROM bitacora_mcp")
        ya = cur.fetchone()["n"]
        for m in mcp:
            if m["n"] <= ya:
                continue
            contenido = _json({k: v for k, v in m.items() if k not in ("hash_anterior", "hash")})
            cur.execute(
                """INSERT INTO bitacora_mcp (n, fecha, tool, argumentos, transporte, pid, resultado,
                                             duracion_ms, contenido, hash_anterior, hash)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (m["n"], m["fecha"], m["tool"], Jsonb(m.get("argumentos") or {}), m.get("transporte"),
                 m.get("pid"), str(m.get("resultado")), m.get("duracion_ms"), Jsonb(contenido),
                 m["hash_anterior"], m["hash"]))

    # Comprobacion: la cadena leida desde la BD debe validar con el codigo de la skill
    sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "Entregable-1", "02-skill",
                                    "evidencia-auditoria-pims", "scripts"))
    import evidencia
    evidencia.ALMACEN = almacen
    problemas = evidencia.comprobar_cadena(exp, evidencia.leer_indice(exp))
    mcp_ok = almacen.verificar_mcp()

    with almacen.conexion().cursor() as cur:
        cur.execute("SELECT count(*) AS a, (SELECT count(*) FROM hallazgos h JOIN auditorias x "
                    "ON x.id = h.auditoria_id WHERE x.proyecto = %s) AS h FROM auditorias WHERE proyecto = %s",
                    (args.proyecto, args.proyecto))
        aud = cur.fetchone()

    print("Proyecto '%s' migrado a %s:" % (args.proyecto, almacen.descripcion()))
    print("  evidencias=%d  custodia=%d  pertinencia=%d  ejecuciones=%d"
          % (len(indice["evidencias"]), len(custodia), len(revs), n_ej))
    print("  auditorias=%d  hallazgos=%d" % (aud["a"], aud["h"]))
    print("  decisiones=%d  eventos=%d  llamadas_mcp=%d" % (len(decisiones), len(eventos), len(mcp)))
    print("  cadena de custodia: %s" % ("integra" if not problemas else "; ".join(problemas)))
    print("  bitacora MCP: %s" % ("integra" if mcp_ok["integra"] else "; ".join(mcp_ok["problemas"])))


if __name__ == "__main__":
    main()
