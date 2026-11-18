# TIF Auditoría de Sistemas · Entregable 3 · Grupo 6: Agente de Evidencia y Auditoría

Respuesta a los mensajes del docente:

- **Mensaje 2:** las plantillas ISO/IEC 27001:2013 se **corrigieron y alinearon a ISO/IEC
  27701:2025**, se **llenaron con IA para una implementación simulada del PIMS en la UNSA**, se
  **subieron a la base de datos de documentos** (PostgreSQL) y el **agente trabaja sobre ellas**:
  las usa como criterio de la auditoría interna, verifica su control documental y emite los
  registros que piden.
- **Mensaje 3:** el **listado de la información documentada** que soporta el PIMS ISO/IEC
  27701:2025, con las **cláusulas y controles** que exige cada documento, es la lista maestra
  **PIMS-RG-01** (documento y tabla `lista_maestra_pims`). Los **26 documentos** de la lista
  existen, están aprobados y cargados en la BD: 9 del Grupo 6 y 17 de los otros equipos del PIMS,
  que elaboramos con IA en coordinación con ellos para que no quede ninguno pendiente.

> Documentos académicos: cargos y unidades salen de resoluciones públicas de la UNSA
> (`docs-unsa/`); las aprobaciones y firmas son simuladas y así lo dice cada documento.

## 1. Documentos PIMS

Plantillas originales del docente en `documentos-pims/plantillas-originales/` (Mensaje 2: control
de documentos, medidas correctivas y su formulario, metodología de riesgos, apéndices 1 a 3, plan
de tratamiento y plan de capacitación). Resultado en `documentos-pims/generados/` (Grupo 6),
`documentos-pims/otros-grupos/` (demás equipos; cuadros de riesgos `.xlsx` en `anexos/`) y
`documentos-pims/pdf/`.

### 1.1 Lista maestra PIMS-RG-01 (Mensaje 3)

| Código | Documento | Cláusulas y controles | Exp. guía | Elabora |
|---|---|---|---|---|
| PIMS-MA-01 | Manual del PIMS: contexto (FODA/PESTEL con cambio climático), partes interesadas, alcance, procesos, RACI, recursos, comunicación | 4.1–4.4, 5.1, 5.3, 7.1, 7.4, A.3.4, A.3.13 | D01–D03, D07, D09, D37 | Alta dirección – CGTD |
| PIMS-POL-01 | Política de privacidad del PIMS | 5.1, 5.2, A.3.3 | D08 | Agente 3 |
| PIMS-PL-03 | Objetivos de privacidad y planificación de cambios | 6.2, 6.3 | D10 | Alta dirección – CGTD |
| PIMS-RG-02 | Inventario de actividades de tratamiento (RoPA) | 4.3, A.1.2.2, A.1.2.3, A.1.2.9, A.1.5.4 | D04, D05, D17 | Agente 1 |
| PIMS-PR-09 | Minimización, calidad, conservación y eliminación | 8.1, A.1.4.2–A.1.4.10 | D22 | Agente 1 |
| PIMS-MT-01 | Metodología de riesgos de privacidad (plantilla del docente) | 6.1.1–6.1.3, 8.2 | D12 | Agente 2 |
| PIMS-IN-01 | Informe de riesgos y DPIA (plantilla Apéndice 3 + cuadros .xlsx) | 6.1.2, 8.2, 8.3, A.1.2.6 | D13, D21 | Agente 2 |
| PIMS-RG-03 | Declaración de aplicabilidad (A.1 y A.3; A.2 excluido) | 6.1.3 | D14 | Agente 3 |
| PIMS-PL-01 | Plan de tratamiento de riesgos y control operacional (plantilla del docente) | 6.1.3, 6.3, 8.1, 8.3 | D15, D16, D31 | Agente 3 |
| PIMS-PR-08 | Seguridad de la información para datos personales | A.3.3, A.3.5–A.3.9, A.3.18–A.3.31 | D16, D26, D27, D29 | Agente 3 |
| PIMS-PR-01 v1.2 | Control de la información documentada y de los registros | 7.5, A.3.14 | D11, D29 | Grupo 6 |
| PIMS-RG-01 v1.1 | Lista maestra de información documentada | 7.5 | D11 | Grupo 6 |
| PIMS-RG-05 | Registro de documentos de origen externo (con SHA-256) | 7.5, A.3.13 | D02, D11 | Grupo 6 |
| PIMS-PR-02 v1.1 | No conformidades y acciones correctivas | 10.1, 10.2 | D34 | Grupo 6 |
| PIMS-FO-01 v1.3 | Formulario de no conformidades y acciones correctivas | 10.2 | D34 | Grupo 6 |
| PIMS-PR-03 v1.1 | Procedimiento y programa de auditoría interna | 9.2, A.3.15, A.3.16 | D33 | Grupo 6 |
| PIMS-PR-04 v1.1 | Seguimiento, medición, análisis y evaluación (11 indicadores) | 9.1 | D32 | Grupo 6 |
| PIMS-IN-02 | Informe de auditoría interna AUD-2026-002 | 9.2, 10.2 | D06, D33 | Grupo 6 |
| PIMS-IN-03 | Informe trimestral de desempeño (IV-2026) | 9.1 | D32 | Grupo 6 |
| PIMS-PR-05 | Atención de derechos de los titulares (ARCO, decisiones automatizadas) | 8.1, A.1.3.2, A.1.3.7–A.1.3.11 | D20 | Agente 5 |
| PIMS-PR-07 | Avisos de privacidad y consentimiento | A.1.2.2, A.1.2.4, A.1.2.5, A.1.3.3–A.1.3.6 | D18, D19 | Agente 5 |
| PIMS-PR-06 | Incidentes y brechas de datos personales | A.3.11, A.3.12 | D28 | Agente 6 |
| PIMS-RG-04 | Encargados, contratos, transferencias y divulgaciones | A.1.2.7, A.1.2.8, A.1.5.2–A.1.5.5, A.3.10 | D23–D25 | Agente 7 |
| PIMS-PL-02 | Plan de capacitación y concienciación (plantilla del docente) | 7.2, 7.3, A.3.17 | D30 | Agente 8 |
| PIMS-RG-06 | Competencias, formación y acuerdos de confidencialidad | 7.2, A.3.17, A.3.18 | D30 | Agente 8 |
| PIMS-AC-01 | Acta de revisión por la dirección 1-2026 | 9.3, 10.1 | D35 | Alta dirección – CGTD |

Toda cláusula 4–10 y todo control A.1 y A.3 tiene al menos un documento. Los expedientes
D01–D37 de la guía también, salvo **D36** (certificación externa, marcado «X»: solo si se decide
solicitarla; el acta AC-01 lo deja para después de AUD-2027-001). La UNSA actúa como responsable
del tratamiento, por eso A.2 (encargado) se excluye en la SoA con su justificación.

**Documentos de los otros equipos.** Los elaboró el Grupo 6 con IA para completar la simulación,
y cada uno lo declara en la portada («Documento elaborado con apoyo de IA por el Grupo 6 en
coordinación con el equipo …») y en el historial. Si un equipo entrega su propia versión, se deja
en `otros-grupos/` con la versión siguiente (o se sube desde la web) y el control de cambios deja
obsoleta la nuestra.

**Datos.** Son reales los bancos de datos y sus finalidades (Política de Privacidad de la UNSA),
las unidades (ROF), los cargos designados por resolución y el canal ARCO `odp@unsa.edu.pe`. Son
simulados los volúmenes, las valoraciones de riesgo, los contratos, las solicitudes, las
capacitaciones y las aprobaciones. Todo está en `scripts/datos_pims_unsa.py`, para que los
documentos no se contradigan. Ningún registro contiene datos personales reales.

Qué se corrigió respecto de las plantillas 27001:2013: SGSI/SGCN → PIMS; ISO 27001/22301/BS 25999
→ ISO/IEC 27701:2025 (cláusulas y controles A.1/A.3); se agregaron la Ley N.° 29733 y su
reglamento (D.S. 016-2024-JUS), la Ley 27806 y las directivas de la UNSA; se quitaron la
licencia, el autor y los campos `[...]` de la plantilla (también en encabezados y pies); se
añadieron la protección de registros de tratamiento de datos personales (A.3.14), la evaluación
de impacto (DPIA) en la metodología de riesgos y la integración con el agente.

## 2. Base de datos

`BD/migracion_documentos_pims.sql` (también al final de `BD/schema.sql`) crea `documentos_pims`
y la vista `v_documentos_pims`. Cada documento queda en:

- `documentos` + `documento_paginas`: archivo, SHA-256 y texto por sección (lo lee el RAG);
- `documentos_pims`: código, versión, aprobador, confidencialidad, propietario, validez,
  historial, requisitos, equipo autor, estado y resultado del control documental;
- `evidencias` + `cadena_custodia`: como evidencia del expediente, para que cuente en la
  cobertura. Al registrar una versión aprobada nueva, la anterior pasa a `obsoleto`;
- `lista_maestra_pims` (nueva): la lista maestra PIMS-RG-01 (código, requisitos, expedientes de
  la guía, marca E/C/S, equipo, propietario, confidencialidad). La fuente es
  `agente/lista_maestra_pims.py` y `cargar_documentos_pims.py` la sincroniza.

## 3. Cómo trabaja el agente con los documentos PIMS

Flujo `auditoria_interna` (LangGraph), con dos pasos nuevos:

1. **planificar**: toma como criterio el programa vigente PIMS-PR-03 (y avisa si no existe).
2. verificar integridad → matriz de cobertura.
3. **control_documental** (nuevo): aplica las reglas de PR-01 a cada documento PIMS de la BD:
   código, versión aprobada, aprobador, fecha, confidencialidad, historial al día, validez,
   propietario, sin campos `[...]` y sin restos de la plantilla 27001. Lee la lista maestra de la
   BD y la compara con lo registrado: si un documento falla o **falta alguno de los 26**, propone
   un hallazgo sobre la cláusula 7.5 que nombra el documento y el equipo que debe entregarlo.
4. pertinencia → priorizar → redactar → **aprobación del auditor** (decisión humana).
5. informe (con la sección de control documental) → **plan de acción + PIMS-FO-01** (nuevo):
   genera el formulario de PR-02 prellenado con cada no conformidad aprobada y lo registra
   como evidencia de 10.2. Plazos de PR-02 = plazos del plan de acción del agente.

Estado de la BD (18-11-2026):

| Auditoría | Qué fue | Resultado |
|---|---|---|
| AUD-2026-001 | Diagnóstica (27-10-2026), antes de los documentos PIMS | Cobertura 7.9 %, 35 no conformidades |
| AUD-2026-002 | Seguimiento de la información documentada (17-11-2026), con solo los 5 documentos del Grupo 6 | Cobertura **21.1 %** (8 cubiertos y 1 parcial de 38), 5 documentos conformes, 30 hallazgos y PIMS-FO-01 con 30 registros |
| AUD-2026-003 | Seguimiento con los 26 documentos de la lista maestra (18-11-2026, ejecución `AUD-20261118-162603-ejv0`) | Control documental: **26 conformes, 0 sin registrar**; matriz: 38 de 38 controles con evidencia documental vigente; 44 evidencias íntegras; 0 hallazgos. Aprobada por el auditor líder (simulado) y cerrada: `datos/salidas/informe_auditoria_unsa_20261118_164947.md` |

La cobertura de AUD-2026-003 es **documental**: muestra que cada requisito tiene su documento
aprobado, no que los controles ya funcionen. La eficacia (registros de operación) se verifica en
AUD-2027-001, como dicen el acta PIMS-AC-01 y el informe PIMS-IN-03.

El formulario lleno está en `documentos-pims/registros/PIMS-FO-01_AUD-2026-002_no_conformidades`
(.docx y .pdf). El de `documentos-pims/generados/` es el formulario **en blanco** aprobado.

El control documental detectó fallas reales en nuestras propias primeras versiones (FO-01 sin
historial ni validez; pies de página con la licencia de la plantilla). Se corrigieron subiendo
de versión, y eso consta en el historial de modificaciones de cada documento. El 18-11-2026 se
aplicó lo mismo: PR-01 1.1 → 1.2 (la lista maestra pasa a RG-01), FO-01 1.2 → 1.3 (un cambio de
formato que estaba en el código y nunca se había registrado) y RG-01 1.0 → 1.1. Las versiones
anteriores quedaron como obsoletas en la BD.

**Reinicio del expediente (17-11-2026).** Durante las pruebas se registraron por error varias
copias de la misma versión de los documentos PIMS. Con `scripts/reiniciar_expediente.py` (antes:
respaldo completo `BD/respaldos/antes_reinicio_expediente_20261117.dump`) se vació el expediente y
se reconstruyó: 14 evidencias de `docs-unsa/` + una sola versión vigente de cada documento PIMS.
Se conservaron los 51 documentos de la UNSA ya leídos con OCR y la auditoría AUD-2026-001. El
reinicio quedó en la bitácora de decisiones.

**Tildes.** El catálogo de controles de la skill del Entregable 1 y los textos deterministas del
agente venían sin tildes. `agente/tildes.py` las corrige al cargar (sin tocar el Entregable 1) y
`scripts/corregir_tildes_catalogo.py` las corrigió en las tablas `requisitos` y `expedientes`.

## 4. Interfaz nueva

`agente/web/` se rehízo con la skill *frontend-design*: identidad de expediente de auditoría
(papel frío, tinta, guinda UNSA solo para sellos y decisiones), Archivo + IBM Plex Mono, y
navegación por flujo de trabajo (Auditar, Evidencia, Trazabilidad, Sistema). Novedades:

- **Panel**: sello de cobertura con un segmento por control aplicable (se puede pulsar),
  dictamen en lenguaje claro, cadena de custodia, resumen de la lista maestra y estado de los
  documentos PIMS del grupo.
- **Documentos PIMS** (nuevo): la lista maestra completa (26 documentos, con el equipo que
  elabora cada uno y su expediente de la guía), ficha de cada uno
  (portada leída, reglas de PR-01, historial, texto guardado en la BD, descarga) y subida con
  vista previa del control.
- **Auditorías**: pasos numerados, bloque de decisión del auditor, descarga del PIMS-FO-01 y del
  Excel de GESTITEL.
- **Grafo de conocimiento**: el mismo grafo del Entregable 1 (`Entregable-1/04-aplicacion/grafo.py`:
  fuentes del RAG, grupos, controles, remisiones de la norma, semejanza FAISS y evidencias)
  ampliado con los documentos PIMS de la lista maestra, enlazados a los controles que documentan y
  a su evidencia (`/api/agente/grafo`).
- La web trata el tema del Grupo 6 (evidencia y auditoría). De los otros equipos solo muestra sus
  documentos en la lista maestra, porque su control documental es parte de nuestro tema; no
  muestra sus flujos (el flujo de incidentes del Entregable 2 queda solo en el backend/MCP).
- Botón de modo claro/oscuro en la barra superior; la preferencia se guarda en el navegador
  (sin preferencia, sigue al sistema). Adaptable a móvil y con foco visible.
- La web arranca en segundos: los índices de búsqueda se preparan en segundo plano.
- **Chat con la IA local**: botón flotante «Preguntar a la IA» (o `Ctrl + /`) que abre un panel
  acoplado a la derecha. Usa el asistente AUDITA-PIMS del Entregable 1 (RAG con la norma, el
  conocimiento y el expediente) más un resumen del proyecto que arma `agente/chat_proyecto.py`:
  documentos PIMS, última auditoría y su plan de acción. La respuesta llega a medida que Ollama
  la genera (`POST /api/agente/chat`, NDJSON), se puede detener, muestra las fuentes consultadas
  y la conversación se recuerda en el navegador. Con `qwen2.5:7b` en CPU tarda alrededor de un
  minuto por respuesta.
- Movimiento: el sello de cobertura se estampa al cargar, la cadena de custodia se escanea al
  verificar, cae un sello al aprobar una auditoría y el tema cambia con un revelado circular.
  Todo se desactiva si el sistema pide reducir el movimiento.

## 5. Puesta en marcha

```bash
cd BD && docker compose up -d                      # PostgreSQL + pgAdmin
docker exec -i pims_g6_postgres psql -U agente -d pims_auditoria < migracion_documentos_pims.sql
python cargar_documentos.py                         # 51 documentos públicos de la UNSA (OCR)
cd ../Entregable-3
python scripts/generar_documentos_pims.py           # documentos del Grupo 6 (salida determinista)
python scripts/generar_documentos_otros_grupos.py   # documentos de los otros equipos + cuadros .xlsx
powershell -ExecutionPolicy Bypass -File scripts/exportar_pdf.ps1   # PDF con Word (Grupo 6)
powershell -ExecutionPolicy Bypass -File scripts/exportar_pdf.ps1 -Carpeta documentos-pims/otros-grupos
python scripts/cargar_documentos_pims.py            # lista maestra + documentos a la BD (idempotente)
cd agente && python servidor_web.py                 # http://127.0.0.1:5000/agente
python cli_agente.py auditoria --rapido             # o desde la terminal
```

Regenerar un documento solo tiene sentido si cambia su contenido: entonces hay que subir su
versión en el script (PR-01, control de cambios); un archivo idéntico no se vuelve a registrar.

## 6. Archivos

| Ruta | Qué es |
|---|---|
| `agente/lista_maestra_pims.py` | Lista maestra PIMS-RG-01 (Mensaje 3): documentos, cláusulas y controles, expedientes y equipos |
| `agente/plantillas_pims.py` | Corrige las plantillas del docente, lee la portada de un .docx PIMS y genera PIMS-FO-01 |
| `agente/documentos_pims.py` | Registro en BD, lista maestra, reglas de PR-01 y paso de control documental |
| `agente/orquestador.py` | Pasos `control_documental` y FO-01 dentro de `auditoria_interna` |
| `agente/servidor_web.py` | API `/api/agente/documentos-pims…`, `/salidas/…`, `/custodia` |
| `agente/web/` | Interfaz nueva |
| `agente/tildes.py` | Corrige tildes del catálogo heredado y de los textos del agente |
| `scripts/generar_documentos_pims.py`, `exportar_pdf.ps1`, `cargar_documentos_pims.py` | Generar documentos del Grupo 6, exportar PDF y cargar a la BD |
| `scripts/generar_documentos_otros_grupos.py` (+ `docs_direccion.py`, `docs_riesgos_controles.py`, `docs_titulares_terceros.py`, `comun_otros_grupos.py`) | Documentos de los otros equipos del PIMS |
| `scripts/datos_pims_unsa.py` | Datos comunes de la simulación (tratamientos, encargados, riesgos, plan, indicadores) |
| `scripts/reiniciar_expediente.py` | Reinicio limpio del expediente (conserva documentos UNSA y AUD-2026-001) |
| `scripts/corregir_tildes_catalogo.py` | Tildes en `requisitos` y `expedientes` (correr tras `cargar_catalogo.py`) |
| `documentos-pims/registros/` | Registros llenos emitidos por el agente (PIMS-FO-01 de AUD-2026-002) |
| `pruebas/` | 26 pruebas (`python -m unittest discover -s ../pruebas` desde `agente/`) y casos CP-01 a CP-17 |
| `datos/` | Copia de trabajo del expediente (Entregable 2 queda intacto) |

Notas: la base de datos es la misma que usa el Entregable 2, pero los archivos del expediente
de este entregable viven en `Entregable-3/datos`. Los archivos de 12 evidencias del Entregable 2
tenían otro nombre en disco que el registrado en la BD; aquí se repusieron comprobando su SHA-256
contra los originales de `docs-unsa/`, y el expediente quedó íntegro.
