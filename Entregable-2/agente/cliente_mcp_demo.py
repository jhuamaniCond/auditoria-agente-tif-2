# -*- coding: utf-8 -*-
"""
Cliente MCP de demostracion para el servidor "evidencias-pims".

Lanza servidor_mcp.py por stdio (como lo haria Claude Desktop o Claude Code),
lista sus tools, resources y prompts, y llama a las tools deterministas (sin IA)
sobre el proyecto 'unsa': listar_proyectos, estado_expediente,
verificar_integridad y matriz_cobertura.

    python cliente_mcp_demo.py                 # solo deterministas
    python cliente_mcp_demo.py --ia            # ademas buscar_evidencia (Ollama)
    python cliente_mcp_demo.py --ia --consulta "registro de actividades de tratamiento"
"""

import argparse
import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

AQUI = os.path.dirname(os.path.abspath(__file__))
SERVIDOR = os.path.join(AQUI, "servidor_mcp.py")


def _campo(obj, *nombres):
    """Compatibilidad SDK v1 (camelCase) / v2 (snake_case)."""
    for n in nombres:
        if hasattr(obj, n):
            return getattr(obj, n)
    return None


def datos(resultado):
    """Contenido JSON de un CallToolResult; lanza RuntimeError si la tool fallo."""
    textos = [c.text for c in resultado.content if getattr(c, "type", "") == "text"]
    if _campo(resultado, "is_error", "isError"):
        raise RuntimeError(" ".join(textos))
    estructurado = _campo(resultado, "structured_content", "structuredContent")
    if estructurado:
        # Algunas versiones envuelven el valor devuelto en {"result": ...}
        if set(estructurado) == {"result"}:
            return estructurado["result"]
        return estructurado
    return json.loads(textos[0]) if textos else None


def titulo(texto):
    print("\n" + texto)
    print("-" * len(texto))


async def demo(proyecto, ia, consulta):
    params = StdioServerParameters(command=sys.executable, args=[SERVIDOR], cwd=AQUI,
                                   env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    with open(os.devnull, "w") as silencio:     # los logs del servidor (stderr) no ensucian
        async with stdio_client(params, errlog=silencio) as (leer, escribir):
            async with ClientSession(leer, escribir) as s:
                info = await s.initialize()
                srv = _campo(info, "server_info", "serverInfo")
                print("Conectado a MCP '%s' (protocolo %s)" % (
                    srv.name, _campo(info, "protocol_version", "protocolVersion")))

                titulo("Tools publicadas")
                for t in (await s.list_tools()).tools:
                    desc = (t.description or "").strip().splitlines()[0]
                    print("  %-26s %s" % (t.name, desc))
                titulo("Resources y prompts")
                for r in (await s.list_resources()).resources:
                    print("  resource  %s" % r.uri)
                plantillas = await s.list_resource_templates()
                for r in _campo(plantillas, "resource_templates", "resourceTemplates") or []:
                    print("  template  %s" % _campo(r, "uri_template", "uriTemplate"))
                for p in (await s.list_prompts()).prompts:
                    print("  prompt    %s" % p.name)

                titulo("listar_proyectos")
                for p in datos(await s.call_tool("listar_proyectos", {}))["proyectos"]:
                    print("  %-6s %s | rol %s | %s evidencias" % (
                        p["id"], p["nombre"], p["rol"], p["evidencias"]))

                titulo("estado_expediente('%s')" % proyecto)
                est = datos(await s.call_tool("estado_expediente", {"proyecto": proyecto}))
                print("  Evidencias registradas: %d" % len(est["evidencias"]))
                for ev in est["evidencias"][:10]:
                    print("    %s  %-12s %-45.45s %s" % (ev["id"], ev["tipo"], ev["titulo"],
                                                    ",".join(ev["controles"])))
                if len(est["evidencias"]) > 10:
                    print("    ... (%d mas)" % (len(est["evidencias"]) - 10))
                print("  Integridad (consulta): %s" % ("INTEGRO" if est["integridad"]["integro"]
                                                       else "PROBLEMAS"))

                titulo("verificar_integridad('%s')" % proyecto)
                v = datos(await s.call_tool("verificar_integridad", {"proyecto": proyecto}))
                r = v["resultados"]
                print("  Total %d | OK %d | ALTERADA %d | FALTANTE %d | cadena %s -> %s" % (
                    v["total"], len(r["OK"]), len(r["ALTERADA"]), len(r["FALTANTE"]),
                    "integra" if not v["problemas_cadena"] else v["problemas_cadena"],
                    "EXPEDIENTE INTEGRO" if v["integro"] else "ALERTA DE INTEGRIDAD"))

                titulo("matriz_cobertura('%s')" % proyecto)
                m = datos(await s.call_tool("matriz_cobertura", {"proyecto": proyecto}))
                print("  %s | rol %s | corte %s" % (m["norma"], m["rol"], m["fecha_corte"]))
                print("  Controles aplicables: %d | cobertura %.1f %%" % (
                    m["controles_aplicables"], m["porcentaje_cobertura"]))
                print("  " + " | ".join("%s: %s" % kv for kv in m["conteo_estados"].items()))
                for f in m["controles"]:
                    if f["estado"] != "Sin evidencia":
                        print("    %-9s %-14s %s" % (f["ref"], f["estado"],
                                                    ",".join(f["evidencias"])))

                titulo("resource norma://control/9.2 (extracto)")
                rr = await s.read_resource("norma://control/9.2")
                print("  " + rr.contents[0].text[:300].replace("\n", "\n  ") + " ...")

                titulo("Manejo de errores: matriz_cobertura('no-existe')")
                try:
                    datos(await s.call_tool("matriz_cobertura", {"proyecto": "no-existe"}))
                except RuntimeError as e:
                    print("  Error controlado: %s" % e)

                if ia:
                    titulo("buscar_evidencia (IA local): %r" % consulta)
                    try:
                        b = datos(await s.call_tool("buscar_evidencia",
                                                    {"consulta": consulta, "proyecto": proyecto,
                                                     "k": 4}))
                        for i, frag in enumerate(b["resultados"], 1):
                            origen = frag.get("cita") or frag.get("origen") or frag.get(
                                "fuente") or frag.get("titulo") or frag.get("tipo")
                            texto = (frag.get("texto") or "").replace("\n", " ")
                            print("  %d. [%s] %.140s..." % (i, origen, texto))
                    except RuntimeError as e:
                        print("  Error controlado: %s" % e)
    print("\nCada llamada quedo registrada en Entregable-2/datos/bitacora_mcp.jsonl")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--proyecto", default="unsa")
    ap.add_argument("--ia", action="store_true", help="incluir buscar_evidencia (Ollama)")
    ap.add_argument("--consulta", default="auditoria interna del sistema de gestion de privacidad")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    asyncio.run(demo(a.proyecto, a.ia, a.consulta))


if __name__ == "__main__":
    main()
