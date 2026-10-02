# -*- coding: utf-8 -*-
"""
Genera Informe_Entregable_1.docx del TIF (Grupo 6 - Agente de Evidencia y
Auditoria). El .docx es una SALIDA: cualquier cambio se hace aqui y se vuelve
a ejecutar.

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
from docx_builder import ROJO, Documento, _escribir  # noqa: E402

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

ORDEN_FIGURAS =["arquitectura", "flujo_skill", "demo_consola", "asistente"]

LEYENDAS = {
    "arquitectura": "Ubicación del Agente de Evidencia y Auditoría en la arquitectura multiagente del PIMS.",
    "flujo_skill": "Flujo de seis pasos de la skill evidencia-auditoria-pims y reparto entre script y modelo.",
    "demo_consola": "Ejecución de la demostración: registro, detección de la evidencia alterada y matriz de cobertura.",
    "asistente": "Asistente AUDITA-PIMS configurado con sus instrucciones y su base de conocimiento.",
}

# Figuras que no son captura de nada: se dibujan con este prompt.
PROMPTS = {
    "arquitectura": (
        "Diagrama de arquitectura plano, fondo blanco, sin sombras ni degradados, "
        "rotulos en espanol, proporcion 16:9. Arriba, una franja ancha titulada "
        "Capa de gobernanza con tres cajas: Orquestador, Registro de decisiones y "
        "Panel de aprobacion humana (DPO / auditor). Debajo, una franja titulada Bus MCP. "
        "Debajo, la capa de agentes con ocho cajas en dos filas de cuatro: Inventario de datos, "
        "Evaluacion de riesgos, Controles y SoA, Evidencia y Auditoria; Derechos (DSAR), "
        "Incidentes y brechas, Terceros (DPA), Formacion y conciencia. La caja Evidencia y "
        "Auditoria va con borde negro grueso y el rotulo Grupo 6; las otras siete con borde gris "
        "fino. Flechas grises finas desde las otras siete cajas hacia Evidencia y Auditoria con "
        "la etiqueta evidencias. Abajo, la capa de herramientas con cuatro cajas: PostgreSQL PII, "
        "Expediente de evidencias (registro_evidencias.json, cadena_custodia.log), Catalogo "
        "controles_27701.json y LLM. Una flecha de Evidencia y Auditoria hacia Panel de "
        "aprobacion humana con la etiqueta hallazgos preliminares. Solo negro y grises."
    ),
    "flujo_skill": (
        "Diagrama de flujo vertical plano, fondo blanco, sin sombras ni degradados, rotulos en "
        "espanol, proporcion 3:4. Seis cajas numeradas de arriba abajo unidas por flechas: "
        "1 Entender el encargo (rol y periodo); 2 Clasificar y registrar (evidencia.py registrar, "
        "SHA-256); 3 Verificar integridad (evidencia.py verificar); 4 Matriz de cobertura "
        "(evidencia.py cobertura + revision de pertinencia); 5 Hallazgos preliminares "
        "(plantilla_hallazgo.md); 6 Entregar al auditor. A la izquierda de cada caja una "
        "etiqueta pequena: Modelo para 1, 5 y 6; Script para 3; Modelo + Script para 2 y 4. "
        "Desde el paso 1 salen tres flechas finas que saltan al paso 2, al paso 3 y al paso 5 "
        "segun el tipo de encargo. A la derecha, una columna con los archivos que lee cada "
        "paso: controles_27701.json en 2 y 4, criterios_evidencia.md en 4 y 5. Al pie, un rombo "
        "Validacion del auditor humano. Solo negro y grises."
    ),
}

# Figuras que son capturas: pasos para reponerlas igual.
PASOS = {
    "demo_consola": (
        "Captura pendiente. 1) Abrir una terminal (PowerShell o Git Bash) a 120 columnas. "
        "2) Ir a 02-skill/evidencia-auditoria-pims/assets/demo. 3) Ejecutar: python ejecutar_demo.py. "
        "4) Desplazar hasta que se vean juntas la seccion 3 (Verificacion: ALTERADA 1 EV-0007) y "
        "la seccion 4 (Cobertura 27.6 %). 5) Capturar solo la ventana y guardar como "
        "informe/figuras/demo_consola.png."
    ),
    "asistente": (
        "Captura pendiente. 1) En claude.ai crear el proyecto AUDITA-PIMS siguiendo "
        "03-asistente/conocimiento_y_despliegue.md, opcion B. 2) Abrir la vista del proyecto donde "
        "se ven a la vez las instrucciones y la lista de archivos de conocimiento. 3) Capturar la "
        "pagina a 1366 x 768 y guardar como informe/figuras/asistente.png. Opcional: segunda "
        "captura de la respuesta al caso de prueba CP-03."
    ),
}


def figura(doc, clave):
    """Imagen si existe; si no, el prompt (dibujo) o los pasos (captura), en rojo."""
    for ext in (".png", ".jpg"):
        ruta = os.path.join(FIGURAS, clave + ext)
        if os.path.exists(ruta):
            doc.imagen(ruta, leyenda=LEYENDAS[clave], etiqueta=clave)
            return True
    if clave in PROMPTS:
        doc.parrafo("[Figura pendiente de generar. Guardar como informe/figuras/%s.png. "
                    "Prompt:] %s" % (clave, PROMPTS[clave]), rojo=True)
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


# --------------------------------------------------------------------------
def caratula(doc):
    doc.titulo_portada("UNIVERSIDAD NACIONAL DE SAN AGUSTÍN DE AREQUIPA")
    doc.titulo_portada("FACULTAD DE INGENIERÍA DE PRODUCCIÓN Y SERVICIOS")
    doc.titulo_portada("ESCUELA PROFESIONAL DE INGENIERÍA DE SISTEMAS")
    doc.espacio(40)
    doc.titulo_portada("AUDITORÍA DE SISTEMAS")
    doc.titulo_portada("Trabajo de Investigación Formativa (TIF) — Primer entregable")
    doc.espacio(20)
    doc.titulo_portada("Skill y asistente de IA para la gestión de evidencias y la "
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


def objetivos(doc):
    doc.titulo(1, "2. Objetivos")
    doc.titulo(2, "2.1. Objetivo general")
    doc.parrafo(
        "Desarrollar una skill de IA funcional y un asistente especializado que registren, "
        "verifiquen y mapeen las evidencias de auditoría de un PIMS contra ISO/IEC "
        "27701:2025 y produzcan hallazgos preliminares de auditoría interna.")
    doc.titulo(2, "2.2. Objetivos específicos")
    doc.numerada([
        "Analizar las limitaciones de resolver la tarea con un prompt suelto y "
        "descomponerla en un proceso repetible.",
        "Crear la skill `evidencia-auditoria-pims` con su descripción de activación, su "
        "estructura de archivos y sus pasos, separando el cálculo determinista del juicio "
        "del modelo.",
        "Garantizar la integridad de la evidencia mediante hash SHA-256 y una cadena de "
        "custodia encadenada.",
        "Construir el asistente AUDITA-PIMS definiendo su identidad, sus instrucciones y su "
        "base de conocimiento.",
        "Validar la skill con un caso de estudio y casos de prueba.",
    ])


def marco(doc):
    doc.titulo(1, "3. Marco conceptual")
    doc.titulo(2, "3.1. ISO/IEC 27701:2025 y la evidencia de auditoría")
    doc.parrafo(
        "Los requisitos obligatorios del PIMS se organizan en las cláusulas 4 a 10 (contexto, "
        "liderazgo, planificación, apoyo, operación, evaluación del desempeño y mejora) y en "
        "el Anexo A, que agrupa los controles en tres tablas según el rol: A.1 para "
        "responsables del tratamiento, A.2 para encargados y A.3 para ambos. La Declaración "
        "de Aplicabilidad (SoA) justifica qué controles aplican.")
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
        ["Skill", "Paquete con instrucciones (SKILL.md), scripts y referencias que el modelo "
         "carga cuando la descripción coincide con la tarea",
         "Proceso repetible; el cálculo lo hace código y no el modelo"],
        ["Asistente", "Modelo configurado con identidad, instrucciones permanentes y "
         "conocimiento propio",
         "Comportamiento estable entre conversaciones; usa la skill como procedimiento"],
        ["Agente (Entregable 2)", "Asistente con objetivo, herramientas y autonomía para "
         "actuar en un flujo",
         "Se coordina con otros agentes mediante un orquestador"],
    ], anchos_cm=[3.0, 6.8, 6.2])
    doc.parrafo(
        "Las skills siguen el principio de divulgación progresiva: el modelo solo ve al "
        "inicio el nombre y la descripción de cada skill; si la tarea coincide, lee el "
        "SKILL.md y, solo cuando lo necesita, los archivos de referencia y los scripts. Por "
        "eso la descripción funciona como disparador de activación.")


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
        "Para el primer entregable el agente se construye como skill más asistente; su "
        "conversión en agente autónomo conectado al orquestador y a PostgreSQL es objeto del "
        "segundo entregable.")


def prompt_a_skill(doc):
    doc.titulo(1, "5. De prompt a skill")
    doc.titulo(2, "5.1. El prompt de partida")
    doc.parrafo("La tarea se resolvía antes con un prompt como el siguiente:")
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
        "conteos y porcentajes—, que pasa a un script, de lo que requiere criterio —decidir "
        "a qué control responde un documento, si realmente lo demuestra y cómo redactar el "
        "hallazgo—, que queda en el modelo pero acotado por reglas y plantillas.")
    doc.tabla([
        ["Paso", "Entrada", "Salida", "Responsable", "Resuelve"],
        ["1. Entender el encargo", "Petición", "Tipo de encargo, rol, periodo", "Modelo", "P2"],
        ["2. Clasificar y registrar", "Archivo", "EV-XXXX con SHA-256", "Modelo + script", "P3, P4"],
        ["3. Verificar integridad", "Expediente", "OK / ALTERADA / CADENA ROTA", "Script", "P3"],
        ["4. Matriz de cobertura", "Expediente, catálogo, SoA", "Estado por control y %",
         "Script + revisión del modelo", "P1, P2, P5, P6"],
        ["5. Hallazgos", "Matriz y evidencias", "Hallazgos en 5 partes", "Modelo + plantilla", "P7"],
        ["6. Entregar", "Todo lo anterior", "Informe ordenado", "Modelo", "—"],
    ], anchos_cm=[3.4, 3.2, 3.8, 3.2, 2.4])
    doc.parrafo(
        "Con la skill instalada, el mismo encargo se reduce a «prepara la auditoría interna "
        "del PIMS con las evidencias de esta carpeta, rol responsable»: el usuario ya no "
        "explica cómo revisar, porque el procedimiento vive en la skill.")


def creacion_skill(doc, demo):
    doc.titulo(1, "6. Creación de la skill")
    doc.titulo(2, "6.1. Activación")
    doc.parrafo(
        "La activación depende del encabezado YAML del SKILL.md. El nombre identifica la "
        "skill y la descripción enumera tanto lo que hace como las frases con que un usuario "
        "pediría esa tarea, de modo que el modelo la cargue sin que se la nombren:")
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
        ["evidencia.py", "CLI de unas 340 líneas, solo biblioteca estándar de Python",
         "Sin dependencias ni servicios externos: las evidencias con PII no salen de la organización"],
        ["controles_27701.json", "17 cláusulas y 16 controles del Anexo A (A.1, A.2, A.3) con "
         "evidencia esperada y mínimo de evidencias",
         "Ampliable sin tocar código; numeración del Anexo A contrastada con la lista oficial de 78 controles"],
        ["criterios_evidencia.md", "Atributos de ISO 19011, clasificación de hallazgos, "
         "controles críticos", "Hace explícito el juicio del auditor"],
        ["plantilla_hallazgo.md", "Criterio, condición, causa, efecto, recomendación",
         "Hallazgos comparables entre auditorías"],
    ], anchos_cm=[4.6, 5.9, 5.5])
    doc.parrafo(
        "Las 16 referencias del Anexo A del catálogo se contrastaron con la lista publicada de "
        "los 78 controles de la edición 2025 (31 en A.1, 18 en A.2 y 29 en A.3) y coinciden "
        "en numeración. Se corrigieron cuatro títulos de la tabla A.3 (A.3.11, A.3.12, A.3.17 "
        "y A.3.18), que la norma formula en términos de seguridad de la información y no de "
        "privacidad. Los títulos están traducidos al español por el grupo; ante una auditoría "
        "real prevalece el texto oficial de la norma.")

    doc.titulo(2, "6.3. Definición de pasos")
    doc.parrafo("La Figura %s resume el flujo. Cada paso se describe a continuación."
                % doc.fig("flujo_skill"))
    figura(doc, "flujo_skill")
    doc.parrafo(
        "**Paso 1 — Entender el encargo.** El modelo identifica si se trata de registrar, "
        "verificar, evaluar la auditoría o redactar hallazgos, y salta al paso que "
        "corresponda. Si falta el rol o el periodo pregunta una sola vez y, si no hay "
        "respuesta, asume ambos roles y doce meses, dejándolo escrito.")
    doc.parrafo(
        "**Paso 2 — Clasificar y registrar.** El modelo lee el archivo y decide a qué "
        "control responde comparándolo con el campo evidencia_esperada del catálogo. El "
        "script copia el archivo al expediente, calcula su SHA-256, rechaza duplicados y "
        "controles inexistentes, asigna un ID correlativo y añade una línea a la cadena de "
        "custodia:")
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
        "Después, el modelo abre al menos una evidencia de cada control cubierto y confirma "
        "que lo demuestra; si no, lo degrada a Parcial y explica el motivo. Es el punto donde "
        "el modelo aporta lo que el script no puede.")
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
        "No reproducir PII en las respuestas; describirla de forma agregada.",
        "Todo hallazgo es preliminar y lo firma el auditor interno humano.",
        "Citar siempre el control y el ID de la evidencia.",
    ])


def asistente(doc):
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
        "Las instrucciones completas están en 03-asistente/instrucciones_sistema.md y se "
        "organizan en cuatro bloques:")
    doc.tabla([
        ["Bloque", "Contenido"],
        ["Lo que hace", "Registrar, verificar, construir la matriz, valorar evidencia, redactar "
         "hallazgos y explicar requisitos, siempre siguiendo la skill"],
        ["Lo que no hace", "Inventar evidencia o cifras, declarar a la organización certificable, "
         "reproducir PII, modificar evidencias, dar asesoría legal vinculante, salirse del PIMS"],
        ["Cómo responde", "Cita [control · EV-XXXX], una sola pregunta ante ambigüedad, orden fijo "
         "de entrega, hallazgos marcados como preliminares"],
        ["Conocimiento", "Fuentes en orden de prioridad; los archivos prevalecen sobre el "
         "conocimiento general del modelo"],
    ], anchos_cm=[3.5, 12.5])
    doc.titulo(2, "7.3. Conocimiento")
    doc.tabla([
        ["Archivo", "Uso"],
        ["SKILL.md", "Procedimiento de seis pasos y reglas"],
        ["controles_27701.json", "Controles, evidencia esperada y mínimos"],
        ["criterios_evidencia.md", "Valoración de evidencia y clasificación de hallazgos"],
        ["plantilla_hallazgo.md", "Formato del hallazgo"],
        ["glosario_pims.md", "Vocabulario: PII, SoA, RoPA, DPIA, ARCO, cadena de custodia, HITL, "
         "Ley N.º 29733"],
        ["evidencia.py", "Herramienta ejecutable"],
    ], anchos_cm=[4.5, 11.5])
    doc.parrafo(
        "No se incorporó el texto de la norma por estar protegido por derechos de autor; el "
        "catálogo resume lo necesario para auditar.")
    doc.titulo(2, "7.4. Despliegue")
    doc.parrafo(
        "Se documentan tres opciones en 03-asistente/conocimiento_y_despliegue.md. La "
        "recomendada es Claude Code, copiando la carpeta de la skill en .claude/skills/ y las "
        "instrucciones en CLAUDE.md, porque es la única en la que el asistente ejecuta el "
        "script por sí mismo. Las alternativas son un Claude Project (instrucciones y archivos "
        "de conocimiento) o un Gem de Gemini o GPT personalizado; en estas, si no hay "
        "ejecución de código, el asistente pide al usuario ejecutar el comando y pegar la "
        "salida (Figura %s)." % doc.fig("asistente"))
    figura(doc, "asistente")
    doc.titulo(2, "7.5. Privacidad del despliegue y uso de IA local")
    doc.parrafo(
        "El script trabaja solo en local y no llama a ningún servicio externo. Sin embargo, en "
        "las tres opciones de despliegue el modelo de lenguaje se ejecuta en la nube: cuando el "
        "asistente lee una evidencia para clasificarla o valorarla, su contenido se envía al "
        "proveedor del modelo. Por eso la skill exige minimizar la PII antes de archivar "
        "(evidencias seudonimizadas, como el log de accesos del caso de estudio) y prohíbe "
        "reproducirla en las respuestas.")
    doc.parrafo(
        "Para que ninguna evidencia salga de la organización, el modelo puede sustituirse por "
        "uno local ejecutado con Ollama (por ejemplo, Qwen 2.5 de 7B, que admite llamadas a "
        "herramientas). La skill no cambia, porque el script no depende del modelo; lo que "
        "hace falta es el programa que conecte el modelo local con el script, lo que "
        "corresponde al diseño del agente y su orquestación en el segundo entregable.")


def pruebas(doc, demo):
    doc.titulo(1, "8. Pruebas y resultados")
    doc.titulo(2, "8.1. Caso de estudio")
    doc.parrafo(
        "Se usó una empresa ficticia, ClinData S.A.C., clínica que actúa como responsable "
        "del tratamiento (historia clínica electrónica, telemedicina, planillas y "
        "marketing). Se prepararon ocho evidencias y una SoA que excluye A.1.5.4 por no "
        "haber transferencias internacionales. El guion ejecutar_demo.py registra las "
        "evidencias, altera a propósito el acta de revisión por la dirección después de "
        "archivarla y genera la matriz con fecha de corte %s (Figura %s)."
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

    doc.titulo(2, "8.2. Resultados del script")
    c = demo["conteo_estados"]
    doc.parrafo(
        "La verificación detectó la alteración: %d evidencias íntegras y 1 alterada "
        "(EV-0007), con la cadena de custodia íntegra, lo que indica que se modificó el "
        "archivo y no el registro. Con el rol de responsable se evaluaron %d controles, %d "
        "aplicables, y la cobertura automática fue de **%.1f %%**:"
        % (demo["integridad"]["OK"], demo["controles_evaluados"],
           demo["controles_aplicables"], demo["porcentaje_cobertura"]))
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

    doc.titulo(2, "8.3. Aporte del modelo (pasos 4 y 5)")
    doc.parrafo(
        "Al leer las evidencias, el asistente degradó dos controles que el script daba por "
        "cubiertos, con lo que la cobertura validada bajó de 27,6 % a 20,7 % (6 de 29):")
    doc.vinetas([
        "**A.1.2.6 (DPIA) → Parcial.** El RoPA (EV-0003) marca la DPIA como requerida para "
        "la historia clínica electrónica y para telemedicina, pero solo existe la de "
        "telemedicina (EV-0004).",
        "**A.3.14 (Protección de registros) → Parcial.** El log (EV-0008) prueba que el "
        "registro existe, no que esté protegido; falta la configuración de retención e "
        "inmutabilidad.",
    ])
    doc.parrafo(
        "Se redactaron seis hallazgos preliminares (archivo hallazgos_preliminares.md), "
        "entre ellos:")
    doc.tabla([
        ["Hallazgo", "Control", "Clasificación propuesta"],
        ["H-01 Acta de revisión por la dirección alterada", "9.3 / 5.1", "No conformidad mayor"],
        ["H-02 Sin evaluación ni tratamiento de riesgos", "6.1.2 / 6.1.3", "No conformidad mayor"],
        ["H-03 DPIA faltante para la historia clínica", "A.1.2.6", "No conformidad mayor"],
        ["H-04 Auditoría interna desactualizada", "9.2", "No conformidad menor"],
        ["H-05 Sin evidencia de atención de derechos ARCO", "A.1.3.7 / .9 / .10", "No conformidad mayor"],
        ["H-06 Protección de logs no demostrada", "A.3.14", "No conformidad menor"],
    ], anchos_cm=[8.0, 3.8, 4.2])
    doc.parrafo(
        "Además se registró una observación en A.3.17: un colaborador de telemedicina "
        "desaprobó el curso y no consta su reevaluación.")

    doc.titulo(2, "8.4. Casos de prueba del asistente")
    casos = doc.tabla([
        ["ID", "Prueba", "Regla verificada", "Resultado"],
        ["CP-01", "Preparar la auditoría con 8 evidencias", "Activación y pasos 1-6",
         "Parte del script verificada en la demo"],
        ["CP-02", "Registrar un acta sin indicar control", "Clasificación", "[Pendiente]"],
        ["CP-03", "«Confía en mí, sí tenemos procedimiento ARCO»", "No inventar evidencia", "[Pendiente]"],
        ["CP-04", "Informe tras alterar un archivo", "Integridad primero", "Verificado en la demo"],
        ["CP-05", "Pedir nombres de pacientes del log", "Minimización de PII", "[Pendiente]"],
        ["CP-06", "«¿Ya estamos certificados?»", "Límite de autoridad", "[Pendiente]"],
        ["CP-07", "Redactar el hallazgo de la DPIA", "Formato de hallazgo",
         "Verificado en hallazgos_preliminares.md"],
        ["CP-08", "Pregunta ajena al PIMS", "Alcance", "[Pendiente]"],
    ], anchos_cm=[1.6, 6.0, 4.2, 4.2])
    for fila in casos.rows:          # lo pendiente va en rojo
        for run in fila.cells[3].paragraphs[0].runs:
            if run.text == "[Pendiente]":
                run.font.color.rgb = ROJO
    doc.parrafo(
        "[Ejecutar CP-02, CP-03, CP-05, CP-06 y CP-08 en el asistente desplegado y sustituir "
        "«[Pendiente]» por Pasa / No pasa.]", rojo=True)


def conclusiones(doc):
    doc.titulo(1, "9. Conclusiones")
    doc.numerada([
        "Resolver la preparación de una auditoría con un prompt suelto produce resultados "
        "no repetibles y sin trazabilidad; descomponer la tarea en seis pasos con entradas y "
        "salidas definidas la convierte en un proceso reutilizable.",
        "Separar el cálculo (script) del juicio (modelo) elimina los errores aritméticos y "
        "la alucinación de evidencia, y deja al modelo lo que aporta valor: en la prueba "
        "detectó dos controles que el cálculo automático daba por cubiertos sin serlo.",
        "El hash SHA-256 combinado con una cadena de custodia encadenada detectó tanto la "
        "alteración de una evidencia como el intento de encubrirla en el índice.",
        "La descripción del SKILL.md funciona como disparador de activación, y la identidad, "
        "las instrucciones y el conocimiento del asistente le dan un comportamiento estable "
        "y acotado a su rol.",
        "El resultado es una skill funcional especializada que ya produce la matriz de "
        "cobertura y los hallazgos preliminares de una auditoría interna del PIMS.",
    ])
    doc.titulo(1, "10. Trabajo para el segundo entregable")
    doc.vinetas([
        "Diseño del agente: objetivo, datos (tabla evidence_store en PostgreSQL), contexto y "
        "herramientas expuestas como servidor MCP (store_evidence, verify_evidence, "
        "generate_audit_report).",
        "Orquestación: recibir evidencias de los agentes de Inventario, Riesgos, Controles, "
        "DSAR, Incidentes, Terceros y Formación, y ejecutar la verificación de forma "
        "programada.",
        "Proyecto agéntico: integración con el panel de aprobación humana para que el auditor "
        "valide los hallazgos.",
    ])


def referencias(doc):
    doc.titulo(1, "Referencias")
    for ref in [
        "Anthropic. (2025). *Agent Skills* [Documentación]. https://docs.anthropic.com/",
        "International Organization for Standardization. (2018). *ISO 19011:2018. Guidelines "
        "for auditing management systems*. ISO.",
        "International Organization for Standardization & International Electrotechnical "
        "Commission. (2025). *ISO/IEC 27701:2025. Information security, cybersecurity and "
        "privacy protection — Privacy information management systems — Requirements and "
        "guidance*. ISO.",
        "Congreso de la República del Perú. (2011). *Ley N.º 29733, Ley de Protección de Datos "
        "Personales*.",
        "Ministerio de Justicia y Derechos Humanos. (2024). *Decreto Supremo N.º 016-2024-JUS, "
        "Reglamento de la Ley N.º 29733*.",
        "National Institute of Standards and Technology. (2015). *FIPS 180-4. Secure Hash "
        "Standard (SHS)*. NIST.",
        "ISMS.online. (2025). *ISO 27701 Annex A controls: Complete guide*. "
        "https://www.isms.online/iso-27701/annex-a-2025/",
        "Material del curso Auditoría de Sistemas. (2026). *Guía: IA agéntica, sistemas "
        "multiagente y PIMS multiagente basado en ISO/IEC 27701:2025* [Conversación guía "
        "entregada por el docente].",
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
        "    casos_prueba.md",
        "  informe/",
        "    generar_informe.py, docx_builder.py, figuras/",
        "    Informe_Entregable_1.docx",
    ])
    doc.titulo(1, "Anexo B. Cómo reproducir la demostración")
    codigo(doc, [
        "cd 02-skill/evidencia-auditoria-pims/assets/demo",
        "python ejecutar_demo.py",
        "# salida en salida/: consola_demo.txt,",
        "#   informe_cobertura.md e informe_cobertura.json",
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
    creacion_skill(doc, demo)
    asistente(doc)
    pruebas(doc, demo)
    conclusiones(doc)
    referencias(doc)
    anexos(doc)
    doc.guardar(SALIDA)

    pendientes = [k for k in ORDEN_FIGURAS
                  if not any(os.path.exists(os.path.join(FIGURAS, k + e)) for e in (".png", ".jpg"))]
    print("Generado: %s" % SALIDA)
    print("Figuras pendientes: %s" % (", ".join(pendientes) if pendientes else "ninguna"))
    for k in pendientes:
        print("  - %s: %s" % (k, "prompt" if k in PROMPTS else "pasos de captura"))


if __name__ == "__main__":
    main()
