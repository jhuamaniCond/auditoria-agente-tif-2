# TIF Auditoría de Sistemas — Entregable 2 — Grupo 6: Agente de Evidencia y Auditoría

Resultado: el **proyecto agéntico** del Agente de Evidencia y Auditoría (Agente 4
del PIMS multiagente basado en ISO/IEC 27701:2025, cláusulas 9.1, 9.2 y control
A.3.14), aplicado a un caso real: la **Universidad Nacional de San Agustín de
Arequipa (UNSA)**.

El agente convierte la skill `evidencia-auditoria-pims` y la aplicación
AUDITA-PIMS del Entregable 1 en:

- una **capa de herramientas** común (6 deterministas, 5 con IA local y una
  decisión solo humana);
- un **orquestador LangGraph** con tres flujos: `auditoria_interna`,
  `incidente` y `bandeja`, con puertas de aprobación humana (auditor y DPO);
- un **servidor MCP** (`evidencias-pims`) que expone el agente a otros agentes y hosts;
- un **bus de eventos** para coordinarse con el Agente de Incidentes y el resto del PIMS;
- **automatizaciones** (bandeja de entrada y verificación periódica de integridad);
- un **panel web** `/agente` con línea de tiempo en vivo, aprobación humana,
  informes y bitácoras.

El expediente de la UNSA se arma solo con **documentos públicos reales**
descargados de sitios oficiales (URLs en `datos/documentos_unsa/fuentes.json`).
No hay documentos inventados: lo que la universidad no publica queda *Sin
evidencia* y es un hallazgo real.

**Tecnologías:** Python · Flask · HTML · CSS · JavaScript puro · FAISS ·
`nomic-embed-text` · LLM local `qwen2.5:3b` (en lugar de `qwen2.5:7b`, por
rendimiento en una laptop i5-6200U sin GPU) servidos con Ollama · LangGraph ·
MCP (SDK oficial). Todo se ejecuta en la máquina del auditor.

| Tarea del TIF | Dónde está |
|---|---|
| Diseño de agente — objetivo, datos, contexto y herramientas | `01-diseno-agente/diseno_agente.md` |
| Orquestación y automatización — coordinación de skills, agentes y flujos | `02-orquestacion/orquestacion.md` |
| Proyecto agéntico — integración y aplicación de una solución funcional | `03-proyecto-agentico/proyecto_agentico.md` (incluye guía de demo) |
| Código del agente | `agente/` (ver tabla siguiente) |
| Casos de prueba y pruebas automáticas | `pruebas/casos_prueba.md`, `pruebas/` |
| Datos de la UNSA (documentos públicos, expediente, salidas, bitácoras) | `datos/` |
| Informe | `informe/Informe_Entregable_2.docx` (se regenera con `python informe/generar_informe.py`) |

| Archivo en `agente/` | Qué hace |
|---|---|
| `nucleo.py` | Importa la skill y la app del Entregable 1 sin copiarlas; crea el proyecto `unsa` |
| `herramientas.py` | Contrato común de herramientas (JSON de entrada y salida) |
| `servidor_mcp.py` | Servidor MCP `evidencias-pims` (SDK oficial; stdio, o `--http` en `http://127.0.0.1:8765/mcp`): 11 tools, resources y prompt `auditoria_interna` |
| `cliente_mcp_demo.py` | Cliente MCP de demostración |
| `mcp_config_ejemplo.json` | Configuración para registrar el servidor en un host MCP |
| `orquestador.py` | Grafos LangGraph `auditoria_interna`, `incidente`, `bandeja`; puertas HITL con `interrupt`; modo rápido sin LLM; estado en `datos/ejecuciones` |
| `coordinacion.py` | Bus de eventos entre agentes y simulador del Agente de Incidentes |
| `bandeja.py` | Vigilancia de `datos/bandeja_entrada` y verificación periódica de integridad |
| `servidor_web.py` + `web/` | App del Entregable 1 en `/` y panel del agente en `/agente` |
| `cli_agente.py` | Los mismos flujos desde la terminal |

Trazabilidad: `datos/bitacora_mcp.jsonl` (llamadas MCP),
`datos/bitacora_decisiones.jsonl` (decisiones humanas), `datos/eventos.jsonl`
(eventos entre agentes) y la cadena de custodia del expediente.

## Puesta en marcha

```bash
# Modelos locales (una vez)
ollama pull nomic-embed-text
ollama pull qwen2.5:3b

# Dependencias (desde la raíz del repositorio)
pip install -r Entregable-2/requirements.txt

# Panel del agente
cd Entregable-2/agente
python servidor_web.py            # http://127.0.0.1:5000/agente

# En otra terminal (también en Entregable-2/agente)
python cliente_mcp_demo.py        # tools, resources y prompt del servidor MCP
python cli_agente.py auditoria --rapido   # auditoría interna sin LLM hasta la puerta humana
```

Otros comandos de la CLI: `python cli_agente.py incidente "descripción" --rapido`,
`bandeja [--auto]`, `listar`, `estado ID`, `aprobar ID --auditor "Nombre" [--rechazar]`
y `grafo auditoria_interna` (dibuja el grafo).

## Pruebas

```bash
cd Entregable-2/agente
python -m unittest discover -s ../pruebas
```

Los casos funcionales (MCP, orquestador, HITL, integridad alterada, incidente,
bandeja, PII y rechazo) están en `pruebas/casos_prueba.md`.

## Regenerar el informe

```bash
pip install python-docx
python Entregable-2/informe/generar_informe.py
```

El informe reutiliza el motor de estilo del Entregable 1
(`Entregable-1/informe/docx_builder.py`) y lee en tiempo de ejecución
`datos/documentos_unsa/fuentes.json` y la matriz de cobertura del proyecto `unsa`.
