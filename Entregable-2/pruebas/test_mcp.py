# -*- coding: utf-8 -*-
"""
Prueba automatica del servidor MCP "evidencias-pims" (sin IA, solo lectura).

Arranca Entregable-2/agente/servidor_mcp.py por stdio con el SDK oficial de MCP y
comprueba: tools publicadas (y que decidir_pertinencia NO lo esta), resources,
prompt, matriz_cobertura con 38 controles, error controlado sin traceback y que
la llamada quedo en la bitacora encadenada.

    python -m unittest Entregable-2/pruebas/test_mcp.py -v
"""

import asyncio
import json
import os
import sys
import unittest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PRUEBAS = os.path.dirname(os.path.abspath(__file__))
AGENTE = os.path.join(os.path.dirname(PRUEBAS), "agente")
SERVIDOR = os.path.join(AGENTE, "servidor_mcp.py")
BITACORA = os.path.join(os.path.dirname(PRUEBAS), "datos", "bitacora_mcp.jsonl")

TOOLS_ESPERADAS = {
    "registrar_evidencia", "verificar_integridad", "matriz_cobertura", "estado_expediente",
    "buscar_evidencia", "clasificar_evidencia", "evaluar_pertinencia", "redactar_hallazgo",
    "generar_informe_auditoria", "listar_proyectos", "preguntar_asistente",
}


def _campo(obj, *nombres):
    for n in nombres:
        if hasattr(obj, n):
            return getattr(obj, n)
    return None


def _json(resultado):
    estructurado = _campo(resultado, "structured_content", "structuredContent")
    if estructurado:
        return estructurado
    return json.loads(resultado.content[0].text)


async def _sesion_completa():
    """Una sola sesion stdio: recoge todo lo que verifican los tests."""
    params = StdioServerParameters(command=sys.executable, args=[SERVIDOR], cwd=AGENTE,
                                   env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    r = {}
    with open(os.devnull, "w") as silencio:
        async with stdio_client(params, errlog=silencio) as (leer, escribir):
            async with ClientSession(leer, escribir) as s:
                r["init"] = await s.initialize()
                r["tools"] = {t.name: t for t in (await s.list_tools()).tools}
                r["resources"] = [str(x.uri) for x in (await s.list_resources()).resources]
                plant = await s.list_resource_templates()
                r["plantillas"] = [_campo(x, "uri_template", "uriTemplate")
                                   for x in _campo(plant, "resource_templates",
                                                   "resourceTemplates")]
                r["prompts"] = [p.name for p in (await s.list_prompts()).prompts]
                r["matriz"] = await s.call_tool("matriz_cobertura", {"proyecto": "unsa"})
                r["error"] = await s.call_tool("estado_expediente", {"proyecto": "no-existe"})
                r["catalogo"] = await s.read_resource("pims://catalogo")
                r["norma"] = await s.read_resource("norma://control/A.1.2.2")
    return r


class TestServidorMCP(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.n_bitacora = cls._lineas_bitacora()
        cls.r = asyncio.run(asyncio.wait_for(_sesion_completa(), timeout=180))

    @staticmethod
    def _lineas_bitacora():
        if not os.path.exists(BITACORA):
            return 0
        with open(BITACORA, encoding="utf-8") as f:
            return sum(1 for l in f if l.strip())

    def test_nombre_servidor(self):
        self.assertEqual(_campo(self.r["init"], "server_info", "serverInfo").name,
                         "evidencias-pims")

    def test_tools_esperadas(self):
        self.assertTrue(TOOLS_ESPERADAS <= set(self.r["tools"]),
                        "faltan: %s" % (TOOLS_ESPERADAS - set(self.r["tools"])))

    def test_tools_documentadas(self):
        for nombre, t in self.r["tools"].items():
            self.assertTrue((t.description or "").strip(), "%s sin descripcion" % nombre)
            schema = _campo(t, "input_schema", "inputSchema")
            self.assertEqual(schema.get("type"), "object", nombre)

    def test_decidir_pertinencia_no_publicada(self):
        # Human-in-the-loop: aceptar/rechazar la propuesta de la IA es del auditor.
        self.assertNotIn("decidir_pertinencia", self.r["tools"])
        props = _campo(self.r["tools"]["generar_informe_auditoria"], "input_schema",
                       "inputSchema")["properties"]
        self.assertNotIn("aprobado_por", props)

    def test_resources_y_prompt(self):
        self.assertIn("pims://catalogo", self.r["resources"])
        self.assertIn("norma://control/{ref}", self.r["plantillas"])
        self.assertIn("auditoria_interna", self.r["prompts"])
        catalogo = json.loads(self.r["catalogo"].contents[0].text)
        self.assertGreaterEqual(catalogo["total"], 38)
        self.assertIn("A.1.2.2", self.r["norma"].contents[0].text)

    def test_matriz_cobertura_38_controles(self):
        res = self.r["matriz"]
        self.assertFalse(_campo(res, "is_error", "isError"))
        m = _json(res)
        self.assertEqual(len(m["controles"]), 38)
        self.assertEqual(m["controles_aplicables"], 38)
        self.assertEqual(sum(m["conteo_estados"].values()), 38)
        self.assertEqual(m["norma"], "ISO/IEC 27701:2025")

    def test_error_claro_sin_traceback(self):
        res = self.r["error"]
        self.assertTrue(_campo(res, "is_error", "isError"))
        texto = res.content[0].text
        self.assertIn("No existe el proyecto", texto)
        self.assertNotIn("Traceback", texto)

    def test_bitacora_registra_llamadas(self):
        self.assertGreaterEqual(self._lineas_bitacora(), self.n_bitacora + 2)
        with open(BITACORA, encoding="utf-8") as f:
            ultimas = [json.loads(l) for l in f if l.strip()][-2:]
        for e in ultimas:
            for campo in ("fecha", "tool", "argumentos", "resultado", "duracion_ms",
                          "hash_anterior", "hash"):
                self.assertIn(campo, e)
        self.assertEqual(ultimas[1]["hash_anterior"], ultimas[0]["hash"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
