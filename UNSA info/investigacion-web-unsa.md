# UNSA — información pública útil para la auditoría PIMS (ISO/IEC 27701:2025)

Recopilado el 2026-10-26 de fuentes públicas (portal web y repositorio de transparencia de la UNSA).
Documentos descargados en esta carpeta:

| Archivo | Qué es |
|---|---|
| `RCU-0153-2025-aulas-virtuales.pdf` / `.txt` (texto por OCR) | RCU 0153-2025, aprueba la **Directiva N.° 003-2025-UM-OTI «Regulación del almacenamiento de información de aulas virtuales»** (17/03/2025) |
| `RCU-0422-2026-plan-contingencia-datacenter.pdf` / `.txt` | RCU 0422-2026 (27/08/2026), **Plan de Contingencia y Plan de Atenciones SLA para Data Center**, OTI, v1.0 julio 2026 |
| `Politica de privacidad.txt` (ya estaba) | Política de privacidad publicada en https://www.unsa.edu.pe/servicios/politica-proteccion-datos.html |

---

## 1. Perfil de la organización

- Universidad pública, Calle Santa Catalina 117, Cercado, Arequipa. RUC 20163646499.
- Licenciada por SUNEDU en agosto de 2018 por 10 años (vence en 2028). En enero de 2026 recibió la acreditación institucional internacional IAC-CINDA por 7 años.
- 18 facultades en tres áreas (Ingenierías, Biomédicas, Sociales). En 2018 tenía 245 programas (59 de pregrado, 75 maestrías, 20 doctorados, 91 segundas especialidades). No encontré una cifra oficial de estudiantes.
- ROF y organigrama aprobados por **RCU 0306-2022** (lo cita la Directiva 003-2025).

### Área de TI
- **Oficina de Tecnologías de la Información (OTI)**, antes OUIS. Calle Universidad 107. ouis@unsa.edu.pe, +51 54 391911 anexo 1201.
- Dentro de la OTI está la **Unidad de Sistemas de Información, Redes y Telecomunicaciones (USIRT)**, que configura y supervisa las aulas virtuales (Directiva 003-2025, 7.3.2).
- El jefe de la OTI es además el responsable del Portal de Transparencia (RR 1043-2026 y RR 1375-2026).
- **Data Center**: 6 gabinetes (2 son de investigación), UPS, aires acondicionados comerciales (sin HVAC de precisión) y una demanda prevista de 78 kVA (RCU 0422-2026).

### Sistemas que tratan datos personales (inventario de activos)
| Sistema | URL | Datos personales |
|---|---|---|
| Aula virtual (Moodle, una instancia por semestre) | aulavirtual.unsa.edu.pe/2026B, /aulaposgrado | entregas, notas, foros, mensajes, logs |
| Matrícula | matricula.unsa.edu.pe | datos del estudiante y académicos |
| SISACAD (docentes, libretas, notas parciales) | extranet.unsa.edu.pe/sisacad/ | notas |
| Trámite documentario | ouis.unsa.edu.pe/tramited | expedientes de administrados |
| UNSAPay (pagos en línea) | ouis.unsa.edu.pe/unsapay | datos de pago |
| UNSACenter, directorio | apps.unsa.edu.pe | datos de contacto del personal |
| Bibliotecas | appsoti.unsa.edu.pe/bibliotecas_unsa | usuarios de biblioteca |
| Repositorio institucional | repositorio.unsa.edu.pe | autores de tesis |
| DUTIC (descarga de aulas virtuales) | dutic.unsa.edu.pe | — |

> Observación: SISACAD y la matrícula se sirven por **http** (sin TLS) según los enlaces del portal. Conviene confirmarlo antes de reportarlo como hallazgo (A.3.26 Uso de criptografía).

---

## 2. Política de privacidad (marzo de 2021)

Lo que ya tiene:
- Finalidades por tipo de titular (visitantes, estudiantes, egresados, postulantes, docentes, administrativos, proveedores, administrados, menores).
- Bancos de datos nombrados: Seguridad y Vigilancia, Estudiantes, Usuarios de Biblioteca, Grados y Títulos, Convenios Becas y Pasantías, Egresados, Postulantes, Recursos Humanos, Proveedores, Administrados.
- Derechos ARCO: se piden en **odp@unsa.edu.pe** o en Mesa de Partes (San Agustín 115, dirigido a Secretaría General), con nombres, petición, domicilio o correo, fecha, firma y sustento.
- Transferencias a entidades públicas, financieras, universidades y centros de salud con convenio.
- Cookies y web beacons.

Brechas que se pueden sustentar:
| Brecha | Control ISO 27701:2025 |
|---|---|
| Fechada en **marzo de 2021**: anterior al nuevo Reglamento de la Ley 29733 (**D.S. 016-2024-JUS**), que exige designar un Oficial de Datos Personales. | 5.3, A.3.13 |
| No se nombra al Oficial de Datos Personales; solo aparece el correo odp@. | 5.3, A.3.4 |
| La autorización vale «de manera indefinida o hasta que revoque su consentimiento»: **sin plazos de conservación**. | A.1.4.8 Retención |
| No da los códigos de inscripción de los bancos de datos en el Registro Nacional de Protección de Datos Personales. | A.1.2.9, A.1.3.3 |
| Las medidas de seguridad se mencionan solo de forma genérica. | A.1.3.3 |
| La autorización se presenta como **obligatoria** para todas las finalidades, incluidas las encuestas y la difusión en el directorio. | A.1.2.3 Base legal, A.1.2.4 Consentimiento |

---

## 3. Directiva N.° 003-2025-UM-OTI — aulas virtuales (RCU 0153-2025)

- Elaborada por la OTI (10/02/2025), revisada por la Unidad de Modernización y aprobada por el Consejo Universitario el 06/03/2025.
- **Clasificación de la información (7.1)**: material didáctico, datos académicos de estudiantes, datos administrativos (asistencia, accesos, logs) y otras evidencias (mensajes privados, foros).
- **Retención (7.2)**: material didáctico 3 años; evaluaciones y calificaciones 2 años; foros 1 año; **logs 1 año**. Los plazos son «orientativos».
- **Responsables (7.3)**: OTI (almacenamiento seguro, backups, archivo y eliminación, accesos), USIRT, decanatos, Asesoría Jurídica (Ley 29733) y docentes.
- **Eliminación (7.4, 8.2)**: cronograma de la OTI, informe previo (valoración según el AGN, método de destrucción segura, existencia de respaldos), conformidad de Secretaría General y acta de verificación.
- **Archivo (8.1)**: activo durante el semestre más 1 semestre; después se archiva en un almacenamiento secundario (on-premise o nube) con acceso restringido.
- **Backup y DRP (8.3)**: «deberá tener copias de seguridad periódicas» y «**se establecerá** un Plan de Recuperación de Desastres» (en futuro).

Sirve como evidencia de **A.1.4.8 Retención, A.1.4.9 Eliminación, A.3.14 Protección de registros, A.3.24 Respaldo de información y A.3.25 Registro de eventos**.

Brechas:
- Su base legal cita el **reglamento derogado D.S. 003-2013-JUS**, aunque se aprobó en marzo de 2025, cuando ya se había publicado el D.S. 016-2024-JUS (A.3.13).
- Los plazos «orientativos» y el hecho de que cada decanato pueda fijar los suyos dejan la retención sin un criterio único verificable (A.1.4.8).
- No fija frecuencia, retención, cifrado ni pruebas de restauración de los backups (A.3.24).
- Un año de logs puede quedarse corto para investigar incidentes (A.3.25).
- Los mensajes privados entran como «otras evidencias» con valor de investigación pedagógica: reutilizarlos así **sería una finalidad distinta** a la declarada en la política de privacidad (A.1.2.2 Identificar y documentar la finalidad).
- Archivar «en la nube» abre preguntas sobre transferencia internacional y contratos con el proveedor (A.1.5.2, A.3.10).

---

## 4. Plan de Contingencia y SLA del Data Center (RCU 0422-2026)

- Niveles de activación N1, N2 y N3; roles: Director de Crisis (jefatura de la OTI), Coordinador del DC, responsables eléctrico, de redes y de HVAC, seguridad y comunicaciones.
- La evaluación técnica califica el **riesgo global del Data Center como ALTO**: documentación eléctrica deficiente, acometida inadecuada, 4 de 6 gabinetes sin etiquetado correcto, recirculación de aire caliente y hot spots, aires comerciales sin monitoreo, y falta de inventario, planos y procedimientos.
- SLA: P1 24x7 con acuse en 15 min y restauración en 4 h; P2 8 h; P3 2 días hábiles; P4 5 días hábiles.
- Bitácora obligatoria de incidentes; revisión post-incidente en 5 días hábiles; pruebas trimestrales, semestrales y anuales.

Brechas (muy aprovechables como hallazgos):
| Brecha | Control |
|---|---|
| **Excluye expresamente** «los planes de continuidad de aplicaciones, respaldo y recuperación de datos, ciberseguridad». Junto con la Directiva 003-2025, que dice que el DRP «se establecerá», muestra que **no hay plan de respaldo/DRP aprobado**. | A.3.24, A.3.11 |
| La matriz de servicios críticos tiene **RTO, RPO y dueño del servicio sin llenar** («[Completar catálogo, RTO, RPO…]»). | A.3.24, 6.1 |
| Las firmas de elaboración, revisión y aprobación y todo el directorio de emergencia (Anexo A) están en «[Completar]» en la versión publicada. | 7.5.3 Control de información documentada |
| Cubre solo incidentes físicos (energía, HVAC, enlaces, incendio); no dice nada sobre **brechas de datos personales** ni sobre la notificación a la ANPDP o a los titulares. | A.3.11, A.3.12, A.1.3.x |
| El documento se rotula «de uso interno» y aun así se publicó entero en el portal de transparencia, con información de la infraestructura crítica. | A.3.5 Clasificación de la información |

---

## 5. Otros datos de contexto

- **Admisión**: en 2019 se anuló un examen porque la prueba se filtró por WhatsApp; en 2025 hubo denuncias de filtración de preguntas y suplantación en la II Fase. No se trata de incidentes informáticos, pero sirven para hablar de riesgos de confidencialidad y de verificación de identidad.
- **ANPDP**: no encontré sanciones a la UNSA en las búsquedas. El registro de sanciones y el compendio de resoluciones de la ANPDP se pueden revisar a mano: https://www.gob.pe/institucion/anpd/informes-publicaciones/1255336-registro-de-sanciones-de-la-autoridad-nacional-de-proteccion-de-datos-personales
- **Precedente útil**: la R.D. 13-2022-JUS/DGTAIPD confirmó la sanción a una universidad por publicar imágenes de alumnos en su web sin autorización.
- No encontré públicamente ninguna **política de seguridad de la información**, SGSI ni Plan de Gobierno Digital de la UNSA. Si de verdad no existen, eso es un hallazgo (A.3.3); si existen, son la primera evidencia que hay que pedir.

## 6. Evidencias que conviene solicitar a la UNSA (no son públicas)

1. Resolución de designación del Oficial de Datos Personales.
2. Constancias de inscripción de los bancos de datos ante la ANPDP.
3. Política de seguridad de la información o del SGSI, si existe.
4. Plan de respaldo y DRP, con registros de backups y de pruebas de restauración.
5. Los anexos del plan del DC (matriz de servicios críticos, cuadro de tickets SLA, informe técnico).
6. Actas de eliminación de aulas virtuales (Directiva 003-2025, 8.2.4).
7. Contratos con encargados del tratamiento (nube, pasarela de UNSAPay, convenios de salud).
8. Registro de solicitudes ARCO atendidas por odp@unsa.edu.pe.

---

## Fuentes
- Portal UNSA: https://www.unsa.edu.pe/
- Política de protección de datos: https://www.unsa.edu.pe/servicios/politica-proteccion-datos.html
- Comunicado de la Directiva de aulas virtuales: https://www.unsa.edu.pe/comunicados/directivas-de-almacenamiento-de-informacion-en-aulas-virtuales/
- RCU 0153-2025: https://transparencia.unsa.edu.pe/bitstream/handle/123456789/1511/RCU-0153-2025.pdf
- RCU 0422-2026: https://transparencia.unsa.edu.pe/handle/123456789/1920
- Reglamentos y documentos oficiales: https://transparencia.unsa.edu.pe/handle/123456789/65
- Normas de la UNSA en gob.pe: https://www.gob.pe/institucion/universidad-nacional-de-san-agustin/normas-legales
- Licenciamiento: https://andina.pe/ingles/noticia-unsa-arequipa-es-universidad-numero-50-recibe-licenciamiento-723270.aspx
- Filtración del examen de admisión: https://proactivo.com.pe/arequipa-unsa-anula-examen-de-admision-por-filtracion-de-prueba-en-redes-sociales/ y https://larepublica.pe/sociedad/2025/03/18/ofrecian-ingreso-por-hasta-s16000-postulantes-unsa-denuncian-fraude-en-admision-2025-en-arequipa-1172412
- D.S. 016-2024-JUS y el Oficial de Datos Personales: https://lpderecho.pe/hasta-donde-puede-llegar-la-autoridad-nacional-de-proteccion-de-datos-personales-una-reflexion-a-los-limites-normativos-en-la-designacion-del-oficial-de-datos-personales/
- R.D. 13-2022-JUS/DGTAIPD: https://lpderecho.pe/confirman-sancion-universidad-difundir-imagenes-alumnos-sitio-web-autorizacion-resolucion-directoral-13-2022-jus-dgtaipd/
