# -*- coding: utf-8 -*-
"""Documentos de la alta dirección (CGTD) y la política: MA-01, POL-01, PL-03 y AC-01."""

import comun_otros_grupos as c
import datos_pims_unsa as du
import plantillas_pims as pp


# =============================================================================== MA-01
def ma01():
    d = c.nuevo(pp.PLANTILLA_PROCEDIMIENTO, "PIMS-MA-01",
                "Manual del PIMS: contexto, partes interesadas, alcance, procesos y roles",
                "Documento nuevo: contexto (4.1), partes interesadas (4.2), alcance (4.3), procesos (4.4), "
                "liderazgo y roles (5.1, 5.3), recursos (7.1) y comunicación (7.4)")
    c.objetivo(d,
               "Este manual describe el Sistema de Gestión de Privacidad de la Información (PIMS) de la UNSA: "
               "el contexto en que opera, las partes interesadas y sus requisitos, el alcance, los procesos "
               "del sistema y sus interacciones, el compromiso de la alta dirección, los roles, los recursos "
               "asignados y la forma de comunicar, según las cláusulas 4, 5, 7.1 y 7.4 de ISO/IEC 27701:2025.",
               "Se aplica a todo el PIMS de la UNSA. Los usuarios son el Consejo Universitario, el Rectorado, "
               "el CGTD, el Oficial y el Coordinador de Datos Personales, el OSCD, los dueños de procesos que "
               "tratan datos personales y los equipos de los ocho agentes del PIMS.",
               "Remite a los documentos de la lista maestra PIMS-RG-01 para el detalle de cada proceso.")
    c.referencias(d, ["ISO/IEC 27701:2025, cláusulas 4.1 a 4.4, 5.1, 5.3, 7.1 y 7.4; controles A.3.4 y A.3.13",
                      "Reglamento de Organización y Funciones de la UNSA (RCU N.° 0306-2022)",
                      "RR N.° 1000-2025 (CGTD), RR N.° 0987-2025 (Oficial de Datos Personales), RR N.° 1244-2025 "
                      "(OSCD) y RR N.° 0503-2026 (CSIRT UNSA)",
                      "PIMS-POL-01, PIMS-RG-01, PIMS-RG-02, PIMS-RG-05"])

    d.h1("Contexto de la UNSA (4.1)")
    d.p("La UNSA es una universidad pública con más de 28 000 estudiantes y unos 4 500 docentes y "
        "servidores, que trata datos personales de postulantes (incluidos menores de edad), estudiantes, "
        "egresados, personal, proveedores, visitantes y administrados en sus bancos de datos inscritos "
        "(Política de Privacidad). Las cuestiones internas y externas que afectan al PIMS son:")
    d.h2("Análisis FODA de la privacidad")
    d.tabla(["Fortalezas (internas)", "Debilidades (internas)"], [
        ["Oficial de Datos Personales, Coordinador y OSCD designados por resolución; CSIRT UNSA conformado",
         "Documentación de privacidad incompleta antes de este proyecto (AUD-2026-001: cobertura 7.9 %)"],
        ["Política de Privacidad publicada y canal ARCO odp@unsa.edu.pe",
         "Archivos en papel con datos sensibles (bienestar, salud) sin control de acceso"],
        ["Plan de Gobierno Digital (RCU N.° 0152-2023) y plan de contingencia de TI vigentes",
         "Personal con acceso a datos personales sin capacitación ni acuerdos de confidencialidad completos"],
    ], anchos=[8, 8], tam=8)
    d.tabla(["Oportunidades (externas)", "Amenazas (externas)"], [
        ["Nuevo Reglamento de la Ley N.° 29733 (D.S. N.° 016-2024-JUS) que precisa obligaciones",
         "Ataques de ransomware y filtraciones a universidades públicas"],
        ["Convenios con otras universidades para auditorías independientes",
         "Sanciones de la Autoridad Nacional de Protección de Datos Personales"],
        ["Herramientas de automatización (agentes del PIMS) para evidencia y control documental",
         "Presupuesto público limitado y rotación de personal"],
    ], anchos=[8, 8], tam=8)
    d.h2("Análisis PESTEL")
    d.tabla(["Factor", "Cuestión relevante para la privacidad", "Efecto en el PIMS"], [
        ["Político", "Prioridad del gobierno digital y de la confianza digital en el Estado",
         "Compromiso institucional y supervisión de la Secretaría de Gobierno Digital"],
        ["Económico", "Presupuesto anual por resultados; costo de las brechas", "Priorizar controles por riesgo"],
        ["Social", "Mayor conciencia de los estudiantes sobre sus derechos; postulantes menores de edad",
         "Más solicitudes de derechos; consentimiento de padres o tutores"],
        ["Tecnológico", "Servicios en la nube, aula virtual, sistemas académicos web",
         "Transferencias internacionales y seguridad de aplicaciones"],
        ["Ecológico (cambio climático)", "Lluvias intensas, sismos y cortes de energía que afectan al centro "
         "de datos; política de reducción de papel", "Se evaluó como **pertinente**: refuerza las copias de "
         "seguridad fuera del centro de datos (A.3.24), el plan de contingencia y la digitalización de "
         "archivos en papel"],
        ["Legal", "Ley N.° 29733 y su reglamento, Ley N.° 27806, Ley N.° 30220", "Requisitos en PIMS-RG-05"],
    ], anchos=[3, 7, 6], tam=8)

    d.h1("Partes interesadas y sus requisitos (4.2)")
    d.tabla(["Parte interesada", "Necesidades y expectativas", "Requisito que la UNSA atiende con el PIMS"], [
        ["Titulares de datos (postulantes, estudiantes, egresados, personal)", "Uso legítimo, seguridad y "
         "ejercicio de derechos", "Ley N.° 29733; PIMS-PR-05 y PIMS-PR-07"],
        ["Padres o tutores de postulantes menores de edad", "Autorizar el tratamiento", "Consentimiento "
         "(A.1.2.4, A.1.2.5)"],
        ["Autoridad Nacional de Protección de Datos Personales", "Cumplimiento y notificación de incidentes",
         "Reglamento D.S. N.° 016-2024-JUS; PIMS-PR-06"],
        ["SUNEDU y MINEDU", "Información para el licenciamiento y registros nacionales", "Transferencias "
         "por ley (PIMS-RG-04)"],
        ["Encargados del tratamiento (proveedores)", "Instrucciones y contratos claros", "A.1.2.7; PIMS-RG-04"],
        ["Ciudadanía (Ley N.° 27806)", "Acceso a la información pública sin vulnerar datos personales",
         "PIMS-PR-01 y PIMS-PR-09"],
        ["Alta dirección y Consejo Universitario", "Cumplir la ley y proteger la reputación", "PIMS-POL-01"],
    ], anchos=[4.5, 5.5, 6], tam=8)
    d.p("El detalle de las leyes y documentos externos aplicables está en el registro PIMS-RG-05 "
        "(control A.3.13).")

    d.h1("Alcance del PIMS (4.3)")
    d.p("**El PIMS de la UNSA comprende el tratamiento de datos personales que realiza la UNSA como "
        "responsable del tratamiento** en las actividades del inventario PIMS-RG-02: admisión, registro "
        "académico y matrícula, bienestar universitario, salud y psicopedagogía, recursos humanos, "
        "biblioteca, videovigilancia, grados y títulos, trámite documentario y proveedores, en la sede "
        "central y las áreas académicas de Arequipa, y los sistemas de información de la OTI que los "
        "soportan.")
    d.tabla(["Aspecto", "Decisión"], [
        ["Rol en el tratamiento", "Responsable del tratamiento (se aplican A.1 y A.3)"],
        ["Rol de encargado", "Excluido: la UNSA no trata datos por encargo de terceros dentro del alcance; "
         "los controles A.2 se excluyen en la SoA PIMS-RG-03"],
        ["Interfaces y dependencias", "Encargados del registro PIMS-RG-04 y entidades que reciben datos por "
         "ley (SUNEDU, MINEDU, SUNAT, EsSalud)"],
        ["Fuera del alcance", "Centros de producción y empresas vinculadas con personería propia"],
    ], anchos=[4, 12])

    d.h1("Procesos del PIMS y sus interacciones (4.4)")
    d.p("El PIMS se establece, implementa, mantiene y mejora con los procesos siguientes. Cada equipo del "
        "PIMS opera un agente de IA que apoya su proceso; las decisiones las toman personas:")
    d.tabla(["Proceso", "Equipo / agente", "Entradas", "Salidas", "Documentos"], [
        ["Inventario de tratamientos", "Agente 1", "Procesos de las unidades", "RoPA, flujos", "RG-02, PR-09"],
        ["Evaluación de riesgos y DPIA", "Agente 2", "RoPA, contexto", "Riesgos, DPIA", "MT-01, IN-01"],
        ["Controles y SoA", "Agente 3", "Riesgos, requisitos", "SoA, plan de tratamiento, política",
         "POL-01, RG-03, PL-01, PR-08"],
        ["Evidencia y auditoría", "Agente 4 (Grupo 6)", "Documentos y evidencias", "Control documental, "
         "auditorías, no conformidades, indicadores", "PR-01 a PR-04, FO-01, RG-01, RG-05, IN-02, IN-03"],
        ["Derechos de los titulares", "Agente 5", "Solicitudes", "Respuestas y registro", "PR-05, PR-07"],
        ["Incidentes y brechas", "Agente 6", "Alertas", "Registro y notificaciones", "PR-06"],
        ["Terceros y encargados", "Agente 7", "Contratos", "Registro de encargados y transferencias", "RG-04"],
        ["Formación y concienciación", "Agente 8", "Roles", "Plan y registros de formación", "PL-02, RG-06"],
        ["Dirección del sistema", "CGTD", "Resultados del PIMS", "Objetivos, revisión, recursos",
         "MA-01, PL-03, AC-01"],
    ], anchos=[3.2, 2.4, 3, 3.6, 3.8], tam=8)
    d.p("Interacciones principales: el inventario (Agente 1) alimenta la evaluación de riesgos (Agente 2); "
        "sus resultados definen la SoA y el plan (Agente 3); los incidentes (Agente 6) y las solicitudes "
        "(Agente 5) generan evidencia que el Agente 4 registra con su huella SHA-256 y audita; la formación "
        "(Agente 8) atiende las brechas de competencia; la dirección revisa todo en la revisión por la "
        "dirección. Los agentes se coordinan por un bus de eventos con bitácora.")

    d.h1("Liderazgo y compromiso (5.1)")
    d.p("La alta dirección demuestra su compromiso: aprobó la política PIMS-POL-01 en el Consejo "
        "Universitario, designó al Oficial de Datos Personales y al OSCD, conformó el CGTD y el CSIRT, "
        "asignó los recursos de la sección 9 y preside la revisión por la dirección (PIMS-AC-01).")

    d.h1("Roles, responsabilidades y autoridades (5.3, A.3.4)")
    d.tabla(["Actividad", "CU / Rector", "CGTD", "ODP", "CDP", "OSCD", "OTI", "Dueño de proceso",
             "Auditor"], [
        ["Aprobar política y alcance", "A", "R", "C", "I", "C", "I", "I", "I"],
        ["Inventario y avisos de privacidad", "I", "I", "A", "R", "C", "C", "R", "I"],
        ["Evaluación de riesgos y DPIA", "I", "A", "R", "C", "R", "C", "R", "I"],
        ["SoA y plan de tratamiento", "I", "A", "R", "C", "R", "R", "C", "I"],
        ["Atención de derechos", "I", "I", "A", "R", "I", "C", "R", "I"],
        ["Incidentes y brechas", "I", "I", "A (notificar)", "C", "R", "R", "C", "I"],
        ["Control documental y evidencias", "I", "I", "A", "R", "C", "C", "C", "I"],
        ["Auditoría interna", "I", "A", "C", "C", "C", "C", "C", "R"],
        ["Revisión por la dirección", "R", "R", "C", "C", "C", "I", "I", "C"],
    ], anchos=[4, 1.5, 1.4, 1.6, 1.3, 1.4, 1.3, 2, 1.5], tam=7)
    d.p("R: responsable de ejecutar; A: aprueba y rinde cuentas; C: consultado; I: informado. ODP: Oficial "
        "de Datos Personales (Jefe de la Oficina de Asesoría Jurídica, RR N.° 0987-2025); CDP: Coordinador "
        "de Datos Personales; OSCD: Oficial de Seguridad y Confianza Digital (RR N.° 1244-2025).")

    d.h1("Recursos (7.1)")
    d.tabla(["Recurso", "Asignación 2027 (simulada)", "Responsable"], [
        ["Personas", "ODP y CDP (30 % de su jornada), OSCD (50 %), 8 equipos de agentes (4 personas c/u, "
         "4 h por semana), auditor líder y 3 auditores internos", "Rector"],
        ["Herramientas", "Servidor PostgreSQL del repositorio documental, agentes del PIMS, SIEM del CSIRT",
         "Jefe(a) de la OTI"],
        ["Formación", "Plan PIMS-PL-02 (S/ 18 000)", "Unidad de Recursos Humanos"],
        ["Auditoría independiente", "Convenio con otra universidad pública (A.3.15) (S/ 12 000)", "CGTD"],
        ["Mejoras técnicas del plan PL-01", "Doble factor, digitalización, registro de accesos (S/ 48 000)",
         "Oficina de Planeamiento y Presupuesto"],
    ], anchos=[3.5, 9, 3.5], tam=8)

    d.h1("Comunicación (7.4)")
    d.tabla(["Qué se comunica", "Cuándo", "A quién", "Cómo", "Quién comunica"], [
        ["Política de privacidad y avisos", "Al aprobarse y en cada cambio", "Comunidad universitaria y "
         "público", "Portal web, correo institucional", "Oficina Universitaria de Imagen Institucional"],
        ["Documentos PIMS nuevos o actualizados", "Al publicarse", "Usuarios de cada documento",
         "Correo institucional y repositorio", "Propietario del documento"],
        ["Resultados de auditoría y de indicadores", "Trimestral y tras cada auditoría", "CGTD y Rector",
         "Informe IN-02 / IN-03", "Auditor líder / CDP"],
        ["Brechas de datos personales", "En el plazo legal", "ANPD y titulares afectados", "Canales oficiales",
         "Oficial de Datos Personales"],
        ["Campañas de concienciación", "Según PIMS-PL-02", "Personal y estudiantes", "Correo, aula virtual, "
         "afiches", "Unidad de Recursos Humanos"],
        ["Respuestas a solicitudes de derechos", "En el plazo de PIMS-PR-05", "Titular", "Correo o Mesa de "
         "Partes", "Coordinador de Datos Personales"],
    ], anchos=[3.6, 2.8, 3, 3.2, 3.4], tam=8)

    c.registros(d, [
        ["Análisis de contexto y partes interesadas", "Repositorio documental del PIMS", c.ODP,
         "Versiones según PIMS-PR-01", "5 años"],
        ["Registro de comunicaciones del PIMS", "Correo institucional y repositorio", c.CDP,
         "Acceso por rol", "3 años"],
    ])
    c.validez(d, "PIMS-MA-01", [
        "cambios del contexto no reflejados en el manual en la revisión anual;",
        "procesos del PIMS sin dueño o sin documento asociado;",
        "comunicaciones previstas que no se realizaron.",
    ])
    c.firmas(d, c.ODP, "CGTD", "Rector(a) de la UNSA")
    return c.guardar(d, "PIMS-MA-01_Manual_del_PIMS.docx")


# =============================================================================== POL-01
def pol01():
    d = c.nuevo(pp.PLANTILLA_PROCEDIMIENTO, "PIMS-POL-01",
                "Política de privacidad y protección de datos personales del PIMS",
                "Actualización de la Política de Privacidad publicada (marzo 2021) como política del sistema "
                "de gestión (cláusula 5.2) y alineación al D.S. N.° 016-2024-JUS",
                aprobado_por=c.APROBADO_CU, aprobador_corto="Consejo Universitario", revisor="CGTD")
    c.objetivo(d,
               "Esta política establece el compromiso de la UNSA con la protección de los datos personales y "
               "el marco para fijar los objetivos de privacidad del PIMS (cláusula 5.2 de ISO/IEC 27701:2025).",
               "Se aplica a todos los tratamientos de datos personales de la UNSA dentro del alcance del PIMS "
               "(PIMS-MA-01) y a todas las personas que los realizan: autoridades, docentes, servidores, "
               "estudiantes con funciones administrativas y encargados del tratamiento.",
               "Es un documento público: se publica en el portal web y se comunica a toda la comunidad "
               "universitaria.")
    c.referencias(d, ["Política de Privacidad de la UNSA publicada en unsa.edu.pe (marzo 2021), que esta "
                      "política actualiza", "PIMS-MA-01 Manual del PIMS", "PIMS-PL-03 Objetivos de privacidad"])
    d.h1("Declaración de la política")
    d.p("La Universidad Nacional de San Agustín de Arequipa trata los datos personales de postulantes, "
        "estudiantes, egresados, docentes, servidores, proveedores, visitantes y administrados solo para "
        "las finalidades de sus funciones universitarias, con respeto a la dignidad y a la vida privada de "
        "las personas. Para ello, la UNSA se compromete a:")
    d.vinetas([
        "**cumplir los requisitos aplicables**: la Ley N.° 29733 y su reglamento, la Ley Universitaria, la "
        "Ley de Transparencia y los contratos con encargados;",
        "aplicar los **principios de la Ley N.° 29733**: legalidad, consentimiento, finalidad, "
        "proporcionalidad, calidad, seguridad, disposición de recurso y nivel de protección adecuado;",
        "informar a los titulares y **facilitar el ejercicio de sus derechos** de acceso, rectificación, "
        "cancelación y oposición (odp@unsa.edu.pe o Mesa de Partes, calle San Agustín N.° 115);",
        "proteger los datos con medidas de seguridad proporcionales al riesgo y **notificar las brechas** "
        "en los plazos legales;",
        "exigir a los encargados del tratamiento las mismas garantías mediante contrato;",
        "fijar **objetivos de privacidad** medibles (PIMS-PL-03) y revisarlos cada año;",
        "**mejorar continuamente** el PIMS a partir de auditorías, indicadores e incidentes.",
    ])
    d.h1("Responsabilidades")
    d.vinetas([
        "El Consejo Universitario aprueba esta política; el Rector la hace cumplir.",
        "El Oficial de Datos Personales vela por su cumplimiento y es el punto de contacto con la Autoridad "
        "y con los titulares.",
        "El Oficial de Seguridad y Confianza Digital dirige las medidas de seguridad (políticas temáticas "
        "de PIMS-PR-08, control A.3.3).",
        "Cada dueño de proceso aplica la política en los tratamientos a su cargo.",
        "Todo el personal la conoce y la cumple; su incumplimiento se trata según el Reglamento General de "
        "Trabajo y las normas disciplinarias de la UNSA.",
    ])
    d.h1("Comunicación y revisión")
    d.p("Esta política se publica en el portal web, se comunica por correo institucional al personal y se "
        "incluye en la inducción (PIMS-PL-02). Se revisa al menos una vez al año en la revisión por la "
        "dirección y cuando cambie la normativa.")
    c.registros(d, [["Constancias de conocimiento de la política", "Registro PIMS-RG-06", c.RRHH,
                     "Nivel Restringido; acceso por rol", "Mientras dure la relación laboral + 5 años"]])
    c.validez(d, "PIMS-POL-01", [
        "porcentaje del personal que declaró conocer la política;",
        "cantidad de incumplimientos de la política detectados en auditorías.",
    ])
    c.firmas(d, c.ODP, "CGTD", "Consejo Universitario")
    return c.guardar(d, "PIMS-POL-01_Politica_de_privacidad_del_PIMS.docx")


# =============================================================================== PL-03
def pl03():
    d = c.nuevo(pp.PLANTILLA_PROCEDIMIENTO, "PIMS-PL-03", "Objetivos de privacidad y planificación para lograrlos",
                "Documento nuevo: objetivos de privacidad medibles (6.2) y planificación de cambios (6.3)",
                revisor="CGTD")
    c.objetivo(d,
               "Este plan establece los objetivos de privacidad del PIMS de la UNSA y cómo se lograrán: qué se "
               "hará, qué recursos se requieren, quién es responsable, cuándo se finalizará y cómo se evaluarán "
               "los resultados (cláusula 6.2), y planifica los cambios del PIMS (cláusula 6.3).",
               "Se aplica al periodo noviembre 2026 – diciembre 2027.",
               "Los usuarios son el CGTD, el Oficial de Datos Personales, los dueños de los objetivos y el "
               "equipo auditor interno.")
    c.referencias(d, ["PIMS-POL-01", "PIMS-PR-04 (indicadores)", "PIMS-IN-01 y PIMS-PL-01 (riesgos)"])
    d.h1("Objetivos de privacidad 2026–2027")
    d.p("Los objetivos son coherentes con la política PIMS-POL-01, son medibles con los indicadores de "
        "PIMS-PR-04 y consideran los resultados de la evaluación de riesgos (PIMS-IN-01):")
    d.tabla(["ID", "Objetivo", "Qué se hará", "Recursos", "Responsable", "Fecha", "Cómo se evalúa"], [
        ["OBJ-01", "Cobertura de evidencia del PIMS ≥ 80 %", "Registrar documentos y evidencias de "
         "operación; auditorías de seguimiento", "Equipos de los 8 agentes", "Oficial de Datos Personales",
         "30-06-2027", "IND-01"],
        ["OBJ-02", "100 % de tratamientos de alto riesgo con DPIA vigente", "DPIA anual de T01, T03 y T04 y de "
         "todo tratamiento nuevo de alto riesgo", "Equipo del Agente 2", "Oficial de Datos Personales",
         "31-12-2027", "IND-09"],
        ["OBJ-03", "≥ 80 % del personal que trata datos personales capacitado", "Ejecutar PIMS-PL-02",
         "S/ 18 000", "Jefe(a) de la Unidad de Recursos Humanos", "31-07-2027", "IND-08"],
        ["OBJ-04", "100 % de solicitudes de derechos atendidas en plazo", "Operar PIMS-PR-05 con seguimiento "
         "semanal", "CDP y dueños de proceso", "Coordinador de Datos Personales", "Permanente", "IND-06"],
        ["OBJ-05", "100 % de encargados con contrato de tratamiento", "Firmar adendas pendientes", "Asesoría "
         "Jurídica", "Oficial de Datos Personales", "31-03-2027", "IND-10"],
        ["OBJ-06", "100 % de brechas notificables comunicadas en plazo", "Operar PIMS-PR-06 y simulacros",
         "CSIRT UNSA", "Oficial de Seguridad y Confianza Digital", "Permanente", "IND-07"],
        ["OBJ-07", "Aviso de privacidad en el 100 % de formularios que recogen datos", "Revisar formularios "
         "web y en papel (PIMS-PR-07)", "Unidad de Sistemas de Información", "Coordinador de Datos Personales",
         "30-04-2027", "Revisión de formularios en auditoría"],
    ], anchos=[1.3, 3, 3.4, 2.2, 2.6, 1.6, 1.9], tam=7)
    d.p("El avance se informa cada trimestre en el informe de desempeño PIMS-IN-03 y se revisa en la "
        "revisión por la dirección.")
    d.h1("Planificación de los cambios del PIMS (6.3)")
    d.p("Los cambios del PIMS se realizan de forma planificada. Todo cambio se registra con su motivo, "
        "consecuencias, responsable, recursos y fecha, y se aprueba en el CGTD antes de ejecutarse:")
    d.tabla(["Cambio planificado", "Motivo", "Responsable", "Recursos", "Fecha"], [
        ["Incorporar los documentos de los ocho equipos al repositorio", "Brechas de AUD-2026-002",
         "Coordinador de Datos Personales", "Repositorio PostgreSQL", "18-11-2026 (realizado)"],
        ["Extender el alcance a las filiales cuando se integren sus sistemas", "Plan de Gobierno Digital",
         "CGTD", "Equipo del Agente 1", "2027-II"],
        ["Actualizar documentos al reglamento D.S. N.° 016-2024-JUS donde cite el reglamento anterior",
         "Cambio legal", "Oficial de Datos Personales", "Asesoría Jurídica", "31-01-2027"],
        ["Migrar el aula virtual a un nuevo proveedor (si se decide)", "Fin de contrato", "Jefe(a) de la OTI",
         "DPIA previa (Agente 2)", "Cuando se apruebe"],
    ], anchos=[5.5, 3, 3, 2.5, 2], tam=8)
    c.registros(d, [["Seguimiento de objetivos y cambios", "Repositorio documental y PIMS-IN-03", c.CDP,
                     "Versiones según PIMS-PR-01", "5 años"]])
    c.validez(d, "PIMS-PL-03", ["objetivos sin indicador o sin responsable;",
                                "cambios ejecutados sin aprobación previa del CGTD."])
    c.firmas(d, c.ODP, "CGTD", "Presidente del CGTD")
    return c.guardar(d, "PIMS-PL-03_Objetivos_de_privacidad.docx")


# =============================================================================== AC-01
def ac01():
    d = c.nuevo(pp.PLANTILLA_PROCEDIMIENTO, "PIMS-AC-01", "Acta de revisión por la dirección del PIMS (sesión 1-2026)",
                "Acta de la primera revisión por la dirección (cláusula 9.3)",
                aprobado_por="Rector(a) de la UNSA, presidente de la sesión (aprobación simulada)",
                aprobador_corto="Rector(a) de la UNSA", revisor=c.ODP)
    d.h1("Datos de la sesión")
    d.tabla(["Campo", "Valor"], [
        ["Sesión", "Revisión por la dirección del PIMS N.° 1-2026 (sesión simulada)"],
        ["Fecha y lugar", "18-11-2026, Sala de sesiones del Rectorado"],
        ["Preside", "Rector(a) de la UNSA"],
        ["Asistentes (por cargo)", "Vicerrector(a) Académico(a), Vicerrector(a) de Investigación, miembros "
         "del CGTD, Oficial de Datos Personales, Coordinador de Datos Personales, OSCD, Jefe(a) de la OTI, "
         "Auditor líder del PIMS, Secretario(a) General"],
        ["Objetivo", "Revisar el PIMS para asegurar su conveniencia, adecuación y eficacia (9.3.1)"],
    ], anchos=[4, 12])
    d.h1("Entradas revisadas (9.3.2)")
    d.tabla(["Entrada", "Lo que se presentó"], [
        ["a) Estado de las acciones de revisiones anteriores", "Primera revisión: no hay acciones previas."],
        ["b) Cambios en las cuestiones externas e internas", "Nuevo reglamento de la Ley N.° 29733; "
         "cambio climático evaluado como pertinente (PIMS-MA-01)."],
        ["c) Cambios en las necesidades de las partes interesadas", "Más solicitudes de derechos; exigencia de "
         "consentimiento de padres o tutores en admisión."],
        ["d) Desempeño: no conformidades y acciones correctivas", "AUD-2026-002: 30 hallazgos en PIMS-FO-01; "
         "plazos en curso."],
        ["d) Desempeño: seguimiento y medición", "Informe PIMS-IN-03: 5 de 11 indicadores en meta, 3 por "
         "debajo (cobertura, capacitación 34.6 % y encargados 71.4 %) y 3 aún sin medición posible."],
        ["d) Desempeño: resultados de auditoría", "PIMS-IN-02: cobertura 21.1 % antes de registrar los "
         "documentos de los ocho equipos; 26 de 26 documentos aprobados al 18-11-2026."],
        ["e) Retroalimentación de partes interesadas", "6 solicitudes de derechos atendidas en plazo; sin "
         "quejas ante la Autoridad."],
        ["f) Resultados de la evaluación de riesgos y estado del plan", "PIMS-IN-01: 10 de 12 riesgos no "
         "aceptables antes del tratamiento; plan PIMS-PL-01 con 11 actividades (1 implementada)."],
        ["g) Oportunidades de mejora", "Automatizar los indicadores con los agentes; digitalizar archivos en "
         "papel."],
    ], anchos=[5.5, 10.5], tam=8)
    d.h1("Decisiones y acuerdos (9.3.3)")
    d.tabla(["N.°", "Acuerdo", "Responsable", "Plazo"], [
        ["AC-01-01", "Se declara que el PIMS es conveniente y adecuado, pero aún no eficaz: la eficacia se "
         "evaluará con AUD-2026-003 y AUD-2027-001.", "CGTD", "04-12-2026"],
        ["AC-01-02", "Se aprueban los recursos 2027 de PIMS-MA-01 (sección Recursos).", "Rector(a)",
         "31-12-2026"],
        ["AC-01-03", "Se aprueban los objetivos de privacidad PIMS-PL-03 sin cambios.", "Oficial de Datos "
         "Personales", "18-11-2026"],
        ["AC-01-04", "Se aceptan los riesgos residuales de PIMS-IN-01 propuestos por sus propietarios.",
         "Propietarios de riesgos", "18-11-2026"],
        ["AC-01-05", "Se prioriza la capacitación y la firma de acuerdos de confidencialidad (IND-08).",
         "Jefe(a) de la Unidad de Recursos Humanos", "31-03-2027"],
        ["AC-01-06", "La certificación externa (expediente D36) se evaluará después de AUD-2027-001.", "CGTD",
         "30-05-2027"],
    ], anchos=[1.8, 9, 3.4, 1.8], tam=8)
    d.h1("Registro de mejoras del periodo (10.1)")
    d.tabla(["Mejora", "Origen", "Fecha", "Resultado"], [
        ["Control documental automatizado de los documentos PIMS", "AUD-2026-001", "17-11-2026",
         "El agente detectó fallas en las primeras versiones; corregidas con nueva versión"],
        ["Lista maestra completa en la base de datos (PIMS-RG-01)", "Mensaje 3 del docente / AUD-2026-002",
         "18-11-2026", "26 documentos con sus cláusulas y controles"],
        ["Simulacro de brecha con el Agente de Incidentes", "Plan PL-01", "17-11-2026",
         "Clasificación en 1 h 40 min"],
    ], anchos=[6, 3.5, 2, 4.5], tam=8)
    c.registros(d, [["Actas de revisión por la dirección", "Repositorio documental y archivo de Secretaría "
                     "General", "Secretario(a) General", "Nivel Uso interno; versiones según PIMS-PR-01",
                     "Permanente"]])
    c.validez(d, "PIMS-AC-01", ["acuerdos vencidos sin cumplir;", "entradas de 9.3.2 no tratadas."])
    c.firmas(d, "Secretario(a) General", c.ODP, "Rector(a) de la UNSA")
    return c.guardar(d, "PIMS-AC-01_Acta_de_revision_por_la_direccion_1-2026.docx")


def generar():
    return [ma01(), pol01(), pl03(), ac01()]
