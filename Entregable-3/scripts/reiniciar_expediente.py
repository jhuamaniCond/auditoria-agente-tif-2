# -*- coding: utf-8 -*-
"""
Reinicia el expediente de la UNSA con un historial limpio y lo reconstruye.

    pg_dump primero (BD/respaldos/), luego:
    python Entregable-3/scripts/reiniciar_expediente.py --actor "Nombre" --confirmar REINICIAR

Conserva:
  - los documentos oficiales de la UNSA ya leidos (tablas documentos / documento_paginas, con OCR);
  - la auditoria diagnostica AUD-2026-001 (27-10-2026), que cita PIMS-PR-03, con su ejecucion,
    checklist, hallazgos, acciones y decisiones.
Vacia el resto con nucleo.vaciar_datos() (la misma funcion de "Vaciar la base de datos") y
reconstruye: las 14 evidencias de docs-unsa y los documentos PIMS vigentes (una version cada uno).
"""
import argparse
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
E3 = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(E3, "agente"))

import nucleo  # noqa: E402
from psycopg.types.json import Jsonb  # noqa: E402

AUDITORIA = "AUD-2026-001"


def _columnas_json(cur, tabla):
    cur.execute("""SELECT column_name FROM information_schema.columns
                   WHERE table_name = %s AND data_type IN ('json', 'jsonb')""", (tabla,))
    return {r["column_name"] for r in cur.fetchall()}


def _leer(cur, tabla, where, params):
    cur.execute("SELECT * FROM %s WHERE %s" % (tabla, where), params)
    return [dict(r) for r in cur.fetchall()]


def _insertar(cur, tabla, filas):
    if not filas:
        return 0
    js = _columnas_json(cur, tabla)
    for f in filas:
        cols = list(f)
        vals = [Jsonb(f[c]) if c in js and f[c] is not None else f[c] for c in cols]
        cur.execute("INSERT INTO %s (%s) VALUES (%s)" % (tabla, ", ".join(cols), ", ".join(["%s"] * len(cols))), vals)
    if "id" not in filas[0]:
        return len(filas)
    cur.execute("SELECT pg_get_serial_sequence(%s, 'id') AS s", (tabla,))
    seq = cur.fetchone()["s"]
    if seq:
        cur.execute("SELECT setval(%s, (SELECT COALESCE(MAX(id), 1) FROM " + tabla + "))", (seq,))
    return len(filas)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--actor", required=True)
    ap.add_argument("--confirmar", required=True, help="escribir REINICIAR")
    ap.add_argument("--sin-reconstruir", action="store_true")
    a = ap.parse_args()
    if a.confirmar != "REINICIAR":
        sys.exit("Escriba --confirmar REINICIAR")
    if nucleo.ALMACEN is None:
        sys.exit("Necesita PostgreSQL (PIMS_BACKEND=postgres)")
    cx = nucleo.ALMACEN.conexion()
    with cx.cursor() as cur:
        cur.execute("SELECT id FROM ejecuciones WHERE estado IN ('en_curso', 'esperando_aprobacion')")
        abiertas = [r["id"] for r in cur.fetchall()]
        if abiertas:
            sys.exit("Hay ejecuciones abiertas: %s. Cancelelas antes." % ", ".join(abiertas))
        conservar = {}
        conservar["documentos"] = _leer(cur, "documentos", "tipo_documento <> 'documento_pims'", ())
        ids_doc = [d["id"] for d in conservar["documentos"]] or [0]
        conservar["documento_paginas"] = _leer(cur, "documento_paginas", "documento_id = ANY(%s)", (ids_doc,))
        aud = _leer(cur, "auditorias", "codigo = %s", (AUDITORIA,))
        conservar["auditorias"] = aud
        aud_ids = [x["id"] for x in aud] or [0]
        ejec = [x["ejecucion_agente"] for x in aud if x.get("ejecucion_agente")] or [""]
        conservar["ejecuciones"] = _leer(cur, "ejecuciones", "id = ANY(%s)", (ejec,))
        conservar["ejecucion_instantaneas"] = _leer(cur, "ejecucion_instantaneas", "ejecucion = ANY(%s)", (ejec,)) \
            if "ejecucion" in {c for c in _columnas_tabla(cur, "ejecucion_instantaneas")} else []
        conservar["decisiones_humanas"] = _leer(cur, "decisiones_humanas", "ejecucion = ANY(%s)", (ejec,))
        conservar["checklist_items"] = _leer(cur, "checklist_items", "auditoria_id = ANY(%s)", (aud_ids,))
        conservar["hallazgos"] = _leer(cur, "hallazgos", "auditoria_id = ANY(%s)", (aud_ids,))
        hal_ids = [h["id"] for h in conservar["hallazgos"]] or [0]
        conservar["acciones"] = _leer(cur, "acciones", "hallazgo_id = ANY(%s)", (hal_ids,))
    cx.close()
    print("Se conserva:", {k: len(v) for k, v in conservar.items()})

    resumen = nucleo.vaciar_datos()
    print("Vaciado:", sum(resumen["filas"].values()), "filas;", len(resumen["carpetas"]), "archivos o carpetas")

    cx = nucleo.ALMACEN.conexion()
    with cx.transaction(), cx.cursor() as cur:
        for tabla in ("documentos", "documento_paginas", "ejecuciones", "ejecucion_instantaneas",
                      "decisiones_humanas", "auditorias", "checklist_items", "hallazgos", "acciones"):
            print("  restaurado %-24s %d" % (tabla, _insertar(cur, tabla, conservar.get(tabla, []))))
        cur.execute("""INSERT INTO decisiones_humanas (fecha, flujo, proyecto, nodo, actor, origen, decision, detalle)
                       VALUES (now(), 'mantenimiento', 'unsa', 'reiniciar_expediente', %s, 'humano',
                               'expediente reiniciado con historial limpio', %s)""",
                    (a.actor, Jsonb({"conservado": {k: len(v) for k, v in conservar.items()},
                                     "respaldo": "BD/respaldos/antes_reinicio_expediente_*.dump",
                                     "motivo": "versiones duplicadas de documentos PIMS registradas durante pruebas"})))
    cx.close()
    nucleo.PROYECTOS._cache.clear()
    nucleo.asegurar_unsa()
    if a.sin_reconstruir:
        return
    print("\nReconstruyendo el expediente (docs-unsa)…")
    import cargar_expediente_unsa
    cargar_expediente_unsa.main()
    print("\nRegistrando los documentos PIMS vigentes…")
    import documentos_pims
    import glob
    documentos_pims.sincronizar_lista_maestra()
    rutas = [r for carpeta in ("generados", "otros-grupos")
             for r in sorted(glob.glob(os.path.join(E3, "documentos-pims", carpeta, "*.docx")))]
    for ruta in rutas:
        d = documentos_pims.registrar(ruta, a.actor)
        print("  %s v%s %s control=%s" % (d["codigo"], d["version"], d["estado"], d["control"]["resultado"]))


def _columnas_tabla(cur, tabla):
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (tabla,))
    return [r["column_name"] for r in cur.fetchall()]


if __name__ == "__main__":
    main()
