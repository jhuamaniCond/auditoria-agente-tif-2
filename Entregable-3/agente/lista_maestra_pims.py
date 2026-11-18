# -*- coding: utf-8 -*-
"""
Lista maestra de información documentada del PIMS de la UNSA (PIMS-RG-01).

Responde al Mensaje 3 del docente: listado de la información documentada que soporta el
PIMS ISO/IEC 27701:2025, con las cláusulas y controles que la exigen, para una
implementación (simulada) en la UNSA. Es la única fuente de la lista:

  - scripts/generar_documentos_pims.py la escribe como documento PIMS-RG-01 (.docx);
  - scripts/cargar_documentos_pims.py la sincroniza con la tabla `lista_maestra_pims`;
  - documentos_pims.py (agente) la lee de la BD (o de aquí si la tabla está vacía) para
    saber qué documentos faltan en el control documental de cada auditoría.

Cada expediente D01–D37 de la guía del docente (Guia_documentos_ISO_27701_2025.pdf) queda
atendido por al menos un documento, salvo D36 (certificación externa, solo si se decide).
"""

G6 = "Grupo 6 – Evidencia y Auditoría"            # Agente 4 de la guía (nuestro grupo)
A1 = "Agente 1 – Inventario de datos"
A2 = "Agente 2 – Evaluación de riesgos"
A3 = "Agente 3 – Controles y SoA"
A5 = "Agente 5 – Derechos de los titulares"
A6 = "Agente 6 – Incidentes y brechas"
A7 = "Agente 7 – Terceros y encargados"
A8 = "Agente 8 – Formación y concienciación"
DIR = "Alta dirección – CGTD"

EQUIPOS = [G6, A1, A2, A3, A5, A6, A7, A8, DIR]

# marca de la guía: E exigida por la norma, C ligada a un control, S formato de apoyo
LISTA = [
    # código, título, tipo, requisitos (cláusulas y controles), expedientes, marca, equipo,
    # propietario, confidencialidad
    ("PIMS-MA-01", "Manual del PIMS: contexto, partes interesadas, alcance, procesos y roles", "manual",
     ["4.1", "4.2", "4.3", "4.4", "5.1", "5.3", "7.1", "7.4", "A.3.4", "A.3.13"],
     ["D01", "D02", "D03", "D07", "D09", "D37"], "E", DIR, "Oficial de Datos Personales", "Uso interno"),
    ("PIMS-POL-01", "Política de privacidad y protección de datos personales del PIMS", "política",
     ["5.1", "5.2", "A.3.3"], ["D08"], "E", A3, "Oficial de Datos Personales", "Público"),
    ("PIMS-PL-03", "Objetivos de privacidad y planificación para lograrlos", "plan",
     ["6.2", "6.3"], ["D10"], "E", DIR, "Oficial de Datos Personales", "Uso interno"),
    ("PIMS-RG-02", "Inventario y registro de actividades de tratamiento de datos personales", "registro",
     ["4.3", "A.1.2.2", "A.1.2.3", "A.1.2.9", "A.1.5.4"], ["D04", "D05", "D17"], "C", A1,
     "Coordinador de Datos Personales", "Confidencial"),
    ("PIMS-PR-09", "Procedimiento de minimización, calidad, conservación y eliminación de datos personales",
     "procedimiento", ["8.1", "A.1.4.2", "A.1.4.3", "A.1.4.4", "A.1.4.5", "A.1.4.6", "A.1.4.7", "A.1.4.8",
                       "A.1.4.9", "A.1.4.10"], ["D22"], "C", A1,
     "Coordinador de Datos Personales", "Uso interno"),
    ("PIMS-MT-01", "Metodología de evaluación y tratamiento de riesgos de privacidad", "metodología",
     ["6.1.1", "6.1.2", "6.1.3", "8.2"], ["D12"], "E", A2, "Oficial de Datos Personales", "Uso interno"),
    ("PIMS-IN-01", "Informe de evaluación y tratamiento de riesgos de privacidad y DPIA", "informe",
     ["6.1.2", "8.2", "8.3", "A.1.2.6"], ["D13", "D21"], "E", A2, "Oficial de Datos Personales",
     "Confidencial"),
    ("PIMS-RG-03", "Declaración de aplicabilidad (SoA)", "registro",
     ["6.1.3"], ["D14"], "E", A3, "Oficial de Seguridad y Confianza Digital", "Confidencial"),
    ("PIMS-PL-01", "Plan de tratamiento de riesgos de privacidad y control operacional", "plan",
     ["6.1.3", "6.3", "8.1", "8.3"], ["D15", "D16", "D31"], "E", A3,
     "Oficial de Seguridad y Confianza Digital", "Confidencial"),
    ("PIMS-PR-08", "Procedimiento de seguridad de la información para datos personales", "procedimiento",
     ["A.3.3", "A.3.5", "A.3.6", "A.3.7", "A.3.8", "A.3.9", "A.3.18", "A.3.19", "A.3.20", "A.3.21",
      "A.3.22", "A.3.23", "A.3.24", "A.3.25", "A.3.26", "A.3.27", "A.3.28", "A.3.29", "A.3.30", "A.3.31"],
     ["D16", "D26", "D27", "D29"], "C", A3,
     "Oficial de Seguridad y Confianza Digital", "Uso interno"),
    ("PIMS-PR-01", "Control de la información documentada y de los registros", "procedimiento",
     ["7.5", "A.3.14"], ["D11", "D29"], "E", G6, "Coordinador de Datos Personales", "Uso interno"),
    ("PIMS-RG-01", "Lista maestra de información documentada del PIMS", "registro",
     ["7.5"], ["D11"], "E", G6, "Coordinador de Datos Personales", "Uso interno"),
    ("PIMS-RG-05", "Registro de documentos de origen externo", "registro",
     ["7.5", "A.3.13"], ["D02", "D11"], "E", G6, "Coordinador de Datos Personales", "Uso interno"),
    ("PIMS-PR-02", "No conformidades y acciones correctivas", "procedimiento",
     ["10.1", "10.2"], ["D34"], "E", G6, "Oficial de Datos Personales", "Uso interno"),
    ("PIMS-FO-01", "Formulario de no conformidades y acciones correctivas", "formulario",
     ["10.2"], ["D34"], "E", G6, "Coordinador de Datos Personales", "Uso interno"),
    ("PIMS-PR-03", "Procedimiento y programa de auditoría interna", "procedimiento",
     ["9.2", "A.3.15", "A.3.16"], ["D33"], "E", G6, "Oficial de Datos Personales", "Uso interno"),
    ("PIMS-PR-04", "Seguimiento, medición, análisis y evaluación", "procedimiento",
     ["9.1"], ["D32"], "E", G6, "Oficial de Datos Personales", "Uso interno"),
    ("PIMS-IN-02", "Informe de auditoría interna AUD-2026-002", "informe",
     ["9.2", "10.2"], ["D06", "D33"], "E", G6, "Auditor líder del PIMS", "Confidencial"),
    ("PIMS-IN-03", "Informe trimestral de desempeño del PIMS (IV trimestre 2026)", "informe",
     ["9.1"], ["D32"], "E", G6, "Coordinador de Datos Personales", "Uso interno"),
    ("PIMS-PR-05", "Procedimiento de atención de solicitudes de derechos de los titulares", "procedimiento",
     ["8.1", "A.1.3.2", "A.1.3.7", "A.1.3.8", "A.1.3.9", "A.1.3.10", "A.1.3.11"], ["D20"], "C", A5,
     "Coordinador de Datos Personales", "Uso interno"),
    ("PIMS-PR-07", "Procedimiento de información a los titulares, avisos de privacidad y consentimiento",
     "procedimiento", ["A.1.2.2", "A.1.2.4", "A.1.2.5", "A.1.3.3", "A.1.3.4", "A.1.3.5", "A.1.3.6"],
     ["D18", "D19"],
     "C", A5, "Coordinador de Datos Personales", "Uso interno"),
    ("PIMS-PR-06", "Gestión de incidentes y brechas de datos personales", "procedimiento",
     ["A.3.11", "A.3.12"], ["D28"], "C", A6, "Oficial de Seguridad y Confianza Digital", "Uso interno"),
    ("PIMS-RG-04", "Registro de encargados, contratos, transferencias y divulgaciones", "registro",
     ["A.1.2.7", "A.1.2.8", "A.1.5.2", "A.1.5.3", "A.1.5.4", "A.1.5.5", "A.3.10"], ["D23", "D24", "D25"],
     "C", A7, "Oficial de Datos Personales", "Confidencial"),
    ("PIMS-PL-02", "Plan de capacitación y concienciación en privacidad", "plan",
     ["7.2", "7.3", "A.3.17"], ["D30"], "E", A8, "Jefe de la Unidad de Recursos Humanos", "Uso interno"),
    ("PIMS-RG-06", "Registro de competencias, formación y acuerdos de confidencialidad", "registro",
     ["7.2", "A.3.17", "A.3.18"], ["D30"], "E", A8, "Jefe de la Unidad de Recursos Humanos",
     "Restringido"),
    ("PIMS-AC-01", "Acta de revisión por la dirección del PIMS (sesión 1-2026)", "acta",
     ["9.3", "10.1"], ["D35"], "E", DIR, "Secretario(a) General", "Uso interno"),
]

# Expediente de la guía que no se abre en este ciclo, con su justificación (no es un faltante).
NO_APLICA = {
    "D36": "Expediente de certificación externa: la guía lo marca «X» (solo si se decide solicitarla). "
           "El CGTD acordó en PIMS-AC-01 evaluarla después de la auditoría interna AUD-2027-001.",
}

# Títulos de las cláusulas y de los controles del Anexo A de ISO/IEC 27701:2025 (A.1 responsable,
# A.3 seguridad), con la numeración que usan la guía del docente y el catálogo de la skill.
CLAUSULAS = {
    "4.1": "Comprensión de la organización y de su contexto",
    "4.2": "Necesidades y expectativas de las partes interesadas",
    "4.3": "Determinación del alcance del PIMS", "4.4": "Sistema de gestión de la privacidad",
    "5.1": "Liderazgo y compromiso", "5.2": "Política de privacidad",
    "5.3": "Roles, responsabilidades y autoridades",
    "6.1.1": "Acciones para abordar riesgos y oportunidades", "6.1.2": "Evaluación de riesgos de privacidad",
    "6.1.3": "Tratamiento de riesgos de privacidad", "6.2": "Objetivos de privacidad y planificación",
    "6.3": "Planificación de los cambios", "7.1": "Recursos", "7.2": "Competencia",
    "7.3": "Toma de conciencia", "7.4": "Comunicación", "7.5": "Información documentada",
    "8.1": "Planificación y control operacional", "8.2": "Evaluación de riesgos de privacidad (operación)",
    "8.3": "Tratamiento de riesgos de privacidad (operación)",
    "9.1": "Seguimiento, medición, análisis y evaluación", "9.2": "Auditoría interna",
    "9.3": "Revisión por la dirección", "10.1": "Mejora continua",
    "10.2": "No conformidad y acción correctiva",
}
CONTROLES_A1 = [
    ("A.1.2.2", "Identificar y documentar la finalidad"), ("A.1.2.3", "Identificar la base legal"),
    ("A.1.2.4", "Determinar cuándo y cómo obtener el consentimiento"),
    ("A.1.2.5", "Obtener y registrar el consentimiento"), ("A.1.2.6", "Evaluación de impacto en la privacidad"),
    ("A.1.2.7", "Contratos con encargados del tratamiento"), ("A.1.2.8", "Corresponsable del tratamiento"),
    ("A.1.2.9", "Registros relacionados con el tratamiento de PII"),
    ("A.1.3.2", "Determinar y cumplir las obligaciones con los titulares"),
    ("A.1.3.3", "Determinar la información para los titulares"),
    ("A.1.3.4", "Proporcionar información a los titulares"),
    ("A.1.3.5", "Mecanismo para modificar o retirar el consentimiento"),
    ("A.1.3.6", "Mecanismo para oponerse al tratamiento"), ("A.1.3.7", "Acceso, corrección o supresión"),
    ("A.1.3.8", "Obligación de informar a terceros"), ("A.1.3.9", "Entrega de copia de la PII tratada"),
    ("A.1.3.10", "Gestión de solicitudes"), ("A.1.3.11", "Toma de decisiones automatizada"),
    ("A.1.4.2", "Limitar la recogida"), ("A.1.4.3", "Limitar el tratamiento"),
    ("A.1.4.4", "Exactitud y calidad"), ("A.1.4.5", "Objetivos de minimización de PII"),
    ("A.1.4.6", "Desidentificación y supresión al final del tratamiento"), ("A.1.4.7", "Archivos temporales"),
    ("A.1.4.8", "Conservación"), ("A.1.4.9", "Eliminación"), ("A.1.4.10", "Controles de transmisión de PII"),
    ("A.1.5.2", "Base para la transferencia de PII entre jurisdicciones"),
    ("A.1.5.3", "Países y organizaciones internacionales a los que se transfiere PII"),
    ("A.1.5.4", "Registros de transferencias de PII"), ("A.1.5.5", "Registros de divulgación de PII a terceros"),
]
CONTROLES_A3 = [
    ("A.3.3", "Políticas de seguridad de la información"),
    ("A.3.4", "Roles y responsabilidades de seguridad de la información"),
    ("A.3.5", "Clasificación de la información"), ("A.3.6", "Etiquetado de la información"),
    ("A.3.7", "Transferencia de información"), ("A.3.8", "Gestión de identidades"),
    ("A.3.9", "Derechos de acceso"), ("A.3.10", "Seguridad en los acuerdos con proveedores"),
    ("A.3.11", "Planificación y preparación de la gestión de incidentes"),
    ("A.3.12", "Respuesta a incidentes de seguridad de la información"),
    ("A.3.13", "Requisitos legales, estatutarios, reglamentarios y contractuales"),
    ("A.3.14", "Protección de registros"), ("A.3.15", "Revisión independiente de la seguridad de la información"),
    ("A.3.16", "Cumplimiento de políticas, reglas y normas"), ("A.3.17", "Concienciación, educación y formación"),
    ("A.3.18", "Acuerdos de confidencialidad o no divulgación"), ("A.3.19", "Escritorio y pantalla limpios"),
    ("A.3.20", "Medios de almacenamiento"), ("A.3.21", "Eliminación segura o reutilización de equipos"),
    ("A.3.22", "Dispositivos de punto final de usuario"), ("A.3.23", "Autenticación segura"),
    ("A.3.24", "Copias de seguridad de la información"), ("A.3.25", "Registro de eventos"),
    ("A.3.26", "Uso de criptografía"), ("A.3.27", "Ciclo de vida de desarrollo seguro"),
    ("A.3.28", "Requisitos de seguridad de las aplicaciones"),
    ("A.3.29", "Arquitectura de sistemas y principios de ingeniería seguros"),
    ("A.3.30", "Desarrollo externalizado"), ("A.3.31", "Información de prueba"),
]
TITULOS = dict(CLAUSULAS, **dict(CONTROLES_A1), **dict(CONTROLES_A3))


def clave_ref(ref):
    """Orden natural: 4.1 < 10.2 < A.1.2.2 < A.1.2.10 < A.3.3."""
    partes = ref.split(".")
    return (partes[0] == "A",) + tuple(int(x) if x.isdigit() else 0 for x in partes if x != "A")


def documentos_por_requisito():
    """{ref: [codigos]} ordenado de forma natural."""
    salida = {}
    for f in LISTA:
        for r in f[3]:
            salida.setdefault(r, []).append(f[0])
    return dict(sorted(salida.items(), key=lambda kv: clave_ref(kv[0])))


CAMPOS = ("codigo", "titulo", "tipo", "requisitos", "expedientes", "marca", "equipo", "propietario",
          "confidencialidad")


def filas():
    """Lista de dicts en el orden de la lista maestra."""
    return [dict(zip(CAMPOS, f), orden=i) for i, f in enumerate(LISTA, 1)]


def por_codigo():
    """{codigo: (titulo, requisitos, expedientes, equipo)} (formato que usa documentos_pims)."""
    return {f[0]: (f[1], list(f[3]), list(f[4]), f[6]) for f in LISTA}


def expedientes_cubiertos():
    """{D-xx: [codigos]} para comprobar que todos los expedientes de la guía tienen documento."""
    salida = {}
    for f in LISTA:
        for d in f[4]:
            salida.setdefault(d, []).append(f[0])
    return salida
