---
name: evidencia-auditoria-pims
description: Recolecta, registra con hash SHA-256, verifica y mapea evidencias de auditoría contra las cláusulas 4-10 y los controles del Anexo A de ISO/IEC 27701:2025, y produce la matriz de cobertura y los hallazgos preliminares de una auditoría interna del PIMS (cláusula 9.2). Úsala cuando pidan registrar o archivar una evidencia, preparar o revisar una auditoría interna o de certificación de privacidad, comprobar si una evidencia fue alterada, saber qué controles no tienen evidencia, o redactar hallazgos / no conformidades del PIMS.
---

# Evidencia y Auditoría del PIMS (ISO/IEC 27701:2025)

Esta skill convierte la tarea "revisa estas evidencias y dime si estamos listos
para la auditoría" en un proceso repetible y trazable. Todo lo que es cálculo
(hashes, fechas, conteos, cobertura) lo hace el script `scripts/evidencia.py`;
el modelo solo aporta lo que requiere juicio: clasificar la evidencia, valorar
si es suficiente y redactar los hallazgos.

## Reglas que no se negocian

1. **Nunca inventes evidencia.** Si un control no tiene archivo registrado, el
   estado es "Sin evidencia", aunque la organización diga que el control existe.
2. **Nada entra al expediente sin hash.** Toda evidencia se registra con
   `evidencia.py registrar`, que calcula el SHA-256 y escribe en la cadena de
   custodia. No edites `registro_evidencias.json` ni `cadena_custodia.log` a mano.
3. **No abras ni copies PII en tus respuestas.** Si una evidencia contiene datos
   personales (logs de acceso, exportaciones de BD), describe su contenido
   ("1 240 accesos, 3 usuarios"), nunca reproduzcas nombres, DNI o correos.
4. **Los hallazgos son preliminares.** La clasificación final (no conformidad
   mayor/menor) la firma el auditor interno humano. Márcalos siempre como
   "PRELIMINAR — requiere validación del auditor".
5. **Cita siempre el control y el ID de evidencia** (`EV-0007`, `A.3.17`) en cada
   afirmación de cumplimiento o incumplimiento.

## Datos de trabajo

El expediente vive en una carpeta (por defecto `./expediente`):

| Archivo | Qué es |
|---|---|
| `registro_evidencias.json` | Índice de evidencias: ID, control, tipo, hash, fecha, responsable |
| `cadena_custodia.log` | Bitácora encadenada (cada línea incluye el hash de la anterior) |
| `archivos/` | Copia inmutable de cada evidencia registrada |
| `soa.csv` (opcional) | Declaración de Aplicabilidad: `control_ref,aplicable,justificacion` |

Catálogo de controles y evidencia esperada: `references/controles_27701.json`.
Criterios para valorar evidencia y clasificar hallazgos:
`references/criterios_evidencia.md`. Léelo antes del paso 4.

## Pasos

### Paso 1 — Entender el encargo
Identifica cuál de estos cuatro encargos es y salta al paso que corresponde:

- *Registrar evidencias nuevas* → paso 2.
- *Verificar integridad del expediente* → paso 3.
- *Preparar / evaluar la auditoría* → pasos 3, 4 y 5 en ese orden.
- *Redactar hallazgos* → paso 5 (necesita el informe del paso 4).

Si falta el alcance (qué rol: responsable A.1, encargado A.2 o ambos; qué periodo),
pregúntalo una sola vez; si no responden, asume "ambos roles, últimos 12 meses"
y dilo en el informe.

### Paso 2 — Clasificar y registrar cada evidencia
Para cada archivo recibido:

1. Ábrelo y decide a qué control(es) responde usando el campo
   `evidencia_esperada` de `references/controles_27701.json`. Si no encaja en
   ninguno, no lo registres: díselo al usuario.
2. Decide el tipo: `politica`, `procedimiento`, `registro`, `log`, `acta`,
   `contrato`, `informe`, `configuracion`, `captura`.
3. Registra:

```bash
python scripts/evidencia.py registrar --expediente ./expediente \
  --archivo ruta/al/archivo.pdf --control A.3.17 \
  --tipo registro --titulo "Registro de formación en privacidad 2026" \
  --responsable "Nombre del recolector" --fuente "LMS Moodle" \
  --fecha-documento 2026-03-15
```

Si una misma evidencia sirve para varios controles, repite `--control`
(`--control A.3.17 --control 7.2`). El script devuelve el ID asignado.

### Paso 3 — Verificar integridad

```bash
python scripts/evidencia.py verificar --expediente ./expediente
```

Comprueba que cada archivo conserva su SHA-256 y que la cadena de custodia no
fue reescrita. Cualquier `ALTERADA` o `CADENA ROTA` se reporta primero, antes que
cualquier otra conclusión: una evidencia alterada no sirve como evidencia.

### Paso 4 — Matriz de cobertura

```bash
python scripts/evidencia.py cobertura --expediente ./expediente \
  --rol ambos --vigencia-dias 365 --salida informe_cobertura.md
```

Estados posibles por control: `Cubierto`, `Parcial` (menos evidencias que el
mínimo), `Desactualizada` (más antigua que la vigencia), `Comprometida` (hash no
coincide), `Sin evidencia`, `No aplica` (excluido en la SoA). Lee el informe
generado y, para cada control `Cubierto`, abre al menos una evidencia y
confirma que de verdad demuestra el control (suficiencia y pertinencia, ver
`criterios_evidencia.md`). Si no lo demuestra, degrádalo a `Parcial` y explica
por qué.

### Paso 5 — Hallazgos preliminares
Usa `assets/plantilla_hallazgo.md`. Un hallazgo por control con estado distinto
de `Cubierto` / `No aplica`, con la estructura **criterio – condición – causa –
efecto – recomendación** y la clasificación propuesta según
`criterios_evidencia.md`. Agrupa al final las oportunidades de mejora.

### Paso 6 — Entregar
Entrega al usuario, en este orden:

1. Alertas de integridad (si las hay).
2. Resumen: % de cobertura y número de controles por estado.
3. Los hallazgos preliminares.
4. Las rutas de los archivos generados (`informe_cobertura.md`, `.json`).

Termina recordando qué debe validar el auditor humano.

## Ejemplo completo

`assets/demo/` contiene un expediente de ejemplo (empresa ficticia ClinData
S.A.C.) y `assets/demo/ejecutar_demo.py`, que registra ocho evidencias, altera una
a propósito y genera la matriz de cobertura. Úsalo para comprobar que la skill
funciona en una máquina nueva.
