# -*- coding: utf-8 -*-
"""Documentos de los Agentes 5 (derechos), 6 (incidentes), 7 (terceros) y 8 (formación):
PR-05, PR-07, PR-06, RG-04, PL-02 y RG-06."""

import comun_otros_grupos as c
import datos_pims_unsa as du
import plantillas_pims as pp

CANAL = ("correo odp@unsa.edu.pe o Mesa de Partes (calle San Agustín N.° 115, Cercado de Arequipa), dirigido "
         "a la Secretaría General")


# =============================================================================== PR-05 (Agente 5)
def pr05():
    d = c.nuevo(pp.PLANTILLA_PROCEDIMIENTO, "PIMS-PR-05",
                "Procedimiento de atención de solicitudes de derechos de los titulares",
                "Procedimiento ARCO a partir del canal publicado en la Política de Privacidad de la UNSA")
    c.objetivo(d,
               "Este procedimiento define cómo la UNSA atiende las solicitudes de acceso, rectificación, "
               "cancelación (supresión) y oposición de los titulares de datos personales, entrega copia de sus "
               "datos, informa a terceros de las correcciones y atiende las decisiones automatizadas (controles "
               "A.1.3.2 y A.1.3.7 a A.1.3.11 de ISO/IEC 27701:2025).",
               "Se aplica a todas las actividades de PIMS-RG-02.",
               "Lo usan el Coordinador y el Oficial de Datos Personales, la Secretaría General, los dueños de "
               "proceso y el equipo del Agente 5.")
    c.referencias(d, ["Ley N.° 29733, título III (derechos del titular), y su Reglamento (D.S. N.° 016-2024-JUS)",
                      "Política de Privacidad de la UNSA (canal y requisitos de la solicitud)", "PIMS-RG-02"])
    d.h1("Canal y requisitos de la solicitud")
    d.p("El titular o su representante presenta la solicitud por %s, con: nombres y apellidos, documento de "
        "identidad, petición concreta, domicilio o correo para notificar, fecha y firma, y documentos que "
        "la sustenten. La atención es gratuita salvo los costos de reproducción que la ley permita." % CANAL)
    d.h1("Plazos internos")
    d.p("La UNSA fija plazos internos que no superan los del Reglamento de la Ley N.° 29733; si el reglamento "
        "fija un plazo menor, prevalece el reglamento:")
    d.tabla(["Derecho", "Control", "Plazo interno máximo", "Respuesta"], [
        ["Información", "A.1.3.2", "8 días hábiles", "Qué datos se tratan, para qué y con quién se comparten"],
        ["Acceso y copia", "A.1.3.7, A.1.3.9", "20 días hábiles", "Copia de los datos en formato legible "
         "(PDF o impreso)"],
        ["Rectificación", "A.1.3.7", "10 días hábiles", "Corrección y aviso a los destinatarios (A.1.3.8)"],
        ["Cancelación / supresión", "A.1.3.7", "10 días hábiles", "Supresión salvo obligación legal de "
         "conservar; aviso a destinatarios"],
        ["Oposición", "A.1.3.6, A.1.3.7", "10 días hábiles", "Cese del tratamiento no obligatorio"],
        ["Revisión de decisión automatizada", "A.1.3.11", "10 días hábiles", "Revisión humana (p. ej., "
         "calificación del examen de admisión)"],
    ], anchos=[3.6, 2.6, 3, 6.8], tam=8)
    d.h1("Pasos")
    d.tabla(["Paso", "Qué se hace", "Responsable"], [
        ["1. Registro", "Se asigna el código SD-AAAA-NNN y se registra en el registro de solicitudes "
         "(A.1.3.10).", "Secretaría General / CDP"],
        ["2. Verificación de identidad", "Se verifica la identidad del titular o el poder del representante; "
         "si faltan datos se pide subsanar en 5 días hábiles.", "CDP"],
        ["3. Búsqueda", "Se pide la información al dueño del proceso (banco de datos de PIMS-RG-02).",
         "Dueño de proceso"],
        ["4. Decisión", "Se decide y se fundamenta; una denegación la firma el Oficial de Datos Personales.",
         "CDP / ODP"],
        ["5. Ejecución", "Se corrige, suprime o entrega copia, y se informa a los terceros a quienes se "
         "comunicaron los datos (A.1.3.8).", "Dueño de proceso"],
        ["6. Respuesta y cierre", "Se responde por el medio elegido y se cierra el registro.", "CDP"],
    ], anchos=[3, 9.5, 3.5], tam=8)
    d.h1("Registro de solicitudes del periodo")
    d.p("Registro sin datos personales (los datos del titular están en el expediente físico/digital de cada "
        "solicitud, con nivel Restringido). Periodo de la simulación: 01-10-2026 a 18-11-2026.")
    d.tabla(["Código", "Derecho", "Banco de datos", "Recepción", "Respuesta", "Días hábiles", "Estado"], [
        ["SD-2026-001", "Acceso y copia", "Estudiantes", "05-10-2026", "20-10-2026", "11", "Atendida"],
        ["SD-2026-002", "Rectificación", "Egresados", "09-10-2026", "16-10-2026", "5", "Atendida"],
        ["SD-2026-003", "Cancelación", "Postulantes", "15-10-2026", "27-10-2026", "8", "Atendida (parcial: "
         "resultados se conservan por ley)"],
        ["SD-2026-004", "Oposición (encuestas)", "Estudiantes", "22-10-2026", "28-10-2026", "4", "Atendida"],
        ["SD-2026-005", "Revisión de decisión automatizada", "Postulantes", "30-10-2026", "11-11-2026", "8",
         "Atendida: calificación confirmada"],
        ["SD-2026-006", "Información", "Recursos Humanos", "06-11-2026", "12-11-2026", "4", "Atendida"],
    ], anchos=[2.2, 3.2, 2.4, 2, 2, 1.6, 2.6], tam=8)
    c.registros(d, [
        ["Registro de solicitudes de derechos", "Repositorio documental (nivel Restringido)", c.CDP,
         "Acceso nominal; registro de accesos", "5 años desde el cierre"],
        ["Expedientes de cada solicitud", "Secretaría General / repositorio", "Secretario(a) General",
         "Nivel Restringido", "5 años desde el cierre"],
    ])
    c.validez(d, "PIMS-PR-05", ["porcentaje de solicitudes atendidas en plazo (IND-06);",
                                "solicitudes denegadas sin fundamento escrito."])
    c.firmas(d, c.CDP, c.ODP, "Presidente del CGTD")
    return c.guardar(d, "PIMS-PR-05_Atencion_de_derechos_de_los_titulares.docx")


# =============================================================================== PR-07 (Agente 5)
def pr07():
    d = c.nuevo(pp.PLANTILLA_PROCEDIMIENTO, "PIMS-PR-07",
                "Procedimiento de información a los titulares, avisos de privacidad y consentimiento",
                "Documento nuevo para los controles A.1.2.4, A.1.2.5 y A.1.3.3 a A.1.3.6")
    c.objetivo(d,
               "Este procedimiento asegura que los titulares reciban información clara sobre el tratamiento "
               "de sus datos y que el consentimiento, cuando es la base legal, se obtenga, registre y pueda "
               "retirarse (controles A.1.2.4, A.1.2.5 y A.1.3.3 a A.1.3.6 de ISO/IEC 27701:2025).",
               "Se aplica a todo formulario, sistema o canal por el que la UNSA recoge datos personales.",
               "Lo usan los dueños de proceso, la Unidad de Sistemas de Información, la Oficina Universitaria "
               "de Imagen Institucional y el Coordinador de Datos Personales.")
    c.referencias(d, ["Ley N.° 29733 (art. 18, derecho de información; consentimiento)",
                      "Política de Privacidad de la UNSA", "PIMS-RG-02", "PIMS-PR-05"])
    d.h1("Aviso de privacidad")
    d.p("Todo punto de recogida muestra un aviso en dos capas. La **primera capa**, junto al formulario, "
        "indica: responsable (UNSA, calle Santa Catalina N.° 117), finalidad, banco de datos, si los datos "
        "son obligatorios, destinatarios y cómo ejercer los derechos. La **segunda capa** es la Política de "
        "Privacidad publicada (PIMS-POL-01).")
    d.p("Modelo de primera capa para la inscripción de postulantes:")
    d.p("«La UNSA tratará tus datos en el banco de datos Postulantes para atender tu postulación, cobrar los "
        "derechos, rendir el examen y publicar los resultados con tu código de postulante. Los datos marcados "
        "con * son obligatorios. Podrás ejercer tus derechos en odp@unsa.edu.pe. Más información en la "
        "Política de Privacidad.»", cursiva=True)
    d.h1("Consentimiento")
    d.tabla(["Situación", "Regla"], [
        ["Base legal distinta del consentimiento (ley, relación académica o laboral)", "No se pide "
         "consentimiento; se informa la base legal en el aviso."],
        ["Datos sensibles (salud, socioeconómicos)", "Consentimiento expreso y por escrito o en una casilla "
         "no marcada por defecto."],
        ["Menores de 14 años", "Consentimiento del padre, madre o tutor, verificado en la inscripción."],
        ["Finalidades no necesarias (encuestas, difusión, invitaciones)", "Consentimiento separado y "
         "opcional."],
    ], anchos=[6, 10], tam=8)
    d.p("Cada consentimiento se registra con: titular (código), finalidad, versión del aviso, fecha, hora y "
        "medio. El registro se guarda en el sistema que recoge los datos.")
    d.h1("Retiro del consentimiento y oposición")
    d.p("El titular puede retirar su consentimiento u oponerse a un tratamiento no obligatorio en cualquier "
        "momento, por el mismo medio por el que lo dio o por %s. El retiro no afecta la licitud del "
        "tratamiento previo y se procesa según PIMS-PR-05." % CANAL)
    d.h1("Revisión de formularios")
    d.p("El Coordinador de Datos Personales revisa cada formulario nuevo o modificado (aviso, campos "
        "necesarios y consentimiento) antes de su publicación (objetivo OBJ-07 de PIMS-PL-03).")
    c.registros(d, [
        ["Registro de consentimientos", "Sistema que recoge los datos (p. ej., sistema de admisión)",
         "Dueño de proceso", "Nivel Restringido; registro inalterable", "Mientras dure el tratamiento + 5 años"],
        ["Versiones de los avisos de privacidad", "Repositorio documental", c.CDP, "Versiones según PIMS-PR-01",
         "5 años"],
    ])
    c.validez(d, "PIMS-PR-07", ["formularios sin aviso de privacidad;", "consentimientos sin registro."])
    c.firmas(d, c.CDP, c.ODP, "Presidente del CGTD")
    return c.guardar(d, "PIMS-PR-07_Avisos_de_privacidad_y_consentimiento.docx")


# =============================================================================== PR-06 (Agente 6)
def pr06():
    d = c.nuevo(pp.PLANTILLA_PROCEDIMIENTO, "PIMS-PR-06", "Gestión de incidentes y brechas de datos personales",
                "Procedimiento de incidentes con el CSIRT UNSA y la notificación de brechas",
                revisor=c.ODP, aprobador_corto="CGTD")
    c.objetivo(d,
               "Este procedimiento define cómo la UNSA se prepara para los incidentes de seguridad que afectan "
               "a datos personales, cómo responde a ellos y cómo notifica las brechas a la Autoridad y a los "
               "titulares (controles A.3.11 y A.3.12 de ISO/IEC 27701:2025).",
               "Se aplica a todo incidente que afecte la confidencialidad, integridad o disponibilidad de datos "
               "personales dentro del alcance del PIMS.",
               "Lo usan el CSIRT UNSA, el OSCD, el Oficial de Datos Personales, la OTI y todo el personal, que "
               "debe reportar los incidentes.")
    c.referencias(d, ["Reglamento de la Ley N.° 29733 (D.S. N.° 016-2024-JUS): incidentes de seguridad",
                      "D.U. N.° 007-2020, Marco de Confianza Digital (incidentes de seguridad digital)",
                      "RR N.° 0503-2026 (CSIRT UNSA)", "Plan de Contingencias de TI (RCU N.° 0350-2021) y "
                      "RCU N.° 0422-2026", "PIMS-PR-02"])
    d.h1("Preparación (A.3.11)")
    d.vinetas([
        "El CSIRT UNSA (RR N.° 0503-2026) es el equipo de respuesta; lo coordina el OSCD.",
        "Canales de reporte: correo del CSIRT, mesa de ayuda de la OTI y el Agente de Incidentes, que recibe "
        "las alertas del SIEM y las publica en el bus de eventos del PIMS.",
        "Simulacro semestral de brecha (el primero se hizo el 17-11-2026).",
        "Contactos de la Autoridad Nacional de Protección de Datos Personales y del Centro Nacional de "
        "Seguridad Digital actualizados cada semestre.",
    ])
    d.h1("Clasificación")
    d.tabla(["Severidad", "Criterio", "Tiempo de decisión sobre la notificación"], [
        ["Alta", "Datos sensibles o de menores, más de 100 titulares, o datos exfiltrados", "24 horas"],
        ["Media", "Datos no sensibles de menos de 100 titulares, sin exfiltración confirmada", "48 horas"],
        ["Baja", "Sin datos personales comprometidos (evento contenido)", "Se registra; no se notifica"],
    ], anchos=[2.5, 8.5, 5], tam=8)
    d.h1("Respuesta (A.3.12)")
    d.tabla(["Fase", "Acciones", "Responsable"], [
        ["Detección y registro", "Se registra el incidente con código INC-UNSA-AAAAMMDD-HHMMSS y se preserva "
         "la evidencia con huella SHA-256 (el Agente de Evidencia la registra en el expediente, A.3.14).",
         "CSIRT / Agente 4"],
        ["Contención", "Bloquear cuentas, aislar equipos, rotar credenciales.", "OTI / CSIRT"],
        ["Evaluación", "Datos y titulares afectados, consecuencias para ellos, severidad.", "OSCD con el ODP"],
        ["Notificación", "El Oficial de Datos Personales decide notificar a la Autoridad y a los titulares en "
         "el plazo del Reglamento; los incidentes de seguridad digital se reportan además al Centro Nacional "
         "de Seguridad Digital. Ningún agente notifica por su cuenta.", "Oficial de Datos Personales"],
        ["Recuperación", "Restaurar servicios desde copias verificadas.", "OTI"],
        ["Lecciones aprendidas", "Análisis de causa y acción correctiva en PIMS-FO-01 (PIMS-PR-02).",
         "OSCD"],
    ], anchos=[3, 10, 3], tam=8)
    d.h1("Registro de incidentes del periodo")
    d.tabla(["Código", "Tipo", "Banco de datos", "Severidad", "Notificado", "Estado"], [
        ["INC-UNSA-20261117-194504 (simulacro)", "Acceso no autorizado con cuenta de servicio (ejercicio con "
         "el Agente de Incidentes)", "Estudiantes", "Alta", "No (simulacro): decisión del ODP registrada en "
         "1 h 40 min", "Cerrado; lecciones en PIMS-FO-01"],
    ], anchos=[3.6, 4.4, 2, 1.4, 2.8, 1.8], tam=8)
    d.p("En el periodo no se registraron incidentes reales con datos personales.")
    c.registros(d, [
        ["Registro de incidentes y reportes", "Base de datos pims_auditoria y repositorio del CSIRT", c.OSCD,
         "Nivel Restringido; solo inserción; SHA-256", "5 años"],
        ["Notificaciones a la Autoridad y a titulares", "Secretaría General", c.ODP, "Nivel Confidencial",
         "5 años"],
    ])
    c.validez(d, "PIMS-PR-06", ["incidentes notificados fuera de plazo (IND-07);",
                                "incidentes sin análisis de causa;", "simulacros no realizados."])
    c.firmas(d, c.OSCD, c.ODP, "Presidente del CGTD")
    return c.guardar(d, "PIMS-PR-06_Gestion_de_incidentes_y_brechas.docx")


# =============================================================================== RG-04 (Agente 7)
def rg04():
    d = c.nuevo(pp.PLANTILLA_PROCEDIMIENTO, "PIMS-RG-04",
                "Registro de encargados, contratos, transferencias y divulgaciones",
                "Registro inicial de encargados y destinatarios a partir de PIMS-RG-02")
    trat = {t[0]: t for t in du.TRATAMIENTOS}
    c.objetivo(d,
               "Este registro identifica a los encargados del tratamiento de la UNSA y sus contratos, a los "
               "corresponsables, las transferencias internacionales y las divulgaciones a terceros (controles "
               "A.1.2.7, A.1.2.8, A.1.5.2 a A.1.5.5 y A.3.10 de ISO/IEC 27701:2025).",
               "Comprende los encargados de las actividades de PIMS-RG-02. Los proveedores se identifican de "
               "forma genérica en esta versión académica.",
               "Lo usan el Oficial de Datos Personales, la Oficina de Asesoría Jurídica, la Oficina de "
               "Abastecimiento y el equipo del Agente 7.")
    c.referencias(d, ["Ley N.° 29733 (encargado del tratamiento y flujo transfronterizo)", "PIMS-RG-02",
                      "PIMS-PR-08 (A.3.10 seguridad en acuerdos con proveedores)"])
    d.h1("Cláusulas mínimas de un contrato con encargado (A.1.2.7, A.3.10)")
    d.vinetas(["tratar los datos solo según instrucciones documentadas de la UNSA;",
               "confidencialidad del personal del encargado;", "medidas de seguridad equivalentes a PIMS-PR-08;",
               "no subcontratar sin autorización previa y escrita;", "asistir en la atención de derechos y de "
               "brechas (aviso a la UNSA en 24 horas);", "devolver o eliminar los datos al terminar el servicio;",
               "permitir auditorías de la UNSA."])
    d.h1("Encargados del tratamiento")
    d.tabla(["ID", "Encargado", "Servicio", "Tratamientos", "Contrato y cláusulas", "Subencargados",
             "Transf. internacional", "Estado"],
            [[e[0], e[1], e[2], ", ".join(e[3]), e[4], e[5], e[6], e[7]] for e in du.ENCARGADOS],
            anchos=[0.9, 2.6, 2.6, 1.6, 3.4, 1.6, 1.6, 2], tam=7)
    conformes = sum(1 for e in du.ENCARGADOS if e[7] == "Conforme")
    d.p("%d de %d encargados con contrato conforme; las dos adendas en firma son una actividad de PIMS-PL-01 "
        "(IND-10)." % (conformes, len(du.ENCARGADOS)))
    d.h1("Corresponsables del tratamiento (A.1.2.8)")
    d.p("En los convenios de investigación con otras universidades en que se deciden en conjunto los fines y "
        "medios, el convenio define qué parte informa a los titulares, atiende sus derechos y notifica las "
        "brechas. En el periodo no hay convenios vigentes con tratamiento conjunto de datos personales.")
    d.h1("Transferencias internacionales (A.1.5.2, A.1.5.3, A.1.5.4)")
    d.tabla(["Encargado", "Datos", "País o región de destino", "Base de la transferencia", "Registro"], [
        ["E02 Correo, aula virtual y bases en la nube", "Cuentas institucionales, contenido del aula virtual",
         "Centros de datos del proveedor fuera del Perú", "Garantías contractuales del proveedor; evaluación del "
         "nivel de protección en curso (PIMS-PL-01, riesgo R07)", "TR-2026-001"],
    ], anchos=[3.4, 3.4, 3, 4.2, 2], tam=8)
    d.h1("Divulgaciones a terceros por obligación legal (A.1.5.5)")
    filas = []
    for t in du.TRATAMIENTOS:
        if t[12] and t[12] != "—":
            filas.append([t[0] + " " + t[1], t[12], t[6].split(";")[0], "Según requerimiento o periodicidad legal"])
    d.tabla(["Tratamiento", "Destinatario", "Base legal", "Frecuencia"], filas, anchos=[5, 4, 4.5, 2.5], tam=8)
    c.registros(d, [
        ["Contratos y adendas con encargados", "Oficina de Abastecimiento y repositorio documental", c.ODP,
         "Nivel Confidencial", "Vigencia del contrato + 10 años"],
        ["Registro de transferencias y divulgaciones", "Repositorio documental", c.ODP, "Nivel Confidencial",
         "5 años"],
    ])
    c.validez(d, "PIMS-RG-04", ["encargados sin contrato conforme (IND-10);",
                                "transferencias sin base documentada."])
    c.firmas(d, c.ODP, "Jefe(a) de la Oficina de Asesoría Jurídica", "Presidente del CGTD")
    return c.guardar(d, "PIMS-RG-04_Registro_de_encargados_y_transferencias.docx")


# =============================================================================== PL-02 (Agente 8)
def pl02():
    d = c.nuevo(pp.PLANTILLA_PLAN_CAPACITACION, "PIMS-PL-02", "Plan de capacitación y concienciación en privacidad",
                "Adaptación de la plantilla «Plan de capacitación y concienciación» (ISO/IEC 27001:2013) a ISO/IEC "
                "27701:2025 y a la UNSA", revisor=c.ODP, portada="simple")
    d.h1("Objetivo")
    d.p("Con el objetivo de preparar al personal que cumple una función en el PIMS, la UNSA define los "
        "conocimientos y habilidades necesarios y la capacitación para lograrlos (cláusula 7.2 de ISO/IEC "
        "27701:2025). Para que todo el personal comprenda la importancia de la protección de datos personales "
        "y las consecuencias de no cumplir la política, se realizan las acciones de concienciación del "
        "cuadro 2 (cláusula 7.3 y control A.3.17).")
    d.h1("Cuadro 1. Capacitación por cargo")
    d.tabla(["Cargo o rol", "Conocimientos y habilidades necesarios", "Capacitación necesaria",
             "Registro de implementación", "¿Se lograron los objetivos?", "Evaluación"], [
        ["Oficial y Coordinador de Datos Personales", "Ley N.° 29733 y reglamento, ISO/IEC 27701:2025, DPIA",
         "Curso de 40 h en protección de datos e ISO/IEC 27701", "PIMS-RG-06", "Sí (aprobado 30-10-2026)",
         "Examen ≥ 14/20"],
        ["OSCD y CSIRT UNSA", "Gestión de incidentes, controles A.3", "Taller de respuesta a brechas (16 h)",
         "PIMS-RG-06", "Sí (simulacro 17-11-2026)", "Simulacro"],
        ["Auditores internos", "ISO 19011, ISO/IEC 27701", "Curso de auditor interno (24 h)", "PIMS-RG-06",
         "Sí (3 de 3)", "Examen ≥ 14/20"],
        ["Personal de admisión, bienestar, salud y RR. HH.", "Datos sensibles, menores, derechos ARCO",
         "Taller práctico (4 h)", "PIMS-RG-06", "En curso (ola 1)", "Cuestionario"],
        ["Personal de la OTI", "Seguridad para datos personales (PIMS-PR-08)", "Taller técnico (8 h)",
         "PIMS-RG-06", "En curso", "Cuestionario"],
        ["Todo el personal con acceso a datos personales", "Política PIMS-POL-01 y deberes de confidencialidad",
         "Inducción virtual (1 h) y acuerdo de confidencialidad", "PIMS-RG-06", "En curso (34.6 %)",
         "Constancia de lectura"],
    ], anchos=[3.6, 4.2, 3.6, 2.2, 2.8, 2.6], tam=7)
    d.h1("Cuadro 2. Concienciación 2027")
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

    def fila(nombre, marcas):
        return [nombre] + ["X" if m in marcas else "" for m in meses]
    d.tabla(["Método de concienciación"] + meses, [
        fila("Correo institucional con consejos de privacidad", meses),
        fila("Afiches en oficinas que atienden al público", ["Mar", "Ago"]),
        fila("Charla en la inducción de nuevo personal", ["Mar", "Ago"]),
        fila("Semana de la protección de datos (28 de enero)", ["Ene"]),
        fila("Mensajes en el aula virtual para estudiantes", ["Mar", "Abr", "Ago", "Sep"]),
        fila("Simulacro de phishing para el personal", ["Jun", "Nov"]),
    ], anchos=[5] + [0.9] * 12, tam=7)
    d.h1("Responsabilidades")
    d.vinetas([
        "El Jefe(a) de la Unidad de Recursos Humanos coordina toda la capacitación y concienciación.",
        "La Unidad de Recursos Humanos lleva los registros de capacitación (PIMS-RG-06).",
        "El Oficial de Datos Personales evalúa el logro de los objetivos de capacitación.",
    ])
    d.p("Este documento es válido hasta el %s." % c.VALIDO_HASTA)
    d.p("El propietario de este documento es el Jefe(a) de la Unidad de Recursos Humanos, que lo archiva en el "
        "repositorio documental del PIMS y debe verificarlo y, si es necesario, actualizarlo cada año.")
    c.firmas(d, c.RRHH, c.ODP, "Presidente del CGTD")
    return c.guardar(d, "PIMS-PL-02_Plan_de_capacitacion_y_concienciacion.docx")


# =============================================================================== RG-06 (Agente 8)
def rg06():
    d = c.nuevo(pp.PLANTILLA_PROCEDIMIENTO, "PIMS-RG-06",
                "Registro de competencias, formación y acuerdos de confidencialidad",
                "Registro de perfiles de competencia, capacitaciones realizadas y acuerdos firmados",
                revisor=c.ODP)
    c.objetivo(d,
               "Este registro conserva la evidencia de la competencia del personal del PIMS (cláusula 7.2), de "
               "la formación y concienciación realizadas (7.3, A.3.17) y de los acuerdos de confidencialidad "
               "firmados (A.3.18).",
               "Contiene cifras agregadas por rol; las listas nominales están en la Unidad de Recursos Humanos "
               "con nivel Restringido.",
               "Lo usan la Unidad de Recursos Humanos, el Oficial de Datos Personales y el equipo auditor.")
    c.referencias(d, ["PIMS-PL-02", "PIMS-POL-01", "Reglamento General de Trabajo (RCU N.° 348-2011)"])
    d.h1("Perfiles de competencia (7.2)")
    d.tabla(["Rol", "Formación requerida", "Experiencia", "Personas", "Cumplen"], [
        ["Oficial de Datos Personales", "Abogado; curso en protección de datos", "3 años en gestión pública", "1",
         "1"],
        ["Coordinador de Datos Personales", "Profesional; curso en ISO/IEC 27701", "2 años", "1", "1"],
        ["OSCD", "Ingeniero; formación en seguridad de la información", "3 años en TI", "1", "1"],
        ["Auditores internos", "Curso de auditor interno ISO 19011 / 27701", "1 auditoría como observador", "4",
         "3 (1 en formación)"],
        ["Equipos de los agentes del PIMS", "Inducción PIMS (8 h)", "—", "32", "32"],
    ], anchos=[4, 5, 3, 1.6, 2.4], tam=8)
    d.h1("Capacitaciones realizadas (7.2, 7.3, A.3.17)")
    d.tabla(["Código", "Actividad", "Fecha", "Dirigida a", "Asistentes", "Aprobados"], [
        ["CAP-2026-01", "Curso de protección de datos e ISO/IEC 27701 (40 h)", "06-10 al 30-10-2026",
         "ODP, CDP, OSCD", "3", "3"],
        ["CAP-2026-02", "Curso de auditor interno (24 h)", "19-10 al 23-10-2026", "Auditores internos", "4", "3"],
        ["CAP-2026-03", "Inducción PIMS para los equipos de los agentes (8 h)", "03-11-2026", "Equipos de agentes",
         "32", "32"],
        ["CAP-2026-04", "Taller de datos sensibles y derechos ARCO (4 h), ola 1", "09-11 al 13-11-2026",
         "Admisión, bienestar, salud, RR. HH.", "86", "81"],
        ["CAP-2026-05", "Simulacro de brecha", "17-11-2026", "CSIRT UNSA", "9", "—"],
        ["CAP-2026-06", "Inducción virtual en la política de privacidad (1 h)", "Desde 10-11-2026",
         "Todo el personal con acceso a datos", "180", "180"],
    ], anchos=[2, 5.4, 2.6, 3.4, 1.4, 1.2], tam=8)
    d.h1("Constancias y acuerdos de confidencialidad (7.3, A.3.18)")
    d.tabla(["Grupo", "Personal con acceso a datos personales", "Constancia de conocimiento de la política",
             "Acuerdo de confidencialidad firmado"], [
        ["Dirección de Admisión", "60", "48", "45"],
        ["Dirección de Bienestar Universitario y Unidad de Salud", "70", "38", "36"],
        ["Unidad de Recursos Humanos", "40", "36", "36"],
        ["OTI", "50", "30", "28"],
        ["Resto de unidades", "300", "28", "25"],
        ["Total", "520", "180 (34.6 %)", "170 (32.7 %)"],
    ], anchos=[5, 3.6, 3.8, 3.6], tam=8)
    d.p("La meta es 100 % de acuerdos firmados al 31-03-2027 (PIMS-PL-01) y 80 % de personal capacitado al "
        "31-07-2027 (OBJ-03).")
    c.registros(d, [
        ["Listas de asistencia y evaluaciones", "Unidad de Recursos Humanos", c.RRHH, "Nivel Restringido",
         "5 años"],
        ["Acuerdos de confidencialidad firmados", "Legajo personal", c.RRHH, "Nivel Restringido",
         "Relación laboral + 5 años"],
    ])
    c.validez(d, "PIMS-RG-06", ["personal con acceso a datos personales sin acuerdo firmado;",
                                "roles del PIMS sin perfil de competencia."])
    c.firmas(d, c.RRHH, c.ODP, "Presidente del CGTD")
    return c.guardar(d, "PIMS-RG-06_Registro_de_competencias_y_formacion.docx")


def generar():
    return [pr05(), pr07(), pr06(), rg04(), pl02(), rg06()]
