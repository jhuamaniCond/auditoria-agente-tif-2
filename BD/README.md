# BD — Base de datos PostgreSQL del Agente de Evidencia y Auditoría (Grupo 6)

El agente del Entregable 2 ya no trabaja con archivos JSON / JSONL / LOG: todo lo
guarda en **PostgreSQL 16**, como pidió el delegado. Se ve en el navegador con
**pgAdmin** (http://localhost:5050). El modelo sigue la plataforma del profesor,
**GESTITEL** (https://unsa.27k.pe):

| En GESTITEL | En esta BD |
|---|---|
| Análisis de brecha · SOA (142 controles: 93 de 27001:2022 + 49 de 27701:2025 A.1–A.2) | `requisitos` (+ 29 controles A.3 con `cubierto_por` y 25 cláusulas) y `soa_evaluaciones` |
| Análisis de brecha · Cláusulas 4–10 (69 requisitos: `4.2.a`, `6.1.3.c`, `9.2.1`…) | `requisitos_brecha` (cada uno apunta a su cláusula en `requisitos`) |
| Estados de una letra (`I`, `C`, `N`, `O`…) | `gestitel_codigos` (los no confirmados quedan en NULL) |
| Auditorías → General / Checklist / Hallazgos / Seguimiento | `auditorias`, `checklist_items`, `hallazgos`, `acciones`, vista `v_auditoria_avance` |
| "Exportar / Importar Excel" de Auditorías | vista `v_export_auditorias_gestitel` + `exportar_gestitel.py` (mismo formato) |
| Evidencia (solo texto) | `evidencias` con SHA-256, `evidencia_requisito`, `hallazgo_evidencia`, `cadena_custodia` |

## Puesta en marcha

```bash
cd BD
docker compose up -d                 # PostgreSQL (5432) + pgAdmin (5050); aplica schema.sql
pip install -r requirements.txt
python cargar_catalogo.py            # catálogo verificado contra la norma
python migrar_datos_agente.py        # pasa los datos del agente (Entregable-2/datos) a la BD
```

Después el agente (`Entregable-2/agente`) usa PostgreSQL por defecto. Para volver
al modo anterior con archivos: `PIMS_BACKEND=archivos`.

- **pgAdmin**: http://localhost:5050, sin login. El servidor *PIMS G6 - pims_auditoria*
  ya está registrado: *Servers → PIMS G6 → Databases → pims_auditoria → Schemas →
  public → Tables* (clic derecho → *View/Edit Data*).
- **Conexión directa**: `localhost:5432`, base `pims_auditoria`, usuario `agente`,
  clave `agente_local` (solo desarrollo local). Variables `PIMS_DB_*` o `PIMS_DATABASE_URL`.
- **Empezar de cero**: `docker compose down -v && docker compose up -d` y volver a cargar.
  Es necesario si la BD se creó antes de que existieran `requisitos_brecha` y `gestitel_codigos`
  (`schema.sql` solo se aplica al crear el volumen).
- Sin Docker: instalar PostgreSQL 16, `psql -f schema.sql` y definir `PIMS_DB_*`.

## Archivos

| Archivo | Qué es |
|---|---|
| `docker-compose.yml` | PostgreSQL 16.4 + pgAdmin 4 (9.19) |
| `pgadmin/` | Servidor pre-registrado y credencial para pgAdmin |
| `schema.sql` | Tablas, restricciones, triggers de solo inserción y vistas |
| `db.py` | Conexión |
| `almacen_pg.py` | Capa de datos del agente: todo lo que antes iba a JSON/JSONL |
| `cargar_catalogo.py` | Expedientes, requisitos y relaciones, verificados contra la norma (idempotente) |
| `migrar_datos_agente.py` | Migra `Entregable-2/datos` a la BD y comprueba las cadenas de hash (idempotente) |
| `exportar_gestitel.py` | Excel de Auditorías con el formato de GESTITEL |
| `datos/soa_gestitel.xlsx` | Export de la SOA de GESTITEL (142 controles, Ley 29733) |
| `datos/expedientes_guia.json` | D01–D37 y relación requisito → expediente (guía del delegado) |
| `datos/programa_seguridad_6_1_3c.json` | Tema de 6.1.3 c) de cada control 27001 sin equivalente A.3 |
| `datos/formato_auditorias_gestitel.xlsx` | Export original del módulo Auditorías (referencia) |
| `datos/ejemplo_import_auditorias_unsa.xlsx` | Excel generado con la auditoría de la UNSA (35 hallazgos) |

## Relación requisito → expediente (256 relaciones, columna `fuente`)

| fuente | n | De dónde sale |
|---|---|---|
| `guia` | 151 | Tablas de la guía del delegado (cláusulas, A.1, A.2, A.3) |
| `equivalencia` | 41 | Control 27001 que cubre un A.3 hereda sus expedientes (p. ej. A.5.33 ← A.3.14 → D11, D29) |
| `norma` | 64 | Controles 27001 sin A.3: van al **programa de seguridad de 6.1.3 c)**, que en la guía es **D16** |

`cargar_catalogo.py` comprueba contra `Entregable-1/ISOS/texto/ISO 27701-2025.md`:

- que las 103 referencias de la guía y la skill existen como sección de la norma;
- que los 15 temas mínimos del programa de seguridad (6.1.3 c) aparecen literalmente;
- que cada uno de los 64 controles tiene un tema asignado (`requisitos.tema_programa`).

La asignación a D16 la fija la norma; el tema concreto de cada control es una
clasificación del grupo (según los dominios de ISO/IEC 27002), documentada en
`programa_seguridad_6_1_3c.json`.

## Qué guarda el agente en cada tabla

| Antes (archivo) | Ahora (tabla) |
|---|---|
| `proyecto.json`, `soa.csv` | `proyectos`, `soa_evaluaciones` |
| `registro_evidencias.json` | `evidencias`, `evidencia_requisito` (el PDF/TXT sigue en disco) |
| `cadena_custodia.log` | `cadena_custodia` (solo inserción; `contenido` = línea hasheada) |
| `revisiones_pertinencia.json` | `revisiones_pertinencia` |
| `ejecuciones/*.json`, `_estado/*.json` | `ejecuciones`, `ejecucion_instantaneas` |
| `checkpoints.sqlite` (SqliteSaver) | `checkpoints*` (PostgresSaver de LangGraph) |
| `bitacora_decisiones.jsonl` | `decisiones_humanas` |
| `eventos.jsonl` | `eventos_agentes` |
| `bitacora_mcp.jsonl` (+ `.lock`) | `bitacora_mcp` (solo inserción; bloqueo de BD) |
| — | `auditorias`, `checklist_items`, `hallazgos`, `acciones`: se llenan solas al completarse una auditoría |

## Excel para GESTITEL

```bash
python exportar_gestitel.py                          # todas las auditorías de unsa
python exportar_gestitel.py --auditoria AUD-2026-001 --salida mi.xlsx   # o el id de la ejecución
```

También como herramienta del agente: `herramientas.exportar_gestitel(proyecto, auditoria)`.
Genera la hoja "Auditorías" con la misma cabecera y las mismas 25 columnas que el
"Exportar Excel" de GESTITEL, lista para "Importar Excel". Respeta los límites de su BD
(`gestitel_base_de_datos.sql`):

- **Código de auditoría** `AUD-AAAA-NNN` (`audit_code` admite 20 caracteres); el id de la
  ejecución del agente queda en `auditorias.ejecucion_agente`.
- **Requisito de origen** = código de `requisitos_brecha` (`source_requirement_code`, 10
  caracteres): el mismo código de la cláusula, o el único en que se desglosa; si se desglosa
  en varios (p. ej. 9.2 → 9.2.1/9.2.2/9.2.3) queda vacío.
- **Tipo, Estado, Clasificación, Estado (acción)** con el código de una letra de
  `gestitel_codigos`. Confirmados por su export real: `I` Interna, `C` Cerrada,
  `N` No conformidad, `O` Abierta. El resto (Observación, Oportunidad de mejora, En curso,
  En progreso…) está pendiente de confirmar con el ingeniero: sale como texto y el script
  avisa. Al confirmarlos: `UPDATE gestitel_codigos SET codigo = 'X' WHERE dominio = '…' AND valor = '…';`

## Consultas útiles

```sql
SELECT requisito, nombre, evidencias_vigentes, estado_cobertura, expedientes
FROM v_cobertura WHERE proyecto = 'unsa' ORDER BY requisito;      -- cobertura

SELECT codigo, nombre, tema_programa FROM requisitos WHERE tema_programa IS NOT NULL;

SELECT * FROM v_auditoria_avance;                                   -- seguimiento
SELECT * FROM v_export_auditorias_gestitel;                         -- filas del Excel
```

## Pruebas

```bash
python -m unittest Entregable-2/pruebas/test_orquestador.py Entregable-2/pruebas/test_mcp.py
PIMS_BACKEND=archivos python -m unittest Entregable-2/pruebas/test_orquestador.py Entregable-2/pruebas/test_mcp.py
```

Con PostgreSQL: 15 pruebas (incluida `test_7`: auditoría volcada a las tablas de
GESTITEL, custodia íntegra y Excel con el formato correcto). Con archivos: 14 + 1 omitida.
