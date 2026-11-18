# -*- coding: utf-8 -*-
"""
Chat con la IA local sobre el proyecto (panel lateral de la web).

Reutiliza el asistente AUDITA-PIMS del Entregable 1 (instrucciones de sistema,
RAG con FAISS y busqueda en el texto de ISO/IEC 27701:2025) y le anade un
resumen del proyecto que no esta en el RAG: los documentos PIMS de Evidencia y
Auditoria, la ultima auditoria interna y su plan de accion.

La respuesta se envia a medida que Ollama la genera (NDJSON): primero eventos de
'estado' (que esta buscando), luego las 'fuentes' recuperadas y despues el
'texto' en trozos. Si el navegador corta la conexion, se deja de generar.
"""

import json
import re
import urllib.error
import urllib.request

import nucleo
import herramientas
from nucleo import asistente, llm_local

MAX_HISTORIAL = 6
MAX_PREGUNTA = 2000

INSTRUCCION_PROYECTO = (
    "\n\n## Este chat\n"
    "Respondes preguntas del equipo de Evidencia y Auditoria sobre su proyecto: el "
    "expediente de evidencias, los documentos PIMS, las auditorias internas y la norma "
    "ISO/IEC 27701:2025 aplicada a la UNSA. El bloque PROYECTO tiene el estado actual de "
    "los documentos y de la ultima auditoria: usalo tal cual, sin recalcular cifras. "
    "Responde en espanol, breve (no mas de 200 palabras salvo que pidan detalle), con "
    "listas cuando ayuden, y cita las referencias (control, clausula, EV-xxxx o codigo "
    "PIMS) de donde sale cada dato. Si algo no esta en el contexto, dilo y sugiere donde "
    "buscarlo en la web (Panel, Auditorias, Documentos PIMS, Expediente, Cobertura).")


def _contexto_proyecto(vista=""):
    """Bloque corto con lo que el RAG no sabe: documentos PIMS y ultima auditoria."""
    import documentos_pims
    import orquestador
    lineas = ["PROYECTO (estado actual, calculado por la aplicacion):",
              "Agente de Evidencia y Auditoria (Grupo 6) del PIMS simulado de la UNSA segun "
              "ISO/IEC 27701:2025, Ley 29733 y su reglamento DS 016-2024-JUS."]
    try:
        docs = documentos_pims.lista_maestra()
        lineas.append("Lista maestra PIMS-RG-01 (documentos PIMS de los ocho equipos):")
        for f in docs:
            d = f.get("documento") or {}
            control = (d.get("control") or {}).get("resultado") or "sin verificar"
            lineas.append("- %s %s [%s]: %s%s, requisitos %s, control PIMS-PR-01 %s." % (
                f["codigo"], f["titulo"], f.get("agente_autor") or "-", f["situacion"],
                (" (version %s)" % d["version"]) if d.get("version") else "",
                ", ".join(f.get("requisitos") or []) or "-", control))
    except Exception as e:  # noqa: BLE001  (la base puede estar apagada: el chat sigue)
        lineas.append("Documentos PIMS: no disponibles (%s)." % e)
    try:
        ultima = next((e for e in orquestador.listar("unsa") if e["tipo"] == "auditoria_interna"), None)
        if ultima:
            r = ultima.get("resultado") or {}
            cob = r.get("cobertura") or {}
            ap = r.get("aprobacion") or {}
            fo = r.get("formulario_fo01") or {}
            lineas.append("Ultima auditoria interna: %s, estado %s, iniciada %s. Cobertura %s %% de "
                          "%s controles aplicables; %s controles con hallazgo; decision del auditor: %s%s; "
                          "formulario PIMS-FO-01 con %s no conformidades." % (
                              ultima["id"], ultima["estado"], ultima.get("creado", "")[:16],
                              cob.get("porcentaje_cobertura", "?"), cob.get("controles_aplicables", "?"),
                              r.get("controles_con_hallazgo", "?"), ap.get("decision", "pendiente"),
                              (" por " + ap["auditor"]) if ap.get("auditor") else "",
                              fo.get("registros", 0)))
            plan = r.get("plan_accion") or []
            if plan:
                lineas.append("Plan de accion (primeras prioridades):")
                for p in plan[:6]:
                    lineas.append("- %s (%s): %s Responsable: %s. Fecha limite: %s." % (
                        p.get("ref"), p.get("estado"), p.get("accion"), p.get("responsable"),
                        p.get("fecha_limite")))
        else:
            lineas.append("Aun no se ha hecho ninguna auditoria interna.")
    except Exception as e:  # noqa: BLE001
        lineas.append("Auditorias: no disponibles (%s)." % e)
    if vista:
        lineas.append("El usuario esta viendo la seccion '%s' de la web." % vista[:60])
    return "\n".join(lineas)


def _generar(mensajes):
    """Respuesta de Ollama en trozos (stream=True)."""
    cuerpo = {"model": llm_local.MODELO_CHAT, "messages": mensajes, "stream": True,
              "options": {"temperature": 0.2, "num_ctx": 8192}}
    peticion = urllib.request.Request(llm_local.OLLAMA_URL + "/api/chat",
                                      data=json.dumps(cuerpo).encode("utf-8"),
                                      headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(peticion, timeout=600) as r:
            for linea in r:
                if not linea.strip():
                    continue
                d = json.loads(linea.decode("utf-8"))
                if d.get("error"):
                    raise llm_local.ErrorModelo(d["error"])
                trozo = (d.get("message") or {}).get("content", "")
                if trozo:
                    yield trozo
                if d.get("done"):
                    return
    except urllib.error.HTTPError as e:
        raise llm_local.ErrorModelo("Ollama devolvio %s: %s" % (e.code, e.read().decode("utf-8", "replace")))
    except urllib.error.URLError as e:
        raise llm_local.ErrorModelo("No se pudo conectar con Ollama en %s (%s). Inicia Ollama y vuelve "
                                    "a intentarlo." % (llm_local.OLLAMA_URL, e.reason))


def conversar(mensaje, historial=None, vista=""):
    """Generador de eventos {'tipo': estado|fuentes|texto|fin|error, ...} para la web."""
    mensaje = (mensaje or "").strip()[:MAX_PREGUNTA]
    if not mensaje:
        yield {"tipo": "error", "texto": "Escribe una pregunta."}
        return
    try:
        if nucleo.PREPARACION.get("estado") == "sin_ia":
            raise llm_local.ErrorModelo("La IA local no está disponible: " + nucleo.PREPARACION.get("detalle", ""))
        yield {"tipo": "estado", "texto": "Buscando en el expediente y los documentos PIMS",
               "modelo": llm_local.MODELO_CHAT}
        if nucleo.PREPARACION.get("estado") == "preparando":
            yield {"tipo": "estado", "texto": "Los índices de búsqueda aún se están preparando; esta vez tardará más"}
        herramientas._asegurar_preparado()
        p = nucleo.proyecto("unsa")
        _, resumen = herramientas._resumen(p)
        rag = p.preparar_rag()
        fragmentos = rag.buscar(mensaje, k=5)
        yield {"tipo": "estado", "texto": "Consultando el texto de ISO/IEC 27701:2025"}
        fragmentos += asistente._fragmentos_norma(rag, mensaje, {f["texto"] for f in fragmentos})
        for ev_id in sorted(set(re.findall(r"EV-\d{4}", mensaje))):
            ya = {f["texto"] for f in fragmentos}
            fragmentos.extend(dict(f, similitud=None) for f in rag.fragmentos
                              if f["ref"] == ev_id and f["texto"] not in ya)
        fuentes, vistas = [], set()
        for f in fragmentos:
            clave = (f["fuente"], f.get("ref"))
            if clave not in vistas:
                vistas.add(clave)
                fuentes.append({"fuente": f["fuente"], "tipo": f["tipo"], "ref": f.get("ref"),
                                "similitud": f.get("similitud")})
        yield {"tipo": "fuentes", "fuentes": fuentes}

        mensajes = [{"role": "system", "content": asistente._instrucciones() + INSTRUCCION_PROYECTO}]
        for turno in (historial or [])[-MAX_HISTORIAL:]:
            if turno.get("role") in ("user", "assistant") and isinstance(turno.get("content"), str):
                mensajes.append({"role": turno["role"], "content": turno["content"][:4000]})
        aviso = ""
        if "ALERTA DE INTEGRIDAD" in (resumen or ""):
            aviso = ("\n\nIMPORTANTE: hay una ALERTA DE INTEGRIDAD en el estado del expediente. Si la "
                     "pregunta trata del expediente, la auditoria o el cumplimiento, empieza con esa alerta.")
        mensajes.append({"role": "user", "content": asistente._bloque_contexto(fragmentos, resumen)
                         + "\n\n" + _contexto_proyecto(vista) + aviso
                         + "\n\nPREGUNTA DEL USUARIO:\n" + mensaje})
        yield {"tipo": "estado", "texto": "Redactando la respuesta"}
        for trozo in _generar(mensajes):
            yield {"tipo": "texto", "texto": trozo}
        yield {"tipo": "fin"}
    except (llm_local.ErrorModelo, nucleo.ErrorAgente) as e:
        yield {"tipo": "error", "texto": str(e)}
    except Exception as e:  # noqa: BLE001  (cualquier fallo se informa en el chat, no rompe la web)
        yield {"tipo": "error", "texto": "No se pudo responder: %s" % e}
