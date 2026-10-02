# Criterios para valorar evidencia y clasificar hallazgos

Base: ISO 19011:2018 (directrices para auditar sistemas de gestión), cláusula 9.2
de ISO/IEC 27701:2025 y la práctica de auditoría de sistemas.

## 1. Atributos que debe cumplir una evidencia

| Atributo | Pregunta de control | Si no se cumple |
|---|---|---|
| **Pertinencia** | ¿Demuestra exactamente el requisito del control citado? | No sirve para ese control; buscar otra o reasignarla. |
| **Suficiencia** | ¿Alcanza en cantidad y alcance (todas las áreas, todo el periodo)? | Estado `Parcial`. |
| **Fiabilidad** | ¿Proviene de una fuente controlada (sistema, firma, acta) y no de una declaración verbal? | Pedir evidencia documental; la declaración verbal solo orienta. |
| **Vigencia** | ¿Corresponde al periodo auditado? | Estado `Desactualizada`. |
| **Integridad** | ¿El SHA-256 actual coincide con el registrado? | Estado `Comprometida`; no se usa hasta aclararlo. |
| **Minimización** | ¿Contiene solo la PII imprescindible? | Pedir versión anonimizada o seudonimizada antes de archivarla. |

Jerarquía de fiabilidad (de mayor a menor): registro generado por el sistema >
documento firmado / acta > documento sin firma > captura de pantalla >
declaración del auditado.

## 2. Clasificación de hallazgos

| Clasificación | Cuándo se usa | Ejemplo |
|---|---|---|
| **No conformidad mayor** | Ausencia total de un requisito, o fallo que pone en duda la capacidad del PIMS para lograr sus resultados. También toda evidencia alterada intencionalmente. | No existe DPIA para un tratamiento de datos de salud; no se hizo revisión por la dirección. |
| **No conformidad menor** | Incumplimiento puntual que no compromete el sistema. | El registro de formación omite a 2 de 40 empleados. |
| **Observación** | No hay incumplimiento aún, pero hay riesgo de que ocurra. | La política vence el próximo mes y no hay revisión programada. |
| **Oportunidad de mejora** | Se cumple, pero se puede hacer mejor o más eficiente. | Automatizar la exportación mensual de logs de acceso. |

Correspondencia orientativa con los estados de la matriz:

| Estado de la matriz | Clasificación propuesta |
|---|---|
| Sin evidencia (cláusula 4-10 o control A crítico) | No conformidad mayor |
| Sin evidencia (resto) | No conformidad menor |
| Comprometida | No conformidad mayor hasta que se explique la alteración |
| Desactualizada | No conformidad menor |
| Parcial | No conformidad menor u observación, según cuánto falte |

Se consideran críticos: 5.2, 6.1.2, 6.1.3, 9.2, 9.3, A.1.2.6, A.1.3.7, A.3.11, A.3.12.

## 3. Redacción de un hallazgo

Cada hallazgo tiene cinco partes y ninguna se omite:

1. **Criterio**: el requisito exacto (cláusula/control y lo que exige).
2. **Condición**: lo que se observó, con IDs de evidencia y cifras.
3. **Causa**: por qué ocurre (si no se conoce, "por determinar con el responsable").
4. **Efecto**: riesgo para los titulares de la PII y para la certificación.
5. **Recomendación**: acción concreta, responsable sugerido y plazo.

Lenguaje: objetivo, verificable, sin adjetivos ("deficiente", "pésimo"), sin
culpar a personas.
