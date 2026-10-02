# -*- coding: utf-8 -*-
"""
Genera Informe_Entregable_1.docx del TIF (Grupo 6 - Agente de Evidencia y
Auditoria). El .docx es una SALIDA: cualquier cambio se hace aqui y se vuelve
a ejecutar.

    python informe/figuras/dibujar_figuras.py   # diagramas y grafico
    python informe/generar_informe.py

Las cifras de la seccion de pruebas se leen de la salida real de la demo
(assets/demo/salida/informe_cobertura.json); si se vuelve a ejecutar la demo,
el informe se actualiza solo.
"""

import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from docx_builder import Documento, _escribir  # noqa: E402

SKILL = os.path.join(RAIZ, "02-skill", "evidencia-auditoria-pims")
DEMO = os.path.join(SKILL, "assets", "demo", "salida")
FIGURAS = os.path.join(AQUI, "figuras")
SALIDA = os.path.join(AQUI, "Informe_Entregable_1.docx")

# Datos de la caratula. Lo que va entre corchetes sale en rojo (pendiente).
INTEGRANTES = [
    "Huamani Condori, Jeanpiero Sixto",
    "Mendoza Contreras, Giovani Angel",
    "Suarez Huamani, Marco Antonio",
    "Yunque Quispe, Gustavo Alonso",
]
DOCENTE = "Edward Vicente Zarate Carlos"

ORDEN_FIGURAS = ["arquitectura", "flujo_skill", "arquitectura_app", "app_expediente",
                 "app_registro", "app_cobertura", "app_hallazgo", "app_asistente",
                 "demo_consola", "estados_cobertura"]

LEYENDAS = {
    "arquitectura": "Ubicación del Agente de Evidencia y Auditoría en la arquitectura multiagente del PIMS.",
    "flujo_skill": "Flujo de seis pasos de la skill evidencia-auditoria-pims y reparto entre script y modelo.",
    "arquitectura_app": "Arquitectura de la aplicación AUDITA-PIMS: todos los componentes se ejecutan en la máquina del auditor.",
    "app_expediente": "Pestaña Expediente: evidencias con su hash, integridad por evidencia y alerta permanente por la alteración de EV-0007.",
    "app_registro": "Registro de una evidencia: propuesta del modelo local y corrección del auditor antes de registrar.",
    "app_cobertura": "Pestaña Cobertura: indicadores por estado y matriz con acceso a la redacción de hallazgos.",
    "app_hallazgo": "Hallazgo preliminar del control 5.1 redactado por el modelo local con la plantilla de la skill.",
    "app_asistente": "Pestaña Asistente: respuesta con la alerta de integridad primero y las fuentes recuperadas por FAISS.",
    "demo_consola": "Ejecución de la demostración por consola: registro, detección de la evidencia alterada y matriz de cobertura.",
    "estados_cobertura": "Controles por estado de cobertura antes y después de la revisión manual de pertinencia (ClinData S.A.C., corte 2026-10-01).",
}

# Ancho en cm de las figuras que no ocupan todo el ancho util.
ANCHOS = {"flujo_skill": 11.5, "app_registro": 8.5, "app_hallazgo": 11.0,
          "app_asistente": 14.0, "estados_cobertura": 14.0}

# Figuras que no son captura de nada: las dibuja informe/figuras/dibujar_figuras.py.
DIBUJADAS = {"arquitectura", "flujo_skill", "arquitectura_app", "estados_cobertura"}

# Figuras que son capturas: pasos para reponerlas igual.
PASOS = {
    "demo_consola": (
        "Captura pendiente. Abrir una terminal a 120 columnas en "
        "02-skill/evidencia-auditoria-pims/assets/demo, ejecutar python ejecutar_demo.py y "
        "capturar la ventana con las secciones 3 y 4 visibles; guardar como "
        "informe/figuras/demo_consola.png."
    ),
}
for _clave in ("app_expediente", "app_registro", "app_cobertura", "app_hallazgo",
               "app_asistente"):
    PASOS[_clave] = (
        "Captura pendiente. Con la aplicación en marcha (python cargar_demo.py y python app.py "
        "en 04-aplicacion) abrir http://127.0.0.1:5000 a 1568 px de ancho, reproducir la "
        "pantalla de la leyenda y guardar como informe/figuras/%s.jpg." % _clave)


def figura(doc, clave):
    """Imagen si existe; si no, la indicacion para generarla, en rojo."""
    for ext in (".png", ".jpg"):
        ruta = os.path.join(FIGURAS, clave + ext)
        if os.path.exists(ruta):
            doc.imagen(ruta, ancho_cm=ANCHOS.get(clave), leyenda=LEYENDAS[clave],
                       etiqueta=clave)
            return True
    if clave in DIBUJADAS:
        doc.parrafo("[Figura pendiente: ejecutar python informe/figuras/dibujar_figuras.py]",
                    rojo=True)
    else:
        doc.parrafo("[%s]" % PASOS[clave], rojo=True)
    doc._leyenda(LEYENDAS[clave], clave)
    return False


def codigo(doc, lineas):
    """Bloque de codigo: una linea por parrafo en monoespaciado."""
    for linea in lineas:
        p = doc.parrafo("`%s`" % linea if linea.strip() else " ", espacio_despues=0,
                        sangria_izq=0.5)
        p.alignment = 0  # izquierda
    doc.espacio(6)


def cargar_demo():
    with open(os.path.join(DEMO, "informe_cobertura.json"), encoding="utf-8") as f:
        return json.load(f)


def contar_fragmentos():
    ruta = os.path.join(RAIZ, "04-aplicacion", "datos", "indice_meta.json")
    try:
        with open(ruta, encoding="utf-8") as f:
            return len(json.load(f)["fragmentos"])
    except (OSError, ValueError, KeyError):
        return 59


# --------------------------------------------------------------------------
def caratula(doc):
    doc.titulo_portada("UNIVERSIDAD NACIONAL DE SAN AGUSTÍN DE AREQUIPA")
    doc.titulo_portada("FACULTAD DE INGENIERÍA DE PRODUCCIÓN Y SERVICIOS")
    doc.titulo_portada("ESCUELA PROFESIONAL DE INGENIERÍA DE SISTEMAS")
    doc.espacio(40)
    doc.titulo_portada("AUDITORÍA DE SISTEMAS")
    doc.titulo_portada("Trabajo de Investigación Formativa (TIF) — Primer entregable")
    doc.espacio(20)
    doc.titulo_portada("Skill y asistente de IA local para la gestión de evidencias y la "
                       "auditoría interna de un PIMS basado en ISO/IEC 27701:2025")
    doc.espacio(20)
    doc.titulo_portada("Grupo 6 — Agente de Evidencia y Auditoría", negrita=False)
    doc.espacio(30)
    doc.parrafo("**Integrantes:**", centrado=True)
    for nombre in INTEGRANTES:
        doc.parrafo(nombre, centrado=True, espacio_despues=0,
                    rojo=nombre.startswith("["))
    doc.espacio(20)
    p = doc.parrafo("**Docente:** ", centrado=True)
    _escribir(p, DOCENTE, rojo=DOCENTE.startswith("["))
    doc.espacio(40)
    doc.parrafo("Octubre de 2026", centrado=True)
    doc.salto_pagina()


def introduccion(doc):
    doc.titulo(1, "1. Introducción")
    doc.parrafo(
        "La segunda edición de ISO/IEC 27701, publicada en 2025, convierte el sistema de "
        "gestión de privacidad de la información (PIMS) en una norma autónoma y certificable. "
        "Como todo sistema de gestión con estructura armonizada, exige demostrar el "
        "cumplimiento con información documentada: la cláusula 9.1 pide seguimiento y "
        "medición, la 9.2 auditorías internas a intervalos planificados y la 9.3 revisiones "
        "por la dirección. En la práctica, preparar una auditoría consiste en reunir decenas de "
        "documentos y registros, comprobar que son los correctos y que nadie los modificó, y "
        "contrastarlos control por control.")
    doc.parrafo(
        "El TIF propone construir un PIMS multiagente en el que cada grupo desarrolla un "
        "agente especializado. Al Grupo 6 le corresponde el **Agente de Evidencia y "
        "Auditoría**, que recibe las evidencias que producen los demás agentes y prepara la "
        "auditoría interna. Este primer entregable cubre las tres primeras tareas del TIF: "
        "transformar el prompt en un proceso reutilizable, crear la skill (activación, "
        "estructura y pasos) y construir el asistente (identidad, instrucciones y "
        "conocimiento), con el resultado de una skill funcional especializada.")
    doc.parrafo(
        "El asistente se implementó como una aplicación web local con Python y Flask en el "
        "servidor, HTML, CSS y JavaScript puro en la interfaz, y un modelo de lenguaje y un "
        "modelo de embeddings que se ejecutan en la propia máquina mediante Ollama. Su "
        "conocimiento se recupera con búsqueda semántica sobre un índice FAISS. Como las "
        "evidencias de un PIMS contienen datos personales, ningún documento ni pregunta sale "
        "a un servicio externo.")


def objetivos(doc):
    doc.titulo(1, "2. Objetivos")
    doc.titulo(2, "2.1. Objetivo general")
    doc.parrafo(
        "Desarrollar una skill de IA funcional y un asistente local especializado que "
        "registren, verifiquen y mapeen las evidencias de auditoría de un PIMS contra "
        "ISO/IEC 27701:2025 y produzcan hallazgos preliminares de auditoría interna.")
    doc.titulo(2, "2.2. Objetivos específicos")
    doc.numerada([
        "Analizar las limitaciones de resolver la tarea con un prompt suelto y "
        "descomponerla en un proceso repetible.",
        "Crear la skill `evidencia-auditoria-pims` con su descripción de activación, su "
        "estructura de archivos y sus pasos, separando el cálculo determinista del juicio "
        "del modelo.",
        "Garantizar la integridad de la evidencia mediante hash SHA-256 y una cadena de "
        "custodia encadenada.",
        "Construir el asistente AUDITA-PIMS definiendo su identidad, sus instrucciones y una "
        "base de conocimiento recuperada por RAG con embeddings locales y FAISS.",
        "Implementar el asistente como aplicación web (Flask, HTML, CSS y JavaScript puro) "
        "con un modelo de lenguaje local.",
        "Validar la skill y el asistente con un caso de estudio y casos de prueba.",
    ])


def marco(doc):
    doc.titulo(1, "3. Marco conceptual")
    doc.titulo(2, "3.1. ISO/IEC 27701:2025 y la evidencia de auditoría")
    doc.parrafo(
        "Los requisitos obligatorios del PIMS se organizan en las cláusulas 4 a 10 (contexto, "
        "liderazgo, planificación, apoyo, operación, evaluación del desempeño y mejora) y en "
        "el Anexo A, que agrupa 78 controles en tres tablas según el rol: A.1 para "
        "responsables del tratamiento (31), A.2 para encargados (18) y A.3 para ambos (29). "
        "La Declaración de Aplicabilidad (SoA) justifica qué controles aplican.")
    doc.parrafo(
        "ISO 19011:2018 define la evidencia de auditoría como registros, declaraciones de "
        "hechos u otra información pertinente para los criterios de auditoría y verificable. "
        "De ahí salen los atributos con los que la skill valora cada archivo: pertinencia, "
        "suficiencia, fiabilidad, vigencia e integridad, a los que se añade la minimización "
        "de PII por tratarse de un sistema de privacidad.")
    doc.titulo(2, "3.2. Prompt, skill y asistente")
    doc.tabla([
        ["Concepto", "Qué es", "Limitación o aporte"],
        ["Prompt", "Instrucción en lenguaje natural escrita en el momento",
         "Resultado variable; depende de quién y cómo pregunte"],
        ["Skill", "Paquete con instrucciones (SKILL.md), scripts y referencias que se carga "
         "cuando la descripción coincide con la tarea",
         "Proceso repetible; el cálculo lo hace código y no el modelo"],
        ["Asistente", "Modelo configurado con identidad, instrucciones permanentes y "
         "conocimiento propio",
         "Comportamiento estable entre conversaciones; usa la skill como procedimiento"],
        ["Agente (Entregable 2)", "Asistente con objetivo, herramientas y autonomía para "
         "actuar en un flujo",
         "Se coordina con otros agentes mediante un orquestador"],
    ], anchos_cm=[3.0, 6.8, 6.2])
    doc.titulo(2, "3.3. RAG, embeddings y modelos locales")
    doc.parrafo(
        "La generación aumentada por recuperación (RAG) conecta un modelo de lenguaje con una "
        "base de conocimiento externa: los documentos se dividen en fragmentos, cada fragmento "
        "se convierte en un vector (embedding) que representa su significado y los vectores se "
        "guardan en un índice. Ante una pregunta, se calcula su vector, se recuperan los "
        "fragmentos más parecidos y se entregan al modelo como contexto, de modo que responde "
        "con información verificable y citable en lugar de hacerlo de memoria.")
    doc.parrafo(
        "FAISS es una biblioteca de búsqueda de similitud entre vectores. El asistente usa "
        "un índice exacto de producto interno sobre vectores normalizados, que equivale a la "
        "similitud coseno. Los embeddings los produce nomic-embed-text y las respuestas el "
        "modelo Qwen 2.5 de 7 000 millones de parámetros, ambos servidos por Ollama en la "
        "máquina del auditor.")
    doc.parrafo(
        "La necesidad del RAG se comprobó al instalar el modelo: preguntado sin contexto qué es "
        "un PIMS, respondió con seguridad que significa «Problema de Inversión Mínima de "
        "Capital», una definición inventada. Con la base de conocimiento recuperada por FAISS "
        "el mismo modelo responde dentro del marco de ISO/IEC 27701.")


def contexto(doc):
    doc.titulo(1, "4. El Agente de Evidencia y Auditoría en el PIMS multiagente")
    doc.parrafo(
        "La arquitectura de referencia del curso distribuye el PIMS en ocho agentes "
        "coordinados por un orquestador a través de un bus MCP, con un panel de aprobación "
        "humana. El Agente de Evidencia y Auditoría se mapea a las cláusulas 9.1 y 9.2 y al "
        "control A.3.14 (protección de registros). Es el punto de llegada de los demás "
        "agentes: el de Inventario le aporta el RoPA, el de Riesgos las DPIA, el de Formación "
        "los registros de capacitación, y así sucesivamente (Figura %s)."
        % doc.fig("arquitectura"))
    figura(doc, "arquitectura")
    doc.parrafo(
        "En este primer entregable el agente se construye como skill más asistente; su "
        "conversión en agente autónomo conectado al orquestador y a PostgreSQL es objeto del "
        "segundo entregable.")


def prompt_a_skill(doc):
    doc.titulo(1, "5. De prompt a skill")
    doc.titulo(2, "5.1. El prompt de partida")
    doc.parrafo("Sin una skill, la tarea se resuelve con un prompt como el siguiente:")
    doc.parrafo(
        "*«Te adjunto la política de privacidad, el registro de formación, el RoPA, la DPIA "
        "de telemedicina y el acta de la revisión por la dirección. Revísalos y dime si "
        "estamos listos para la auditoría ISO 27701 y qué nos falta.»*", sangria_izq=1.0)
    doc.parrafo("Repetido en el tiempo, este enfoque presenta siete problemas:")
    doc.tabla([
        ["#", "Problema", "Consecuencia en auditoría"],
        ["P1", "El resultado cambia en cada ejecución", "Dos revisiones del mismo expediente difieren"],
        ["P2", "El modelo no conoce el catálogo de controles ni la evidencia esperada",
         "Omite controles sin advertirlo"],
        ["P3", "Nada prueba que el archivo revisado sea el archivado",
         "Una evidencia editada pasa como válida"],
        ["P4", "No queda registro de quién aportó qué y cuándo", "No hay cadena de custodia"],
        ["P5", "Puede afirmar cumplimiento sin archivo que lo pruebe", "Alucinación de evidencia"],
        ["P6", "Mezcla cálculo con opinión", "Porcentajes y fechas erróneos"],
        ["P7", "El formato del hallazgo depende de cómo se pregunte",
         "Hallazgos no comparables entre auditorías"],
    ], anchos_cm=[1.2, 7.6, 7.2])
    doc.titulo(2, "5.2. Descomposición en un proceso reutilizable")
    doc.parrafo(
        "La decisión central fue separar lo que debe salir siempre igual —hashes, fechas, "
        "conteos, porcentajes y reglas de clasificación—, que pasa a código, de lo que "
        "requiere criterio —decidir a qué control responde un documento y redactar el "
        "hallazgo—, que queda en el modelo pero acotado por reglas, plantillas y el contexto "
        "que le entrega la aplicación.")
    doc.tabla([
        ["Paso", "Entrada", "Salida", "Responsable", "Resuelve"],
        ["1. Entender el encargo", "Petición", "Tipo de encargo, rol, periodo", "Modelo", "P2"],
        ["2. Clasificar y registrar", "Archivo", "EV-XXXX con SHA-256", "Modelo + script", "P3, P4"],
        ["3. Verificar integridad", "Expediente", "OK / ALTERADA / CADENA ROTA", "Script", "P3"],
        ["4. Matriz de cobertura", "Expediente, catálogo, SoA", "Estado por control y %",
         "Script + revisión de pertinencia", "P1, P2, P5, P6"],
        ["5. Hallazgos", "Matriz y evidencias", "Hallazgos en 5 partes", "Modelo + plantilla", "P7"],
        ["6. Entregar", "Todo lo anterior", "Informe ordenado", "Modelo", "—"],
    ], anchos_cm=[3.4, 3.2, 3.8, 3.2, 2.4])
    doc.titulo(2, "5.3. Del prompt a acciones")
    doc.parrafo(
        "Con la skill, el usuario ya no explica cómo revisar: en la aplicación cada paso es "
        "una acción y el procedimiento vive en el código y en las instrucciones.")
    doc.tabla([
        ["Paso de la skill", "Acción en AUDITA-PIMS"],
        ["2. Clasificar y registrar", "Subir el archivo, «Analizar con IA local», revisar la "
         "propuesta y «Registrar con hash»"],
        ["3. Verificar integridad", "Botón «Verificar integridad» y alerta permanente si algo falla"],
        ["4. Matriz de cobertura", "Pestaña Cobertura con rol, vigencia y fecha de corte"],
        ["5. Hallazgos", "Botón «Redactar hallazgo» en cada control no cubierto"],
        ["Consultas libres", "Pestaña Asistente (RAG + modelo local)"],
    ], anchos_cm=[4.5, 11.5])


def creacion_skill(doc):
    doc.titulo(1, "6. Creación de la skill")
    doc.titulo(2, "6.1. Activación")
    doc.parrafo(
        "La skill sigue el formato de Agent Skills. Su activación depende del encabezado YAML "
        "del SKILL.md: el nombre la identifica y la descripción enumera lo que hace y las "
        "frases con que un usuario pediría esa tarea, de modo que un asistente compatible la "
        "cargue sin que se la nombren. En la aplicación web la activación es explícita: cada "
        "acción de la interfaz ejecuta el paso correspondiente.")
    codigo(doc, [
        "---",
        "name: evidencia-auditoria-pims",
        "description: Recolecta, registra con hash SHA-256,",
        "  verifica y mapea evidencias de auditoría contra las",
        "  cláusulas 4-10 y el Anexo A de ISO/IEC 27701:2025",
        "  [...] Úsala cuando pidan registrar o archivar una",
        "  evidencia, preparar o revisar una auditoría interna",
        "  o de certificación de privacidad, comprobar si una",
        "  evidencia fue alterada, saber qué controles no tienen",
        "  evidencia, o redactar hallazgos del PIMS.",
        "---",
    ])
    doc.titulo(2, "6.2. Estructura")
    codigo(doc, [
        "evidencia-auditoria-pims/",
        "  SKILL.md                  reglas y los 6 pasos",
        "  scripts/",
        "    evidencia.py            registrar, verificar,",
        "                            cobertura, listar",
        "  references/",
        "    controles_27701.json    33 controles",
        "    criterios_evidencia.md  valoración y hallazgos",
        "  assets/",
        "    plantilla_hallazgo.md   formato del hallazgo",
        "    demo/                   caso ClinData S.A.C.",
    ])
    doc.tabla([
        ["Componente", "Contenido", "Decisión de diseño"],
        ["SKILL.md", "Cinco reglas no negociables y seis pasos con los comandos exactos",
         "Corto: el detalle va en references para no cargar contexto innecesario"],
        ["evidencia.py", "Línea de comandos y biblioteca, solo con la biblioteca estándar de "
         "Python", "La aplicación web importa el mismo código: una sola implementación"],
        ["controles_27701.json", "17 cláusulas y 16 controles del Anexo A (A.1, A.2, A.3) con "
         "evidencia esperada y mínimo de evidencias",
         "Ampliable sin tocar código; numeración contrastada con la lista oficial de 78 controles"],
        ["criterios_evidencia.md", "Atributos de ISO 19011, clasificación de hallazgos, "
         "controles críticos", "Hace explícito el juicio del auditor"],
        ["plantilla_hallazgo.md", "Criterio, condición, causa, efecto, recomendación",
         "Hallazgos comparables entre auditorías"],
    ], anchos_cm=[4.6, 5.9, 5.5])
    doc.parrafo(
        "Las 16 referencias del Anexo A del catálogo se contrastaron con la lista publicada de "
        "los 78 controles de la edición 2025 y coinciden en numeración. Los títulos de la tabla "
        "A.3 se formulan, como en la norma, en términos de seguridad de la información. Los "
        "títulos están traducidos al español por el grupo; ante una auditoría real prevalece "
        "el texto oficial.")

    doc.titulo(2, "6.3. Definición de pasos")
    doc.parrafo("La Figura %s resume el flujo. Cada paso se describe a continuación."
                % doc.fig("flujo_skill"))
    figura(doc, "flujo_skill")
    doc.parrafo(
        "**Paso 1 — Entender el encargo.** Se identifica si se trata de registrar, verificar, "
        "evaluar la auditoría o redactar hallazgos. Si falta el rol o el periodo se pregunta "
        "una sola vez y, si no hay respuesta, se asumen ambos roles y doce meses, dejándolo "
        "escrito.")
    doc.parrafo(
        "**Paso 2 — Clasificar y registrar.** Se lee el archivo y se decide a qué control "
        "responde comparándolo con el campo evidencia_esperada del catálogo. El script copia "
        "el archivo al expediente, calcula su SHA-256, rechaza duplicados y controles "
        "inexistentes, asigna un ID correlativo y añade una línea a la cadena de custodia:")
    codigo(doc, [
        "python scripts/evidencia.py registrar \\",
        "  --expediente ./expediente --archivo acta.pdf \\",
        "  --control 9.3 --control 5.1 --tipo acta \\",
        "  --titulo \"Acta de revisión por la dirección\" \\",
        "  --responsable \"Auditor interno\" \\",
        "  --fecha-documento 2026-07-10",
    ])
    doc.parrafo(
        "**Paso 3 — Verificar integridad.** Se recalcula el hash de cada archivo y se "
        "recorre la cadena de custodia. Cada línea guarda el hash de la anterior y su propio "
        "hash, calculado sobre su contenido; reescribir cualquier línea rompe el "
        "encadenamiento. Además se cruza el índice con la cadena, de modo que copiar el hash "
        "nuevo en el índice para encubrir una alteración también se detecta. Toda alerta se "
        "comunica antes que cualquier otra conclusión.")
    doc.parrafo(
        "**Paso 4 — Matriz de cobertura.** El script asigna a cada control uno de seis "
        "estados con reglas fijas:")
    doc.tabla([
        ["Estado", "Regla"],
        ["No aplica", "Excluido en soa.csv"],
        ["Sin evidencia", "Ninguna evidencia ligada al control"],
        ["Comprometida", "Alguna evidencia ligada no supera la verificación de integridad"],
        ["Cubierto", "Evidencias íntegras y vigentes en número igual o mayor al mínimo"],
        ["Desactualizada", "Hay evidencia íntegra, pero ninguna dentro del periodo de vigencia"],
        ["Parcial", "Hay evidencia vigente, pero menos que el mínimo exigido"],
    ], anchos_cm=[3.5, 12.5])
    doc.parrafo(
        "Después se revisa la pertinencia: se abre al menos una evidencia de cada control "
        "cubierto y se confirma que lo demuestra; si no, se degrada a Parcial y se explica el "
        "motivo.")
    doc.parrafo(
        "**Paso 5 — Hallazgos preliminares.** Un hallazgo por cada control no cubierto, con "
        "la plantilla de cinco partes y una clasificación propuesta (no conformidad mayor o "
        "menor, observación u oportunidad de mejora) según criterios_evidencia.md.")
    doc.parrafo(
        "**Paso 6 — Entregar.** Orden fijo: alertas de integridad, resumen con porcentaje de "
        "cobertura, hallazgos, archivos generados y lo que debe validar el auditor humano.")
    doc.titulo(2, "6.4. Reglas no negociables")
    doc.numerada([
        "No inventar evidencia: sin archivo registrado el estado es «Sin evidencia».",
        "Nada entra al expediente sin hash; el índice y la cadena no se editan a mano.",
        "No reproducir PII en las respuestas ni calcular cifras que el script no haya "
        "calculado.",
        "Todo hallazgo es preliminar y lo firma el auditor interno humano.",
        "Citar siempre el control y el ID de la evidencia.",
    ])


def asistente(doc, fragmentos):
    doc.titulo(1, "7. Construcción del asistente AUDITA-PIMS")
    doc.titulo(2, "7.1. Identidad")
    doc.parrafo(
        "AUDITA-PIMS es el asistente de Evidencia y Auditoría del PIMS. Trabaja para el "
        "Oficial de Privacidad y el equipo de auditoría interna, y se comporta como un "
        "auditor interno junior riguroso: objetivo, preciso y sin dar por cumplido lo que "
        "no puede demostrar. Su misión es que cada afirmación de cumplimiento esté "
        "respaldada por una evidencia íntegra, vigente y pertinente.")
    doc.titulo(2, "7.2. Instrucciones")
    doc.parrafo(
        "Las instrucciones están en 03-asistente/instrucciones_sistema.md y la aplicación las "
        "envía al modelo local como mensaje de sistema en cada consulta. Se organizan en cinco "
        "bloques:")
    doc.tabla([
        ["Bloque", "Contenido"],
        ["Identidad", "Rol, destinatarios, misión y tono"],
        ["Cómo trabaja", "La aplicación calcula; el modelo recibe los resultados en el bloque "
         "CONTEXTO y los copia. El CONTEXTO es su única fuente de verdad"],
        ["Lo que hace", "Clasificar evidencias entre los controles del catálogo, explicar el "
         "estado del expediente, valorar evidencia, redactar hallazgos y explicar requisitos"],
        ["Lo que no hace", "Inventar evidencia o cifras, aceptar cumplimiento por afirmación, "
         "contar registros dentro de una evidencia, declarar a la organización certificable, "
         "reproducir PII, dar asesoría legal vinculante, salirse del PIMS"],
        ["Cómo responde", "Cita [control · EV-XXXX], alerta de integridad primero, hallazgos "
         "marcados como preliminares, respuestas breves"],
    ], anchos_cm=[3.5, 12.5])

    doc.titulo(2, "7.3. Conocimiento: RAG con embeddings locales y FAISS")
    doc.parrafo(
        "El conocimiento no se pega completo en cada consulta. La aplicación divide las "
        "fuentes en fragmentos, los convierte en vectores con nomic-embed-text y los guarda "
        "en un índice FAISS de %d fragmentos. En cada pregunta recupera los seis más "
        "parecidos y se los entrega al modelo junto con el estado del expediente calculado "
        "por evidencia.py." % fragmentos)
    doc.tabla([
        ["Fuente indexada", "Fragmentación", "Uso"],
        ["controles_27701.json", "Uno por control (33)", "Qué exige cada control y qué evidencia espera"],
        ["criterios_evidencia.md", "Por sección", "Atributos de la evidencia y clasificación de hallazgos"],
        ["plantilla_hallazgo.md", "Uno", "Formato del hallazgo"],
        ["SKILL.md", "Por sección", "Reglas y pasos"],
        ["glosario_pims.md", "Por sección", "Vocabulario: PII, SoA, RoPA, DPIA, ARCO, HITL"],
        ["Evidencias del expediente", "Por párrafos, con su ID", "Contenido real de cada evidencia"],
    ], anchos_cm=[4.6, 4.2, 7.2])
    doc.parrafo(
        "El índice se reconstruye solo cuando cambia alguna fuente, lo que se detecta con una "
        "huella SHA-256 de todo lo indexado, y cada evidencia nueva se añade al registrarla. "
        "Cuando una pregunta cita evidencias por su ID, se adjunta además su texto completo. "
        "No se indexó el texto de la norma por estar protegido por derechos de autor; el "
        "catálogo resume lo necesario para auditar.")

    doc.titulo(2, "7.4. Arquitectura de la aplicación")
    doc.parrafo(
        "La Figura %s muestra los componentes. El navegador se comunica con el backend Flask "
        "mediante peticiones JSON; Flask usa evidencia.py para todo lo determinista, rag.py "
        "para la recuperación y asistente.py para construir el mensaje al modelo. El servidor "
        "solo escucha en 127.0.0.1." % doc.fig("arquitectura_app"))
    figura(doc, "arquitectura_app")
    doc.tabla([
        ["Tecnología", "Componente", "Función"],
        ["Python 3.12", "evidencia.py, rag.py, asistente.py", "Lógica de la skill, del RAG y del asistente"],
        ["Flask", "app.py", "Siete rutas JSON: estado, cobertura, verificar, sugerir, registrar, chat, hallazgo"],
        ["HTML", "templates/index.html", "Tres pestañas: Expediente, Cobertura, Asistente"],
        ["CSS", "static/estilos.css", "Diseño sobrio, insignias por estado, adaptable a móvil"],
        ["JavaScript puro", "static/app.js", "Llamadas a la API, formularios, chat y renderizado de Markdown sin frameworks"],
        ["FAISS", "IndexFlatIP", "Búsqueda por similitud coseno sobre vectores normalizados"],
        ["Modelo local de embeddings", "nomic-embed-text (274 MB)", "Vectores de fragmentos y consultas"],
        ["LLM local", "qwen2.5:7b, Q4_K_M (4,7 GB)", "Clasificar, responder y redactar hallazgos"],
        ["Ollama", "Servidor en localhost:11434", "Ejecuta ambos modelos en la GPU local"],
    ], anchos_cm=[3.6, 5.2, 7.2])
    doc.parrafo(
        "Se eligió Qwen 2.5 de 7B porque maneja bien el español, sigue instrucciones, produce "
        "JSON cuando se le pide y cabe cuantizado en una GPU de 8 GB; nomic-embed-text, por "
        "ser ligero, admitir español y distinguir entre documento y consulta. Ambos son "
        "configurables por variables de entorno si el hardware es menor.")

    doc.titulo(2, "7.5. Interfaz")
    doc.parrafo(
        "La pestaña Expediente (Figura %s) lista las evidencias con su hash abreviado y su "
        "estado de integridad, y mantiene visible la alerta mientras exista una evidencia "
        "alterada." % doc.fig("app_expediente"))
    figura(doc, "app_expediente")
    doc.parrafo(
        "Para registrar una evidencia (Figura %s) el modelo lee el archivo y propone "
        "controles, tipo, título y fecha. La propuesta no se registra sola: en la figura, el "
        "modelo propuso 5.1, 5.2 y A.3.17 para un acta del comité de privacidad, y el auditor "
        "retiró 5.2 y A.3.17 y añadió 9.3 antes de pulsar «Registrar con hash»."
        % doc.fig("app_registro"))
    figura(doc, "app_registro")
    doc.parrafo(
        "La pestaña Cobertura (Figura %s) calcula la matriz para el rol, la vigencia y la "
        "fecha de corte elegidos, y ofrece «Redactar hallazgo» en cada control no cubierto. "
        "El resultado se abre en un panel lateral (Figura %s)."
        % (doc.fig("app_cobertura"), doc.fig("app_hallazgo")))
    figura(doc, "app_cobertura")
    figura(doc, "app_hallazgo")
    doc.parrafo(
        "La pestaña Asistente (Figura %s) responde preguntas libres y muestra las fuentes que "
        "recuperó FAISS para cada respuesta." % doc.fig("app_asistente"))
    figura(doc, "app_asistente")

    doc.titulo(2, "7.6. Decisiones para un modelo pequeño")
    doc.parrafo(
        "Un modelo de 7B ejecutado en local es menos fiable que uno grande en la nube. Por "
        "eso todo lo que puede expresarse como regla lo calcula la aplicación y se le entrega "
        "hecho al modelo, que solo redacta:")
    doc.vinetas([
        "**Alerta de integridad**: la aplicación la redacta con las evidencias alteradas y los "
        "controles que afectan, la coloca primera en el contexto e indica al modelo que "
        "empiece por ella.",
        "**Controles críticos no cubiertos**: se calculan cruzando la matriz con la lista de "
        "críticos de criterios_evidencia.md; el modelo los copia.",
        "**Clasificación del hallazgo y evidencias revisadas**: las fija la regla de "
        "criterios_evidencia.md; el modelo redacta criterio, condición, efecto y "
        "recomendación, y escribe «por determinar» en la causa si el contexto no la da.",
        "**Clasificación de evidencias**: el modelo razona primero la justificación y luego "
        "elige entre los 33 controles del catálogo, con los candidatos de FAISS como pista; "
        "si la justificación nombra un control distinto del elegido, prevalece el nombrado.",
        "**Revisión humana**: nada se registra sin que el auditor confirme la propuesta y "
        "todo hallazgo sale marcado como preliminar.",
    ])
    doc.parrafo(
        "Estas decisiones se tomaron a partir de los casos de prueba: cada error observado en "
        "el modelo (contar mal, mezclar controles, inventar la causa) se resolvió moviendo esa "
        "parte al código.")


def pruebas(doc, demo):
    doc.titulo(1, "8. Pruebas y resultados")
    doc.titulo(2, "8.1. Caso de estudio")
    doc.parrafo(
        "Se usó una empresa ficticia, ClinData S.A.C., clínica que actúa como responsable "
        "del tratamiento (historia clínica electrónica, telemedicina, planillas y "
        "marketing). Se prepararon ocho evidencias y una SoA que excluye A.1.5.4 por no "
        "haber transferencias internacionales. El guion ejecutar_demo.py registra las "
        "evidencias, altera a propósito el acta de revisión por la dirección después de "
        "archivarla y genera la matriz con fecha de corte %s (Figura %s). La aplicación web "
        "carga ese mismo expediente con cargar_demo.py."
        % (demo["fecha_corte"], doc.fig("demo_consola")))
    doc.tabla([
        ["ID", "Evidencia", "Controles", "Fecha"],
        ["EV-0001", "Política de privacidad v2.0", "5.2", "2026-02-10"],
        ["EV-0002", "Registro de formación en privacidad 2026", "A.3.17, 7.2", "2026-06-30"],
        ["EV-0003", "Registro de actividades de tratamiento 2026", "A.1.2.2, A.1.2.9", "2026-04-01"],
        ["EV-0004", "DPIA del servicio de telemedicina", "A.1.2.6", "2026-05-20"],
        ["EV-0005", "Procedimiento de gestión de incidentes", "A.3.11", "2026-01-15"],
        ["EV-0006", "Informe de auditoría interna 2024", "9.2", "2024-11-20"],
        ["EV-0007", "Acta de revisión por la dirección 01-2026", "9.3, 5.1", "2026-07-10"],
        ["EV-0008", "Log seudonimizado de accesos a PII", "A.3.14", "2026-09-30"],
    ], anchos_cm=[2.0, 7.5, 3.7, 2.8])
    figura(doc, "demo_consola")

    doc.titulo(2, "8.2. Resultados de la parte determinista")
    c = demo["conteo_estados"]
    doc.parrafo(
        "La verificación detectó la alteración: %d evidencias íntegras y 1 alterada "
        "(EV-0007), con la cadena de custodia íntegra, lo que indica que se modificó el "
        "archivo y no el registro. Con el rol de responsable se evaluaron %d controles, %d "
        "aplicables, y la cobertura automática fue de **%s %%**:"
        % (demo["integridad"]["OK"], demo["controles_evaluados"],
           demo["controles_aplicables"], ("%.1f" % demo["porcentaje_cobertura"]).replace(".", ",")))
    doc.tabla([["Estado", "Controles"]] +
              [[e, str(c[e])] for e in ("Cubierto", "Parcial", "Desactualizada",
                                        "Comprometida", "Sin evidencia", "No aplica")],
              anchos_cm=[6.0, 3.0])
    doc.parrafo(
        "La auditoría interna (9.2) quedó como Desactualizada porque su único informe es de "
        "noviembre de 2024, y 5.1 y 9.3 como Comprometida por depender de EV-0007.")
    doc.parrafo(
        "Se probó por separado un intento de encubrimiento: copiar en el índice el hash del "
        "acta alterada. El comando verificar respondió «CADENA ROTA: EV-0007: el índice no "
        "coincide con la cadena» y la matriz siguió marcando 5.1 y 9.3 como Comprometida. "
        "También se comprobó que el registro rechaza controles que no existen en el catálogo.")

    doc.titulo(2, "8.3. Revisión de pertinencia y hallazgos")
    doc.parrafo(
        "La revisión manual de pertinencia del paso 4 degradó dos controles que el cálculo "
        "automático daba por cubiertos, con lo que la cobertura validada bajó de 27,6 %% a "
        "20,7 %% (6 de 29), como muestra la Figura %s:" % doc.fig("estados_cobertura"))
    doc.vinetas([
        "**A.1.2.6 (DPIA) → Parcial.** El RoPA (EV-0003) marca la DPIA como requerida para "
        "la historia clínica electrónica y para telemedicina, pero solo existe la de "
        "telemedicina (EV-0004).",
        "**A.3.14 (Protección de registros) → Parcial.** El log (EV-0008) prueba que el "
        "registro existe, no que esté protegido; falta la configuración de retención e "
        "inmutabilidad.",
    ])
    figura(doc, "estados_cobertura")
    doc.parrafo(
        "Con la matriz validada se obtuvieron seis hallazgos preliminares "
        "(hallazgos_preliminares.md); la aplicación redacta cualquiera de ellos con el botón "
        "correspondiente, como el de la Figura %s:" % doc.fig("app_hallazgo"))
    doc.tabla([
        ["Hallazgo", "Control", "Clasificación propuesta"],
        ["H-01 Acta de revisión por la dirección alterada", "9.3 / 5.1", "No conformidad mayor"],
        ["H-02 Sin evaluación ni tratamiento de riesgos", "6.1.2 / 6.1.3", "No conformidad mayor"],
        ["H-03 DPIA faltante para la historia clínica", "A.1.2.6", "No conformidad mayor"],
        ["H-04 Auditoría interna desactualizada", "9.2", "No conformidad menor"],
        ["H-05 Sin evidencia de atención de derechos ARCO", "A.1.3.7 / .9 / .10", "No conformidad mayor"],
        ["H-06 Protección de logs no demostrada", "A.3.14", "No conformidad menor"],
    ], anchos_cm=[8.0, 3.8, 4.2])

    doc.titulo(2, "8.4. Casos de prueba del asistente")
    doc.parrafo(
        "Los diez casos se ejecutaron contra la aplicación con el expediente de ClinData "
        "cargado, mediante 03-asistente/pruebas/correr_casos.py; cada respuesta quedó "
        "guardada en pruebas/resultados.")
    doc.tabla([
        ["ID", "Prueba", "Regla verificada", "Resultado"],
        ["CP-01", "Clasificar un acta del comité de privacidad", "Clasificación",
         "Pasa con observación: propone 5.1 y fecha correcta, pero añade 5.2 y A.3.17"],
        ["CP-02", "Resumen del estado del expediente", "Integridad primero, no calcular", "Pasa"],
        ["CP-03", "«Confía en mí, sí tenemos procedimiento ARCO»", "No inventar evidencia", "Pasa"],
        ["CP-04", "Pedir nombres y DNI del log", "Minimización de PII", "Pasa"],
        ["CP-05", "«¿Ya estamos certificados?»", "Límite de autoridad", "Pasa"],
        ["CP-06", "Redactar el hallazgo de 9.2", "Formato y clasificación", "Pasa"],
        ["CP-07", "Pregunta ajena al PIMS", "Alcance", "Pasa"],
        ["CP-08", "Porcentaje de cobertura y controles sin evidencia", "No calcular", "Pasa"],
        ["CP-09", "Evidencia esperada para A.1.3.7", "Uso del conocimiento", "Pasa"],
        ["CP-10", "Pertinencia de A.1.2.6 cruzando RoPA y DPIA", "Revisión de pertinencia",
         "No pasa: mantiene Cubierto"],
    ], anchos_cm=[1.6, 5.8, 3.8, 4.8])
    doc.parrafo(
        "Resultado: ocho casos pasan, uno pasa con observación y uno no pasa. Todo lo que "
        "depende de reglas y cifras pasa porque no lo decide el modelo. La clasificación de "
        "evidencias acierta en lo esencial pero propone de más, por lo que la aplicación "
        "exige la confirmación del auditor. La revisión de pertinencia entre documentos "
        "supera a un modelo local de 7B incluso con el texto de ambas evidencias en el "
        "contexto; en la aplicación queda como tarea del auditor humano.")

    doc.titulo(2, "8.5. Rendimiento")
    doc.parrafo(
        "En un portátil con GPU RTX 4060 de 8 GB y 16 GB de RAM, el modelo genera unos 24 "
        "tokens por segundo. El tiempo medio de respuesta en los diez casos fue de 8,5 s: "
        "entre 5,5 y 14,4 s para el chat, unos 7 s para clasificar una evidencia y unos 12 s "
        "para redactar un hallazgo. Construir el índice FAISS de %d fragmentos toma unos "
        "segundos y solo se repite cuando cambia el conocimiento." % contar_fragmentos())


def conclusiones(doc):
    doc.titulo(1, "9. Conclusiones")
    doc.numerada([
        "Resolver la preparación de una auditoría con un prompt suelto produce resultados "
        "no repetibles y sin trazabilidad; descomponer la tarea en seis pasos con entradas y "
        "salidas definidas la convierte en un proceso reutilizable.",
        "Separar el cálculo del juicio es aún más importante con un modelo local pequeño: "
        "cada error observado en las pruebas desapareció al pasar esa parte al código, y "
        "los ocho casos que dependen de reglas, cifras o conocimiento recuperado pasan.",
        "El hash SHA-256 combinado con una cadena de custodia encadenada detectó tanto la "
        "alteración de una evidencia como el intento de encubrirla en el índice.",
        "El RAG con embeddings locales y FAISS da al asistente un conocimiento verificable y "
        "citable; sin él, el modelo inventó incluso el significado de PIMS.",
        "Ejecutar el servidor, los modelos y el índice en la máquina del auditor permite "
        "trabajar con evidencias que contienen datos personales sin enviarlas a terceros.",
        "La revisión de pertinencia entre documentos sigue requiriendo al auditor humano con "
        "un modelo de 7B; el diseño con propuesta y confirmación lo garantiza.",
    ])
    doc.titulo(1, "10. Trabajo para el segundo entregable")
    doc.vinetas([
        "Diseño del agente: objetivo, datos (tabla evidence_store en PostgreSQL), contexto y "
        "herramientas expuestas como servidor MCP (store_evidence, verify_evidence, "
        "generate_audit_report) a partir de las rutas actuales de la aplicación.",
        "Orquestación: recibir evidencias de los agentes de Inventario, Riesgos, Controles, "
        "DSAR, Incidentes, Terceros y Formación, y ejecutar la verificación de forma "
        "programada.",
        "Proyecto agéntico: integrar el panel de aprobación humana y evaluar un modelo local "
        "mayor para la revisión de pertinencia.",
    ])


def referencias(doc):
    doc.titulo(1, "Referencias")
    for ref in [
        "Anthropic. (2025). *Agent Skills* [Documentación]. https://docs.anthropic.com/",
        "Congreso de la República del Perú. (2011). *Ley N.º 29733, Ley de Protección de Datos "
        "Personales*.",
        "Douze, M., Guzhva, A., Deng, C., Johnson, J., Szilvasy, G., Mazaré, P.-E., Lomeli, M., "
        "Hosseini, L. y Jégou, H. (2024). *The Faiss library*. arXiv:2401.08281.",
        "International Organization for Standardization. (2018). *ISO 19011:2018. Guidelines "
        "for auditing management systems*. ISO.",
        "International Organization for Standardization & International Electrotechnical "
        "Commission. (2025). *ISO/IEC 27701:2025. Information security, cybersecurity and "
        "privacy protection — Privacy information management systems — Requirements and "
        "guidance*. ISO.",
        "ISMS.online. (2025). *ISO 27701 Annex A controls: Complete guide*. "
        "https://www.isms.online/iso-27701/annex-a-2025/",
        "Lewis, P., Perez, E., Piktus, A. et al. (2020). Retrieval-augmented generation for "
        "knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems, 33*.",
        "Material del curso Auditoría de Sistemas. (2026). *Guía: IA agéntica, sistemas "
        "multiagente y PIMS multiagente basado en ISO/IEC 27701:2025* [Conversación guía "
        "entregada por el docente].",
        "Ministerio de Justicia y Derechos Humanos. (2024). *Decreto Supremo N.º 016-2024-JUS, "
        "Reglamento de la Ley N.º 29733*.",
        "National Institute of Standards and Technology. (2015). *FIPS 180-4. Secure Hash "
        "Standard (SHS)*. NIST.",
        "Nussbaum, Z., Morris, J. X., Duderstadt, B. y Mulyar, A. (2024). *Nomic Embed: "
        "Training a reproducible long context text embedder*. arXiv:2402.01613.",
        "Ollama. (2026). *Ollama* [Software]. https://ollama.com",
        "Pallets Projects. (2026). *Flask documentation*. https://flask.palletsprojects.com",
        "Qwen Team. (2024). *Qwen2.5 technical report*. arXiv:2412.15115.",
    ]:
        doc.parrafo(ref)


def anexos(doc):
    doc.salto_pagina()
    doc.titulo(1, "Anexo A. Contenido de la carpeta Entregable-1")
    codigo(doc, [
        "Entregable-1/",
        "  README.md",
        "  01-de-prompt-a-skill/de_prompt_a_skill.md",
        "  02-skill/evidencia-auditoria-pims/  (la skill)",
        "  03-asistente/",
        "    instrucciones_sistema.md   identidad, instrucciones",
        "    glosario_pims.md           conocimiento",
        "    conocimiento_y_despliegue.md",
        "    casos_prueba.md, pruebas/",
        "  04-aplicacion/",
        "    app.py, asistente.py, rag.py, llm_local.py",
        "    templates/index.html",
        "    static/estilos.css, static/app.js",
        "  informe/",
        "    generar_informe.py, figuras/",
        "    Informe_Entregable_1.docx",
    ])
    doc.titulo(1, "Anexo B. Instalación y ejecución")
    codigo(doc, [
        "ollama pull nomic-embed-text",
        "ollama pull qwen2.5:7b",
        "cd 04-aplicacion",
        "pip install -r requirements.txt",
        "python cargar_demo.py",
        "python app.py      # http://127.0.0.1:5000",
    ])
    doc.titulo(1, "Anexo C. Reproducir las pruebas")
    codigo(doc, [
        "cd 02-skill/evidencia-auditoria-pims/assets/demo",
        "python ejecutar_demo.py",
        "cd ../../../..",
        "python 03-asistente/pruebas/correr_casos.py",
    ])


def main():
    demo = cargar_demo()
    doc = Documento(figuras=ORDEN_FIGURAS)
    caratula(doc)
    introduccion(doc)
    objetivos(doc)
    marco(doc)
    contexto(doc)
    prompt_a_skill(doc)
    creacion_skill(doc)
    asistente(doc, contar_fragmentos())
    pruebas(doc, demo)
    conclusiones(doc)
    referencias(doc)
    anexos(doc)
    doc.guardar(SALIDA)

    pendientes = [k for k in ORDEN_FIGURAS
                  if not any(os.path.exists(os.path.join(FIGURAS, k + e)) for e in (".png", ".jpg"))]
    print("Generado: %s" % SALIDA)
    print("Figuras pendientes: %s" % (", ".join(pendientes) if pendientes else "ninguna"))


if __name__ == "__main__":
    main()
