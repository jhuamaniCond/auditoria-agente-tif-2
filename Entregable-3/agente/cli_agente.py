# -*- coding: utf-8 -*-
"""
Linea de comandos del Agente de Evidencia y Auditoria (orquestador).

    python cli_agente.py auditoria [--rapido] [--proyecto unsa] [--max-hallazgos 1]
    python cli_agente.py incidente "descripcion" [--rapido]
    python cli_agente.py bandeja [--rapido] [--auto]
    python cli_agente.py estado ID
    python cli_agente.py aprobar ID --auditor "Nombre" [--rechazar] [--comentario ...]
    python cli_agente.py listar [--proyecto unsa]
    python cli_agente.py grafo auditoria_interna

Sin web, al llegar a la puerta HITL la confirmacion se pide por consola (o se
puede salir con Ctrl+C y aprobar despues con 'aprobar ID').
"""

import argparse
import json
import os
import sys
import time

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(errors="replace")
    except AttributeError:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import orquestador  # noqa: E402
from nucleo import ErrorAgente  # noqa: E402

MARCA = {"pendiente": " ", "en_curso": ">", "ok": "x", "error": "!", "omitido": "-"}


def _imprimir_pasos(ej, vistos):
    for p in ej["pasos"]:
        clave = (p["nodo"], p["estado"])
        if p["estado"] in ("pendiente",) or clave in vistos:
            continue
        vistos.add(clave)
        print("  [%s] %-22s %s" % (MARCA.get(p["estado"], "?"), p["nodo"],
                                    (p.get("resumen") or "")[:160]))


def _seguir(id_, interactivo=True, auditor=None):
    vistos = set()
    while True:
        ej = orquestador.obtener(id_)
        _imprimir_pasos(ej, vistos)
        if ej["estado"] == "en_curso":
            time.sleep(1.5)
            continue
        if ej["estado"] == "esperando_aprobacion" and interactivo:
            _pedir_aprobacion(ej, auditor)
            continue
        return _final(ej)


def _pedir_aprobacion(ej, auditor=None):
    a = ej["aprobacion"]
    print("\n=== PUERTA HITL (%s) ===" % a.get("rol_aprobador", "auditor"))
    print(a["pregunta"])
    for h in a.get("hallazgos") or []:
        print("\n--- Hallazgo %s (%s) ---" % (h["ref"], h["estado"]))
        print(h["texto"][:900])
    decisiones = {}
    for p in a.get("propuestas") or []:
        print("\n* Propuesta %s: %s\n  %s" % (p["ref"], p["veredicto"], p.get("justificacion", "")[:400]))
        r = input("  Aceptar esta propuesta? [s/n/Enter=sin decidir] ").strip().lower()
        if r in ("s", "si", "y"):
            decisiones[p["ref"]] = "aceptada"
        elif r in ("n", "no"):
            decisiones[p["ref"]] = "rechazada"
    r = input("\nAprobar la ejecucion? [s/n] ").strip().lower()
    decision = "aprobada" if r in ("s", "si", "y") else "rechazada"
    auditor = auditor or input("Nombre del auditor/DPO: ").strip() or "auditor"
    comentario = input("Comentario (opcional): ").strip()
    orquestador.aprobar(ej["id"], decision, auditor, comentario, decisiones)
    print("Decision registrada: %s por %s\n" % (decision, auditor))


def _final(ej):
    print("\nEjecucion %s: %s" % (ej["id"], ej["estado"].upper()))
    if ej["estado"] == "esperando_aprobacion":
        print("Pendiente de aprobacion. Usa: python cli_agente.py aprobar %s --auditor NOMBRE"
              % ej["id"])
    res = ej.get("resultado") or {}
    if res.get("informe"):
        print("Informe: %s" % res["informe"])
    for a in (res.get("plan_accion") or [])[:10]:
        print("  - %s %s | %s | %s" % (a.get("ref", ""), a.get("accion", "")[:90],
                                       a.get("responsable", ""),
                                       a.get("fecha_limite") or "%s h" % a.get("plazo_horas")))
    if res.get("registradas"):
        for r in res["registradas"]:
            print("  registrada %s <- %s" % (r["id"], r["archivo"]))
    if ej.get("error"):
        print("ERROR: %s" % ej["error"])
    return 0 if ej["estado"] in ("completada", "rechazada", "esperando_aprobacion") else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Agente de Evidencia y Auditoria (orquestador)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def comunes(s):
        s.add_argument("--proyecto", default="unsa")
        s.add_argument("--rapido", action="store_true", help="sin LLM (textos deterministas)")
        s.add_argument("--no-interactivo", action="store_true",
                       help="no preguntar en la puerta HITL (queda esperando aprobacion)")
        s.add_argument("--auditor", default=None)

    s = sub.add_parser("auditoria", help="auditoria interna (9.2)")
    comunes(s)
    s.add_argument("--max-hallazgos", type=int, default=3)
    s.add_argument("--max-pertinencia", type=int, default=3)
    s.add_argument("--rol", default=None)
    s.add_argument("--alcance", default=None)
    s.add_argument("--periodo", default=None, help="dias de vigencia o AAAA-MM-DD/AAAA-MM-DD")
    s = sub.add_parser("incidente", help="documentar un incidente (A.3.12)")
    s.add_argument("descripcion")
    comunes(s)
    s.add_argument("--simulado", action="store_true",
                   help="publicarlo en el bus como el Agente de Incidentes")
    s = sub.add_parser("bandeja", help="procesar archivos de la bandeja de entrada")
    comunes(s)
    s.add_argument("--auto", action="store_true", help="auto_registrar sin HITL")
    s = sub.add_parser("estado")
    s.add_argument("id")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("aprobar")
    s.add_argument("id")
    s.add_argument("--auditor", required=True)
    s.add_argument("--rechazar", action="store_true")
    s.add_argument("--comentario", default="")
    s.add_argument("--aceptar", nargs="*", default=[], help="refs de propuestas aceptadas")
    s.add_argument("--rechazar-propuestas", nargs="*", default=[])
    s = sub.add_parser("listar")
    s.add_argument("--proyecto", default=None)
    s = sub.add_parser("grafo")
    s.add_argument("tipo", choices=orquestador.TIPOS)
    a = ap.parse_args(argv)

    try:
        if a.cmd in ("auditoria", "incidente", "bandeja"):
            par = {"modo_rapido": a.rapido, "solicitado_por": "cli"}
            if a.cmd == "auditoria":
                par.update(max_hallazgos=a.max_hallazgos, max_pertinencia=a.max_pertinencia)
                for k in ("rol", "alcance", "periodo"):
                    if getattr(a, k):
                        par[k] = getattr(a, k)
                ej = orquestador.iniciar("auditoria_interna", a.proyecto, par)
            elif a.cmd == "incidente":
                if a.simulado:
                    import coordinacion
                    evt = coordinacion.simular_agente_incidentes(a.descripcion, a.proyecto, par)
                    ej = {"id": evt["entregas"][0]["resultado"]["ejecucion"]}
                else:
                    par["descripcion"] = a.descripcion
                    ej = orquestador.iniciar("incidente", a.proyecto, par)
            else:
                par["auto_registrar"] = a.auto
                ej = orquestador.iniciar("bandeja", a.proyecto, par)
            print("Ejecucion %s iniciada (%s)" % (ej["id"], orquestador.TIPO_CHECKPOINTER))
            return _seguir(ej["id"], not a.no_interactivo, a.auditor)
        if a.cmd == "estado":
            ej = orquestador.obtener(a.id)
            if not ej:
                print("No existe %s" % a.id)
                return 1
            if a.json:
                print(json.dumps(ej, ensure_ascii=False, indent=2))
                return 0
            print("%s  %s  %s  proyecto=%s" % (ej["id"], ej["tipo"], ej["estado"], ej["proyecto"]))
            _imprimir_pasos(ej, set())
            return _final(ej)
        if a.cmd == "aprobar":
            dec = {r: "aceptada" for r in a.aceptar}
            dec.update({r: "rechazada" for r in a.rechazar_propuestas})
            orquestador.aprobar(a.id, "rechazada" if a.rechazar else "aprobada", a.auditor,
                                a.comentario, dec)
            return _seguir(a.id, interactivo=True, auditor=a.auditor)
        if a.cmd == "listar":
            for ej in orquestador.listar(a.proyecto):
                print("%-28s %-18s %-21s %s" % (ej["id"], ej["tipo"], ej["estado"], ej["creado"]))
            return 0
        if a.cmd == "grafo":
            print(orquestador.diagrama(a.tipo))
            return 0
    except ErrorAgente as e:
        print("Error: %s" % e)
        return 2
    except KeyboardInterrupt:
        print("\nInterrumpido. La ejecucion sigue guardada; consulta con 'estado ID'.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
