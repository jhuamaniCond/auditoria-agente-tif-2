# Diagramas — Entregable 2 (Grupo 6)

| Diagrama | Archivos | Contenido |
|---|---|---|
| Arquitectura | `arquitectura_entregable2.png` · `.svg` | Actores y 5 capas: interfaces (panel + CLI, servidor MCP), coordinación (orquestador LangGraph, bus de eventos, bandeja), herramientas (herramientas.py, skill y app del E1), IA local (qwen2.5:3b, embeddings + FAISS) y datos (PostgreSQL, disco, GESTITEL) |
| Flujo | `flujo_entregable2.png` · `.svg` | Disparadores → orquestador → grafos auditoría interna, incidente y bandeja, cada uno con su aprobación humana |

Versión simplificada para que se lea en Word: un título corto por caja y letra grande.
Los diagramas siguen el código actual (`Entregable-2/agente/orquestador.py`,
`servidor_mcp.py`, `herramientas.py`, `BD/schema.sql`), con PostgreSQL como
backend por defecto (`PIMS_BACKEND=archivos` como respaldo).

## Regenerar

```bash
python generar_diagramas.py      # escribe los .svg
# PNG a 2x con Chrome (o Edge) headless:
chrome --headless --hide-scrollbars --force-device-scale-factor=2 --window-size=1200,1010 --screenshot=arquitectura_entregable2.png arquitectura_entregable2.svg
chrome --headless --hide-scrollbars --force-device-scale-factor=2 --window-size=1200,1100 --screenshot=flujo_entregable2.png flujo_entregable2.svg
```
