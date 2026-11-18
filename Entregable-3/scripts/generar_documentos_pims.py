# -*- coding: utf-8 -*-
"""
Genera los documentos PIMS del Grupo 6 (Agente de Evidencia y Auditoria) para la
implementacion simulada del PIMS en la UNSA, a partir de las plantillas ISO/IEC
27001:2013 del docente (Mensaje 2), corregidas y alineadas a ISO/IEC 27701:2025.

    python Entregable-3/scripts/generar_documentos_pims.py

Salida (Entregable-3/documentos-pims/generados/):
    PIMS-PR-01  Procedimiento de control de la informacion documentada y de los registros  (7.5, A.3.14 - D11)
    PIMS-PR-02  Procedimiento de no conformidades y acciones correctivas                  (10.2, 10.1 - D34)
    PIMS-FO-01  Formulario de no conformidades y acciones correctivas (en blanco)          (10.2 - D34)
    PIMS-PR-03  Procedimiento y programa de auditoria interna                             (9.2, A.3.15, A.3.16 - D33)
    PIMS-PR-04  Procedimiento de seguimiento, medicion, analisis y evaluacion             (9.1 - D32)

PR-03 y PR-04 no venian entre las plantillas: se construyen sobre la misma plantilla
de procedimiento para mantener el formato comun.
"""

import datetime as dt
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
E3 = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(E3, "agente"))

import lista_maestra_pims as lm  # noqa: E402
import plantillas_pims as pp  # noqa: E402

SALIDA = os.path.join(E3, "documentos-pims", "generados")
FECHA = dt.date(2026, 11, 17)
FECHA2 = dt.date(2026, 11, 18)        # documentos del Mensaje 3 (lista maestra completa)
VALIDO_HASTA = "17-11-2027"
VERSION = "1.1"

# ---- cargos reales de la UNSA (resoluciones publicas en docs-unsa/)
RECTOR = "Rector(a) de la UNSA"
CU = "Consejo Universitario"
CGTD = "Comité de Gobierno y Transformación Digital (CGTD, RR N.° 1000-2025)"
ODP = "Oficial de Datos Personales (Jefe de la Oficina de Asesoría Jurídica, RR N.° 0987-2025)"
ODP_CORTO = "Oficial de Datos Personales"
CDP = "Coordinador de Datos Personales"
OSCD = "Oficial de Seguridad y Confianza Digital (OSCD, RR N.° 1244-2025)"
OSCD_CORTO = "Oficial de Seguridad y Confianza Digital"
OTI = "Oficina de Tecnologías de la Información (OTI)"
CSIRT = "CSIRT UNSA (RR N.° 0503-2026)"
SG = "Secretaría General"
ODO = "Oficina de Desarrollo Organizacional (ODO)"
EQUIPO_AUDITOR = "Equipo auditor interno del PIMS"
AGENTE = "Agente de Evidencia y Auditoría (AUDITA-PIMS)"
REPOSITORIO = ("Repositorio documental del PIMS (base de datos PostgreSQL «pims_auditoria», tablas "
               "documentos, documentos_pims y evidencias)")

CREADO = "Coordinador de Datos Personales – Grupo 6, Agente de Evidencia y Auditoría"
APROBADO = "Comité de Gobierno y Transformación Digital (sesión simulada del 17-11-2026)"


def historial(descripcion_01):
    return [
        ("03-11-2026", "0.1", "Grupo 6 – Agente de Evidencia y Auditoría (borrador asistido por IA)",
         descripcion_01),
        ("10-11-2026", "0.2", CDP, "Revisión de cargos, plazos, registros y coherencia con los "
                                   "documentos de los otros agentes del PIMS"),
        ("17-11-2026", "1.0", ODP_CORTO, "Versión aprobada por el CGTD (aprobación simulada)"),
        ("17-11-2026", "1.1", CDP, "Corrección de forma: el pie de página conservaba el nombre, la "
                                   "versión y la licencia de la plantilla original"),
    ]


ADAPTACION = ("Adaptación de la plantilla ISO/IEC 27001:2013 a ISO/IEC 27701:2025 y a la UNSA")

REF_COMUNES = [
    "Norma ISO/IEC 27701:2025 – Seguridad de la información, ciberseguridad y protección de la "
    "privacidad – Sistemas de gestión de la información de privacidad – Requisitos y orientación",
    "Ley N.° 29733, Ley de Protección de Datos Personales, y su Reglamento aprobado por "
    "D.S. N.° 016-2024-JUS",
    "Política de Privacidad de la UNSA (publicada en unsa.edu.pe)",
]


def validez(d, propietario, criterios):
    d.h1("Validez y gestión de documentos")
    d.p("Este documento es válido hasta el %s." % VALIDO_HASTA)
    d.p("El propietario de este documento es el %s, que debe verificar y, si es necesario, "
        "actualizar el documento por lo menos una vez al año, y además cuando cambien la norma, la "
        "Ley N.° 29733 o su reglamento, la estructura orgánica de la UNSA o los resultados de "
        "auditoría lo justifiquen." % propietario)
    d.p("Al evaluar la eficacia y adecuación de este documento se tienen en cuenta los siguientes "
        "criterios (se miden según PIMS-PR-04):")
    d.vinetas(criterios)


# =============================================================================== PR-01
def pr01():
    d = pp.DocumentoPIMS(pp.PLANTILLA_CONTROL_DOC, "PIMS-PR-01",
                         "Procedimiento de control de la información documentada y de los registros",
                         version="1.2", fecha=FECHA2, creado_por=CREADO, aprobado_por=APROBADO,
                         historial=historial(ADAPTACION) + [
                             ("18-11-2026", "1.2", CDP, "La lista maestra pasa al registro PIMS-RG-01 "
                              "(listado completo de la información documentada con sus cláusulas y "
                              "controles); se agrega el tipo MA (manual) a la codificación")])

    d.h1("Objetivo, alcance y usuarios")
    d.p("El objetivo de este procedimiento es asegurar el control sobre la creación, identificación, "
        "revisión, aprobación, distribución, acceso, uso, almacenamiento, preservación, cambio, "
        "conservación y disposición de la información documentada (documentos y registros) del "
        "Sistema de Gestión de Privacidad de la Información (PIMS) de la UNSA, conforme a la "
        "cláusula 7.5 de ISO/IEC 27701:2025, y proteger los registros relacionados con el "
        "tratamiento de datos personales según el control A.3.14.")
    d.p("Se aplica a toda la información documentada del PIMS, sea creada dentro de la UNSA o de "
        "origen externo, en cualquier medio (electrónico, papel, audio o vídeo), y a los registros "
        "que se generan al tratar datos personales de postulantes, estudiantes, egresados, docentes, "
        "personal administrativo, proveedores y visitantes, en su rol de **responsable del "
        "tratamiento**.")
    d.p("Los usuarios de este documento son los integrantes del CGTD, el Oficial y el Coordinador de "
        "Datos Personales, el OSCD, la OTI, la Secretaría General, los dueños de procesos que tratan "
        "datos personales, el equipo auditor interno y los equipos que operan los agentes del PIMS.")

    d.h1("Documentos de referencia")
    d.vinetas(REF_COMUNES + [
        "ISO/IEC 27701:2025, cláusulas 7.5.1, 7.5.2 y 7.5.3, y control A.3.14 (protección de "
        "registros)",
        "Ley N.° 27806, Ley de Transparencia y Acceso a la Información Pública, y Directiva de "
        "Transparencia y Acceso a la Información Pública de la UNSA (RCU N.° 0748-2019 y "
        "RCU N.° 0309-2020)",
        "Directiva N.° 010-2021-ODO-SDI, procedimientos de organización, protección, conservación "
        "y acceso a documentos (RCU N.° 1163-2021)",
        "Guía para realizar copias de seguridad del Repositorio Institucional y protocolo de "
        "respaldo de base de datos (OTI)",
        "PIMS-PR-02 Procedimiento de no conformidades y acciones correctivas",
        "PIMS-PR-03 Procedimiento y programa de auditoría interna",
    ])

    d.h1("Términos y definiciones")
    d.tabla(["Término", "Definición en este procedimiento"], [
        ["Información documentada", "Información que la UNSA debe controlar y mantener, y el medio "
         "que la contiene (término de ISO/IEC 27000, al que remite ISO/IEC 27701:2025). Comprende "
         "documentos y registros."],
        ["Documento", "Información documentada que establece cómo se hace algo (política, "
         "procedimiento, metodología, plan, formulario en blanco). Se actualiza por versiones."],
        ["Registro", "Información documentada que evidencia resultados o actividades realizadas "
         "(formulario completado, acta, informe, bitácora, log). No se modifica: se corrige con "
         "un nuevo registro."],
        ["Registro de tratamiento de PII", "Registro que contiene o describe datos personales: "
         "inventario de tratamientos, solicitudes de derechos, logs de acceso, consentimientos, "
         "registros de incidentes (control A.3.14)."],
        ["Propietario del documento", "Cargo responsable de su contenido, revisión y "
         "actualización."],
        ["Expediente de evidencias", "Conjunto de evidencias del PIMS con huella SHA-256 y cadena "
         "de custodia que mantiene el Agente de Evidencia y Auditoría."],
    ], anchos=[4.5, 11.5])

    d.h1("Información documentada del PIMS")
    d.p("Según la cláusula 7.5.1, el PIMS de la UNSA incluye: a) la información documentada que "
        "exige ISO/IEC 27701:2025 y b) la que la UNSA determina necesaria para la eficacia del PIMS. "
        "Toda ella se inscribe en la **Lista maestra de información documentada (PIMS-RG-01)**, que "
        "mantiene el Coordinador de Datos Personales en el repositorio documental del PIMS.")
    d.p("La lista maestra completa (cada documento con las cláusulas y controles de ISO/IEC "
        "27701:2025 que lo exigen, el expediente de la guía de implementación, el equipo que lo "
        "elabora, su propietario y su nivel de confidencialidad) se mantiene en **PIMS-RG-01** y en "
        "la tabla lista_maestra_pims del repositorio. Este procedimiento no la repite para no tener "
        "dos versiones de la misma información. Resumen por equipo del PIMS:")
    por_equipo = {}
    for f in lm.filas():
        por_equipo.setdefault(f["equipo"], []).append(f)
    d.tabla(["Equipo del PIMS", "Documentos que elabora", "Expedientes de la guía"], [
        [eq, ", ".join(f["codigo"] for f in fs),
         ", ".join(sorted({x for f in fs for x in f["expedientes"]}, key=lambda x: int(x[1:])))]
        for eq, fs in por_equipo.items()], anchos=[4.5, 7.5, 4], tam=8)

    d.h1("Creación y actualización de la información documentada")
    d.p("Al crear o actualizar información documentada se asegura su identificación y descripción, "
        "su formato y medio, y su revisión y aprobación (cláusula 7.5.2).")
    d.h2("Identificación y descripción")
    d.p("Cada documento lleva en su portada una tabla de control con: **Código, Versión, Fecha de "
        "la versión, Creado por, Aprobado por y Nivel de confidencialidad**, seguida del "
        "**Historial de modificaciones** (fecha DD-MM-AAAA, versión, autor y descripción del cambio). "
        "El Agente de Evidencia y Auditoría lee esta tabla para verificar el control documental, por "
        "lo que no se debe cambiar el nombre de sus campos.")
    d.p("El código sigue el formato **PIMS-TT-NN**, donde TT es el tipo y NN un correlativo de dos "
        "dígitos por tipo:")
    d.tabla(["TT", "Tipo", "Ejemplo"], [
        ["POL", "Política", "PIMS-POL-01"], ["MA", "Manual del sistema", "PIMS-MA-01"],
        ["PR", "Procedimiento", "PIMS-PR-01"],
        ["MT", "Metodología", "PIMS-MT-01"], ["PL", "Plan o programa", "PIMS-PL-01"],
        ["FO", "Formulario (en blanco)", "PIMS-FO-01"], ["RG", "Registro o lista", "PIMS-RG-01"],
        ["IN", "Informe", "PIMS-IN-02"], ["AC", "Acta", "PIMS-AC-01"],
    ], anchos=[1.5, 6, 4])
    d.p("La versión se numera X.Y: los borradores son 0.Y; la primera versión aprobada es 1.0; un "
        "cambio de fondo aumenta X y uno de forma aumenta Y. Los registros generados a partir de un "
        "formulario se identifican con el código del formulario, el año y un correlativo "
        "(p. ej., AC-2026-003 para una acción correctiva).")
    d.h2("Formato y medios")
    d.p("Los documentos se redactan en español, en el formato de la plantilla PIMS (fuente Calibri "
        "11; títulos numerados de nivel 1 a 3), con el nombre de la UNSA y el nivel de "
        "confidencialidad en el encabezado, y el código, título, versión y fecha en el pie de "
        "página. Se elaboran en formato .docx editable y la versión aprobada se publica también en "
        "PDF. El medio oficial es el electrónico; el papel solo se usa cuando la normativa "
        "institucional exige firma manuscrita.")
    d.p("Cada documento define sus usuarios y, si genera registros, incluye la sección «Gestión de "
        "registros guardados en base a este documento».")
    d.h2("Revisión y aprobación")
    d.p("Ningún documento se publica como vigente sin revisión y aprobación. La revisión comprueba "
        "su idoneidad (que responda al requisito de la norma y a la realidad de la UNSA) y su "
        "adecuación (que sea suficiente y aplicable):")
    d.tabla(["Tipo de documento", "Elabora", "Revisa", "Aprueba", "Formaliza"], [
        ["Política del PIMS", ODP_CORTO, "CGTD", CU + " (Resolución de Consejo Universitario)", SG],
        ["Procedimientos, metodologías, planes y programas", "Dueño del proceso o equipo del agente",
         ODP_CORTO + " y " + OSCD_CORTO, "CGTD (acta de sesión)", SG + " (cuando requiere "
         "Resolución Rectoral)"],
        ["Formularios y registros", "Dueño del proceso", CDP, ODP_CORTO, "—"],
        ["Informes de auditoría interna", EQUIPO_AUDITOR, "Auditor líder",
         "Auditor líder (validación humana del informe del agente)", "Se comunica al CGTD y al "
         "Rector"],
    ], anchos=[3.6, 3, 3, 3.6, 2.8])
    d.p("La aprobación queda registrada en el historial de modificaciones y en el repositorio "
        "documental (campo «aprobado por» y fecha de aprobación). Un documento sin aprobador o "
        "con versión 0.Y se considera **borrador** y no sirve como evidencia de cumplimiento.")

    d.h1("Control de la información documentada")
    d.p("La información documentada del PIMS se controla para que esté disponible y sea idónea "
        "para su uso, donde y cuando se necesite, y esté adecuadamente protegida contra la pérdida "
        "de confidencialidad, el uso inadecuado o la pérdida de integridad (cláusula 7.5.3).")
    d.h2("Disponibilidad y medio de publicación")
    d.p("La versión vigente de cada documento se publica en el %s, y se exporta a la plataforma "
        "GESTITEL del PIMS para la gestión de la auditoría. El repositorio guarda el archivo, su "
        "texto, su huella SHA-256 y sus metadatos de control, y es la única fuente de la versión "
        "vigente." % REPOSITORIO)
    d.h2("Niveles de confidencialidad y protección")
    d.p("Como entidad pública, la información documentada del PIMS es, por regla, información "
        "pública (Ley N.° 27806); se restringe solo cuando contiene datos personales o información "
        "de seguridad cuya divulgación expone a la UNSA o a los titulares:")
    d.tabla(["Nivel", "Qué incluye", "Quién accede", "Protección mínima"], [
        ["Público", "Política de privacidad, avisos de privacidad", "Cualquier persona",
         "Publicación en la web institucional; integridad con SHA-256"],
        ["Uso interno", "Procedimientos, planes, programa de auditoría, formularios en blanco",
         "Personal de la UNSA dentro del alcance del PIMS", "Solo lectura en el repositorio; "
         "cambios solo por el propietario"],
        ["Confidencial", "Informes de auditoría, evaluaciones de riesgo, SoA, registros de no "
         "conformidades", "Lista de distribución definida por el propietario", "Acceso por rol, "
         "registro de accesos, sin copias locales"],
        ["Restringido", "Registros con datos personales (RoPA con datos, solicitudes de "
         "derechos, logs de acceso, incidentes)", "Personas autorizadas por el Oficial de Datos "
         "Personales", "Acceso nominal, cifrado en reposo y en tránsito, registro de accesos, "
         "seudonimización cuando sea posible"],
    ], anchos=[2.4, 5, 4, 4.6])
    d.h2("Distribución, acceso, recuperación y uso")
    d.p("Cuando se publica un documento nuevo o una versión nueva, el propietario lo comunica por "
        "correo institucional a los usuarios definidos en el documento. El acceso se concede por "
        "rol: ver solamente, o ver y modificar (solo el propietario y el Coordinador de Datos "
        "Personales). Las copias impresas o descargadas son **copias no controladas**; la versión "
        "válida es siempre la del repositorio.")
    d.h2("Almacenamiento y preservación")
    d.p("Los archivos se guardan en el servidor de la OTI con copias de seguridad según la Guía de "
        "copias de seguridad y protocolo de respaldo de base de datos (respaldo diario incremental y "
        "semanal completo, con una copia fuera del centro de datos). Para preservar la legibilidad, "
        "la versión aprobada se conserva además en PDF/A y se verifica su SHA-256 en cada "
        "verificación de integridad del expediente.")
    d.h2("Control de cambios")
    d.p("Solo el propietario modifica un documento. Todo cambio se registra en el historial de "
        "modificaciones y genera una nueva versión, que vuelve a pasar por revisión y aprobación. "
        "Al aprobarse la nueva versión, la anterior pasa al estado **obsoleto**: se retira de la "
        "carpeta de vigentes, se conserva en la carpeta de obsoletos con la marca «OBSOLETO» y su "
        "huella SHA-256 se mantiene en la cadena de custodia.")
    d.h2("Conservación y disposición")
    d.p("Cada documento define el tiempo de conservación de sus registros. Vencido ese tiempo, el "
        "propietario propone la disposición y la Secretaría General la autoriza conforme a las "
        "normas del Sistema Nacional de Archivos. Los registros con datos personales se eliminan "
        "o anonimizan cuando dejan de ser necesarios para la finalidad del tratamiento (principio "
        "de proporcionalidad de la Ley N.° 29733), con eliminación segura del medio y acta de "
        "eliminación.")

    d.h1("Control y protección de los registros")
    d.p("Cada documento del PIMS define cómo se gestionan los registros que genera: (1) nombre del "
        "registro, (2) ubicación, (3) responsable de su archivo, (4) controles de protección y (5) "
        "tiempo de conservación. Los registros no se modifican una vez cerrados; un error se corrige "
        "con un registro nuevo que referencia al anterior.")
    d.p("Para cumplir el control A.3.14, los registros relacionados con el tratamiento de datos "
        "personales se protegen contra pérdida, destrucción, falsificación, acceso no autorizado y "
        "divulgación no autorizada con estas medidas:")
    d.vinetas([
        "**Integridad:** huella SHA-256 calculada al registrar cada evidencia y cadena de custodia "
        "encadenada por hash; las tablas de custodia y bitácoras son de solo inserción.",
        "**Verificación periódica:** el Agente de Evidencia y Auditoría recalcula las huellas y la "
        "cadena al menos una vez por semana y antes de cada auditoría; una alteración abre una no "
        "conformidad según PIMS-PR-02.",
        "**Disponibilidad:** copias de seguridad probadas según la guía de la OTI.",
        "**Confidencialidad:** acceso por rol y registro de accesos para los niveles Confidencial y "
        "Restringido.",
        "**Trazabilidad:** toda decisión humana (aprobación, rechazo, cancelación, vaciado) queda en "
        "la bitácora de decisiones con fecha, actor y motivo.",
    ])

    d.h1("Información documentada de origen externo")
    d.p("La información de origen externo necesaria para planificar y operar el PIMS (normas ISO, "
        "Ley N.° 29733 y su reglamento, disposiciones de la Autoridad Nacional de Protección de "
        "Datos Personales, contratos y acuerdos con encargados, resoluciones de la propia UNSA que "
        "el PIMS utiliza como evidencia) se identifica y controla en el **Registro de documentos "
        "externos (PIMS-RG-05)**, con: número, emisor, título, fecha de emisión, fecha de recepción "
        "o descarga, URL de origen, huella SHA-256 y responsable.")
    d.p("El Coordinador de Datos Personales verifica al menos cada seis meses que las versiones "
        "registradas sigan vigentes (p. ej., cambios del reglamento de la Ley N.° 29733) y "
        "comunica los cambios a los propietarios de los documentos afectados.")

    d.h1("Apoyo automatizado del Agente de Evidencia y Auditoría")
    d.p("El %s apoya este procedimiento, sin reemplazar la aprobación humana:" % AGENTE)
    d.vinetas([
        "registra cada documento y evidencia con su huella SHA-256 y lo anota en la cadena de "
        "custodia;",
        "lee la tabla de control de la portada y comprueba: código con formato PIMS-TT-NN, versión "
        "aprobada (≥ 1.0), aprobador, nivel de confidencialidad, historial de modificaciones y fecha "
        "de validez no vencida;",
        "marca como «Desactualizada» la evidencia que superó su periodo de revisión y como "
        "«Comprometida» la que no coincide con su huella;",
        "propone hallazgos sobre la cláusula 7.5 cuando un documento no cumple estas reglas, que el "
        "auditor acepta o rechaza.",
    ])

    d.h1("Gestión de registros guardados en base a este documento")
    d.tabla(["Nombre del registro", "Ubicación de archivo", "Persona responsable del archivo",
             "Controles para la protección del registro", "Tiempo de retención"], [
        ["Lista maestra de información documentada (PIMS-RG-01)", "Repositorio documental del PIMS "
         "(tabla documentos_pims)", CDP, "Solo el Coordinador de Datos Personales crea o modifica "
         "entradas; cada cambio queda en la bitácora", "Permanente mientras exista el PIMS"],
        ["Versiones obsoletas de documentos", "Repositorio documental, carpeta de obsoletos",
         "Propietario de cada documento", "Solo lectura; huella SHA-256 en la cadena de custodia",
         "5 años desde que quedan obsoletas"],
        ["Registro de documentos externos (PIMS-RG-05)", "Repositorio documental (tabla documentos)",
         CDP, "Solo lectura para usuarios; SHA-256 del archivo de origen", "Mientras el documento "
         "esté vigente y 5 años después"],
        ["Cadena de custodia del expediente de evidencias", "Base de datos pims_auditoria (tabla "
         "cadena_custodia)", OSCD_CORTO, "Solo inserción, encadenada por hash; copia de seguridad "
         "diaria", "Permanente"],
        ["Bitácora de decisiones y accesos", "Base de datos pims_auditoria (tabla "
         "decisiones_humanas)", OSCD_CORTO, "Solo inserción; acceso de lectura para auditores",
         "5 años"],
    ], anchos=[3.4, 3.3, 2.8, 4, 2.5], tam=8)
    d.p("Solo el Coordinador de Datos Personales puede conceder a otros empleados acceso a la "
        "lista maestra con permiso de modificación.")

    validez(d, "Coordinador de Datos Personales", [
        "porcentaje de documentos de la lista maestra aprobados y vigentes (indicador IND-03);",
        "cantidad de documentos usados como evidencia que estaban en borrador, vencidos u "
        "obsoletos;",
        "cantidad de registros sin responsable, sin ubicación o sin tiempo de conservación "
        "definidos;",
        "cantidad de alteraciones de integridad detectadas en el expediente (indicador IND-02).",
    ])
    d.firmas([("Elaborado por", CDP), ("Revisado por", ODP_CORTO),
              ("Aprobado por", "Presidente del CGTD")])
    return d.guardar(os.path.join(SALIDA, "PIMS-PR-01_Control_de_informacion_documentada_y_registros.docx"))


# =============================================================================== PR-02
def pr02():
    d = pp.DocumentoPIMS(pp.PLANTILLA_PROCEDIMIENTO, "PIMS-PR-02",
                         "Procedimiento de no conformidades y acciones correctivas",
                         version=VERSION, fecha=FECHA, creado_por=CREADO, aprobado_por=APROBADO,
                         historial=historial(ADAPTACION))
    d.h1("Objetivo, alcance y usuarios")
    d.p("El objetivo de este procedimiento es describir cómo la UNSA reacciona ante una no "
        "conformidad del PIMS, la corrige, elimina sus causas para que no se repita ni ocurra en "
        "otro lugar, verifica la eficacia de las acciones y mejora el sistema, conforme a las "
        "cláusulas 10.1 y 10.2 de ISO/IEC 27701:2025.")
    d.p("Se aplica a todas las no conformidades del PIMS, cualquiera sea su origen, y a las acciones "
        "derivadas de ellas. Los usuarios son el CGTD, el Oficial y el Coordinador de Datos "
        "Personales, el OSCD, los dueños de procesos que tratan datos personales, el equipo auditor "
        "interno y el CSIRT UNSA.")
    d.h1("Documentos de referencia")
    d.vinetas(REF_COMUNES + [
        "ISO/IEC 27701:2025, cláusulas 10.1 (mejora continua) y 10.2 (no conformidad y acción "
        "correctiva)",
        "PIMS-PR-01 Procedimiento de control de la información documentada y de los registros",
        "PIMS-PR-03 Procedimiento y programa de auditoría interna",
        "PIMS-PR-04 Procedimiento de seguimiento, medición, análisis y evaluación",
        "PIMS-PR-06 Gestión de incidentes y brechas de datos personales (Agente 6)",
        "PIMS-FO-01 Formulario de no conformidades y acciones correctivas",
    ])
    d.h1("Términos y definiciones")
    d.tabla(["Término", "Definición"], [
        ["No conformidad (NC)", "Incumplimiento de un requisito de ISO/IEC 27701:2025, de la Ley "
         "N.° 29733 y su reglamento, de un documento interno del PIMS o de una obligación "
         "contractual con encargados o titulares."],
        ["NC mayor", "Ausencia total de un requisito, fallo sistémico, o incumplimiento que afecta "
         "o puede afectar los derechos de los titulares de datos personales."],
        ["NC menor", "Incumplimiento puntual que no compromete la eficacia del PIMS ni afecta a los "
         "titulares."],
        ["Observación", "Situación que, sin ser incumplimiento, puede convertirse en NC si no se "
         "atiende."],
        ["Corrección", "Acción para eliminar la NC detectada y contener sus consecuencias "
         "(10.2 a)."],
        ["Acción correctiva", "Acción para eliminar la causa de la NC y evitar que se repita "
         "(10.2 b–c)."],
        ["Eficacia", "Comprobación, con evidencia, de que la causa fue eliminada y la NC no se "
         "repite (10.2 d)."],
    ], anchos=[3.5, 12.5])
    d.h1("Fuentes de las no conformidades")
    d.p("Una no conformidad puede detectarse en:")
    d.vinetas([
        "auditorías internas (PIMS-PR-03) y externas;",
        "la revisión por la dirección (cláusula 9.3);",
        "el seguimiento y medición de indicadores (PIMS-PR-04), cuando un indicador incumple su meta "
        "dos periodos seguidos;",
        "incidentes y brechas de datos personales atendidos por el CSIRT UNSA;",
        "solicitudes o quejas de titulares de datos personales y requerimientos de la Autoridad "
        "Nacional de Protección de Datos Personales;",
        "la verificación de integridad del expediente de evidencias (alteración o pérdida de una "
        "evidencia);",
        "la operación diaria, reportada por cualquier servidor, docente o proveedor.",
    ])
    d.h1("Tratamiento de la no conformidad")
    d.h2("Reacción y corrección")
    d.p("Quien detecta una no conformidad la comunica al dueño del proceso afectado y al Coordinador "
        "de Datos Personales, que abre un registro en el formulario PIMS-FO-01 con un número "
        "correlativo (AC-AAAA-NNN). El dueño del proceso toma de inmediato las acciones para "
        "controlarla y corregirla y para hacer frente a sus consecuencias (10.2 a). Si hay datos "
        "personales comprometidos, se activa además PIMS-PR-06 y el Oficial de Datos Personales "
        "evalúa la notificación a la Autoridad y a los titulares en el plazo que fija el Reglamento "
        "de la Ley N.° 29733.")
    d.h2("Evaluación de la necesidad de acción correctiva")
    d.p("El dueño del proceso, con el apoyo del Coordinador de Datos Personales, evalúa si hace "
        "falta eliminar la causa (10.2 b):")
    d.vinetas([
        "**revisa** la no conformidad y la evidencia que la sustenta;",
        "**determina las causas** con la técnica de los cinco porqués o un diagrama de Ishikawa, "
        "distinguiendo la causa raíz del síntoma;",
        "**busca no conformidades similares** que existan o puedan ocurrir en otros procesos o "
        "facultades, consultando los registros PIMS-FO-01 anteriores y el expediente de evidencias.",
    ])
    d.p("Las no conformidades mayores siempre requieren acción correctiva. Para una NC menor o una "
        "observación, el Oficial de Datos Personales puede decidir que basta la corrección, dejando "
        "la justificación en el formulario.")
    d.h2("Implementación de las acciones correctivas")
    d.p("Una acción correctiva se implementa con los siguientes pasos (10.2 c–e):")
    d.tabla(["Paso", "Persona responsable", "Requisito"], [
        ["Revisión de la no conformidad", "Cualquier persona con una función dentro del PIMS",
         "10.2 b)"],
        ["Determinación de la causa de la no conformidad", "Dueño del proceso donde se identificó",
         "10.2 b)"],
        ["Identificación de no conformidades similares existentes o potenciales",
         "Dueño del proceso con el " + CDP, "10.2 b)"],
        ["Evaluación de la necesidad de acciones para eliminar la causa", "Dueño del proceso; "
         "decide el " + ODP_CORTO + " en NC menores y observaciones", "10.2 b)"],
        ["Definición de las acciones, responsables, recursos y fecha límite, y su aprobación",
         "Dueño del proceso; aprueba el " + ODP_CORTO, "10.2 c)"],
        ["Implementación de las acciones planificadas", "Persona designada por el dueño del "
         "proceso", "10.2 c)"],
        ["Revisión de la eficacia de la acción correctiva", EQUIPO_AUDITOR + " (independiente del "
         "proceso)", "10.2 d)"],
        ["Información a las personas involucradas", "Persona designada por el dueño del proceso",
         "10.2 c)"],
        ["Cambios en el PIMS y en sus documentos, si son necesarios", ODP_CORTO + " (según "
         "PIMS-PR-01)", "10.2 e)"],
    ], anchos=[7, 6.5, 2.5])
    d.p("Cada paso queda registrado en el formulario PIMS-FO-01. Las acciones correctivas deben ser "
        "proporcionales a los efectos de la no conformidad.")
    d.h2("Plazos según la clasificación")
    d.p("Los plazos se cuentan desde la fecha en que el auditor o el Oficial de Datos Personales "
        "valida la no conformidad. Son los mismos que usa el Agente de Evidencia y Auditoría al "
        "proponer el plan de acción:")
    d.tabla(["Clasificación", "Corrección inmediata", "Análisis de causa y plan", "Fecha límite de "
             "implementación", "Verificación de eficacia"], [
        ["Evidencia comprometida (integridad alterada)", "24 horas: contener y avisar al CSIRT",
         "3 días hábiles", "7 días calendario", "Al volver a registrar la evidencia original"],
        ["NC mayor", "5 días hábiles", "10 días hábiles", "30 días calendario",
         "Hasta 90 días después de implementada"],
        ["NC menor", "10 días hábiles", "15 días hábiles", "60 días calendario",
         "En la siguiente auditoría"],
        ["Observación", "No aplica", "Opcional", "90 días calendario", "En la siguiente auditoría"],
    ], anchos=[3.6, 3.2, 2.8, 3, 3.4])
    d.p("Una acción que vence sin implementarse se informa al CGTD en el siguiente reporte "
        "trimestral de desempeño (PIMS-PR-04).")
    d.h2("Revisión de la eficacia y cierre")
    d.p("El equipo auditor interno verifica con evidencia que la causa fue eliminada: el documento o "
        "control existe, está aprobado y vigente, y la no conformidad no se repite en la muestra "
        "revisada. Si la acción es eficaz, se cierra el registro y se bloquea su edición; si no lo "
        "es, se abre una nueva acción vinculada a la anterior.")
    d.h1("Mejora continua")
    d.p("El Oficial de Datos Personales analiza cada semestre las tendencias de no conformidades "
        "(por cláusula, proceso y causa) y las presenta en la revisión por la dirección. Las "
        "oportunidades de mejora que no derivan de una no conformidad se registran también en "
        "PIMS-FO-01, con la clasificación «Oportunidad de mejora» (10.1).")
    d.h1("Apoyo automatizado del Agente de Evidencia y Auditoría")
    d.p("Al aprobar el auditor el informe de una auditoría interna, el agente: registra cada "
        "hallazgo y su acción en la base de datos del PIMS y en el formato de GESTITEL; propone "
        "responsable y fecha límite según la tabla de plazos; y emite el formulario PIMS-FO-01 "
        "prellenado con la descripción, el criterio, la causa preliminar y la acción propuesta. "
        "Los campos de causa raíz, eficacia y firmas los completan las personas responsables.")
    d.h1("Gestión de registros guardados en base a este documento")
    d.tabla(["Nombre del registro", "Ubicación de archivo", "Persona responsable del archivo",
             "Controles para la protección del registro", "Tiempo de retención"], [
        ["Formulario de no conformidades y acciones correctivas (PIMS-FO-01)", "Repositorio "
         "documental del PIMS y plataforma GESTITEL (módulo Auditorías → Hallazgos y Seguimiento)",
         CDP, "Una vez verificada la eficacia se bloquea cualquier agregado o edición; huella "
         "SHA-256 en la cadena de custodia", "5 años desde el cierre"],
        ["Hallazgos y acciones (tablas hallazgos y acciones)", "Base de datos pims_auditoria",
         ODP_CORTO, "Acceso por rol; los cambios quedan en la bitácora de decisiones",
         "5 años desde el cierre"],
    ], anchos=[3.6, 3.8, 2.6, 4, 2])
    validez(d, "Oficial de Datos Personales", [
        "cantidad de acciones correctivas iniciadas y cerradas en el periodo;",
        "porcentaje de no conformidades cerradas dentro de plazo (indicador IND-04);",
        "porcentaje de acciones correctivas verificadas como eficaces (indicador IND-05);",
        "cantidad de acciones tomadas sin registrar en el formulario PIMS-FO-01.",
    ])
    d.h1("Apéndices")
    d.vinetas(["Apéndice: PIMS-FO-01 Formulario de no conformidades y acciones correctivas"])
    d.firmas([("Elaborado por", CDP), ("Revisado por", ODP_CORTO),
              ("Aprobado por", "Presidente del CGTD")])
    return d.guardar(os.path.join(SALIDA, "PIMS-PR-02_No_conformidades_y_acciones_correctivas.docx"))


# =============================================================================== PR-03
def pr03():
    d = pp.DocumentoPIMS(pp.PLANTILLA_PROCEDIMIENTO, "PIMS-PR-03",
                         "Procedimiento y programa de auditoría interna del PIMS",
                         version=VERSION, fecha=FECHA, creado_por=CREADO, aprobado_por=APROBADO,
                         historial=historial("Documento nuevo sobre la plantilla de procedimiento; "
                                             "sustituye al «Procedimiento para auditoría interna» "
                                             "citado en las plantillas 27001"))
    d.h1("Objetivo, alcance y usuarios")
    d.p("El objetivo de este procedimiento es establecer el programa de auditoría interna del PIMS "
        "de la UNSA y la forma de planificar, ejecutar, informar y dar seguimiento a cada auditoría, "
        "para determinar si el PIMS es conforme con los requisitos de la propia UNSA y de "
        "ISO/IEC 27701:2025, y si se implementa y mantiene eficazmente (cláusula 9.2). Cubre también "
        "la revisión independiente de la seguridad de la información relacionada con datos "
        "personales (A.3.15) y la revisión del cumplimiento de políticas y normas (A.3.16).")
    d.p("Se aplica a todos los procesos, unidades y sistemas dentro del alcance del PIMS. Los "
        "usuarios son el CGTD, el Rector, el Oficial de Datos Personales, el equipo auditor interno, "
        "los dueños de procesos auditados y el equipo que opera el Agente de Evidencia y Auditoría.")
    d.h1("Documentos de referencia")
    d.vinetas(REF_COMUNES + [
        "ISO/IEC 27701:2025, cláusulas 9.2.1 y 9.2.2, y controles A.3.15 y A.3.16",
        "ISO 19011:2018 – Directrices para la auditoría de los sistemas de gestión",
        "PIMS-PR-01, PIMS-PR-02 y PIMS-PR-04",
        "Informe de auditoría AUD-2026-001 (auditoría diagnóstica del 27-10-2026)",
    ])
    d.h1("Programa de auditoría interna")
    d.h2("Frecuencia y criterios de priorización")
    d.p("Se realiza al menos una auditoría interna completa del PIMS por año y auditorías de "
        "seguimiento o temáticas según los resultados. Al establecer el programa se consideran la "
        "importancia de los procesos y los resultados de auditorías anteriores (9.2.2):")
    d.vinetas([
        "**Importancia de los procesos:** se priorizan los tratamientos con datos sensibles o de "
        "alto volumen: admisión de postulantes (incluye menores de edad), registro académico y "
        "matrícula, evaluación socioeconómica para comedor y beneficios, servicios de salud, "
        "gestión de recursos humanos, biblioteca y videovigilancia.",
        "**Resultados anteriores:** la auditoría diagnóstica AUD-2026-001 encontró 35 no "
        "conformidades mayores, la mayoría por ausencia de documentos del PIMS; por eso la "
        "siguiente auditoría verifica primero la información documentada que emiten los equipos "
        "de los ocho agentes.",
        "**Cambios significativos:** nuevos sistemas, cambios en la Ley N.° 29733 o su reglamento, "
        "incidentes con datos personales o cambios organizativos motivan auditorías "
        "extraordinarias.",
    ])
    d.h2("Programa 2026–2027")
    d.tabla(["Código", "Auditoría", "Alcance", "Periodo", "Método", "Estado"], [
        ["AUD-2026-001", "Diagnóstica del PIMS", "Cláusulas 4 a 10, A.1 (responsable) y A.3",
         "27-10-2026", "Revisión documental de las resoluciones públicas de la UNSA asistida por el "
         "agente", "Realizada: 35 NC mayores"],
        ["AUD-2026-002", "Seguimiento de la información documentada del PIMS", "Documentos de la "
         "lista maestra (PIMS-RG-01) y acciones de AUD-2026-001; cláusulas 7.5, 9 y 10",
         "23-11-2026 al 04-12-2026", "Revisión documental y control documental automatizado del "
         "agente", "Planificada"],
        ["AUD-2027-001", "Interna completa (previa a la certificación)", "Todo el PIMS; muestra de "
         "procesos: admisión, registro académico, recursos humanos y biblioteca", "Abril 2027",
         "Entrevistas, muestreo de registros, revisión documental", "Planificada"],
        ["AUD-2027-002", "Controles técnicos de seguridad (A.3)", "OTI: copias de seguridad, "
         "registros de eventos, control de accesos, cifrado y desarrollo seguro", "Julio 2027",
         "Pruebas técnicas, revisión de configuraciones y logs", "Planificada"],
        ["AUD-2027-003", "Revisión independiente (A.3.15)", "Enfoque de seguridad de la información "
         "para datos personales: personas, procesos y tecnología", "Octubre 2027", "Auditor externo "
         "a la OTI o de otra universidad pública (convenio)", "Planificada"],
        ["Extraordinaria", "Por evento", "Lo que afecte el incidente o cambio", "Cuando ocurra",
         "Según el caso", "—"],
    ], anchos=[2.2, 3, 4.3, 2.4, 3.6, 2], tam=8)
    d.p("El Oficial de Datos Personales propone el programa y el CGTD lo aprueba. El programa se "
        "revisa después de cada auditoría y cuando cambian los riesgos o el alcance.")
    d.h2("Responsabilidades del programa")
    d.tabla(["Rol", "Responsabilidad"], [
        ["CGTD", "Aprueba el programa, asigna recursos y recibe los resultados."],
        [ODP_CORTO, "Gestiona el programa, propone auditores y hace seguimiento de las acciones."],
        ["Auditor líder", "Planifica cada auditoría, dirige al equipo, valida y firma el informe."],
        [EQUIPO_AUDITOR, "Ejecuta la auditoría, recoge evidencia y redacta hallazgos."],
        [AGENTE, "Prepara la auditoría: verifica la integridad del expediente, calcula la matriz de "
         "cobertura, comprueba el control documental, propone y redacta hallazgos y el plan de "
         "acción. No emite conclusiones sin la aprobación del auditor."],
        ["Dueños de procesos", "Facilitan el acceso a la información y a las personas, y ejecutan "
         "las acciones correctivas."],
    ], anchos=[4, 12])
    d.h1("Selección de los auditores")
    d.p("Para asegurar la objetividad y la imparcialidad del proceso de auditoría (9.2.2 b):")
    d.vinetas([
        "ningún auditor audita su propio trabajo ni el proceso del que depende;",
        "el Oficial de Datos Personales y el OSCD no integran el equipo auditor cuando se auditan "
        "procesos a su cargo;",
        "el auditor líder acredita formación en ISO 19011 y en ISO/IEC 27701, y conocimiento de la "
        "Ley N.° 29733;",
        "cada auditor firma una declaración de independencia y confidencialidad antes de iniciar;",
        "el agente es una herramienta del equipo auditor: sus propuestas son revisadas y aceptadas "
        "o rechazadas por una persona.",
    ])
    d.h1("Planificación de cada auditoría")
    d.p("Para cada auditoría el auditor líder define y comunica, al menos 10 días hábiles antes, el "
        "**plan de auditoría** con (9.2.2 a):")
    d.vinetas([
        "**objetivos:** qué se quiere determinar (conformidad, eficacia, seguimiento);",
        "**criterios:** ISO/IEC 27701:2025, Ley N.° 29733 y su reglamento, documentos del PIMS "
        "vigentes y contratos aplicables;",
        "**alcance:** procesos, unidades, sistemas, sedes y periodo auditado;",
        "fecha de corte, periodo de vigencia de la evidencia (por defecto 365 días), equipo "
        "auditor, agenda y muestra.",
    ])
    d.h1("Ejecución de la auditoría")
    d.p("La auditoría sigue esta secuencia, que coincide con los pasos del flujo «auditoría "
        "interna» del agente:")
    d.tabla(["Paso", "Qué se hace", "Quién"], [
        ["Planificar", "Se registran objetivo, alcance, criterios, rol, fecha de corte y vigencia.",
         "Auditor líder con el agente"],
        ["Verificar integridad", "Se recalcula el SHA-256 de cada evidencia y la cadena de "
         "custodia; una alteración abre una NC según PIMS-PR-02.", "Agente"],
        ["Matriz de cobertura", "Se clasifica cada requisito aplicable como Cubierto, Parcial, "
         "Desactualizado, Comprometido o Sin evidencia.", "Agente"],
        ["Control documental", "Se comprueba que cada documento PIMS cumpla PIMS-PR-01: código, "
         "versión aprobada, aprobador, confidencialidad, historial y validez.", "Agente"],
        ["Evaluar pertinencia", "Se juzga si la evidencia demuestra realmente el requisito.",
         "Agente (IA local) y auditor"],
        ["Priorizar y redactar hallazgos", "Hallazgos con criterio, condición, causa, efecto y "
         "recomendación.", "Agente y equipo auditor"],
        ["Aprobación del auditor", "El auditor acepta o rechaza cada propuesta y valida los "
         "hallazgos.", "Auditor líder (decisión humana)"],
        ["Informe y plan de acción", "Se emite el informe PIMS-IN-02 y el formulario PIMS-FO-01.",
         "Agente; firma el auditor líder"],
    ], anchos=[3.2, 9.3, 3.5])
    d.p("Cuando la auditoría incluye entrevistas o pruebas en sitio, se realiza una reunión de "
        "apertura y otra de cierre con los dueños de los procesos auditados.")
    d.h1("Hallazgos e informe")
    d.p("Los hallazgos se clasifican como no conformidad mayor, no conformidad menor, observación u "
        "oportunidad de mejora (definiciones de PIMS-PR-02). El informe de auditoría (PIMS-IN-02) "
        "contiene: plan de la auditoría, resumen de cobertura, hallazgos con su evidencia, revisión "
        "de pertinencia, plan de acción y trazabilidad de la ejecución.")
    d.p("El auditor líder comunica los resultados a los responsables pertinentes (9.2.2 c): al "
        "Rector y al CGTD, al Oficial de Datos Personales y a los dueños de los procesos auditados, "
        "dentro de los 5 días hábiles siguientes a la aprobación del informe. Los resultados son "
        "entrada de la revisión por la dirección (9.3.2 d).")
    d.h1("Seguimiento")
    d.p("Las no conformidades se tratan según PIMS-PR-02. El equipo auditor verifica la eficacia de "
        "las acciones en la auditoría de seguimiento siguiente; el agente vuelve a calcular la "
        "cobertura y el control queda cerrado solo cuando pasa a «Cubierto» con evidencia íntegra "
        "y vigente.")
    d.h1("Revisión independiente y cumplimiento de políticas")
    d.p("Para el control A.3.15, el enfoque de la UNSA para gestionar la seguridad de la información "
        "relacionada con datos personales (personas, procesos y tecnología) se revisa de forma "
        "independiente al menos cada dos años y cuando ocurren cambios significativos, mediante la "
        "auditoría AUD-2027-003 del programa.")
    d.p("Para el control A.3.16, cada auditoría interna incluye una muestra de verificación del "
        "cumplimiento de la política de privacidad, de las políticas temáticas y de las normas de "
        "seguridad relacionadas con datos personales; las desviaciones se registran como hallazgos.")
    d.h1("Gestión de registros guardados en base a este documento")
    d.tabla(["Nombre del registro", "Ubicación de archivo", "Persona responsable del archivo",
             "Controles para la protección del registro", "Tiempo de retención"], [
        ["Programa de auditoría aprobado", "Repositorio documental del PIMS", ODP_CORTO,
         "Solo lectura; versiones según PIMS-PR-01", "5 años"],
        ["Plan e informe de cada auditoría (PIMS-IN-02)", "Repositorio documental y GESTITEL "
         "(módulo Auditorías)", "Auditor líder", "Nivel Confidencial; huella SHA-256 en la cadena "
         "de custodia", "5 años"],
        ["Checklist, evidencias revisadas y hallazgos", "Base de datos pims_auditoria (tablas "
         "auditorias, checklist_items, hallazgos)", "Auditor líder", "Acceso por rol; bitácora de "
         "decisiones de solo inserción", "5 años"],
        ["Declaraciones de independencia de los auditores", "Repositorio documental", ODP_CORTO,
         "Nivel Confidencial", "5 años"],
    ], anchos=[3.6, 3.8, 2.4, 4, 2.2], tam=8)
    validez(d, "Oficial de Datos Personales", [
        "porcentaje de auditorías del programa realizadas en el periodo previsto (indicador "
        "IND-11);",
        "cantidad de informes de auditoría comunicados fuera de plazo;",
        "cantidad de auditorías con auditores sin declaración de independencia.",
    ])
    d.firmas([("Elaborado por", CDP), ("Revisado por", ODP_CORTO),
              ("Aprobado por", "Presidente del CGTD")])
    return d.guardar(os.path.join(SALIDA, "PIMS-PR-03_Procedimiento_y_programa_de_auditoria_interna.docx"))


# =============================================================================== PR-04
def pr04():
    d = pp.DocumentoPIMS(pp.PLANTILLA_PROCEDIMIENTO, "PIMS-PR-04",
                         "Procedimiento de seguimiento, medición, análisis y evaluación del PIMS",
                         version=VERSION, fecha=FECHA, creado_por=CREADO, aprobado_por=APROBADO,
                         historial=historial("Documento nuevo sobre la plantilla de procedimiento "
                                             "para la cláusula 9.1 de ISO/IEC 27701:2025"))
    d.h1("Objetivo, alcance y usuarios")
    d.p("El objetivo de este procedimiento es determinar qué se sigue y mide en el PIMS de la UNSA, "
        "con qué métodos, cuándo se mide y cuándo se analizan y evalúan los resultados, para "
        "evaluar el desempeño de privacidad y la eficacia del PIMS (cláusula 9.1 de ISO/IEC "
        "27701:2025).")
    d.p("Se aplica a los indicadores del PIMS y a sus fuentes de datos. Los usuarios son el CGTD, el "
        "Oficial y el Coordinador de Datos Personales, el OSCD, los dueños de indicadores y los "
        "equipos de los agentes del PIMS que proveen los datos.")
    d.h1("Documentos de referencia")
    d.vinetas(REF_COMUNES + ["ISO/IEC 27701:2025, cláusula 9.1",
                             "PIMS-PR-02 y PIMS-PR-03"])
    d.h1("Qué se sigue y mide")
    d.p("El PIMS se evalúa con los siguientes indicadores. Cada uno tiene un dueño responsable de "
        "la medición y una fuente de datos verificable:")
    d.tabla(["ID", "Indicador", "Fórmula", "Meta", "Fuente", "Dueño"], [
        ["IND-01", "Cobertura de evidencia del PIMS", "Requisitos cubiertos / requisitos aplicables "
         "× 100", "≥ 80 % a junio 2027", "Matriz de cobertura del Agente 4", ODP_CORTO],
        ["IND-02", "Integridad del expediente", "Evidencias con huella correcta / evidencias "
         "registradas × 100", "100 %", "Verificación de integridad del Agente 4", OSCD_CORTO],
        ["IND-03", "Documentos PIMS aprobados y vigentes", "Documentos aprobados y no vencidos / "
         "documentos de la lista maestra × 100", "≥ 90 %", "Lista maestra PIMS-RG-01", CDP],
        ["IND-04", "No conformidades cerradas en plazo", "NC cerradas dentro de plazo / NC con "
         "plazo vencido en el periodo × 100", "≥ 85 %", "PIMS-FO-01 y GESTITEL", ODP_CORTO],
        ["IND-05", "Eficacia de las acciones correctivas", "Acciones verificadas eficaces / "
         "acciones cerradas × 100", "≥ 90 %", "PIMS-FO-01", EQUIPO_AUDITOR],
        ["IND-06", "Solicitudes de derechos atendidas en plazo", "Solicitudes atendidas en plazo "
         "legal / solicitudes recibidas × 100", "100 %", "Registro del Agente 5 – Derechos", CDP],
        ["IND-07", "Incidentes con datos personales notificados en plazo", "Incidentes notificados "
         "en plazo / incidentes que requerían notificación × 100", "100 %", "Registro del CSIRT "
         "(Agente 6)", OSCD_CORTO],
        ["IND-08", "Personal capacitado en protección de datos", "Personal que trata datos "
         "personales capacitado en el año / total de ese personal × 100", "≥ 80 %", "Registro del "
         "Agente 8 – Formación", "Unidad de Recursos Humanos"],
        ["IND-09", "Tratamientos de alto riesgo con DPIA vigente", "Tratamientos de alto riesgo "
         "con DPIA vigente / tratamientos de alto riesgo × 100", "100 %", "Agente 2 – Riesgos",
         ODP_CORTO],
        ["IND-10", "Encargados con contrato de tratamiento", "Encargados con cláusulas de "
         "protección de datos / encargados × 100", "100 %", "Agente 7 – Terceros", "Área de "
         "abastecimiento"],
        ["IND-11", "Ejecución del programa de auditoría", "Auditorías realizadas / auditorías "
         "programadas en el periodo × 100", "100 %", "PIMS-PR-03", "Auditor líder"],
    ], anchos=[1.3, 3.2, 4.4, 2, 3, 2.3], tam=8)
    d.h1("Métodos para asegurar resultados válidos")
    d.vinetas([
        "Los datos se toman de la fuente de registro (base de datos del PIMS, GESTITEL, registros "
        "de los agentes), no de declaraciones de las áreas.",
        "Cada medición fija su fecha de corte y usa siempre la misma fórmula; si la fórmula cambia, "
        "se documenta y se recalcula el periodo anterior para comparar.",
        "Los indicadores automáticos (IND-01, IND-02 e IND-03) los calcula el Agente de Evidencia y "
        "Auditoría; un responsable humano revisa el resultado antes de reportarlo.",
        "Cada resultado se conserva como registro, con su fecha, valor, fuente y responsable.",
    ])
    d.h1("Cuándo se mide y cuándo se analiza")
    d.tabla(["Indicadores", "Frecuencia de medición", "Análisis y evaluación", "Se informa a"], [
        ["IND-01, IND-02, IND-03", "Semanal (automática) y antes de cada auditoría", "Mensual",
         ODP_CORTO + " y CGTD"],
        ["IND-04, IND-05, IND-06, IND-07", "Mensual", "Trimestral", "CGTD"],
        ["IND-08, IND-09, IND-10", "Semestral", "Semestral", "CGTD"],
        ["IND-11", "Trimestral", "Trimestral", "CGTD"],
    ], anchos=[4, 4, 3.5, 4.5])
    d.h1("Análisis, evaluación y reporte")
    d.p("Cada trimestre el Coordinador de Datos Personales consolida los resultados en el **Informe "
        "trimestral de desempeño del PIMS (PIMS-IN-03)**, que compara cada indicador con su meta y "
        "con el periodo anterior, explica las desviaciones y propone acciones. Un indicador que "
        "incumple su meta dos periodos seguidos se trata como no conformidad según PIMS-PR-02.")
    d.p("Con estos resultados la UNSA evalúa el desempeño de privacidad y la eficacia del PIMS; el "
        "informe es entrada de la revisión por la dirección (9.3.2 d).")
    d.h1("Gestión de registros guardados en base a este documento")
    d.tabla(["Nombre del registro", "Ubicación de archivo", "Persona responsable del archivo",
             "Controles para la protección del registro", "Tiempo de retención"], [
        ["Resultados de medición de indicadores", "Base de datos pims_auditoria y repositorio "
         "documental", CDP, "Solo lectura una vez reportados; fuente y fecha de corte registradas",
         "5 años"],
        ["Informe trimestral de desempeño (PIMS-IN-03)", "Repositorio documental del PIMS", CDP,
         "Nivel Uso interno; versiones según PIMS-PR-01", "5 años"],
    ], anchos=[3.6, 3.8, 2.4, 4, 2.2])
    validez(d, "Oficial de Datos Personales", [
        "cantidad de indicadores sin medir en el periodo previsto;",
        "cantidad de indicadores sin fuente verificable;",
        "cantidad de desviaciones sin acción propuesta en el informe trimestral.",
    ])
    d.firmas([("Elaborado por", CDP), ("Revisado por", ODP_CORTO),
              ("Aprobado por", "Presidente del CGTD")])
    return d.guardar(os.path.join(SALIDA, "PIMS-PR-04_Seguimiento_medicion_analisis_y_evaluacion.docx"))


def fo01():
    return pp.formulario_no_conformidades(
        os.path.join(SALIDA, "PIMS-FO-01_Formulario_no_conformidades_y_acciones_correctivas.docx"),
        fecha=FECHA2, version="1.3", historial=[
            ("03-11-2026", "0.1", "Grupo 6 – Agente de Evidencia y Auditoría",
             "Adaptación del formulario ISO/IEC 27001:2013 a la cláusula 10.2 de ISO/IEC 27701:2025"),
            ("17-11-2026", "1.0", ODP_CORTO, "Versión aprobada (aprobación simulada)"),
            ("17-11-2026", "1.1", CDP, "Se agregan historial, validez y propietario: faltas "
                                       "detectadas por el control documental del agente (PIMS-PR-01)"),
            ("17-11-2026", "1.2", CDP, "Corrección de forma: el pie de página conservaba el nombre, "
                                       "la versión y la licencia de la plantilla original"),
            ("18-11-2026", "1.3", CDP, "Corrección de forma: ninguna fila del formulario se parte "
                                       "entre dos páginas"),
        ])


# =============================================================================== Mensaje 3
# Documentos del Grupo 6 que completan la lista maestra: RG-01, RG-05, IN-02 e IN-03.
VERSIONES = {"PIMS-PR-01": "1.2", "PIMS-FO-01": "1.3", "PIMS-PR-02": "1.1", "PIMS-PR-03": "1.1",
             "PIMS-PR-04": "1.1", "PIMS-RG-01": "1.1"}
APROBADO2 = "Comité de Gobierno y Transformación Digital (sesión simulada del 18-11-2026)"
INFORME_AUD_002 = os.path.join(E3, "datos", "salidas", "informe_auditoria_unsa_20261117_194151.md")
DOCS_UNSA = os.path.join(E3, "datos", "documentos_unsa")


def historial_nuevo(descripcion):
    return [
        ("17-11-2026", "0.1", "Grupo 6 – Agente de Evidencia y Auditoría (borrador asistido por IA)",
         descripcion),
        ("18-11-2026", "0.2", CDP, "Revisión de coherencia con los documentos de los ocho equipos"),
        ("18-11-2026", "1.0", ODP_CORTO, "Versión aprobada por el CGTD (aprobación simulada)"),
    ]


def _refs(lista):
    return "; ".join(lista)


def rg01():
    d = pp.DocumentoPIMS(pp.PLANTILLA_CONTROL_DOC, "PIMS-RG-01",
                         "Lista maestra de información documentada del PIMS",
                         version="1.1", fecha=FECHA2, creado_por=CREADO, aprobado_por=APROBADO2,
                         historial=historial_nuevo("Listado de la información documentada que soporta el "
                                                   "PIMS ISO/IEC 27701:2025 con sus cláusulas y controles") + [
                             ("18-11-2026", "1.1", CDP, "PIMS-PR-07 respalda también A.1.2.2 (el aviso de "
                              "privacidad declara la finalidad); sin esto no quedaba como evidencia del "
                              "expediente")])
    d.h1("Objetivo, alcance y usuarios")
    d.p("Este registro presenta el listado de la información documentada que soporta el Sistema de "
        "Gestión de Privacidad de la Información (PIMS) de la UNSA según ISO/IEC 27701:2025, con las "
        "cláusulas y los controles que exige cada documento, en la implementación simulada del PIMS. "
        "Es la lista maestra que define PIMS-PR-01 (cláusula 7.5.1): qué documentos debe tener el "
        "PIMS, quién los elabora, quién es su propietario y qué nivel de confidencialidad tienen.")
    d.p("Se aplica a la información documentada de los ocho equipos (agentes) del PIMS y de la alta "
        "dirección. La UNSA actúa como **responsable del tratamiento**: aplica las cláusulas 4 a 10, "
        "los controles A.1 (responsable) y A.3 (seguridad). Los controles A.2 (encargado) quedan "
        "excluidos con la justificación de la Declaración de aplicabilidad PIMS-RG-03.")
    d.p("Los usuarios son el Coordinador y el Oficial de Datos Personales, los propietarios de los "
        "documentos, el equipo auditor interno y el Agente de Evidencia y Auditoría, que lee esta lista "
        "desde la base de datos para saber qué documentos faltan en el control documental.")
    d.h1("Documentos de referencia")
    d.vinetas(REF_COMUNES + [
        "PIMS-PR-01 Procedimiento de control de la información documentada y de los registros",
        "Guía «Implementar el PIMS con documentos y evidencias reales» (expedientes D01–D37, "
        "revisión 2 del 31-10-2026) y diagrama de implementación entregados por el docente",
        "PIMS-RG-03 Declaración de aplicabilidad",
    ])
    d.h1("Cómo leer la lista")
    d.tabla(["Marca", "Significado (guía de implementación)"], [
        ["E", "Información documentada exigida expresamente por la norma (puede integrarse en otro "
              "documento)."],
        ["C", "Documento o evidencia relacionado con un control aplicable del Anexo A."],
        ["S", "Formato de apoyo sugerido."],
    ], anchos=[2, 14])
    d.p("La columna «Exp.» indica el expediente de la guía al que responde el documento. La versión "
        "vigente es la del repositorio documental; la que figura aquí es la de la fecha de este registro.")
    d.h1("Lista maestra de información documentada")
    filas = []
    for f in lm.filas():
        filas.append([f["codigo"], f["titulo"], _refs(f["requisitos"]), ", ".join(f["expedientes"]),
                      f["marca"], f["equipo"], f["propietario"], f["confidencialidad"],
                      "v%s aprobada" % VERSIONES.get(f["codigo"], "1.0")])
    d.tabla(["Código", "Documento", "Cláusulas y controles", "Exp.", "Marca", "Elabora", "Propietario",
             "Confid.", "Estado"], filas, anchos=[1.8, 3.6, 2.6, 1.2, 0.9, 2.2, 2.2, 1.4, 1.4], tam=7)
    d.p("Además de estos documentos, el PIMS genera registros a partir de ellos (formularios PIMS-FO-01 "
        "llenos, informes de cada auditoría, actas, solicitudes de derechos, incidentes). Cada documento "
        "indica en su sección «Gestión de registros» dónde se guardan y cuánto tiempo se conservan.")
    d.h1("Trazabilidad por cláusula y control")
    d.p("Cada cláusula de ISO/IEC 27701:2025 y cada control aplicable del Anexo A tiene al menos un "
        "documento que lo soporta:")
    por_req = lm.documentos_por_requisito()
    refs = list(lm.CLAUSULAS) + [c for c, _ in lm.CONTROLES_A1] + [c for c, _ in lm.CONTROLES_A3]
    d.tabla(["Requisito", "Título", "Documentos"],
            [[r, lm.TITULOS[r], ", ".join(por_req.get(r, ["— (ver PIMS-RG-03)"]))] for r in refs],
            anchos=[2, 8, 6], tam=7)
    d.h1("Trazabilidad por expediente de la guía de implementación")
    exps = lm.expedientes_cubiertos()
    filas = []
    for i in range(1, 38):
        cod = "D%02d" % i
        if cod in exps:
            filas.append([cod, ", ".join(exps[cod]), "Atendido"])
        else:
            filas.append([cod, "—", "No aplica en este ciclo: " + lm.NO_APLICA.get(cod, "")])
    d.tabla(["Expediente", "Documentos", "Situación"], filas, anchos=[2, 6, 8], tam=8)
    d.h1("Mantenimiento de la lista")
    d.vinetas([
        "Solo el Coordinador de Datos Personales agrega, modifica o retira entradas, a pedido del "
        "propietario del documento y según PIMS-PR-01.",
        "La fuente de la lista en el sistema es el módulo lista_maestra_pims del agente; el script de "
        "carga la sincroniza con la tabla lista_maestra_pims de la base de datos.",
        "En cada auditoría interna el Agente de Evidencia y Auditoría compara esta lista con los "
        "documentos registrados y propone un hallazgo de la cláusula 7.5 si falta alguno o si alguno "
        "no cumple las reglas de PIMS-PR-01.",
        "La lista se revisa al menos una vez al año y cuando cambian la norma, la Ley N.° 29733 o su "
        "reglamento, el alcance del PIMS o la estructura de los equipos.",
    ])
    d.h1("Gestión de registros guardados en base a este documento")
    d.tabla(["Nombre del registro", "Ubicación de archivo", "Persona responsable del archivo",
             "Controles para la protección del registro", "Tiempo de retención"], [
        ["Versiones anteriores de la lista maestra", "Repositorio documental (tabla documentos_pims, "
         "estado obsoleto)", CDP, "Solo lectura; huella SHA-256 en la cadena de custodia", "5 años"],
        ["Tabla lista_maestra_pims", "Base de datos pims_auditoria", CDP, "Modificación solo por el script "
         "de carga; cambios en la bitácora", "Mientras exista el PIMS"],
    ], anchos=[3.6, 3.8, 2.4, 4, 2.2], tam=8)
    validez(d, "Coordinador de Datos Personales", [
        "cantidad de documentos usados en el PIMS que no figuran en la lista maestra;",
        "cantidad de cláusulas o controles aplicables sin documento asociado;",
        "porcentaje de documentos de la lista aprobados y vigentes (IND-03).",
    ])
    d.firmas([("Elaborado por", CDP), ("Revisado por", ODP_CORTO), ("Aprobado por", "Presidente del CGTD")])
    return d.guardar(os.path.join(SALIDA, "PIMS-RG-01_Lista_maestra_de_informacion_documentada.docx"))


def _sha256(ruta):
    import hashlib
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rg05():
    import json
    d = pp.DocumentoPIMS(pp.PLANTILLA_CONTROL_DOC, "PIMS-RG-05", "Registro de documentos de origen externo",
                         version="1.0", fecha=FECHA2, creado_por=CREADO, aprobado_por=APROBADO2,
                         historial=historial_nuevo("Registro de la información de origen externo que usa "
                                                   "el PIMS (cláusula 7.5.3 y control A.3.13)"))
    d.h1("Objetivo, alcance y usuarios")
    d.p("Este registro identifica y controla la información documentada de origen externo que la UNSA "
        "necesita para planificar y operar el PIMS (cláusula 7.5.3 de ISO/IEC 27701:2025) y los "
        "requisitos legales, reglamentarios y contractuales aplicables a la privacidad (control A.3.13). "
        "Lo mantiene el Coordinador de Datos Personales según PIMS-PR-01.")
    d.h1("Normas técnicas y legislación aplicable")
    d.tabla(["N.°", "Emisor", "Documento", "Uso en el PIMS", "Verificación de vigencia"], [
        ["EXT-01", "ISO / IEC", "ISO/IEC 27701:2025 – Sistemas de gestión de la información de privacidad",
         "Norma de requisitos del PIMS", "18-11-2026"],
        ["EXT-02", "ISO / IEC", "ISO/IEC 27001:2022 y 27002:2022", "Referencia para los controles A.3",
         "18-11-2026"],
        ["EXT-03", "ISO", "ISO 19011:2018 – Directrices para la auditoría de sistemas de gestión",
         "Método de auditoría interna (PIMS-PR-03)", "18-11-2026"],
        ["EXT-04", "Congreso de la República", "Ley N.° 29733, Ley de Protección de Datos Personales",
         "Requisito legal principal", "18-11-2026"],
        ["EXT-05", "Ministerio de Justicia y Derechos Humanos", "Reglamento de la Ley N.° 29733 (D.S. "
         "N.° 016-2024-JUS)", "Plazos de derechos, incidentes y medidas de seguridad", "18-11-2026"],
        ["EXT-06", "Congreso de la República", "Ley N.° 27806, Ley de Transparencia y Acceso a la "
         "Información Pública", "Límites a la entrega de datos personales (PIMS-PR-01)", "18-11-2026"],
        ["EXT-07", "Congreso de la República", "Ley N.° 30220, Ley Universitaria",
         "Base legal de los tratamientos académicos (PIMS-RG-02)", "18-11-2026"],
        ["EXT-08", "Poder Ejecutivo", "D.L. N.° 1412, Ley de Gobierno Digital, y D.U. N.° 007-2020, Marco "
         "de Confianza Digital", "Gestión de incidentes de seguridad digital (PIMS-PR-06)", "18-11-2026"],
    ], anchos=[1.4, 2.8, 5.6, 4, 2.2], tam=8)
    d.h1("Documentos de la UNSA usados como evidencia")
    d.p("Resoluciones y documentos públicos de la UNSA que el expediente de evidencias usa. La huella "
        "SHA-256 se calculó sobre el archivo descargado y es la misma que registra la cadena de custodia.")
    fuentes = json.load(open(os.path.join(DOCS_UNSA, "fuentes.json"), encoding="utf-8"))
    filas = []
    for i, f in enumerate(fuentes, 1):
        ruta = os.path.join(DOCS_UNSA, f["archivo"])
        sha = _sha256(ruta)[:16] + "…" if os.path.isfile(ruta) else "archivo no disponible"
        filas.append(["UNSA-%02d" % i, f["titulo"][:110], f.get("fecha_documento") or "—",
                      f.get("fecha_consulta") or "—", (f.get("url_origen") or "Aportado por el grupo")[:60],
                      sha])
    d.tabla(["N.°", "Título", "Emisión", "Descarga", "Origen", "SHA-256"], filas,
            anchos=[1.4, 6, 1.8, 1.8, 3, 2.4], tam=7)
    d.h1("Control de vigencia")
    d.p("El Coordinador de Datos Personales verifica cada seis meses que las versiones registradas sigan "
        "vigentes y comunica los cambios a los propietarios de los documentos afectados. Un documento "
        "externo que cambia se registra como entrada nueva; la anterior se marca como reemplazada.")
    d.h1("Gestión de registros guardados en base a este documento")
    d.tabla(["Nombre del registro", "Ubicación de archivo", "Persona responsable del archivo",
             "Controles para la protección del registro", "Tiempo de retención"], [
        ["Copias de los documentos externos", "Repositorio documental (tabla documentos) y expediente "
         "de evidencias", CDP, "SHA-256 y cadena de custodia", "Mientras estén vigentes y 5 años después"],
    ], anchos=[3.6, 3.8, 2.4, 4, 2.2], tam=8)
    validez(d, "Coordinador de Datos Personales", [
        "cantidad de documentos externos usados en el PIMS que no figuran en este registro;",
        "cantidad de documentos externos con verificación de vigencia vencida.",
    ])
    d.firmas([("Elaborado por", CDP), ("Revisado por", ODP_CORTO), ("Aprobado por", "Presidente del CGTD")])
    return d.guardar(os.path.join(SALIDA, "PIMS-RG-05_Registro_de_documentos_externos.docx"))


def _leer_informe(ruta):
    """Extrae del informe .md del agente: cobertura, matriz, hallazgos y plan de acción."""
    import re
    texto = open(ruta, encoding="utf-8").read()
    secc = {}
    actual = None
    for linea in texto.splitlines():
        m = re.match(r"^## (.+)", linea)
        if m:
            actual = m.group(1).strip()
            secc[actual] = []
        elif actual:
            secc[actual].append(linea)

    def tabla(nombre):
        filas = [l for l in secc.get(nombre, []) if l.startswith("|")]
        return [[c.strip() for c in l.strip("|").split("|")] for l in filas[2:]]

    hallazgos = []
    for i, l in enumerate(secc.get("5. Hallazgos", [])):
        m = re.match(r"^### (\S+) - (.+) \((.+)\)$", l)
        if m:
            clas = next((x.split(":**", 1)[1].strip() for x in secc["5. Hallazgos"][i:i + 4]
                         if "Clasificación propuesta" in x), "")
            hallazgos.append([m.group(1), m.group(2), m.group(3), clas])
    return {"cobertura": [l[2:] for l in secc.get("2. Resumen de cobertura", []) if l.startswith("- ")],
            "integridad": " ".join(l for l in secc.get("1. Integridad del expediente", []) if l.strip()),
            "plan_auditoria": [l[2:] for l in secc.get("6. Plan de la auditoría", []) if l.startswith("- ")],
            "matriz": tabla("4. Matriz de cobertura"), "hallazgos": hallazgos,
            "acciones": tabla("8. Plan de acción correctiva (propuesto por el agente)")}


def in02():
    inf = _leer_informe(INFORME_AUD_002)
    d = pp.DocumentoPIMS(pp.PLANTILLA_PROCEDIMIENTO, "PIMS-IN-02", "Informe de auditoría interna AUD-2026-002",
                         version="1.0", fecha=FECHA2, creado_por="Auditor líder del PIMS con el " + AGENTE,
                         aprobado_por="Auditor líder del PIMS (validación humana simulada del 17-11-2026)",
                         confidencialidad="Confidencial",
                         historial=[("17-11-2026", "0.1", AGENTE, "Informe generado por el agente al aprobar "
                                     "el auditor (ejecución AUD-20261117-194148-t61j)"),
                                    ("18-11-2026", "1.0", "Auditor líder del PIMS", "Informe formal en el "
                                     "formato PIMS (PIMS-PR-03); contenido sin cambios")])
    d.h1("Datos de la auditoría")
    d.tabla(["Campo", "Valor"], [
        ["Código", "AUD-2026-002 – Seguimiento de la información documentada del PIMS"],
        ["Programa", "PIMS-PR-03 v1.1, programa 2026–2027"],
        ["Fecha de ejecución", "17-11-2026 (fecha de corte 17-11-2026)"],
        ["Auditor líder", "Auditor líder del PIMS (designación simulada)"],
        ["Herramienta", AGENTE + ", flujo auditoria_interna (modo rápido, sin IA)"],
    ] + [[x.split(":", 1)[0], x.split(":", 1)[1].strip()] for x in inf["plan_auditoria"] if ":" in x],
        anchos=[4, 12])
    d.p("Esta auditoría sirve además de diagnóstico de brechas (expediente D06 de la guía) junto con la "
        "auditoría diagnóstica AUD-2026-001 del 27-10-2026 (35 no conformidades, cobertura 7.9 %).")
    d.h1("Integridad del expediente")
    d.p(inf["integridad"] or "Sin datos.")
    d.h1("Resumen de cobertura")
    d.vinetas(inf["cobertura"])
    d.h1("Matriz de cobertura")
    d.tabla(["Control", "Título", "Estado", "Evidencias"], inf["matriz"], anchos=[2, 7, 3, 4], tam=7)
    d.h1("Hallazgos")
    d.p("%d hallazgos validados por el auditor líder. El detalle (criterio, condición, causa, efecto y "
        "recomendación) está en el informe del agente y en el formulario PIMS-FO-01 de esta auditoría."
        % len(inf["hallazgos"]))
    d.tabla(["Control", "Título", "Estado", "Clasificación"], inf["hallazgos"], anchos=[2, 7, 3, 4], tam=7)
    d.h1("Control documental")
    d.p("Los 5 documentos PIMS registrados a la fecha de corte (PR-01, PR-02, PR-03, PR-04 y FO-01) "
        "cumplieron las reglas de PIMS-PR-01. Los documentos de los demás equipos aún no estaban "
        "registrados: es la causa principal de las brechas de las cláusulas 4, 6, 7 y 8 y de los "
        "controles A.1.")
    d.h1("Plan de acción")
    d.tabla(["#", "Control", "Estado", "Acción", "Responsable sugerido", "Plazo", "Fecha límite"],
            inf["acciones"], anchos=[0.7, 1.4, 2, 6, 3.4, 1.2, 1.8], tam=7)
    d.h1("Conclusión y seguimiento")
    d.p("El PIMS de la UNSA no era conforme con ISO/IEC 27701:2025 a la fecha de corte: la "
        "información documentada exigida estaba incompleta. Las acciones se registraron en PIMS-FO-01 "
        "y en GESTITEL. Al 18-11-2026 los ocho equipos registraron sus documentos (PIMS-RG-01); su "
        "eficacia se verificará en la auditoría de seguimiento AUD-2026-003.")
    d.p("Comunicado al Rector, al CGTD, al Oficial de Datos Personales y a los dueños de procesos según "
        "PIMS-PR-03 (9.2.2 c). Es entrada de la revisión por la dirección PIMS-AC-01.")
    validez(d, "Auditor líder del PIMS", [
        "hallazgos sin evidencia suficiente detectados en la revisión del informe;",
        "plazo entre la auditoría y la comunicación de resultados (meta ≤ 5 días hábiles).",
    ])
    d.firmas([("Elaborado por", "Auditor líder del PIMS"), ("Revisado por", ODP_CORTO),
              ("Comunicado a", "Presidente del CGTD")])
    return d.guardar(os.path.join(SALIDA, "PIMS-IN-02_Informe_de_auditoria_interna_AUD-2026-002.docx"))


def in03():
    import datos_pims_unsa as du
    d = pp.DocumentoPIMS(pp.PLANTILLA_PROCEDIMIENTO, "PIMS-IN-03",
                         "Informe trimestral de desempeño del PIMS (IV trimestre 2026)",
                         version="1.0", fecha=FECHA2, creado_por=CDP, aprobado_por=APROBADO2,
                         historial=historial_nuevo("Primer informe de desempeño según PIMS-PR-04 (corte "
                                                   "18-11-2026)"))
    d.h1("Objetivo y periodo")
    d.p("Este informe consolida la medición de los indicadores del PIMS definidos en PIMS-PR-04 "
        "(cláusula 9.1 de ISO/IEC 27701:2025) para el IV trimestre de 2026, con corte al 18-11-2026. "
        "Es el primer periodo del PIMS: varios indicadores establecen su línea base.")
    d.h1("Resultados de los indicadores")
    d.tabla(["ID", "Indicador", "Meta", "Valor", "Cálculo y fuente", "Comentario"],
            [list(x) for x in du.INDICADORES], anchos=[1.3, 3, 2, 1.6, 4.5, 3.6], tam=7)
    d.h1("Análisis y evaluación")
    d.vinetas([
        "**Información documentada (IND-03):** pasó de 5 a 26 documentos aprobados al registrar los "
        "documentos de los ocho equipos. Se espera que la cobertura (IND-01) suba en AUD-2026-003.",
        "**Capacitación (IND-08) y encargados (IND-10):** están por debajo de la meta. Tienen acciones "
        "en el plan de tratamiento PIMS-PL-01 (acuerdos de confidencialidad y adendas con plazo "
        "15-12-2026) y en el plan de capacitación PIMS-PL-02.",
        "**Integridad (IND-02) y derechos (IND-06):** cumplen la meta.",
        "Ningún indicador incumplió su meta dos periodos seguidos: no corresponde abrir no "
        "conformidades por desempeño (PIMS-PR-04).",
    ])
    d.h1("Acciones propuestas")
    d.tabla(["Indicador", "Acción", "Responsable", "Plazo"], [
        ["IND-01", "Ejecutar AUD-2026-003 con los documentos registrados", "Auditor líder", "04-12-2026"],
        ["IND-08", "Completar la segunda ola de capacitación del plan PL-02", "Unidad de Recursos Humanos",
         "31-03-2027"],
        ["IND-10", "Firmar las dos adendas de tratamiento pendientes", ODP_CORTO, "15-12-2026"],
    ], anchos=[2, 8, 4, 2])
    d.p("Este informe es entrada de la revisión por la dirección (9.3.2 d) PIMS-AC-01.")
    d.h1("Gestión de registros guardados en base a este documento")
    d.tabla(["Nombre del registro", "Ubicación de archivo", "Persona responsable del archivo",
             "Controles para la protección del registro", "Tiempo de retención"], [
        ["Mediciones de los indicadores del periodo", "Base de datos pims_auditoria y repositorio "
         "documental", CDP, "Solo lectura una vez reportadas", "5 años"],
    ], anchos=[3.6, 3.8, 2.4, 4, 2.2], tam=8)
    validez(d, "Coordinador de Datos Personales", [
        "indicadores sin medir en el periodo;",
        "desviaciones sin acción propuesta.",
    ])
    d.firmas([("Elaborado por", CDP), ("Revisado por", ODP_CORTO), ("Aprobado por", "Presidente del CGTD")])
    return d.guardar(os.path.join(SALIDA, "PIMS-IN-03_Informe_trimestral_de_desempeno_IV-2026.docx"))


def main():
    rutas = [pr01(), pr02(), fo01(), pr03(), pr04(), rg01(), rg05(), in02(), in03()]
    for r in rutas:
        print("generado:", os.path.relpath(r, E3))


if __name__ == "__main__":
    main()
