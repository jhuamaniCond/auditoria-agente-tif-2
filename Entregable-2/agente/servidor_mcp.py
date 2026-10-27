# -*- coding: utf-8 -*-
"""
Servidor MCP "evidencias-pims" del Agente de Evidencia y Auditoria (Entregable 2).

Publica por Model Context Protocol las herramientas de herramientas.py (el
contrato comun del Entregable 2) para que cualquier host MCP (Claude Desktop,
Claude Code, un IDE u otro agente) gestione el expediente de evidencias del PIMS
ISO/IEC 27701:2025 de la UNSA.

  Tools      registrar_evidencia, verificar_integridad, matriz_cobertura,
             estado_expediente, buscar_evidencia, clasificar_evidencia,
             evaluar_pertinencia, redactar_hallazgo, generar_informe_auditoria,
             listar_proyectos, preguntar_asistente
  Resources  pims://catalogo                 catalogo de controles (JSON)
             pims://catalogo/{ref}           un control del catalogo (JSON)
             norma://control/{ref}           texto de la norma para un control
  Prompt     auditoria_interna               flujo de auditoria interna (cl. 9.2)

Decisiones de diseno:
  * decidir_pertinencia NO se publica (human-in-the-loop). Aceptar o rechazar
    la propuesta de la IA es el juicio profesional del auditor: si fuera una tool,
    el mismo LLM que propone podria "aprobarse" a si mismo. La decision se toma
    en la web del Entregable 1/2 o por linea de comandos, con nombre del auditor.
    Por la misma razon generar_informe_auditoria no acepta "aprobado_por": por MCP
    el informe sale siempre PRELIMINAR.
  * Cada llamada a una tool queda en la bitacora inmutable
    Entregable-2/datos/bitacora_mcp.jsonl (solo anadir, cada linea enlazada por
    SHA-256 con la anterior): fecha, tool, argumentos (rutas, nunca contenido de
    archivos), resultado ok/error y duracion.
  * Los errores esperables (ErrorAgente, ErrorEvidencia, ErrorModelo, ...) se
    devuelven como mensaje claro (is_error=True), nunca como traceback.
  * En stdio, stdout es el canal JSON-RPC: lo que imprima la app del Entregable 1
    se desvia a stderr (al importar y durante cada tool).

Uso:
    python servidor_mcp.py              # stdio (lo lanza el host MCP)
    python servidor_mcp.py --http       # streamable HTTP en http://127.0.0.1:8765/mcp
    python servidor_mcp.py --http --puerto 9000
"""

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
import sys
import time
import traceback
from typing import Annotated, Optional

from pydantic import Field

# --- SDK oficial de MCP (v2: MCPServer; v1: FastMCP) --------------------------
try:
    from mcp.server.mcpserver import MCPServer as _Servidor
    from mcp.server.mcpserver.exceptions import ResourceError, ToolError
    SDK_V2 = True
except ImportError:  # mcp < 2
    from mcp.server.fastmcp import FastMCP as _Servidor
    from mcp.server.fastmcp.exceptions import ResourceError, ToolError
    SDK_V2 = False
from mcp.types import ToolAnnotations

# --- Nucleo del agente: sus prints (app del E1) van a stderr, no a stdout -----
AQUI = os.path.dirname(os.path.abspath(__file__))
if AQUI not in sys.path:
    sys.path.insert(0, AQUI)
with contextlib.redirect_stdout(sys.stderr):
    import herramientas as H  # noqa: E402
    import nucleo  # noqa: E402
    import norma  # noqa: E402  (modulo del Entregable 1, en sys.path gracias a nucleo)
    from nucleo import ErrorAgente, ErrorEvidencia, llm_local  # noqa: E402

BITACORA = os.path.join(nucleo.DATOS, "bitacora_mcp.jsonl")
_CERROJO = BITACORA + ".lock"
GENESIS = "0" * 64
PUERTO_HTTP = 8765
TRANSPORTE = "stdio"

INSTRUCCIONES = (
    "Agente de Evidencia y Auditoria del PIMS ISO/IEC 27701:2025 de la UNSA (Universidad "
    "Nacional de San Agustin de Arequipa). Gestiona un expediente de evidencias con SHA-256 y "
    "cadena de custodia, calcula la matriz de cobertura de 38 controles (rol responsable) y "
    "redacta hallazgos con IA local (Ollama). Proyecto por defecto: 'unsa'. Las tools "
    "deterministas (listar_proyectos, estado_expediente, verificar_integridad, matriz_cobertura, "
    "generar_informe_auditoria, registrar_evidencia) no usan IA; las demas usan un LLM local y "
    "sus resultados son PROPUESTAS que debe validar un auditor humano. Aceptar o rechazar una "
    "propuesta de pertinencia es decision humana y no esta disponible como tool.")

mcp = _Servidor("evidencias-pims", instructions=INSTRUCCIONES)


# =============================================================== bitacora MCP

@contextlib.contextmanager
def _cerrojo():
    """Exclusion entre procesos para que dos servidores no rompan el encadenado."""
    fd = os.open(_CERROJO, os.O_RDWR | os.O_CREAT)
    try:
        if os.name == "nt":
            import msvcrt
            os.lseek(fd, 0, 0)
            msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                os.lseek(fd, 0, 0)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def _ultima_linea():
    """(n, hash) de la ultima entrada de la bitacora, leyendo solo el final."""
    if not os.path.exists(BITACORA) or os.path.getsize(BITACORA) == 0:
        return 0, GENESIS
    with open(BITACORA, "rb") as f:
        f.seek(0, 2)
        pos = f.tell()
        bloque = b""
        while pos > 0 and bloque.count(b"\n") < 2:
            salto = min(4096, pos)
            pos -= salto
            f.seek(pos)
            bloque = f.read(salto) + bloque
    ultima = bloque.strip().splitlines()[-1]
    d = json.loads(ultima.decode("utf-8"))
    return d["n"], d["hash"]


def _hash(contenido, anterior):
    datos = json.dumps(contenido, ensure_ascii=False, sort_keys=True) + anterior
    return hashlib.sha256(datos.encode("utf-8")).hexdigest()


def _anotar(entrada):
    """Anade una linea a la bitacora (append-only, encadenada por SHA-256)."""
    try:
        with _cerrojo():
            n, anterior = _ultima_linea()
            contenido = dict(n=n + 1, **entrada)
            linea = dict(contenido, hash_anterior=anterior, hash=_hash(contenido, anterior))
            with open(BITACORA, "a", encoding="utf-8") as f:
                f.write(json.dumps(linea, ensure_ascii=False) + "\n")
    except Exception as e:  # la bitacora nunca debe tumbar la tool
        print("AVISO bitacora MCP: %s" % e, file=sys.stderr)


def verificar_bitacora():
    """Recorre la bitacora y devuelve los problemas de encadenado encontrados."""
    problemas, anterior, n = [], GENESIS, 0
    if not os.path.exists(BITACORA):
        return {"entradas": 0, "problemas": [], "integra": True}
    with open(BITACORA, encoding="utf-8") as f:
        for linea in f:
            if not linea.strip():
                continue
            d = json.loads(linea)
            n += 1
            contenido = {k: v for k, v in d.items() if k not in ("hash_anterior", "hash")}
            if d["hash_anterior"] != anterior:
                problemas.append("entrada %s: no enlaza con la anterior" % d.get("n"))
            if _hash(contenido, d["hash_anterior"]) != d["hash"]:
                problemas.append("entrada %s: contenido modificado" % d.get("n"))
            anterior = d["hash"]
    return {"entradas": n, "problemas": problemas, "integra": not problemas}


def _sanear(argumentos):
    """Argumentos aptos para la bitacora: rutas si, contenidos no."""
    limpio = {}
    for k, v in argumentos.items():
        if k == "hallazgos" and isinstance(v, dict):
            limpio[k] = {"controles": sorted(v)}            # solo las claves
        elif k == "historial" and isinstance(v, list):
            limpio[k] = {"mensajes": len(v)}
        elif isinstance(v, str) and len(v) > 300:
            limpio[k] = v[:300] + "...[%d caracteres]" % len(v)
        else:
            limpio[k] = v
    return limpio


# =============================================================== ejecucion

ERRORES_ESPERADOS = (ErrorAgente, ErrorEvidencia, llm_local.ErrorModelo, ValueError,
                     KeyError, FileNotFoundError, PermissionError)


def _mensaje_error(e):
    if isinstance(e, llm_local.ErrorModelo):
        return "IA local no disponible (Ollama): %s" % e
    if isinstance(e, FileNotFoundError):
        return "Archivo no encontrado: %s" % (e.filename or e)
    if isinstance(e, KeyError):
        return "Dato no encontrado: %s" % e
    return str(e) or e.__class__.__name__


_IA_LISTA = False


def _preparar_ia():
    """Carga (una vez) los indices RAG: base de conocimiento comun y evidencias.

    herramientas.buscar/... solo preparan el indice de evidencias del proyecto; la norma
    y el catalogo viven en el indice de conocimiento, que hay que cargar antes."""
    global _IA_LISTA
    if not _IA_LISTA:
        nucleo.preparar()           # carga de disco si el indice FAISS sigue vigente
        _IA_LISTA = nucleo.CONOCIMIENTO_RAG.indice is not None


def _ejecutar(tool, funcion, ia=False, **argumentos):
    """Ejecuta una herramienta del contrato con bitacora y errores legibles."""
    inicio = time.perf_counter()
    entrada = {"fecha": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
               "tool": tool, "argumentos": _sanear(argumentos), "transporte": TRANSPORTE,
               "pid": os.getpid()}
    try:
        with contextlib.redirect_stdout(sys.stderr):
            if ia:
                _preparar_ia()
            resultado = funcion(**argumentos)
    except Exception as e:
        esperado = isinstance(e, ERRORES_ESPERADOS)
        mensaje = _mensaje_error(e) if esperado else "Error interno (%s): %s" % (
            e.__class__.__name__, e)
        if not esperado:
            traceback.print_exc(file=sys.stderr)    # el detalle, solo en el log local
        entrada.update(resultado="error", error=mensaje,
                       duracion_ms=round((time.perf_counter() - inicio) * 1000, 1))
        _anotar(entrada)
        raise ToolError(mensaje) from None
    entrada.update(resultado="ok", duracion_ms=round((time.perf_counter() - inicio) * 1000, 1))
    _anotar(entrada)
    return resultado


def _leer_unsa(proyecto):
    return proyecto or "unsa"


SOLO_LECTURA = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True,
                               openWorldHint=False)
ANOTA = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False,
                        openWorldHint=False)
TIPOS_TXT = ", ".join(nucleo.TIPOS)

# Tipos con descripcion: es lo que el LLM lee en el input_schema de cada tool.
Proyecto = Annotated[str, Field(description="Id del proyecto auditado (por defecto 'unsa').")]
Ref = Annotated[str, Field(description="Referencia del control del catalogo, p. ej. 'A.1.2.2' "
                                       "o '9.2' (ver recurso pims://catalogo).")]
RutaArchivo = Annotated[str, Field(description="Ruta ABSOLUTA del archivo en la maquina "
                                               "donde corre el servidor MCP.")]


# =============================================================== tools deterministas

@mcp.tool(title="Listar proyectos de auditoria", annotations=SOLO_LECTURA)
def listar_proyectos() -> dict:
    """Lista las organizaciones auditadas (proyectos) disponibles en el agente.

    Cada proyecto tiene su propio expediente de evidencias. El proyecto por defecto es
    'unsa' (Universidad Nacional de San Agustin de Arequipa, rol 'responsable' del
    tratamiento de datos personales segun la Ley N.o 29733). Sin IA.

    Devuelve {"proyectos": [{id, nombre, rol, descripcion, creado, evidencias}]}.
    """
    return {"proyectos": _ejecutar("listar_proyectos", H.listar_proyectos)}


@mcp.tool(title="Estado del expediente", annotations=SOLO_LECTURA)
def estado_expediente(proyecto: Proyecto = "unsa") -> dict:
    """Muestra las evidencias registradas en el expediente y su integridad actual.

    Recalcula los SHA-256 y revisa la cadena de custodia SIN dejar constancia (consulta
    pura). Usala para saber que evidencias hay (id, titulo, tipo, controles, fechas,
    hash) antes de evaluar o redactar. Sin IA.

    Args:
        proyecto: id del proyecto auditado (por defecto 'unsa').
    """
    return _ejecutar("estado_expediente", H.estado_expediente, proyecto=_leer_unsa(proyecto))


@mcp.tool(title="Verificar integridad del expediente", annotations=ANOTA)
def verificar_integridad(proyecto: Proyecto = "unsa") -> dict:
    """Verifica la integridad del expediente y deja constancia en la cadena de custodia.

    Recalcula el SHA-256 de cada evidencia (OK / ALTERADA / FALTANTE) y comprueba que la
    cadena de custodia enlazada por hash no tenga roturas. A diferencia de
    estado_expediente, anade una linea VERIFICACION a la cadena: usala como paso formal
    de auditoria, no para consultas repetidas. Sin IA.

    Args:
        proyecto: id del proyecto auditado (por defecto 'unsa').

    Devuelve {total, resultados: {OK, ALTERADA, FALTANTE}, problemas_cadena, integro}.
    """
    return _ejecutar("verificar_integridad", H.verificar_integridad,
                     proyecto=_leer_unsa(proyecto), responsable="agente-evidencia (MCP)")


@mcp.tool(title="Matriz de cobertura de controles", annotations=SOLO_LECTURA)
def matriz_cobertura(
        proyecto: Proyecto = "unsa",
        rol: Annotated[Optional[str], Field(
            description="'responsable' o 'encargado' del tratamiento; si se omite, el del "
                        "proyecto.")] = None,
        vigencia_dias: Annotated[int, Field(
            ge=1, description="Antiguedad maxima (dias) de una evidencia para no quedar "
                              "Desactualizada.")] = 365,
        fecha_corte: Annotated[Optional[str], Field(
            description="Fecha de referencia AAAA-MM-DD (por defecto, hoy).")] = None) -> dict:
    """Calcula la matriz de cobertura de los controles ISO/IEC 27701:2025.

    Para cada control aplicable (clausulas 4-10 y Anexo A) indica su estado: Cubierto,
    Parcial, Desactualizada, Comprometida, Sin evidencia o No aplica, las evidencias que
    lo soportan y una nota con lo que se espera. Incluye el % de cobertura y el conteo
    por estado. Sin IA.

    Args:
        proyecto: id del proyecto auditado (por defecto 'unsa').
        rol: 'responsable' o 'encargado' del tratamiento; si se omite, el del proyecto.
        vigencia_dias: antiguedad maxima de una evidencia para no quedar Desactualizada.
        fecha_corte: fecha de referencia AAAA-MM-DD (por defecto, hoy).
    """
    return _ejecutar("matriz_cobertura", H.matriz_cobertura, proyecto=_leer_unsa(proyecto),
                     rol=rol, vigencia_dias=vigencia_dias, fecha_corte=fecha_corte)


@mcp.tool(title="Registrar evidencia", annotations=ANOTA)
def registrar_evidencia(
        ruta_archivo: RutaArchivo,
        controles: Annotated[list[str], Field(
            min_length=1, description="Refs del catalogo que soporta, p. ej. "
                                      "['A.1.2.2', '9.2'].")],
        tipo: Annotated[str, Field(description="Tipo de evidencia: " + TIPOS_TXT + ".")],
        titulo: Annotated[str, Field(min_length=3, description="Titulo descriptivo.")],
        proyecto: Proyecto = "unsa",
        fuente: Annotated[str, Field(
            description="Origen del documento (URL, area, persona entrevistada...).")] = "",
        fecha_documento: Annotated[Optional[str], Field(
            description="Fecha del documento AAAA-MM-DD (si se omite, la de hoy).")] = None,
) -> dict:
    """Registra (store) un archivo como evidencia de auditoria en el expediente.

    Copia el archivo al expediente, calcula su SHA-256, anade la linea REGISTRO a la
    cadena de custodia y lo indexa en el RAG. Es una accion con efecto permanente: la
    cadena es de solo anadir. Si no sabes que controles o tipo asignar, llama antes a
    clasificar_evidencia y confirma la propuesta con el usuario. Sin IA.

    Args:
        ruta_archivo: ruta ABSOLUTA del archivo en la maquina del servidor.
        controles: refs del catalogo que soporta, p. ej. ["A.1.2.2", "9.2"].
        tipo: tipo de evidencia (ver input_schema).
        titulo: titulo descriptivo de la evidencia.
        proyecto: id del proyecto auditado (por defecto 'unsa').
        fuente: origen del documento (URL, area, persona entrevistada...).
        fecha_documento: fecha del documento AAAA-MM-DD (si se omite, la de hoy).
    """
    return _ejecutar("registrar_evidencia", H.registrar, ruta_archivo=ruta_archivo,
                     controles=controles, tipo=tipo, titulo=titulo,
                     proyecto=_leer_unsa(proyecto), responsable="agente-evidencia (MCP)",
                     fuente=fuente, fecha_documento=fecha_documento)


@mcp.tool(title="Generar informe de auditoria (preliminar)", annotations=ANOTA)
def generar_informe_auditoria(
        proyecto: Proyecto = "unsa",
        hallazgos: Annotated[Optional[dict[str, str]], Field(
            description="{ref_control: texto del hallazgo} ya redactados (p. ej. con "
                        "redactar_hallazgo).")] = None) -> dict:
    """Genera el informe de auditoria interna (clausula 9.2) en Markdown.

    Incluye integridad del expediente, resumen de cobertura, evidencias analizadas con su
    hash, la matriz completa y un apartado de hallazgos por cada control no cubierto. El
    informe sale SIEMPRE marcado como PRELIMINAR: la validacion final la firma el auditor
    humano fuera de MCP. Sin IA.

    Args:
        proyecto: id del proyecto auditado (por defecto 'unsa').
        hallazgos: {ref_control: texto} ya redactados (p. ej. con redactar_hallazgo);
            los controles sin texto se listan como "sin redactar".

    Devuelve {ruta, controles_con_hallazgo}.
    """
    return _ejecutar("generar_informe_auditoria", H.generar_informe,
                     proyecto=_leer_unsa(proyecto), hallazgos=hallazgos or {})


# =============================================================== tools con IA local

@mcp.tool(title="Buscar en norma y evidencias (IA)", annotations=SOLO_LECTURA)
def buscar_evidencia(
        consulta: Annotated[str, Field(min_length=2, description="Pregunta o texto a buscar.")],
        proyecto: Proyecto = "unsa",
        k: Annotated[int, Field(ge=1, le=20, description="Fragmentos a devolver.")] = 6) -> dict:
    """Busqueda semantica (RAG) en la norma ISO/IEC 27701, la base de conocimiento y las
    evidencias del proyecto.

    Usa embeddings locales (nomic-embed-text en Ollama) e indice FAISS. Devuelve los k
    fragmentos mas parecidos con su origen (norma con clausula y pagina, o evidencia con
    su id), para citar fuentes en lugar de inventarlas.

    Args:
        consulta: pregunta o texto a buscar, en lenguaje natural.
        proyecto: id del proyecto auditado (por defecto 'unsa').
        k: numero de fragmentos a devolver (1-20).
    """
    k = max(1, min(int(k), 20))
    return {"consulta": consulta,
            "resultados": _ejecutar("buscar_evidencia", H.buscar, ia=True, consulta=consulta,
                                    proyecto=_leer_unsa(proyecto), k=k)}


@mcp.tool(title="Clasificar archivo como evidencia (IA)", annotations=SOLO_LECTURA)
def clasificar_evidencia(ruta_archivo: RutaArchivo, proyecto: Proyecto = "unsa") -> dict:
    """Propone, con IA local, como clasificar un archivo antes de registrarlo.

    Lee el archivo (PDF, DOCX, TXT...) y sugiere controles del catalogo, tipo de
    evidencia, titulo y fecha del documento. NO registra nada: es una propuesta que el
    usuario confirma antes de llamar a registrar_evidencia.

    Args:
        ruta_archivo: ruta ABSOLUTA del archivo en la maquina del servidor.
        proyecto: id del proyecto auditado (por defecto 'unsa').
    """
    return _ejecutar("clasificar_evidencia", H.clasificar, ia=True, ruta_archivo=ruta_archivo,
                     proyecto=_leer_unsa(proyecto))


@mcp.tool(title="Evaluar pertinencia de evidencias (IA)", annotations=ANOTA)
def evaluar_pertinencia(ref: Ref, proyecto: Proyecto = "unsa") -> dict:
    """La IA local lee las evidencias de un control y PROPONE si cumple, cumple
    parcialmente o no cumple el requisito de la norma.

    La propuesta queda guardada como 'pendiente' de revision. Aceptarla o rechazarla es
    decision exclusiva del auditor humano (human-in-the-loop) y no se puede hacer por MCP.
    Solo aplica a controles con evidencia (Cubierto, Parcial...).

    Args:
        ref: referencia del control, p. ej. "A.1.2.2" o "9.2".
        proyecto: id del proyecto auditado (por defecto 'unsa').
    """
    return _ejecutar("evaluar_pertinencia", H.evaluar_pertinencia, ia=True, ref=ref,
                     proyecto=_leer_unsa(proyecto))


@mcp.tool(title="Redactar hallazgo preliminar (IA)", annotations=SOLO_LECTURA)
def redactar_hallazgo(ref: Ref, proyecto: Proyecto = "unsa") -> dict:
    """Redacta con IA local un hallazgo de auditoria preliminar para un control no
    cubierto, con la estructura criterio - condicion - causa - efecto - recomendacion.

    El criterio se apoya en el texto de la norma recuperado por RAG. Es un borrador para
    el auditor; puede pasarse despues a generar_informe_auditoria en "hallazgos".

    Args:
        ref: referencia del control, p. ej. "A.1.3.7" o "6.1".
        proyecto: id del proyecto auditado (por defecto 'unsa').
    """
    return _ejecutar("redactar_hallazgo", H.redactar_hallazgo, ia=True, ref=ref,
                     proyecto=_leer_unsa(proyecto))


@mcp.tool(title="Preguntar al asistente AUDITA-PIMS (IA)", annotations=SOLO_LECTURA)
def preguntar_asistente(
        mensaje: Annotated[str, Field(min_length=2, description="La pregunta, en espanol.")],
        proyecto: Proyecto = "unsa",
        historial: Annotated[Optional[list[dict[str, str]]], Field(
            description="Turnos previos [{'role': 'user'|'assistant', 'content': '...'}].")]
        = None) -> dict:
    """Pregunta libre al asistente AUDITA-PIMS sobre el expediente o la norma.

    Responde con el LLM local (qwen2.5) usando RAG sobre la norma y las evidencias, y el
    resumen de cobertura del proyecto. Devuelve la respuesta y las fuentes citadas.

    Args:
        mensaje: la pregunta, en espanol.
        proyecto: id del proyecto auditado (por defecto 'unsa').
        historial: turnos previos [{"role": "user"|"assistant", "content": "..."}].
    """
    return _ejecutar("preguntar_asistente", H.preguntar, ia=True, mensaje=mensaje,
                     proyecto=_leer_unsa(proyecto), historial=historial or [])


# =============================================================== resources

def _control(ref):
    c = next((c for c in nucleo.CATALOGO if c["ref"] == ref), None)
    if not c:
        raise ResourceError("Control no encontrado en el catalogo: %s" % ref)
    return c


@mcp.resource("pims://catalogo", name="catalogo_controles", mime_type="application/json",
              title="Catalogo de controles ISO/IEC 27701:2025")
def recurso_catalogo() -> str:
    """Catalogo de controles del PIMS (clausulas 4-10 y Anexo A de ISO/IEC 27701:2025)
    con la evidencia esperada y el minimo de evidencias de cada uno."""
    return json.dumps({"norma": "ISO/IEC 27701:2025", "total": len(nucleo.CATALOGO),
                       "controles": nucleo.CATALOGO}, ensure_ascii=False, indent=2)


@mcp.resource("pims://catalogo/{ref}", name="control_catalogo", mime_type="application/json",
              title="Un control del catalogo")
def recurso_control(ref: str) -> str:
    """Ficha de un control del catalogo (titulo, grupo, evidencia esperada, minimo)."""
    return json.dumps(_control(ref), ensure_ascii=False, indent=2)


@mcp.resource("norma://control/{ref}", name="texto_norma_control", mime_type="text/markdown",
              title="Texto de la norma para un control")
def recurso_norma(ref: str) -> str:
    """Texto de ISO/IEC 27701:2025 que corresponde a un control del catalogo: la clausula
    con sus subapartados, o el requisito del Anexo A con su guia del Anexo B, con cita
    (norma, seccion y pagina del PDF)."""
    control = _control(ref)
    secciones = norma.para_control(ref)
    lin = ["# %s %s" % (ref, control["titulo"]), ""]
    if not secciones:
        lin.append("_No se encontro texto de la norma para %s en ISOS/texto._" % ref)
    for s in secciones:
        lin += ["## [%s] %s %s" % (norma.cita(s), s["ref"], s["titulo"]), "", s["texto"], ""]
    return "\n".join(lin)


# =============================================================== prompt

@mcp.prompt(name="auditoria_interna", title="Auditoria interna del PIMS (cl. 9.2)")
def auditoria_interna(proyecto: str = "unsa", alcance: str = "todos los controles") -> str:
    """Guia paso a paso para ejecutar una auditoria interna del PIMS con las tools de
    este servidor, respetando la revision humana."""
    return """Actua como auditor interno del PIMS ISO/IEC 27701:2025 (clausula 9.2) del proyecto
'{p}'. Alcance: {a}. Usa solo las tools del servidor evidencias-pims y cita fuentes.

1. listar_proyectos y estado_expediente(proyecto="{p}"): resume que evidencias hay.
2. verificar_integridad(proyecto="{p}"): si hay evidencias ALTERADAS/FALTANTES o la cadena
   de custodia esta rota, detente y reportalo como hallazgo critico.
3. matriz_cobertura(proyecto="{p}"): presenta el % de cobertura y el conteo por estado.
4. Para cada control Parcial/Cubierto relevante, evaluar_pertinencia(ref): presenta la
   propuesta de la IA e indica que el auditor humano debe aceptarla o rechazarla
   (no puedes decidirlo tu; no existe tool para ello).
5. Para cada control Sin evidencia/Parcial/Desactualizada/Comprometida del alcance,
   redactar_hallazgo(ref). Apoya el criterio en el recurso norma://control/<ref>.
6. generar_informe_auditoria(proyecto="{p}", hallazgos={{ref: texto}}) y entrega la ruta.
   Recuerda que el informe es PRELIMINAR hasta que el auditor lo valide.

No registres evidencias nuevas sin confirmacion explicita del usuario. Distingue siempre
hechos (hash, matriz, cadena) de propuestas de la IA.""".format(p=proyecto, a=alcance)


# =============================================================== arranque

def main(argv=None):
    global TRANSPORTE
    ap = argparse.ArgumentParser(description="Servidor MCP evidencias-pims")
    ap.add_argument("--http", action="store_true",
                    help="streamable HTTP en lugar de stdio (http://HOST:PUERTO/mcp)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--puerto", type=int, default=PUERTO_HTTP)
    a = ap.parse_args(argv)
    if a.http:
        TRANSPORTE = "streamable-http"
        print("evidencias-pims: MCP streamable HTTP en http://%s:%d/mcp" % (a.host, a.puerto),
              file=sys.stderr)
        if SDK_V2:
            mcp.run("streamable-http", host=a.host, port=a.puerto)
        else:
            mcp.settings.host, mcp.settings.port = a.host, a.puerto
            mcp.run(transport="streamable-http")
    else:
        mcp.run("stdio")


if __name__ == "__main__":
    main()
