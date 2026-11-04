# Diagramas — Entregable 2 (Grupo 6)

| Diagrama | Archivos | Contenido |
|---|---|---|
| Arquitectura | `arquitectura_entregable2.png` · `.svg` | Actores y 5 capas: presentación y gobernanza (panel Flask, CLI, orquestador LangGraph), comunicación (servidor MCP `evidencias-pims`, bus de eventos, `bandeja.py`), herramientas (herramientas.py, skill y app del E1), IA local (Ollama `qwen2.5:3b`, `nomic-embed-text`, FAISS) y persistencia (PostgreSQL `pims_auditoria`, pgAdmin, disco, export a GESTITEL) |
| Flujo | `flujo_entregable2.png` · `.svg` | Disparadores → orquestador → grafos `auditoria_interna`, `incidente` y `bandeja` con sus puertas HITL (auditor, DPO, bandeja) → salidas y persistencia común |

Los diagramas siguen el código actual (`Entregable-2/agente/orquestador.py`,
`servidor_mcp.py`, `herramientas.py`, `BD/schema.sql`), con PostgreSQL como
backend por defecto (`PIMS_BACKEND=archivos` como respaldo).

## Regenerar

```bash
python generar_diagramas.py      # escribe los .svg
# PNG a 2x con Chrome (o Edge) headless:
chrome --headless --hide-scrollbars --force-device-scale-factor=2 --window-size=1700,1360 --screenshot=arquitectura_entregable2.png arquitectura_entregable2.svg
chrome --headless --hide-scrollbars --force-device-scale-factor=2 --window-size=1700,1612 --screenshot=flujo_entregable2.png flujo_entregable2.svg
```
