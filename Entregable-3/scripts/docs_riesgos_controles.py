# -*- coding: utf-8 -*-
"""Documentos de los Agentes 1 (inventario), 2 (riesgos) y 3 (controles y SoA):
RG-02, PR-09, MT-01, IN-01 (+ cuadros .xlsx de los apéndices 1 y 2), RG-03, PL-01 y PR-08."""

import os

import comun_otros_grupos as c
import datos_pims_unsa as du
import lista_maestra_pims as lm
import plantillas_pims as pp

TRAT = {t[0]: t for t in du.TRATAMIENTOS}


# =============================================================================== RG-02 (Agente 1)
def rg02():
    d = c.nuevo(pp.PLANTILLA_PROCEDIMIENTO, "PIMS-RG-02",
                "Inventario y registro de actividades de tratamiento de datos personales",
                "Inventario inicial a partir de los bancos de datos de la Política de Privacidad y del ROF")
    c.objetivo(d,
               "Este registro documenta las actividades de tratamiento de datos personales de la UNSA como "
               "responsable del tratamiento: finalidad, base legal, categorías de datos y de titulares, "
               "destinatarios, transferencias y plazos de conservación (controles A.1.2.2, A.1.2.3, A.1.2.9 y "
               "A.1.5.4 de ISO/IEC 27701:2025). Delimita además el alcance del PIMS (cláusula 4.3).",
               "Comprende los bancos de datos declarados en la Política de Privacidad de la UNSA. Los volúmenes "
               "son estimaciones de la simulación.",
               "Lo usan el Coordinador y el Oficial de Datos Personales, los dueños de proceso, el equipo del "
               "Agente 2 para evaluar riesgos y el equipo auditor.")
    c.referencias(d, ["Política de Privacidad de la UNSA (bancos de datos y finalidades)",
                      "ROF de la UNSA (RCU N.° 0306-2022)", "PIMS-PR-09 (conservación y eliminación)",
                      "PIMS-RG-04 (encargados y transferencias)"])
    d.h1("Actividades de tratamiento")
    d.tabla(["ID", "Actividad", "Banco de datos", "Unidad responsable", "Titulares", "Finalidad", "Base legal"],
            [[t[0], t[1], t[2], t[3], t[4], t[5], t[6]] for t in du.TRATAMIENTOS],
            anchos=[0.9, 2.6, 1.8, 2.6, 2.4, 3.2, 2.9], tam=7)
    d.h1("Datos, destinatarios y conservación")
    d.tabla(["ID", "Categorías de datos", "Datos sensibles", "Volumen anual", "Conservación", "Encargados",
             "Destinatarios por ley", "Transf. internacional", "DPIA"],
            [[t[0], t[7], t[8], t[9], t[10], ", ".join(t[11]) or "—", t[12], t[13], t[14]]
             for t in du.TRATAMIENTOS], anchos=[0.9, 2.8, 1.6, 1.4, 2, 1.4, 2.2, 1.6, 2.1], tam=7)
    d.p("Los encargados (E01–E07) están en PIMS-RG-04 con su contrato. Los tratamientos marcados con DPIA "
        "se evaluaron en PIMS-IN-01.")
    d.h1("Flujos de datos y activos de soporte")
    d.tabla(["Tratamiento", "Recogida", "Sistema o archivo", "Salidas"], [
        ["T01 Admisión", "Formulario web de inscripción; pago en banco (E01)", "Sistema de admisión (OTI); "
         "lectora óptica (E04)", "Resultados publicados; SUNEDU"],
        ["T02 Registro académico", "Matrícula web", "Sistema académico; correo y aula virtual en la nube (E02)",
         "Constancias; SUNEDU, MINEDU"],
        ["T03 Bienestar", "Ficha socioeconómica (papel, en digitalización)", "Archivo de la Dirección de "
         "Bienestar", "Padrón de beneficiarios"],
        ["T04 Salud", "Atención presencial", "Sistema de historias clínicas; laboratorio externo (E05)",
         "Informes al titular"],
        ["T05 Recursos humanos", "Legajo y planilla", "Sistema de planillas (E06)", "SUNAT, EsSalud, AFP, MEF"],
        ["T07 Videovigilancia", "Cámaras del campus", "Grabadores (E03)", "Policía o Fiscalía a requerimiento"],
    ], anchos=[3, 4.5, 5, 3.5], tam=8)
    c.registros(d, [["Versiones del inventario", "Repositorio documental del PIMS", c.CDP,
                     "Nivel Confidencial; versiones según PIMS-PR-01", "5 años desde que se reemplazan"]])
    c.validez(d, "PIMS-RG-02", ["tratamientos detectados en auditoría que no figuran en el inventario;",
                                "tratamientos sin finalidad, base legal o plazo de conservación."])
    c.firmas(d, c.CDP, c.ODP, "Presidente del CGTD")
    return c.guardar(d, "PIMS-RG-02_Inventario_de_actividades_de_tratamiento.docx")


# =============================================================================== PR-09 (Agente 1)
def pr09():
    d = c.nuevo(pp.PLANTILLA_PROCEDIMIENTO, "PIMS-PR-09",
                "Procedimiento de minimización, calidad, conservación y eliminación de datos personales",
                "Documento nuevo para los controles A.1.4 (privacidad desde el diseño y por defecto)")
    c.objetivo(d,
               "Este procedimiento asegura que la UNSA recoja y trate solo los datos personales necesarios, "
               "los mantenga exactos, los conserve el tiempo justo y los elimine de forma segura (controles "
               "A.1.4.2 a A.1.4.10 de ISO/IEC 27701:2025), como parte del control operacional (8.1).",
               "Se aplica a todas las actividades de PIMS-RG-02, en cualquier soporte.",
               "Lo usan los dueños de proceso, la OTI, la Unidad de Archivo Central y el Coordinador de Datos "
               "Personales.")
    c.referencias(d, ["Ley N.° 29733, principios de finalidad, proporcionalidad y calidad",
                      "PIMS-RG-02", "PIMS-PR-08 (eliminación segura de equipos y medios)"])
    d.h1("Reglas")
    d.tabla(["Control", "Regla en la UNSA", "Quién la aplica"], [
        ["A.1.4.2 Limitar la recogida", "Cada formulario pide solo los campos necesarios para la finalidad "
         "declarada; el CDP revisa todo formulario nuevo antes de publicarlo.", "Dueño de proceso y CDP"],
        ["A.1.4.3 Limitar el tratamiento", "Los datos no se usan para otra finalidad sin nueva base legal o "
         "consentimiento.", "Dueño de proceso"],
        ["A.1.4.4 Exactitud y calidad", "El titular puede actualizar sus datos en línea; las áreas corrigen en "
         "10 días hábiles los errores comunicados (PIMS-PR-05).", "Dueño de proceso"],
        ["A.1.4.5 Objetivos de minimización", "Meta: publicar resultados solo con código de postulante; "
         "seudonimizar los datos de investigación.", "Director(a) de Admisión; Dirección de Investigación"],
        ["A.1.4.6 Desidentificación y supresión", "Al terminar la finalidad los datos se eliminan o se "
         "anonimizan para estadística.", "Dueño de proceso con la OTI"],
        ["A.1.4.7 Archivos temporales", "Exportaciones y archivos temporales se borran en 7 días; las carpetas "
         "compartidas se revisan cada mes.", "Unidad de Sistemas de Información"],
        ["A.1.4.8 Conservación", "Plazos de la tabla siguiente.", "Unidad de Archivo Central"],
        ["A.1.4.9 Eliminación", "Papel: trituración con acta; digital: borrado seguro o destrucción del medio "
         "(PIMS-PR-08).", "Unidad de Archivo Central y OTI"],
        ["A.1.4.10 Controles de transmisión", "Envíos con datos sensibles solo cifrados o por canales "
         "institucionales; prohibido usar correos personales.", "Todo el personal"],
    ], anchos=[3.6, 9, 3.4], tam=8)
    d.h1("Plazos de conservación")
    d.tabla(["Tratamiento", "Plazo", "Acción al vencer"],
            [[t[0] + " " + t[1], t[10], "Eliminación segura o anonimización"] for t in du.TRATAMIENTOS],
            anchos=[6.5, 5, 4.5], tam=8)
    d.h1("Procedimiento de eliminación")
    d.vinetas([
        "Cada semestre el dueño del proceso identifica los registros con plazo vencido.",
        "El Coordinador de Datos Personales verifica que no exista una obligación legal de conservarlos.",
        "La Secretaría General autoriza la eliminación (normas del Sistema Nacional de Archivos).",
        "Se elimina y se firma el acta de eliminación (fecha, registros, método, responsables).",
    ])
    c.registros(d, [
        ["Actas de eliminación", "Unidad de Archivo Central y repositorio documental", "Jefe(a) de la Unidad de "
         "Archivo Central", "Nivel Uso interno", "10 años"],
        ["Revisiones de formularios", "Repositorio documental", c.CDP, "Versiones según PIMS-PR-01", "5 años"],
    ])
    c.validez(d, "PIMS-PR-09", ["registros conservados más allá de su plazo;",
                                "formularios publicados sin revisión del CDP."])
    c.firmas(d, c.CDP, c.ODP, "Presidente del CGTD")
    return c.guardar(d, "PIMS-PR-09_Minimizacion_conservacion_y_eliminacion.docx")


# =============================================================================== MT-01 (Agente 2)
def mt01():
    d = c.nuevo(pp.PLANTILLA_METODOLOGIA, "PIMS-MT-01", "Metodología de evaluación y tratamiento de riesgos de privacidad",
                "Adaptación de la plantilla «Metodología de evaluación y tratamiento de riesgos» (ISO/IEC "
                "27001:2013) a los riesgos de privacidad de ISO/IEC 27701:2025 y a la UNSA",
                revisor=c.OSCD)
    c.objetivo(d,
               "Esta metodología define cómo la UNSA evalúa y trata los riesgos de privacidad, es decir, los "
               "riesgos para los titulares de los datos personales y para la UNSA, según las cláusulas 6.1.1, "
               "6.1.2, 6.1.3, 8.2 y 8.3 de ISO/IEC 27701:2025, y cuándo hace una evaluación de impacto en la "
               "privacidad (DPIA, control A.1.2.6).",
               "Se aplica a todo el alcance del PIMS (PIMS-MA-01) y a cada actividad de PIMS-RG-02.",
               "La usan los propietarios de riesgos, el equipo del Agente 2, el Oficial de Datos Personales y "
               "el OSCD.")
    c.referencias(d, ["ISO/IEC 27701:2025, cláusulas 6.1, 8.2 y 8.3, y control A.1.2.6",
                      "PIMS-RG-02 Inventario de actividades de tratamiento",
                      "PIMS-RG-03 Declaración de aplicabilidad", "PIMS-PL-01 Plan de tratamiento de riesgos"])
    d.h1("Metodología de evaluación y tratamiento de riesgos")
    d.h2("Riesgos y oportunidades del PIMS (6.1.1)")
    d.p("Al planificar el PIMS se consideran las cuestiones del contexto y los requisitos de las partes "
        "interesadas de PIMS-MA-01. Los riesgos del sistema (p. ej., falta de presupuesto o rotación del "
        "personal clave) y las oportunidades (automatización con agentes, convenios de auditoría) se "
        "registran en PIMS-IN-01 y sus acciones en PIMS-PL-01; su eficacia se evalúa con los indicadores "
        "de PIMS-PR-04.")
    d.h2("Evaluación de riesgos")
    d.h3("El proceso")
    d.p("La evaluación se registra en el Cuadro de evaluación de riesgos (Apéndice 1). La realizan los "
        "propietarios de riesgos con el equipo del Agente 2, por entrevistas y revisión de documentos, al "
        "menos una vez al año y cuando hay cambios significativos.")
    d.h3("Activos, amenazas y vulnerabilidades")
    d.p("La unidad de análisis es la **actividad de tratamiento** de PIMS-RG-02 y sus activos de soporte "
        "(sistemas, archivos, personas, encargados). Para cada activo se identifican las amenazas a los "
        "titulares (acceso no autorizado, uso para otra finalidad, conservación excesiva, inexactitud, "
        "transferencia sin garantías, imposibilidad de ejercer derechos) y las vulnerabilidades que las "
        "permiten.")
    d.h3("Identificación de los propietarios de riesgos")
    d.p("El propietario del riesgo es el jefe de la unidad responsable de la actividad de tratamiento "
        "(columna «Unidad responsable» de PIMS-RG-02).")
    d.h3("Consecuencias y probabilidad")
    d.tabla(["Consecuencia", "Valor", "Criterio (titulares y UNSA)"], [
        ["Baja", "0", "Molestia menor para el titular; sin datos sensibles; sin incumplimiento legal relevante"],
        ["Media", "1", "Afecta derechos de pocos titulares o expone datos no sensibles; posible observación "
         "de la Autoridad"],
        ["Alta", "2", "Datos sensibles o de menores, muchos titulares, daño material o moral, o sanción grave"],
    ], anchos=[2.5, 1.5, 12])
    d.tabla(["Probabilidad", "Valor", "Criterio"], [
        ["Baja", "0", "Controles adecuados; no ha ocurrido en los últimos 3 años"],
        ["Media", "1", "Controles parciales; ocurrió alguna vez o hay indicios"],
        ["Alta", "2", "Sin controles o ya ocurre"],
    ], anchos=[2.5, 1.5, 12])
    d.p("**Nivel de riesgo = consecuencia + probabilidad** (de 0 a 4).")
    d.h2("Criterios para la aceptación de riesgos")
    d.p("Los niveles 0, 1 y 2 son aceptables; los niveles 3 y 4 no son aceptables y deben tratarse. La "
        "aceptación de un riesgo residual no elimina las obligaciones legales de la Ley N.° 29733.")
    d.h2("Evaluación de impacto en la privacidad (DPIA)")
    d.p("Se hace una DPIA, antes de iniciar o cambiar el tratamiento, cuando se presenta al menos uno de "
        "estos criterios: datos sensibles (salud, socioeconómicos, biométricos) a gran escala; datos de "
        "menores de edad; videovigilancia sistemática; decisiones automatizadas con efectos sobre el "
        "titular; transferencias internacionales; nuevas tecnologías. La firma el Oficial de Datos "
        "Personales y su resultado se incluye en PIMS-IN-01.")
    d.h2("Tratamiento del riesgo")
    d.p("Para los riesgos de nivel 3 y 4 se elige una o más opciones (Cuadro de tratamiento, Apéndice 2):")
    d.vinetas([
        "**1. Elección de controles** de los Anexos A.1 y A.3 de ISO/IEC 27701:2025 u otros controles;",
        "**2. Transferencia** a terceros mediante contrato (el responsable sigue respondiendo ante el titular);",
        "**3. Evitar el riesgo** dejando de realizar el tratamiento o la parte que lo causa;",
        "**4. Aceptación del riesgo**, solo si el costo de las demás opciones es desproporcionado y el "
        "propietario lo acepta por escrito.",
    ])
    d.p("Tras elegir controles se estima el riesgo residual con la misma escala.")
    d.h2("Revisiones periódicas")
    d.p("Los propietarios revisan sus riesgos una vez al año y cuando hay incidentes, cambios de sistemas o "
        "de normativa; el equipo del Agente 2 actualiza los cuadros y PIMS-IN-01.")
    d.h2("Declaración de aplicabilidad y Plan de tratamiento del riesgo")
    d.p("El Oficial de Seguridad y Confianza Digital documenta en la Declaración de aplicabilidad "
        "(PIMS-RG-03) los controles aplicables, su justificación y su estado. Los propietarios de riesgos "
        "aceptan los riesgos residuales en la revisión por la dirección (PIMS-AC-01). El OSCD prepara el "
        "Plan de tratamiento (PIMS-PL-01) con responsables, recursos y plazos.")
    d.h2("Informes")
    d.p("El Oficial de Datos Personales documenta los resultados en PIMS-IN-01 y el OSCD informa el avance "
        "del plan cada trimestre al CGTD (PIMS-IN-03).")
    c.registros(d, [
        ["Cuadro de evaluación de riesgos (Apéndice 1)", "Repositorio documental (anexo de PIMS-IN-01)",
         c.ODP, "Nivel Confidencial", "5 años"],
        ["Cuadro de tratamiento de riesgos (Apéndice 2)", "Repositorio documental (anexo de PIMS-IN-01)",
         c.OSCD, "Nivel Confidencial", "5 años"],
        ["Informe de evaluación y tratamiento y DPIA (PIMS-IN-01)", "Repositorio documental", c.ODP,
         "Nivel Confidencial; huella SHA-256", "5 años"],
    ])
    c.validez(d, "PIMS-MT-01", [
        "incidentes ocurridos que no estaban incluidos en la evaluación de riesgos;",
        "riesgos no aceptables sin tratamiento;",
        "errores de evaluación por definiciones poco claras.",
    ])
    d.h1("Apéndices")
    d.vinetas(["Apéndice 1: Cuadro de evaluación de riesgos (PIMS-IN-01_Apendice_1.xlsx)",
               "Apéndice 2: Cuadro de tratamiento de riesgos (PIMS-IN-01_Apendice_2.xlsx)",
               "Apéndice 3: Informe sobre evaluación y tratamiento de riesgos (PIMS-IN-01)"])
    c.firmas(d, c.ODP, c.OSCD, "Presidente del CGTD")
    return c.guardar(d, "PIMS-MT-01_Metodologia_de_riesgos_de_privacidad.docx")


# =============================================================================== IN-01 (Agente 2)
def in01():
    d = c.nuevo(pp.PLANTILLA_INFORME_RIESGOS, "PIMS-IN-01",
                "Informe de evaluación y tratamiento de riesgos de privacidad y DPIA",
                "Adaptación del «Apéndice 3: Informe sobre evaluación y tratamiento de riesgos» a ISO/IEC "
                "27701:2025, con las DPIA de los tratamientos de alto riesgo", revisor=c.OSCD)
    c.objetivo(d,
               "Este informe presenta los resultados de la evaluación y del tratamiento de los riesgos de "
               "privacidad de la UNSA (cláusulas 6.1.2, 8.2 y 8.3 de ISO/IEC 27701:2025) y las evaluaciones de "
               "impacto en la privacidad de los tratamientos de alto riesgo (control A.1.2.6).",
               "La evaluación se aplicó a las actividades de PIMS-RG-02, según PIMS-MT-01.",
               "Está dirigido a la alta dirección, al CGTD, al Oficial de Datos Personales, al OSCD y a los "
               "propietarios de riesgos.")
    c.referencias(d, ["PIMS-MT-01 Metodología de evaluación y tratamiento de riesgos de privacidad",
                      "PIMS-MA-01 (alcance)", "PIMS-POL-01", "PIMS-RG-02"])
    d.h1("Proceso de evaluación y tratamiento de riesgos")
    d.h2("Alcance y periodo")
    d.p("La evaluación se realizó entre el 02-11-2026 y el 13-11-2026 en las unidades responsables de las "
        "actividades T01 a T10 de PIMS-RG-02. La dirigió el Oficial de Datos Personales con el equipo del "
        "Agente 2; participaron los propietarios de riesgos y el OSCD. La información se obtuvo de "
        "entrevistas, de las resoluciones públicas de la UNSA y del expediente de evidencias.")
    d.h2("Resumen de la metodología aplicada")
    d.vinetas([
        "Se identificaron las actividades de tratamiento y sus activos de soporte.",
        "Se identificaron amenazas para los titulares y vulnerabilidades.",
        "Se valoraron consecuencia y probabilidad de 0 a 2; nivel = suma (0 a 4).",
        "Los niveles 3 y 4 se consideraron no aceptables y se trataron con controles de A.1 y A.3.",
        "Se estimó el riesgo residual y los propietarios lo aceptaron.",
    ])
    d.h1("Resultados de la evaluación de riesgos (8.2)")
    filas = []
    for r in du.RIESGOS:
        n = du.nivel(r[6], r[7])
        filas.append([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], "%d%s" % (n, "" if du.aceptable(n) else " ✗")])
    d.tabla(["ID", "Trat.", "Activo", "Amenaza", "Vulnerabilidad", "Propietario", "C", "P", "Nivel"], filas,
            anchos=[0.9, 0.9, 2.8, 2.4, 3.2, 2.6, 0.6, 0.6, 1], tam=7)
    no_acept = sum(1 for r in du.RIESGOS if not du.aceptable(du.nivel(r[6], r[7])))
    d.p("%d de %d riesgos no son aceptables (nivel 3 o 4)." % (no_acept, len(du.RIESGOS)))
    d.h1("Resultados del tratamiento de riesgos (8.3)")
    filas = []
    for r in du.RIESGOS:
        n2 = du.nivel(r[11], r[12])
        filas.append([r[0], du.nivel(r[6], r[7]), r[9], r[10], n2, "Aceptado por el propietario"
                      if du.aceptable(n2) else "Requiere más tratamiento"])
    d.tabla(["ID", "Nivel inicial", "Opción", "Medio de implementación", "Nivel residual", "Decisión"], filas,
            anchos=[0.9, 1.4, 2.8, 6.5, 1.4, 3], tam=7)
    d.p("El avance de las acciones se registra en el Plan de tratamiento PIMS-PL-01. Los riesgos residuales "
        "se aceptaron en la revisión por la dirección PIMS-AC-01 (acuerdo AC-01-04).")
    d.h1("Evaluaciones de impacto en la privacidad (A.1.2.6)")
    for tid, extra in (("T01", "El examen de admisión se califica con lectora óptica: es una decisión "
                                "automatizada, por lo que el postulante puede pedir revisión humana (PIMS-PR-05)."),
                       ("T03", "Los datos socioeconómicos de la familia se recogen con consentimiento expreso y "
                               "solo para determinar el beneficio."),
                       ("T04", "Las historias clínicas se rigen además por la Ley General de Salud.")):
        t = TRAT[tid]
        d.h2("DPIA %s – %s" % (tid, t[1]))
        d.tabla(["Aspecto", "Resultado"], [
            ["Necesidad y proporcionalidad", "Finalidad: %s. Base legal: %s." % (t[5], t[6])],
            ["Datos y titulares", "%s. Sensibles: %s. Titulares: %s (%s al año)." % (t[7], t[8], t[4], t[9])],
            ["Riesgos para los titulares", ", ".join(r[0] + " " + r[3].lower() for r in du.RIESGOS
                                                      if r[1] == tid) or "Los del cuadro de evaluación"],
            ["Medidas", "; ".join(r[10] for r in du.RIESGOS if r[1] == tid) or "Controles de PIMS-PR-08"],
            ["Observación", extra],
            ["Conclusión", "El tratamiento puede continuar con las medidas del plan PIMS-PL-01; riesgo residual "
                           "aceptable. Firmado por el Oficial de Datos Personales (firma simulada) el 13-11-2026."],
        ], anchos=[4, 12], tam=8)
    d.h1("Documentos utilizados")
    d.vinetas(["Cuadro de evaluación de riesgos (Apéndice 1, PIMS-IN-01_Apendice_1_Cuadro_de_evaluacion.xlsx)",
               "Cuadro de tratamiento de riesgos (Apéndice 2, PIMS-IN-01_Apendice_2_Cuadro_de_tratamiento.xlsx)",
               "PIMS-RG-02, PIMS-RG-03 y PIMS-PL-01"])
    c.registros(d, [["DPIA firmadas", "Repositorio documental", c.ODP, "Nivel Confidencial; SHA-256",
                     "Mientras exista el tratamiento + 5 años"]])
    c.validez(d, "PIMS-IN-01", ["riesgos materializados que no figuraban en el informe;",
                                "tratamientos de alto riesgo sin DPIA."])
    c.firmas(d, c.ODP, c.OSCD, "Presidente del CGTD")
    return c.guardar(d, "PIMS-IN-01_Informe_de_riesgos_de_privacidad_y_DPIA.docx")


def _periodo(ws):
    for celda in ws[1]:
        if isinstance(celda.value, str) and "[fecha]" in celda.value:
            celda.value = ("UNSA – PIMS ISO/IEC 27701:2025 · Implementado desde el 02-11-2026 hasta el "
                           "13-11-2026 (simulación)")


def cuadros_xlsx():
    """Llena los Apéndices 1 y 2 (.xlsx) del docente con los riesgos de la UNSA."""
    import openpyxl
    rutas = []
    wb = openpyxl.load_workbook(pp.PLANTILLA_CUADRO_EVALUACION)
    ws = wb["Cuadro de evaluación de riesgos"]
    _periodo(ws)
    for i, r in enumerate(du.RIESGOS):
        fila = 4 + i
        for col, v in zip("ABCDEFGHJ", [i + 1, "%s %s – %s" % (r[1], TRAT[r[1]][1], r[2]),
                                        TRAT[r[1]][3], r[3], r[4], r[5], r[6], r[7], r[8]]):
            ws["%s%d" % (col, fila)] = v
    ruta = os.path.join(c.SALIDA, "anexos", "PIMS-IN-01_Apendice_1_Cuadro_de_evaluacion.xlsx")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    wb.save(ruta)
    rutas.append(ruta)

    wb = openpyxl.load_workbook(pp.PLANTILLA_CUADRO_TRATAMIENTO)
    ws = wb["Cuadro tratamiento riesgos"]
    _periodo(ws)
    for i, r in enumerate(du.RIESGOS):
        fila = 5 + i
        for col, v in zip("ABCDEFGHJKLM", [i + 1, "%s %s – %s" % (r[1], TRAT[r[1]][1], r[2]), TRAT[r[1]][3],
                                           r[3], r[4], r[5], r[6], r[7], r[9], r[10], r[11], r[12]]):
            ws["%s%d" % (col, fila)] = v
        ws["I%d" % fila] = "=G%d+H%d" % (fila, fila)
    wc = wb["Controles"]
    wc.delete_rows(1, wc.max_row)
    wc["A1"] = "Controles de ISO/IEC 27701:2025 (Anexo A.1 responsable y A.3 seguridad)"
    for i, (ref, tit) in enumerate(lm.CONTROLES_A1 + lm.CONTROLES_A3, 3):
        wc["A%d" % i] = "%s %s" % (ref, tit)
    ruta = os.path.join(c.SALIDA, "anexos", "PIMS-IN-01_Apendice_2_Cuadro_de_tratamiento.xlsx")
    wb.save(ruta)
    rutas.append(ruta)
    return rutas


# =============================================================================== RG-03 (Agente 3)
IMPLEMENTADOS = {"A.1.2.2", "A.1.2.3", "A.1.2.9", "A.1.3.2", "A.1.3.7", "A.1.3.9", "A.1.3.10", "A.1.4.4",
                 "A.1.5.5", "A.3.3", "A.3.4", "A.3.11", "A.3.12", "A.3.13", "A.3.14", "A.3.15", "A.3.16",
                 "A.3.24"}
EN_CURSO = {"A.1.2.4", "A.1.2.5", "A.1.2.7", "A.1.4.2", "A.1.4.8", "A.1.5.2", "A.1.5.3", "A.1.5.4", "A.3.9",
            "A.3.17", "A.3.18", "A.3.23", "A.3.25"}
JUSTIFICACION = {
    "A.1.2.8": "Convenios de investigación con otras universidades en los que se decide en conjunto",
    "A.1.3.11": "El examen de admisión se califica de forma automatizada (lectora óptica)",
    "A.1.5.2": "Correo, aula virtual y bases bibliográficas en la nube fuera del Perú",
    "A.1.5.3": "Correo, aula virtual y bases bibliográficas en la nube fuera del Perú",
    "A.3.30": "Parte del software académico se contrata a terceros",
    "A.3.31": "Pruebas de sistemas que usan copias de datos reales",
}


def rg03():
    d = c.nuevo(pp.PLANTILLA_PROCEDIMIENTO, "PIMS-RG-03", "Declaración de aplicabilidad (SoA)",
                "SoA inicial a partir de PIMS-IN-01: controles A.1 y A.3 aplicables y exclusión de A.2",
                aprobador_corto="CGTD", revisor=c.ODP)
    c.objetivo(d,
               "Esta declaración indica qué controles del Anexo A de ISO/IEC 27701:2025 aplica la UNSA, por qué "
               "se incluyen o excluyen y su estado de implementación (cláusula 6.1.3 d) a e)).",
               "Se aplica al alcance de PIMS-MA-01, donde la UNSA es responsable del tratamiento.",
               "La usan el OSCD, el Oficial de Datos Personales, el CGTD y el equipo auditor.")
    c.referencias(d, ["PIMS-MT-01 y PIMS-IN-01", "PIMS-PL-01", "PIMS-RG-01 (documentos de cada control)"])
    d.h1("Criterios")
    d.vinetas([
        "Un control se **incluye** cuando trata un riesgo de PIMS-IN-01 o lo exige la Ley N.° 29733.",
        "**A.2 (encargado del tratamiento) se excluye completo:** la UNSA no trata datos personales por "
        "encargo de terceros dentro del alcance (PIMS-MA-01). Si en el futuro presta servicios como "
        "encargado, se revisará esta declaración.",
        "Estado: **Implementado** (documento aprobado y evidencia de operación), **En implementación** "
        "(actividad en PIMS-PL-01) o **Planificado**.",
    ])
    por_req = lm.documentos_por_requisito()

    def filas(controles):
        salida = []
        for ref, tit in controles:
            estado = ("Implementado" if ref in IMPLEMENTADOS else "En implementación" if ref in EN_CURSO
                      else "Planificado")
            salida.append([ref, tit, "Sí", JUSTIFICACION.get(ref, "Riesgos de PIMS-IN-01 y Ley N.° 29733"),
                           estado, ", ".join(por_req.get(ref, []))])
        return salida
    d.h1("Controles A.1 – Responsable del tratamiento")
    d.tabla(["Control", "Título", "Aplica", "Justificación", "Estado", "Documento"], filas(lm.CONTROLES_A1),
            anchos=[1.6, 4.4, 1, 4.2, 2.2, 2.6], tam=7)
    d.h1("Controles A.2 – Encargado del tratamiento")
    d.tabla(["Control", "Título", "Aplica", "Justificación", "Estado", "Documento"], [
        ["A.2.2 a A.2.5", "Todos los controles para encargados", "No", "La UNSA no actúa como encargado en el "
         "alcance del PIMS (PIMS-MA-01)", "No aplica", "—"]], anchos=[1.6, 4.4, 1, 4.2, 2.2, 2.6], tam=7)
    d.h1("Controles A.3 – Seguridad de la información")
    d.tabla(["Control", "Título", "Aplica", "Justificación", "Estado", "Documento"], filas(lm.CONTROLES_A3),
            anchos=[1.6, 4.4, 1, 4.2, 2.2, 2.6], tam=7)
    n = len(lm.CONTROLES_A1) + len(lm.CONTROLES_A3)
    imp = len(IMPLEMENTADOS)
    cur = len(EN_CURSO)
    d.p("Resumen: %d controles aplicables; %d implementados, %d en implementación y %d planificados. "
        "Controles A.2 excluidos." % (n, imp, cur, n - imp - cur))
    c.registros(d, [["Versiones de la SoA", "Repositorio documental", c.OSCD,
                     "Nivel Confidencial; versiones según PIMS-PR-01", "5 años"]])
    c.validez(d, "PIMS-RG-03", ["controles aplicados que no figuran en la SoA;",
                                "estados que no coinciden con la evidencia del expediente."])
    c.firmas(d, c.OSCD, c.ODP, "Presidente del CGTD")
    return c.guardar(d, "PIMS-RG-03_Declaracion_de_aplicabilidad.docx")


# =============================================================================== PL-01 (Agente 3)
def pl01():
    d = c.nuevo(pp.PLANTILLA_PLAN_TRATAMIENTO, "PIMS-PL-01",
                "Plan de tratamiento de riesgos de privacidad y control operacional",
                "Adaptación de la plantilla «Plan de tratamiento del riesgo» (ISO/IEC 27001:2013) a ISO/IEC "
                "27701:2025 con las acciones de PIMS-IN-01", aprobador_corto="CGTD", revisor=c.ODP,
                portada="simple")
    d.h1("Objetivo y alcance")
    d.p("Para cumplir los objetivos del PIMS (PIMS-PL-03) y tratar los riesgos no aceptables de PIMS-IN-01, la "
        "UNSA realizará las siguientes actividades (cláusulas 6.1.3 e) a g), 8.1 y 8.3 de ISO/IEC 27701:2025). "
        "Los propietarios de los riesgos aprobaron el plan y aceptaron el riesgo residual (PIMS-AC-01).")
    d.h1("Actividades")
    d.tabla(["Descripción de actividades", "Recursos generales y financieros", "Persona responsable",
             "Plazos de inicio y finalización", "Programas de capacitación y concienciación",
             "Método para evaluación de resultados", "Estado", "Riesgo"],
            [list(p) for p in du.PLAN], anchos=[5, 3.4, 3, 2.6, 2.8, 3.2, 2, 1.2], tam=7)
    d.h1("Control operacional (8.1)")
    d.p("Los procesos que tratan datos personales se operan con los procedimientos PIMS-PR-05 (derechos), "
        "PIMS-PR-06 (incidentes), PIMS-PR-07 (avisos y consentimiento), PIMS-PR-08 (seguridad) y PIMS-PR-09 "
        "(conservación). Los procesos contratados externamente se controlan con los contratos de PIMS-RG-04. "
        "Los cambios planificados se gestionan según PIMS-PL-03 (6.3) y, si afectan a un tratamiento de alto "
        "riesgo, requieren una DPIA previa.")
    d.h1("Seguimiento")
    d.p("El OSCD actualiza el estado de cada actividad cada mes y lo informa al CGTD cada trimestre en "
        "PIMS-IN-03. Una actividad vencida sin ejecutar se trata como no conformidad según PIMS-PR-02.")
    d.p("Este documento es válido hasta el %s." % c.VALIDO_HASTA)
    d.p("El propietario de este documento es el Oficial de Seguridad y Confianza Digital, que debe "
        "verificarlo y, si es necesario, actualizarlo cada trimestre y cuando cambie la evaluación de riesgos.")
    d.p("Al evaluar la eficacia y adecuación de este documento se tienen en cuenta los siguientes criterios: "
        "porcentaje de actividades ejecutadas en plazo y riesgos residuales que vuelven a ser no aceptables.")
    c.firmas(d, c.OSCD, c.ODP, "Presidente del CGTD")
    return c.guardar(d, "PIMS-PL-01_Plan_de_tratamiento_de_riesgos.docx")


# =============================================================================== PR-08 (Agente 3)
def pr08():
    d = c.nuevo(pp.PLANTILLA_PROCEDIMIENTO, "PIMS-PR-08",
                "Procedimiento de seguridad de la información para datos personales",
                "Políticas temáticas y medidas técnicas de seguridad para los controles A.3",
                revisor=c.ODP)
    c.objetivo(d,
               "Este procedimiento reúne las reglas de seguridad de la información que protegen los datos "
               "personales en la UNSA (controles A.3.3, A.3.5 a A.3.9 y A.3.18 a A.3.31 de ISO/IEC 27701:2025) "
               "y constituye el programa de seguridad documentado del PIMS.",
               "Se aplica a todos los sistemas, archivos, equipos y personas dentro del alcance del PIMS.",
               "Lo usan la OTI, el OSCD, el CSIRT UNSA, los dueños de proceso y todo el personal.")
    c.referencias(d, ["Guía de copias de seguridad y protocolo de respaldo de base de datos (OTI)",
                      "Plan de contingencia y SLA del data center (RCU N.° 0422-2026)",
                      "PIMS-PR-01 (clasificación de la información documentada)", "PIMS-PR-06"])
    d.h1("Reglas de seguridad")
    reglas = [
        ("A.3.3", "Este procedimiento y la política PIMS-POL-01 son las políticas de seguridad para datos "
                  "personales; se revisan cada año."),
        ("A.3.5 / A.3.6", "La información se clasifica en Público, Uso interno, Confidencial y Restringido "
                          "(PIMS-PR-01) y se etiqueta en el encabezado del documento o en la ficha del sistema."),
        ("A.3.7", "Datos Confidenciales o Restringidos solo se envían por canales institucionales cifrados; "
                  "las entregas a terceros constan en PIMS-RG-04."),
        ("A.3.8 / A.3.9", "Cuentas nominales; altas, cambios y bajas por solicitud del jefe de la unidad; "
                          "revisión trimestral de accesos a sistemas con datos personales."),
        ("A.3.18", "Todo el personal con acceso a datos personales firma un acuerdo de confidencialidad "
                   "(registro en PIMS-RG-06)."),
        ("A.3.19", "Escritorio y pantalla limpios; bloqueo automático a los 5 minutos."),
        ("A.3.20 / A.3.21", "Medios extraíbles cifrados; borrado seguro o destrucción con acta antes de "
                            "reutilizar o dar de baja equipos."),
        ("A.3.22", "Equipos institucionales con antivirus, actualizaciones y cifrado de disco en portátiles."),
        ("A.3.23", "Doble factor de autenticación en sistemas con datos sensibles o de menores (admisión, "
                   "salud, bienestar)."),
        ("A.3.24", "Respaldo diario incremental y semanal completo con copia fuera del centro de datos; "
                   "prueba de restauración trimestral con acta."),
        ("A.3.25", "Registro de accesos a datos personales conservado 1 año, en almacenamiento de solo "
                   "inserción e inalterable (requisito de A.3.14)."),
        ("A.3.26", "TLS 1.2 o superior en tránsito; cifrado AES-256 en reposo para datos Restringidos."),
        ("A.3.27 / A.3.28 / A.3.29", "Privacidad desde el diseño: todo sistema nuevo define requisitos de "
                                     "privacidad, pasa revisión de arquitectura y DPIA si corresponde."),
        ("A.3.30", "El desarrollo contratado incluye cláusulas de seguridad y confidencialidad y pruebas de "
                   "aceptación de seguridad."),
        ("A.3.31", "Las pruebas usan datos anonimizados o ficticios; está prohibido copiar datos reales a "
                   "entornos de prueba sin autorización del Oficial de Datos Personales."),
    ]
    d.tabla(["Control", "Regla"], [list(r) for r in reglas], anchos=[3, 13], tam=8)
    d.h1("Verificación")
    d.p("El OSCD verifica el cumplimiento cada semestre con una muestra de sistemas; la auditoría AUD-2027-002 "
        "del programa PIMS-PR-03 revisa los controles técnicos.")
    c.registros(d, [
        ["Revisiones de accesos", "Repositorio de la OTI", "Jefe(a) de la OTI", "Nivel Confidencial", "3 años"],
        ["Actas de pruebas de restauración", "Repositorio de la OTI", "Jefe(a) de la OTI", "Nivel Uso interno",
         "3 años"],
        ["Registros de acceso a datos personales", "Servidor de registros (solo inserción)", c.OSCD,
         "Inalterable; acceso de lectura para auditores", "1 año"],
    ])
    c.validez(d, "PIMS-PR-08", ["accesos sin revisión en el trimestre;", "pruebas de restauración fallidas;",
                                "incidentes causados por reglas no aplicadas."])
    c.firmas(d, c.OSCD, c.ODP, "Presidente del CGTD")
    return c.guardar(d, "PIMS-PR-08_Seguridad_de_la_informacion_para_datos_personales.docx")


def generar():
    return [rg02(), pr09(), mt01(), in01(), rg03(), pl01(), pr08()] + cuadros_xlsx()
