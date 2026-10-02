# -*- coding: utf-8 -*-
"""
evidencia.py - Parte determinista de la skill evidencia-auditoria-pims.

Gestiona el expediente de evidencias de auditoria del PIMS (ISO/IEC 27701:2025):

    registrar  copia la evidencia al expediente, calcula su SHA-256 y la anota
               en el indice y en la cadena de custodia.
    verificar  recalcula los hashes y comprueba que la cadena de custodia no
               fue reescrita.
    cobertura  cruza las evidencias con el catalogo de controles (y la SoA, si
               existe) y genera la matriz de cobertura en Markdown y JSON.
    listar     muestra el indice de evidencias.

Solo usa la biblioteca estandar de Python 3.8+.
"""

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
CATALOGO_POR_DEFECTO = os.path.join(AQUI, "..", "references", "controles_27701.json")

INDICE = "registro_evidencias.json"
CADENA = "cadena_custodia.log"
CARPETA_ARCHIVOS = "archivos"
SOA = "soa.csv"

TIPOS = ("politica", "procedimiento", "registro", "log", "acta", "contrato",
         "informe", "configuracion", "captura")

GRUPOS_POR_ROL = {
    "responsable": ("clausula", "A.1", "A.3"),
    "encargado": ("clausula", "A.2", "A.3"),
    "ambos": ("clausula", "A.1", "A.2", "A.3"),
}

ORDEN_ESTADOS = ("Cubierto", "Parcial", "Desactualizada", "Comprometida",
                 "Sin evidencia", "No aplica")

GENESIS = "0" * 64


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------
def sha256_archivo(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(65536), b""):
            h.update(bloque)
    return h.hexdigest()


def ahora():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def leer_indice(expediente):
    ruta = os.path.join(expediente, INDICE)
    if not os.path.exists(ruta):
        return {"norma": "ISO/IEC 27701:2025", "evidencias": []}
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def guardar_indice(expediente, indice):
    ruta = os.path.join(expediente, INDICE)
    temporal = ruta + ".tmp"
    with open(temporal, "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False, indent=2)
    os.replace(temporal, ruta)


def leer_cadena(expediente):
    ruta = os.path.join(expediente, CADENA)
    if not os.path.exists(ruta):
        return []
    with open(ruta, encoding="utf-8") as f:
        return [json.loads(linea) for linea in f if linea.strip()]


def _hash_linea(contenido, hash_anterior):
    canonico = json.dumps(contenido, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256((hash_anterior + canonico).encode("utf-8")).hexdigest()


def anotar_custodia(expediente, accion, responsable, **datos):
    """Anade una linea a la cadena de custodia enlazada por hash."""
    cadena = leer_cadena(expediente)
    anterior = cadena[-1]["hash_linea"] if cadena else GENESIS
    contenido = {"n": len(cadena) + 1, "fecha": ahora(), "accion": accion,
                 "responsable": responsable}
    contenido.update(datos)
    linea = dict(contenido)
    linea["hash_anterior"] = anterior
    linea["hash_linea"] = _hash_linea(contenido, anterior)
    with open(os.path.join(expediente, CADENA), "a", encoding="utf-8") as f:
        f.write(json.dumps(linea, ensure_ascii=False) + "\n")
    return linea


def leer_catalogo(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)["controles"]


def leer_soa(expediente):
    """Devuelve {control_ref: (aplicable, justificacion)} o {} si no hay SoA."""
    ruta = os.path.join(expediente, SOA)
    if not os.path.exists(ruta):
        return {}
    soa = {}
    with open(ruta, encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            aplicable = fila["aplicable"].strip().lower() in ("si", "sí", "true", "1", "yes")
            soa[fila["control_ref"].strip()] = (aplicable, fila.get("justificacion", "").strip())
    return soa


def estado_integridad(expediente, evidencia):
    ruta = os.path.join(expediente, evidencia["archivo"])
    if not os.path.exists(ruta):
        return "FALTANTE"
    return "OK" if sha256_archivo(ruta) == evidencia["sha256"] else "ALTERADA"


def comprobar_cadena(expediente, indice):
    """Devuelve la lista de problemas encontrados en la cadena de custodia."""
    problemas = []
    anterior = GENESIS
    registros = {}
    for linea in leer_cadena(expediente):
        contenido = {k: v for k, v in linea.items()
                     if k not in ("hash_anterior", "hash_linea")}
        if linea["hash_anterior"] != anterior:
            problemas.append("linea %s: no enlaza con la anterior" % linea["n"])
        if _hash_linea(contenido, linea["hash_anterior"]) != linea["hash_linea"]:
            problemas.append("linea %s: contenido modificado" % linea["n"])
        anterior = linea["hash_linea"]
        if linea["accion"] == "REGISTRO":
            registros[linea["evidencia"]] = linea["sha256"]
    # El indice no puede contradecir a la cadena (p. ej. alguien cambio un hash
    # en registro_evidencias.json para encubrir una alteracion).
    for ev_id in inconsistentes_con_cadena(indice, registros):
        problemas.append("%s: el indice no coincide con la cadena" % ev_id)
    return problemas


def registros_en_cadena(expediente):
    return {l["evidencia"]: l["sha256"] for l in leer_cadena(expediente)
            if l["accion"] == "REGISTRO"}


def inconsistentes_con_cadena(indice, registros):
    return [ev["id"] for ev in indice["evidencias"]
            if registros.get(ev["id"]) != ev["sha256"]]


def _consola_utf8():
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


# --------------------------------------------------------------------------
# Subcomandos
# --------------------------------------------------------------------------
def cmd_registrar(args):
    if not os.path.isfile(args.archivo):
        sys.exit("No existe el archivo: %s" % args.archivo)
    catalogo = {c["ref"] for c in leer_catalogo(args.catalogo)}
    desconocidos = [c for c in args.control if c not in catalogo]
    if desconocidos:
        sys.exit("Controles no presentes en el catalogo: %s" % ", ".join(desconocidos))
    if args.fecha_documento:
        dt.date.fromisoformat(args.fecha_documento)  # valida el formato

    os.makedirs(os.path.join(args.expediente, CARPETA_ARCHIVOS), exist_ok=True)
    indice = leer_indice(args.expediente)
    huella = sha256_archivo(args.archivo)

    repetida = next((e for e in indice["evidencias"] if e["sha256"] == huella), None)
    if repetida:
        sys.exit("Ese archivo ya esta registrado como %s" % repetida["id"])

    nuevo_id = "EV-%04d" % (len(indice["evidencias"]) + 1)
    destino = os.path.join(CARPETA_ARCHIVOS,
                           "%s_%s" % (nuevo_id, os.path.basename(args.archivo)))
    shutil.copy2(args.archivo, os.path.join(args.expediente, destino))

    evidencia = {
        "id": nuevo_id,
        "controles": args.control,
        "tipo": args.tipo,
        "titulo": args.titulo,
        "archivo": destino.replace(os.sep, "/"),
        "sha256": huella,
        "tamano_bytes": os.path.getsize(args.archivo),
        "fecha_documento": args.fecha_documento or dt.date.today().isoformat(),
        "fecha_registro": ahora(),
        "responsable": args.responsable,
        "fuente": args.fuente,
    }
    indice["evidencias"].append(evidencia)
    guardar_indice(args.expediente, indice)
    anotar_custodia(args.expediente, "REGISTRO", args.responsable,
                    evidencia=nuevo_id, sha256=huella, controles=args.control)
    print("%s registrada  sha256=%s  controles=%s"
          % (nuevo_id, huella[:16] + "...", ",".join(args.control)))


def cmd_verificar(args):
    indice = leer_indice(args.expediente)
    resultados = {"OK": [], "ALTERADA": [], "FALTANTE": []}
    for ev in indice["evidencias"]:
        resultados[estado_integridad(args.expediente, ev)].append(ev["id"])
    problemas_cadena = comprobar_cadena(args.expediente, indice)

    print("Evidencias verificadas: %d" % len(indice["evidencias"]))
    for estado in ("OK", "ALTERADA", "FALTANTE"):
        ids = resultados[estado]
        print("  %-9s %3d  %s" % (estado, len(ids), ", ".join(ids) if estado != "OK" else ""))
    if problemas_cadena:
        print("CADENA ROTA:")
        for p in problemas_cadena:
            print("  - " + p)
    else:
        print("Cadena de custodia: integra")

    anotar_custodia(args.expediente, "VERIFICACION", args.responsable,
                    ok=len(resultados["OK"]), alteradas=resultados["ALTERADA"],
                    faltantes=resultados["FALTANTE"],
                    cadena_integra=not problemas_cadena)
    if resultados["ALTERADA"] or resultados["FALTANTE"] or problemas_cadena:
        sys.exit(1)


def evaluar_cobertura(expediente, catalogo, rol, vigencia_dias, fecha_corte):
    indice = leer_indice(expediente)
    soa = leer_soa(expediente)
    integridad = {ev["id"]: estado_integridad(expediente, ev) for ev in indice["evidencias"]}
    for ev_id in inconsistentes_con_cadena(indice, registros_en_cadena(expediente)):
        integridad[ev_id] = "ALTERADA"
    limite = fecha_corte - dt.timedelta(days=vigencia_dias)

    filas = []
    for control in catalogo:
        if control["grupo"] not in GRUPOS_POR_ROL[rol]:
            continue
        ligadas = [ev for ev in indice["evidencias"] if control["ref"] in ev["controles"]]
        ids = [ev["id"] for ev in ligadas]
        aplicable, justificacion = soa.get(control["ref"], (True, ""))
        validas = [ev for ev in ligadas if integridad[ev["id"]] == "OK"]
        vigentes = [ev for ev in validas
                    if dt.date.fromisoformat(ev["fecha_documento"]) >= limite]

        if not aplicable:
            estado, nota = "No aplica", justificacion or "Excluido en la SoA"
        elif not ligadas:
            estado, nota = "Sin evidencia", "Se espera: " + control["evidencia_esperada"]
        elif len(validas) < len(ligadas):
            malas = [e for e in ids if integridad[e] != "OK"]
            estado, nota = "Comprometida", "Integridad fallida en " + ", ".join(malas)
        elif len(vigentes) >= control["minimo"]:
            estado, nota = "Cubierto", ""
        elif not vigentes:
            estado = "Desactualizada"
            nota = "Evidencia anterior a %s" % limite.isoformat()
        else:
            estado = "Parcial"
            nota = "%d de %d evidencias vigentes requeridas. Se espera: %s" % (
                len(vigentes), control["minimo"], control["evidencia_esperada"])
        filas.append({"ref": control["ref"], "grupo": control["grupo"],
                      "titulo": control["titulo"], "estado": estado,
                      "evidencias": ids, "nota": nota})

    conteo = {e: sum(1 for f in filas if f["estado"] == e) for e in ORDEN_ESTADOS}
    aplicables = len(filas) - conteo["No aplica"]
    porcentaje = round(100.0 * conteo["Cubierto"] / aplicables, 1) if aplicables else 0.0
    return {
        "norma": "ISO/IEC 27701:2025",
        "fecha_corte": fecha_corte.isoformat(),
        "rol": rol,
        "vigencia_dias": vigencia_dias,
        "total_evidencias": len(indice["evidencias"]),
        "integridad": {k: sum(1 for v in integridad.values() if v == k)
                       for k in ("OK", "ALTERADA", "FALTANTE")},
        "controles_evaluados": len(filas),
        "controles_aplicables": aplicables,
        "porcentaje_cobertura": porcentaje,
        "conteo_estados": conteo,
        "controles": filas,
    }


def informe_markdown(r):
    lineas = [
        "# Matriz de cobertura de evidencias - ISO/IEC 27701:2025",
        "",
        "- Fecha de corte: %s" % r["fecha_corte"],
        "- Rol evaluado: %s" % r["rol"],
        "- Vigencia de la evidencia: %d dias" % r["vigencia_dias"],
        "- Evidencias en el expediente: %d (OK %d, alteradas %d, faltantes %d)" % (
            r["total_evidencias"], r["integridad"]["OK"],
            r["integridad"]["ALTERADA"], r["integridad"]["FALTANTE"]),
        "- **Cobertura: %.1f %%** (%d de %d controles aplicables cubiertos)" % (
            r["porcentaje_cobertura"], r["conteo_estados"]["Cubierto"],
            r["controles_aplicables"]),
        "",
        "## Resumen por estado",
        "",
        "| Estado | Controles |",
        "|---|---|",
    ]
    lineas += ["| %s | %d |" % (e, r["conteo_estados"][e]) for e in ORDEN_ESTADOS]
    lineas += ["", "## Matriz", "",
               "| Control | Titulo | Estado | Evidencias | Observacion |",
               "|---|---|---|---|---|"]
    for f in r["controles"]:
        lineas.append("| %s | %s | %s | %s | %s |" % (
            f["ref"], f["titulo"], f["estado"], ", ".join(f["evidencias"]) or "-",
            f["nota"] or "-"))
    brechas = [f for f in r["controles"] if f["estado"] not in ("Cubierto", "No aplica")]
    lineas += ["", "## Brechas para redactar hallazgos (%d)" % len(brechas), ""]
    for f in brechas:
        lineas.append("- **%s %s** - %s. %s" % (f["ref"], f["titulo"], f["estado"], f["nota"]))
    lineas += ["", "> Resultado automatico. Los hallazgos son PRELIMINARES y requieren "
               "validacion del auditor interno (clausula 9.2)."]
    return "\n".join(lineas) + "\n"


def cmd_cobertura(args):
    fecha = dt.date.fromisoformat(args.fecha_corte) if args.fecha_corte else dt.date.today()
    r = evaluar_cobertura(args.expediente, leer_catalogo(args.catalogo),
                          args.rol, args.vigencia_dias, fecha)
    md = informe_markdown(r)
    if args.salida:
        with open(args.salida, "w", encoding="utf-8") as f:
            f.write(md)
        with open(os.path.splitext(args.salida)[0] + ".json", "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=2)
        print("Informe escrito en %s (y .json)" % args.salida)
    print("Cobertura %.1f %% | %s" % (r["porcentaje_cobertura"], " | ".join(
        "%s %d" % (e, r["conteo_estados"][e]) for e in ORDEN_ESTADOS)))


def cmd_listar(args):
    indice = leer_indice(args.expediente)
    for ev in indice["evidencias"]:
        print("%s  %-13s %-10s %-22s %s" % (ev["id"], ev["tipo"], ev["fecha_documento"],
                                            ",".join(ev["controles"]), ev["titulo"]))


# --------------------------------------------------------------------------
def main(argv=None):
    _consola_utf8()
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("--catalogo", default=CATALOGO_POR_DEFECTO)
    sub = p.add_subparsers(dest="comando", required=True)

    r = sub.add_parser("registrar", help="registra una evidencia")
    r.add_argument("--expediente", default="expediente")
    r.add_argument("--archivo", required=True)
    r.add_argument("--control", action="append", required=True,
                   help="referencia del control; se puede repetir")
    r.add_argument("--tipo", choices=TIPOS, required=True)
    r.add_argument("--titulo", required=True)
    r.add_argument("--responsable", required=True)
    r.add_argument("--fuente", default="")
    r.add_argument("--fecha-documento", help="AAAA-MM-DD; por defecto hoy")
    r.set_defaults(func=cmd_registrar)

    v = sub.add_parser("verificar", help="verifica hashes y cadena de custodia")
    v.add_argument("--expediente", default="expediente")
    v.add_argument("--responsable", default="agente-evidencia")
    v.set_defaults(func=cmd_verificar)

    c = sub.add_parser("cobertura", help="genera la matriz de cobertura")
    c.add_argument("--expediente", default="expediente")
    c.add_argument("--rol", choices=sorted(GRUPOS_POR_ROL), default="ambos")
    c.add_argument("--vigencia-dias", type=int, default=365)
    c.add_argument("--fecha-corte", help="AAAA-MM-DD; por defecto hoy")
    c.add_argument("--salida", help="ruta del informe .md (se crea tambien .json)")
    c.set_defaults(func=cmd_cobertura)

    l = sub.add_parser("listar", help="lista las evidencias registradas")
    l.add_argument("--expediente", default="expediente")
    l.set_defaults(func=cmd_listar)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
