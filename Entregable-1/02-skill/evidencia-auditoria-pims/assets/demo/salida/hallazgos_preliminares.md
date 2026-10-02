# Hallazgos preliminares — ClinData S.A.C. — corte 2026-10-01

> PRELIMINAR — requiere validación del auditor interno (cláusula 9.2).
> Producido en el paso 5 de la skill a partir de `informe_cobertura.md` y de la
> lectura de las evidencias (paso 4).

## 1. Alerta de integridad

EV-0007 (acta de revisión por la dirección 01-2026) **no conserva su SHA-256**
registrado: se añadió un "Acuerdo (4)" después de archivarla. La cadena de
custodia está íntegra, así que la alteración se hizo sobre el archivo y no sobre
el registro. Afecta a 5.1 y 9.3.

## 2. Resumen

- Rol evaluado: responsable del tratamiento. 30 controles; 1 excluido por la SoA
  (A.1.5.4).
- Cobertura automática: 27,6 % (8 de 29). Tras la revisión de pertinencia del
  paso 4, **2 controles bajan de Cubierto a Parcial** (A.1.2.6 y A.3.14), así que
  la cobertura validada es **20,7 % (6 de 29)**.

| Estado | Automático | Tras revisión |
|---|---|---|
| Cubierto | 8 | 6 |
| Parcial | 0 | 2 |
| Desactualizada | 1 | 1 |
| Comprometida | 2 | 2 |
| Sin evidencia | 18 | 18 |

## 3. Controles degradados en la revisión de pertinencia

- **A.1.2.6 (DPIA) → Parcial.** El RoPA (EV-0003) marca `dpia_requerida = Sí` para
  *Historia clínica electrónica* y *Telemedicina*, pero solo existe la DPIA de
  telemedicina (EV-0004).
- **A.3.14 (Protección de registros) → Parcial.** EV-0008 es un extracto del log
  de accesos: prueba que el log existe, no que esté protegido. Falta la
  configuración de retención e inmutabilidad.

## 4. Hallazgos

### H-01 — 9.3 / 5.1 — Evidencia de revisión por la dirección alterada
| Campo | Contenido |
|---|---|
| Clasificación propuesta | No conformidad mayor (hasta que se explique la alteración) |
| Evidencias | EV-0007 |

**Criterio.** 9.3 exige conservar información documentada de los resultados de la
revisión por la dirección; 7.5 exige protegerla contra modificaciones no
intencionadas.
**Condición.** El acta registrada el 2026-10-01 con hash `d504442b…` fue
modificada después: el hash actual no coincide y contiene un acuerdo que no
figuraba en la versión archivada.
**Causa.** Por determinar con Gerencia General.
**Efecto.** No se puede demostrar qué decidió la dirección; un auditor externo
rechazaría el acta como evidencia.
**Recomendación.** Recuperar la versión firmada original, documentar el motivo
del cambio y, si el acuerdo (4) es legítimo, emitir una adenda firmada y
registrarla como evidencia nueva. Responsable: Oficial de Privacidad. Plazo: 10 días.

### H-02 — 6.1.2 / 6.1.3 — Sin evaluación ni tratamiento de riesgos de privacidad
| Campo | Contenido |
|---|---|
| Clasificación propuesta | No conformidad mayor (controles críticos) |
| Evidencias | Ninguna |

**Criterio.** 6.1.2 y 6.1.3 exigen un proceso de evaluación de riesgos de
privacidad y una Declaración de Aplicabilidad con justificación por control.
**Condición.** No hay metodología, matriz de riesgos ni SoA firmada en el
expediente. La `soa.csv` disponible solo contiene una exclusión.
**Causa.** Por determinar.
**Efecto.** Sin SoA no puede definirse el alcance de la certificación ni
justificarse las exclusiones.
**Recomendación.** Elaborar la matriz de riesgos y la SoA completa (Agente de
Riesgos y Agente de Controles en el Entregable 2). Responsable: DPO. Plazo: 30 días.

### H-03 — A.1.2.6 — DPIA faltante para la historia clínica electrónica
| Campo | Contenido |
|---|---|
| Clasificación propuesta | No conformidad mayor (datos de salud) |
| Evidencias | EV-0003, EV-0004 |

**Criterio.** A.1.2.6 exige DPIA cuando el tratamiento implica alto riesgo.
**Condición.** El RoPA identifica dos tratamientos con DPIA requerida; solo hay
DPIA para telemedicina.
**Causa.** Por determinar con el Oficial de Privacidad.
**Efecto.** Riesgos no evaluados sobre datos de salud de todos los pacientes.
**Recomendación.** Realizar la DPIA de la HCE. Responsable: DPO. Plazo: 45 días.

### H-04 — 9.2 — Auditoría interna desactualizada
| Campo | Contenido |
|---|---|
| Clasificación propuesta | No conformidad menor |
| Evidencias | EV-0006 |

**Criterio.** 9.2 exige auditorías internas a intervalos planificados.
**Condición.** El último informe es del 2024-11-20 (más de 365 días antes del
corte) y se hizo contra la edición 2019 de la norma. No hay programa ni plan de
auditoría 2026 (mínimo 2 evidencias).
**Causa.** El acta 01-2026 programa la auditoría para octubre de 2026, aún no
ejecutada (dato tomado de EV-0007, cuya integridad está en duda: confirmar).
**Efecto.** El ciclo PDCA no tiene la etapa de verificación del periodo.
**Recomendación.** Aprobar el programa de auditoría 2026 contra la edición 2025.
Responsable: Auditor interno. Plazo: 15 días.

### H-05 — A.1.3.7 / A.1.3.9 / A.1.3.10 — Sin evidencia de atención de derechos ARCO
Clasificación propuesta: No conformidad mayor (A.1.3.7 es crítico). No hay
procedimiento ni registro de solicitudes. Recomendación: implantar el
procedimiento ARCO con plazos legales y su registro (Agente DSAR). Plazo: 30 días.

### H-06 — A.3.14 — Protección de logs no demostrada
Clasificación propuesta: No conformidad menor. Ver sección 3. Recomendación:
aportar la configuración de retención e inmutabilidad de `audit_query`.

## 5. Observaciones y oportunidades de mejora

- **Observación (A.3.17).** EV-0002: COL-006 (Telemedicina) desaprobó el curso
  (nota 11) y no consta reevaluación.
- **Oportunidad de mejora (A.1.2.2).** El RoPA no registra plazos de
  conservación por actividad.
- Los otros 13 controles sin evidencia (4.1, 4.2, 4.3, 5.3, 6.2, 7.5, 8.1, 9.1,
  10.1, 10.2, A.1.2.7, A.3.12, A.3.18) se listan en `informe_cobertura.md`;
  deben solicitarse al auditado antes de clasificarlos.

## 6. Qué debe validar el auditor humano

1. La explicación de la alteración de EV-0007 antes de cerrar H-01.
2. La clasificación mayor/menor propuesta en cada hallazgo.
3. Si los controles sin evidencia existen y simplemente no se entregaron.
