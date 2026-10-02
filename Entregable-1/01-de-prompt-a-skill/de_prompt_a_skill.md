# De Prompt a Skill — Agente de Evidencia y Auditoría (Grupo 6)

## 1. Punto de partida: el prompt suelto

Así se le pedía la tarea a un chat de IA antes de la skill:

> "Te adjunto la política de privacidad, el registro de formación, el RoPA, la
> DPIA de telemedicina y el acta de la revisión por la dirección. Revísalos y
> dime si estamos listos para la auditoría ISO 27701 y qué nos falta."

Funciona una vez, pero tiene siete problemas cuando se repite:

| # | Problema | Consecuencia en auditoría |
|---|---|---|
| P1 | El resultado cambia en cada ejecución | Dos revisiones del mismo expediente dan conclusiones distintas |
| P2 | El modelo no sabe qué controles existen ni qué evidencia espera cada uno | Revisa "de memoria" y omite controles sin decir que los omitió |
| P3 | Nada prueba que el archivo revisado sea el que se archivó | Una evidencia editada después pasa como válida |
| P4 | No queda registro de quién aportó qué ni cuándo | No hay cadena de custodia |
| P5 | Puede afirmar que un control "está implementado" sin archivo que lo pruebe | Alucinación de evidencia |
| P6 | Mezcla cálculo (fechas, conteos, %) con opinión | Errores aritméticos y porcentajes inventados |
| P7 | El formato del hallazgo depende de cómo se pregunte | No se puede comparar entre auditorías |

## 2. Descomposición de la tarea

Se separó la tarea en lo que **debe ser determinista** (un script lo hace
siempre igual) y lo que **requiere juicio** (lo hace el modelo, con reglas):

| Paso | Entrada | Salida | Quién lo hace | Problema que resuelve |
|---|---|---|---|---|
| 1. Entender el encargo | Petición del usuario | Tipo de encargo, rol y periodo | Modelo | P2 |
| 2. Clasificar y registrar | Archivo de evidencia | `EV-XXXX` con SHA-256 en índice y cadena | Modelo clasifica, script registra | P3, P4 |
| 3. Verificar integridad | Expediente | OK / ALTERADA / FALTANTE / CADENA ROTA | Script | P3 |
| 4. Matriz de cobertura | Expediente + catálogo + SoA | Estado por control y % de cobertura | Script calcula, modelo revisa pertinencia | P1, P2, P5, P6 |
| 5. Hallazgos | Matriz + evidencias | Hallazgos criterio-condición-causa-efecto-recomendación | Modelo con plantilla | P7 |
| 6. Entregar | Todo lo anterior | Alertas, resumen, hallazgos, rutas | Modelo | — |

## 3. Qué se fijó para que sea reutilizable

- **Conocimiento explícito**: catálogo `controles_27701.json` (33 controles con
  evidencia esperada y mínimo de evidencias) y `criterios_evidencia.md`.
- **Reglas duras**: no inventar evidencia, nada sin hash, no reproducir PII,
  hallazgos siempre preliminares, citar control e ID.
- **Formato fijo de salida**: plantilla de hallazgo y orden de entrega.
- **Parámetros** en lugar de texto libre: `--rol`, `--vigencia-dias`,
  `--fecha-corte`, `soa.csv`.

## 4. Después de la skill

El usuario ya no escribe un prompt explicando cómo revisar. En la aplicación
AUDITA-PIMS (`04-aplicacion`) cada paso es una acción:

| Paso de la skill | En la aplicación |
|---|---|
| 2. Clasificar y registrar | Subir el archivo → "Analizar con IA local" → revisar la propuesta → "Registrar con hash" |
| 3. Verificar integridad | Botón "Verificar integridad" y alerta permanente si algo falla |
| 4. Matriz de cobertura | Pestaña Cobertura con rol, vigencia y fecha de corte |
| 5. Hallazgos | Botón "Redactar hallazgo" en cada control no cubierto |
| Preguntas libres | Pestaña Asistente (RAG + LLM local) |

Y la misma skill, en formato Agent Skill, se activa en Claude Code con una
frase como "prepara la auditoría interna del PIMS, rol responsable".
