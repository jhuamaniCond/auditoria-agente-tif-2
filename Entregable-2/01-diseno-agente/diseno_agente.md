# Diseño del agente — Agente de Evidencia y Auditoría (Grupo 6)

Ficha de diseño del agente que el Entregable 2 construye a partir de la skill
`evidencia-auditoria-pims` y del asistente AUDITA-PIMS del Entregable 1. Cubre
la tarea del TIF *Diseño de agente: definición de objetivo, datos, contexto y
herramientas*.

| Campo | Valor |
|---|---|
| Nombre | Agente de Evidencia y Auditoría (Agente 4 del PIMS multiagente) |
| Organización auditada (caso real) | Universidad Nacional de San Agustín de Arequipa (UNSA), proyecto `unsa` |
| Rol de la UNSA frente a la PII | Responsable del tratamiento (controles A.1 del Anexo A) |
| Norma de referencia | ISO/IEC 27701:2025 — cláusulas 9.1, 9.2 y control A.3.14 |
| Marco legal | Ley N.º 29733 y su reglamento, D.S. N.º 016-2024-JUS |
| Usuarios | Auditor interno (decide), Oficial de Datos Personales / DPO (aprueba incidentes) |
| Ejecución | Local: Python, Ollama (`qwen2.5:3b`, `nomic-embed-text`), FAISS |
| Código | `Entregable-2/agente/` |

---

## 1. Objetivo

**Objetivo general.** Mantener el expediente de evidencias del PIMS de la UNSA
íntegro y trazable, y preparar la auditoría interna (cláusula 9.2) de forma
repetible, de modo que cada afirmación de cumplimiento esté respaldada por una
evidencia registrada con hash y toda conclusión pase por una persona antes de
emitirse.

**Objetivo SMART.**

| Criterio | Definición |
|---|---|
| **S**pecific | Para el proyecto `unsa`, ejecutar el flujo `auditoria_interna`: verificar la integridad de todas las evidencias, calcular la matriz de cobertura de los 38 controles aplicables al rol responsable, proponer pertinencia y hallazgos preliminares, y emitir el informe y el plan de acción solo tras la aprobación del auditor. |
| **M**easurable | 100 % de evidencias con SHA-256 verificado; 100 % de controles no cubiertos con hallazgo; 0 controles marcados como cubiertos sin evidencia; 100 % de decisiones humanas y de llamadas a herramientas en bitácora. |
| **A**chievable | Reutiliza el motor determinista de la skill (`evidencia.py`) y el RAG del Entregable 1; el LLM local solo interviene en clasificación, pertinencia y redacción. |
| **R**elevant | Responde a 9.1 (seguimiento y medición), 9.2 (auditoría interna) y A.3.14 (protección de registros), y es la fuente de evidencias del resto de agentes del PIMS. |
| **T**ime-bound | Una auditoría completa en modo rápido (sin LLM) en menos de 2 minutos en la laptop del equipo (i5-6200U, sin GPU); con IA local, dentro de la sesión de trabajo del auditor. Entrega funcional al cierre del semestre 2026-II. |

## 2. Alcance y rol en el PIMS multiagente

El PIMS de la guía del curso tiene ocho agentes especializados coordinados por
un orquestador, un bus MCP y un panel de aprobación humana. Este agente es el
**Agente 4**: recibe evidencias de los demás y prepara la auditoría.

```mermaid
flowchart TB
    subgraph GOB["Capa de gobernanza"]
        ORQ["Orquestador LangGraph"]
        REG["Registro de decisiones<br/>(bitácoras JSONL)"]
        HITL["Panel de aprobación humana<br/>/agente"]
    end
    BUS(["Bus MCP + bus de eventos"])
    subgraph AG["Capa de agentes especializados"]
        A1["1. Inventario de Datos<br/>A.1.2.2 · A.1.2.9"]
        A2["2. Evaluación de Riesgos<br/>A.1.2.6 · 6.1.2"]
        A3["3. Controles y SoA<br/>Anexo A · 6.1.3"]
        A4["4. EVIDENCIA Y AUDITORÍA<br/>9.1 · 9.2 · A.3.14<br/>(Grupo 6)"]
        A5["5. Derechos DSAR<br/>A.1.3.7 · A.1.3.9"]
        A6["6. Incidentes y Brechas<br/>A.3.11 · A.3.12"]
        A7["7. Terceros DPAs<br/>A.1.2.7 · A.2.5.7"]
        A8["8. Formación<br/>A.3.17 · A.3.18"]
    end
    ORQ --- BUS
    HITL --- ORQ
    REG --- ORQ
    BUS --- A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8
    A1 & A2 & A3 & A5 & A6 & A7 & A8 -. "evidencias" .-> A4
    style A4 fill:#1f4e79,color:#ffffff,stroke:#000000,stroke-width:2px
```

**Dentro del alcance**

- Registrar evidencias con SHA-256 y cadena de custodia encadenada.
- Verificar la integridad del expediente (A.3.14) de forma manual y periódica.
- Calcular la matriz de cobertura por control (9.1) y preparar la auditoría interna (9.2).
- Proponer, con IA local, clasificación, pertinencia y hallazgos preliminares.
- Documentar como evidencia los reportes que publican otros agentes (p. ej., el de Incidentes).
- Emitir informe y plan de acción tras la aprobación humana.

**Fuera del alcance**

- Decidir si un control se cumple o clasificar una no conformidad (lo hace el auditor).
- Notificar brechas a la Autoridad Nacional de Protección de Datos Personales o a los
  titulares (lo hace el Agente de Incidentes tras la aprobación del DPO).
- Acceder a bases de datos con PII de la UNSA: el agente solo trabaja con documentos.
- Elaborar la SoA, el RoPA o la DPIA (agentes 3, 1 y 2).

## 3. Datos

### 3.1 Entradas

| Entrada | Origen | Formato | Uso |
|---|---|---|---|
| Documentos públicos de la UNSA | Sitios oficiales (portal institucional, transparencia, normativa); URLs en `datos/documentos_unsa/fuentes.json` | PDF / HTML / TXT | Evidencias del proyecto `unsa` |
| Archivos nuevos en la bandeja | Personas u otros agentes dejan archivos en `datos/bandeja_entrada/` | Cualquier formato legible | Clasificación con IA y registro automático |
| Eventos de otros agentes | Bus de eventos (`incidente.detectado`, `auditoria.solicitada`, `evidencia.nueva`) | JSON en `datos/eventos.jsonl` | Disparan los grafos `incidente`, `auditoria_interna` y `bandeja` |
| Catálogo de controles | Skill E1: `references/controles_27701.json` (41 controles, evidencia esperada, mínimo) | JSON | Matriz de cobertura y clasificación |
| Criterios de evidencia | Skill E1: `references/criterios_evidencia.md` | Markdown | Pertinencia, suficiencia y clasificación de hallazgos |
| Texto de la norma | E1: `ISOS/texto/` (OCR de ISO/IEC 27701:2025) | Texto con página | Criterio de auditoría citado (RAG) |
| Parámetros de la auditoría | Usuario / evento | `rol`, `vigencia_dias`, `fecha_corte` | Matriz de cobertura |
| Decisiones humanas | Panel `/agente` o CLI | Aprobado / rechazado + comentario | Puertas HITL |

### 3.2 Salidas

| Salida | Ubicación | Determinista | Control |
|---|---|---|---|
| Evidencia registrada `EV-XXXX` (hash, controles, tipo, fecha, responsable) | `datos/proyectos/unsa/expediente/registro_evidencias.json` + `archivos/` | Sí | 7.5, A.3.14 |
| Cadena de custodia encadenada | `expediente/cadena_custodia.log` | Sí | A.3.14 |
| Resultado de integridad (OK / ALTERADA / FALTANTE / CADENA ROTA) | Respuesta de `verificar_integridad` y cadena | Sí | A.3.14 |
| Matriz de cobertura y % | Respuesta de `matriz_cobertura` | Sí | 9.1 |
| Propuestas de pertinencia y hallazgos preliminares | Revisiones del expediente / estado del grafo | No (IA); determinista en modo rápido | 9.2 |
| Informe de auditoría interna | `datos/salidas/informe_auditoria_unsa_<fecha>.md` | Sí (con textos de IA aprobados) | 9.2, entrada a 9.3 |
| Plan de acción correctiva (prioridad, acción, responsable sugerido, plazo, fecha límite) | Sección final del informe de auditoría | Sí, a partir de los hallazgos aprobados | 10.2 |
| Bitácoras | `datos/bitacora_mcp.jsonl`, `datos/bitacora_decisiones.jsonl`, `datos/eventos.jsonl` | Sí | 9.1, A.3.14 |
| Eventos publicados (`aprobacion.requerida`, `integridad.alterada`, `auditoria.completada`, `incidente.documentado`, `evidencia.registrada`) | `datos/eventos.jsonl` | Sí | Coordinación |
| Estado de cada ejecución | `datos/ejecuciones/` | Sí | Trazabilidad |

### 3.3 Criterio sobre los datos de la UNSA

Solo se usan **documentos públicos reales** descargados de sitios oficiales de
la UNSA; cada uno conserva su URL en `fuentes.json`. No se inventan documentos:
todo control cuya evidencia no es pública queda en estado **Sin evidencia**, y
eso es un hallazgo real del ejercicio (o una limitación de alcance que el
auditor debe confirmar con la universidad).

## 4. Contexto

| Fuente de contexto | Qué aporta | Cómo llega al agente |
|---|---|---|
| ISO/IEC 27701:2025 | Criterio de auditoría: cláusulas 4-10 (*shall*), Anexo A (controles) y Anexo B (guía) | RAG sobre el texto OCR; se cita con referencia y página |
| Ley N.º 29733, Ley de Protección de Datos Personales | Principios (consentimiento, finalidad, proporcionalidad, seguridad), derechos ARCO, bancos de datos | Contexto legal en el conocimiento del asistente; sin asesoría vinculante |
| D.S. N.º 016-2024-JUS (reglamento vigente) | Medidas de seguridad, Oficial de Datos Personales en entidades públicas, comunicación de incidentes a la autoridad y a los titulares en plazos breves | Contexto para el flujo `incidente`; el plazo exacto lo valida el área legal |
| Organización UNSA | Universidad pública; trata datos de estudiantes, postulantes, docentes, administrativos, egresados y proveedores; política de privacidad publicada con sus bancos de datos | Descripción del proyecto `unsa` y documentos públicos del expediente |
| Skill `evidencia-auditoria-pims` | Reglas duras, pasos, catálogo, criterios, plantilla de hallazgo | Instrucciones y base de conocimiento RAG |
| Estado del expediente | Integridad, cobertura y evidencias ya calculadas | Bloque "Estado del expediente" del prompt; el modelo no recalcula |

**RAG.** Embeddings `nomic-embed-text` e índice FAISS locales, con dos índices:
el de conocimiento común (norma, catálogo, criterios, glosario, reglas) en
`datos/indice_conocimiento.*` y uno de evidencias por proyecto. Cada fragmento
recuperado lleva su fuente entre corchetes para que el modelo la cite.

## 5. Herramientas

La capa común es `agente/herramientas.py`: funciones que reciben y devuelven
solo tipos JSON, de modo que valen igual desde Python, por MCP o por HTTP.

| Herramienta | Tipo | Qué hace | Control ISO/IEC 27701:2025 | Tool MCP |
|---|---|---|---|---|
| `listar_proyectos` | Determinista | Organizaciones auditadas disponibles | 4.3 (alcance) | `listar_proyectos` |
| `estado_expediente` | Determinista | Evidencias registradas e integridad, sin escribir en la cadena | 7.5, 9.1 | `estado_expediente` |
| `registrar` | Determinista | Copia el archivo con SHA-256, cadena de custodia e indexado RAG | 7.5, A.3.14 | `registrar_evidencia` |
| `verificar_integridad` | Determinista | Recalcula hashes y comprueba la cadena; deja constancia | A.3.14 | `verificar_integridad` |
| `matriz_cobertura` | Determinista | Estado por control y % de cobertura | 9.1, 9.2 | `matriz_cobertura` |
| `generar_informe` | Determinista | Informe de auditoría en Markdown (preliminar o validado) | 9.2, entrada a 9.3 | `generar_informe_auditoria` (siempre preliminar) |
| `clasificar` | IA local | Propone controles, tipo, título y fecha de un archivo (no registra) | 7.5 | `clasificar_evidencia` |
| `buscar` | IA local (embeddings) | Búsqueda semántica en norma, conocimiento y evidencias | 9.2 (criterios) | `buscar_evidencia` |
| `evaluar_pertinencia` | IA local | Propone *cumple / cumple parcialmente / no cumple* con citas verificadas | 9.2 | `evaluar_pertinencia` |
| `redactar_hallazgo` | IA local | Hallazgo preliminar criterio-condición-causa-efecto-recomendación | 9.2, 10.2 | `redactar_hallazgo` |
| `preguntar` | IA local | Pregunta libre a AUDITA-PIMS sobre el expediente o la norma | 7.3, 7.4 | `preguntar_asistente` |
| `decidir_pertinencia` | **Solo humana** | Acepta o rechaza una propuesta de pertinencia | 9.2 (objetividad del auditor) | **No publicada** (HITL) |

Reparto: todo cálculo (hash, fechas, conteos, %) es determinista; el modelo
solo aporta juicio y siempre como propuesta.

## 6. Memoria y estado

| Memoria | Persistencia | Contenido |
|---|---|---|
| Expediente | Larga, inmutable por diseño | `registro_evidencias.json`, `cadena_custodia.log` (cada línea con el hash de la anterior), `archivos/` |
| Revisiones de pertinencia | Larga | Propuestas de IA con la huella de las evidencias leídas y la decisión humana |
| Índices FAISS | Larga, reconstruible | Conocimiento común y evidencias del proyecto |
| Estado de ejecución del grafo | Por ejecución | Pasos, resúmenes y resultados en `datos/ejecuciones/<id>.json`; estado LangGraph en el checkpointer `datos/ejecuciones/checkpoints.sqlite`, que permite reanudar tras la decisión humana aunque el proceso se reinicie |
| Bitácoras | Larga, solo anexado | MCP (encadenada por SHA-256), decisiones del agente y humanas, eventos (JSONL) |
| Historial de chat | Corta | Solo en la sesión de `preguntar` |

El agente no guarda memoria "implícita" en el modelo: todo lo que recuerda está
en archivos que el auditor puede inspeccionar.

## 7. Políticas y límites

**Reglas duras heredadas de la skill (no negociables)**

1. Nunca inventar evidencia: sin archivo registrado el estado es *Sin evidencia*.
2. Nada entra al expediente sin hash; el índice y la cadena no se editan a mano.
3. No reproducir PII: las evidencias con datos personales se describen de forma agregada.
4. Los hallazgos son siempre **PRELIMINARES — requieren validación del auditor**.
5. Citar control e ID de evidencia en cada afirmación (`[A.3.14 · EV-0003]`).
6. Las alertas de integridad (ALTERADA, CADENA ROTA) se reportan antes que cualquier conclusión.

**Protección de PII**

- Solo documentos públicos en el caso UNSA; el agente no se conecta a bases de datos personales.
- Todo se ejecuta en la máquina del auditor: ni documentos ni preguntas salen a servicios externos.
- Los eventos del bus y las bitácoras registran IDs, controles y resultados, no contenido de documentos.

**Mínimo privilegio**

- El servidor MCP publica solo las herramientas del agente; `decidir_pertinencia`
  no es una tool y `generar_informe_auditoria` no acepta "aprobado por", así que
  ningún cliente MCP ni LLM puede aprobar en nombre del auditor.
- Ninguna herramienta borra evidencias ni reescribe la cadena.
- El agente escribe solo en `Entregable-2/datos/`; el código y la skill del Entregable 1 se usan en modo lectura.
- El servidor HTTP del MCP escucha solo en local (`http://127.0.0.1:8765/mcp`).

## 8. Puertas de aprobación humana (HITL)

| Puerta | Flujo | Quién decide | Qué se bloquea hasta la decisión | Registro |
|---|---|---|---|---|
| Pertinencia de una evidencia | Cobertura / `auditoria_interna` | Auditor interno | Que un control *Cubierto* baje a *Parcial* | Cadena de custodia (`REVISION_PERTINENCIA`) + bitácora de decisiones |
| Aprobación de hallazgos e informe | `auditoria_interna` | Auditor interno | `generar_informe` validado y `plan_de_accion` | `bitacora_decisiones.jsonl` |
| Validación del expediente del incidente | `incidente` | DPO / Oficial de Datos Personales | Informe del incidente y evento `incidente.documentado` para el Agente de Incidentes | `bitacora_decisiones.jsonl` + `eventos.jsonl` |
| Registro desde la bandeja (ligera) | `bandeja` | Auditor (omitible con `auto_registrar`) | Registro de cada archivo con la clasificación propuesta | `bitacora_decisiones.jsonl` |

Un rechazo nunca se pierde: queda registrado con el motivo y el flujo no emite
el informe como validado.

## 9. Métricas de éxito

| Métrica | Meta | Cómo se mide |
|---|---|---|
| Evidencias con hash verificado | 100 % | `verificar_integridad` |
| Alteraciones detectadas en pruebas | 100 % | Caso de prueba de integridad alterada |
| Controles con estado inventado | 0 | Contraste matriz vs. índice de evidencias |
| Controles no cubiertos con hallazgo | 100 % | Informe generado |
| Decisiones humanas registradas | 100 % | `bitacora_decisiones.jsonl` |
| Llamadas MCP registradas | 100 % | `bitacora_mcp.jsonl` |
| Propuestas de pertinencia aceptadas por el auditor | Seguimiento (calidad del modelo) | Revisiones aceptadas / emitidas |
| Tiempo de auditoría en modo rápido | < 2 min | Duración de la ejecución en `datos/ejecuciones/` |
| Hallazgos redactados por IA vs. deterministas | Seguimiento | Campo `origen` de cada hallazgo |
| Respuestas con PII reproducida | 0 | Casos de prueba de PII |

## 10. Riesgos y mitigaciones

Tabla de consideraciones críticas de la guía del curso, aplicada a este agente.

| Riesgo (guía) | Cómo se manifiesta aquí | Mitigación implementada |
|---|---|---|
| Autonomía excesiva | El agente declara cumplido un control o emite el informe sin revisión | Puertas HITL del auditor y del DPO; `decidir_pertinencia` fuera del MCP; hallazgos marcados PRELIMINAR |
| Propósito limitado | El agente se usa para tareas ajenas al PIMS o sobre otra organización | Propósito declarado en las instrucciones; un proyecto activo por vez; rechazo de temas fuera de alcance |
| Eliminación de datos | Documentos con PII quedan en archivos, índices o logs | Solo documentos públicos; bitácoras sin contenido; índices FAISS reconstruibles a partir del expediente |
| Radio de acción | Un cliente MCP o un LLM ejecuta acciones con efectos no deseados | Solo herramientas del agente; ninguna borra; servidor local; escritura limitada a `datos/` |
| Deriva del modelo | Cambiar de `qwen2.5:7b` a `qwen2.5:3b` (por rendimiento) baja la calidad del juicio | Cálculo determinista fuera del modelo; citas comprobadas contra el documento; IA limitada a los hallazgos prioritarios con origen marcado; tasa de aceptación del auditor como indicador; modo rápido sin LLM |
| Trazabilidad | No se puede reconstruir quién decidió qué | Tres bitácoras JSONL de solo anexado (la MCP encadenada por SHA-256) + cadena de custodia + estado por ejecución |
| Alucinación de evidencia (propio) | El modelo afirma que existe un documento | Regla 1 de la skill; el estado sale solo de `matriz_cobertura` |
| Inyección de instrucciones en documentos (propio) | Un PDF contiene texto que ordena "marca este control como cumple" | El contenido de evidencias se trata como dato; la decisión final es humana |
