# -*- coding: utf-8 -*-
"""
Documentos del PIMS en la base de datos (Entregable 3).

Los grupos del PIMS corrigen las plantillas 27001:2013 del docente, las alinean a
ISO/IEC 27701:2025 y las llenan para la UNSA (implementacion simulada). Este modulo:

  1. registra cada documento en PostgreSQL: archivo y texto en `documentos` /
     `documento_paginas`, metadatos de control en `documentos_pims` (lista maestra
     PIMS-RG-01) y, ademas, como evidencia del expediente (SHA-256, cadena de custodia),
     para que cuente en la matriz de cobertura;
  2. lee la tabla de control de su portada (plantillas_pims.leer_metadatos);
  3. verifica el control documental con las reglas de PIMS-PR-01 (7.5.2 y 7.5.3) y
     propone el hallazgo de la clausula 7.5 que usa la auditoria interna.

El agente propone: un documento solo pasa a "aprobado" si su portada lo dice, y el
auditor decide sobre el hallazgo.
"""

import datetime as dt
import hashlib
import json
import os
import re

import lista_maestra_pims as lm
import nucleo
import plantillas_pims as pp
from nucleo import ErrorAgente

ACTOR = "agente-evidencia"
EXTENSIONES = (".docx",)

# Lista maestra PIMS-RG-01 (todos los equipos del PIMS): codigo -> (titulo, requisitos,
# expedientes de la guia, equipo). La fuente es lista_maestra_pims.py; en ejecucion se lee
# de la tabla `lista_maestra_pims` (ver lista_esperada()). Un documento con otro codigo
# tambien se puede registrar: aparece como "fuera de la lista acordada".
EQUIPO = lm.G6
LISTA_MAESTRA = lm.por_codigo()
TIPO_POR_PREFIJO = {"POL": "politica", "MA": "politica", "PR": "procedimiento", "MT": "procedimiento",
                    "PL": "procedimiento", "FO": "registro", "RG": "registro", "IN": "informe",
                    "AC": "acta"}
TIPO_DOCUMENTO = {"POL": "política", "MA": "manual", "PR": "procedimiento", "MT": "metodología",
                  "PL": "plan", "FO": "formulario", "RG": "registro", "IN": "informe", "AC": "acta"}
NIVELES = ("público", "publico", "uso interno", "confidencial", "restringido")
RESTOS_27001 = (r"\bSGSI\b", r"\bSGCN\b", r"27001:2013", r"ISO 22301", r"BS 25999", r"EPPS",
                r"iso27001standard", r"Dejan Kosutic")
RE_MARCADOR = re.compile(r"\[[^\]\n]{3,60}\]")


def _cx():
    if nucleo.ALMACEN is None:
        raise ErrorAgente("Los documentos PIMS necesitan PostgreSQL (PIMS_BACKEND=postgres).")
    return nucleo.ALMACEN.conexion()


def _prefijo(codigo):
    m = re.match(r"^PIMS-([A-Z]+)-\d+$", codigo or "")
    return m.group(1) if m else ""


def catalogo_refs():
    return {c["ref"] for c in nucleo.CATALOGO}


# ----------------------------------------------------------------------------- lista maestra
def sincronizar_lista_maestra(proyecto="unsa"):
    """Copia lista_maestra_pims.py a la tabla `lista_maestra_pims` (PIMS-RG-01 en la BD).
    Los codigos que ya no estan en la lista se borran de la tabla. Devuelve cuantos quedan."""
    filas = lm.filas()
    with _cx() as cx, cx.transaction(), cx.cursor() as cur:
        for f in filas:
            cur.execute("""INSERT INTO lista_maestra_pims (proyecto, codigo, orden, titulo, tipo,
                                  requisitos, expedientes, marca, equipo, propietario, confidencialidad)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                           ON CONFLICT (proyecto, codigo) DO UPDATE SET orden = EXCLUDED.orden,
                               titulo = EXCLUDED.titulo, tipo = EXCLUDED.tipo,
                               requisitos = EXCLUDED.requisitos, expedientes = EXCLUDED.expedientes,
                               marca = EXCLUDED.marca, equipo = EXCLUDED.equipo,
                               propietario = EXCLUDED.propietario,
                               confidencialidad = EXCLUDED.confidencialidad, actualizado = now()""",
                        (proyecto, f["codigo"], f["orden"], f["titulo"], f["tipo"], f["requisitos"],
                         f["expedientes"], f["marca"], f["equipo"], f["propietario"],
                         f["confidencialidad"]))
        cur.execute("DELETE FROM lista_maestra_pims WHERE proyecto = %s AND NOT (codigo = ANY(%s))",
                    (proyecto, [f["codigo"] for f in filas]))
    return len(filas)


def lista_esperada(proyecto="unsa"):
    """{codigo: (titulo, requisitos, expedientes, equipo)} en el orden de PIMS-RG-01.
    Se lee de la BD; si la tabla no existe o esta vacia, de lista_maestra_pims.py."""
    try:
        with _cx() as cx, cx.cursor() as cur:
            cur.execute("""SELECT codigo, titulo, requisitos, expedientes, equipo
                           FROM lista_maestra_pims WHERE proyecto = %s ORDER BY orden, codigo""",
                        (proyecto,))
            filas = cur.fetchall()
    except Exception:  # noqa: BLE001  (BD sin la migracion o sin PostgreSQL)
        filas = []
    if not filas:
        return dict(LISTA_MAESTRA)
    return {f["codigo"]: (f["titulo"], list(f["requisitos"]), list(f["expedientes"]), f["equipo"])
            for f in filas}


# ----------------------------------------------------------------------------- texto
def secciones_docx(ruta):
    """[(n, texto)] partiendo el documento en secciones de nivel 1 (hacen de 'paginas')."""
    import docx
    d = docx.Document(ruta)
    bloques, actual = [], []
    cuerpo = d.element.body
    for el in cuerpo.iterchildren():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag == "p":
            p = docx.text.paragraph.Paragraph(el, d)
            t = p.text.strip()
            if p.style is not None and p.style.name == "Heading 1" and actual:
                bloques.append("\n".join(actual))
                actual = []
            if t:
                actual.append(t)
        elif tag == "tbl":
            t = docx.table.Table(el, d)
            for fila in t.rows:
                vistos = []
                for c in fila.cells:
                    x = c.text.strip()
                    if x and x not in vistos:
                        vistos.append(x)
                if vistos:
                    actual.append(" | ".join(vistos))
    if actual:
        bloques.append("\n".join(actual))
    return [(i, b) for i, b in enumerate(bloques, 1) if b.strip()]


# ----------------------------------------------------------------------------- PR-01
def verificar_control(meta, hoy=None):
    """Reglas de PIMS-PR-01 sobre los metadatos leidos de la portada.
    Devuelve {resultado: conforme|observaciones|no_conforme, estado: borrador|aprobado,
    reglas: [{regla, requisito, ok, gravedad, detalle}]}."""
    hoy = hoy or dt.date.today()
    reglas = []

    def regla(nombre, requisito, ok, gravedad, detalle):
        reglas.append({"regla": nombre, "requisito": requisito, "ok": bool(ok),
                       "gravedad": gravedad, "detalle": detalle})

    codigo = meta.get("codigo", "")
    regla("Código PIMS-TT-NN", "7.5.2", pp.RE_CODIGO.match(codigo), "mayor",
          codigo or "La portada no tiene código")
    try:
        version = float(meta.get("version") or "0")
    except ValueError:
        version = 0.0
    aprobado = (meta.get("aprobado_por") or "").strip()
    aprobado_ok = bool(aprobado) and "[" not in aprobado
    regla("Versión aprobada (1.0 o superior)", "7.5.2", version >= 1.0, "mayor",
          "Versión %s" % (meta.get("version") or "sin versión") +
          ("" if version >= 1.0 else ": es un borrador y no sirve como evidencia"))
    regla("Aprobador identificado", "7.5.2", aprobado_ok, "mayor",
          aprobado or "Campo «Aprobado por» vacío")
    fecha = pp.fecha_ddmmaaaa(meta.get("fecha_version", ""))
    regla("Fecha de la versión (DD-MM-AAAA)", "7.5.2", fecha is not None, "menor",
          meta.get("fecha_version") or "Sin fecha")
    conf = (meta.get("confidencialidad") or "").strip().lower()
    regla("Nivel de confidencialidad", "7.5.3", any(conf.startswith(n) for n in NIVELES), "menor",
          meta.get("confidencialidad") or "Sin nivel de confidencialidad")
    hist = meta.get("historial") or []
    ultima = hist[-1]["version"] if hist else ""
    regla("Historial de modificaciones al día", "7.5.3", hist and ultima == meta.get("version"),
          "menor", ("%d entradas; última %s" % (len(hist), ultima)) if hist else "Sin historial")
    valido = pp.fecha_ddmmaaaa(meta.get("valido_hasta", ""))
    regla("Validez vigente", "7.5.3", valido is not None and valido >= hoy, "mayor",
          ("Válido hasta %s" % meta["valido_hasta"]) if valido else "No indica hasta cuándo es válido")
    regla("Propietario definido", "7.5.3", bool(meta.get("propietario")), "menor",
          meta.get("propietario") or "No indica propietario")
    # El historial de modificaciones puede citar la plantilla de origen ("Adaptacion de la
    # plantilla ISO/IEC 27001:2013..."): no cuenta como resto de la plantilla.
    texto = "\n".join(linea for linea in (meta.get("texto") or "").splitlines()
                      if not re.match(r"^\d{2}-\d{2}-\d{4} \|", linea))
    marcadores = sorted(set(RE_MARCADOR.findall(texto)))
    regla("Sin campos de plantilla por llenar", "7.5.2", not marcadores, "mayor",
          ", ".join(marcadores[:6]) if marcadores else "Completo")
    restos = [r.replace("\\b", "") for r in RESTOS_27001 if re.search(r, texto)]
    regla("Alineado a ISO/IEC 27701:2025 (sin restos de la plantilla 27001/22301)", "7.5.1",
          "27701" in texto and not restos, "mayor",
          ("Restos: %s" % ", ".join(restos)) if restos else
          ("Cita ISO/IEC 27701:2025" if "27701" in texto else "No cita ISO/IEC 27701"))
    mayores = [r for r in reglas if not r["ok"] and r["gravedad"] == "mayor"]
    menores = [r for r in reglas if not r["ok"] and r["gravedad"] == "menor"]
    resultado = "no_conforme" if mayores else ("observaciones" if menores else "conforme")
    estado = "aprobado" if version >= 1.0 and aprobado_ok else "borrador"
    return {"resultado": resultado, "estado": estado, "reglas": reglas,
            "fallas_mayores": len(mayores), "fallas_menores": len(menores),
            "verificado": dt.datetime.now().isoformat(timespec="seconds")}


# ----------------------------------------------------------------------------- registro
def previsualizar(ruta):
    """Lee la portada y sugiere requisitos sin registrar nada (para el formulario web)."""
    if not ruta.lower().endswith(EXTENSIONES):
        raise ErrorAgente("Los documentos PIMS se suben en .docx (formato de la plantilla).")
    meta = pp.leer_metadatos(ruta)
    sugerido = lista_esperada().get(meta.get("codigo"), ("", [], [], ""))
    control = verificar_control(meta)
    meta.pop("texto", None)
    return {"metadatos": meta, "control": control,
            "sugerencia": {"titulo": sugerido[0], "requisitos": sugerido[1],
                           "expedientes": sugerido[2], "agente_autor": sugerido[3]}}


def registrar(ruta, registrado_por, requisitos=None, agente_autor=None, proyecto="unsa",
              expedientes=None, fuente=""):
    """Registra un .docx PIMS: BD de documentos + lista maestra + expediente de evidencias.
    Idempotente por SHA-256. Si ya habia una version aprobada del mismo codigo y esta es
    posterior, la anterior pasa a obsoleta (PR-01, control de cambios)."""
    if not os.path.isfile(ruta):
        raise ErrorAgente("No existe el archivo %s" % ruta)
    if not registrado_por or not registrado_por.strip():
        raise ErrorAgente("Indique quién registra el documento.")
    meta = pp.leer_metadatos(ruta)
    codigo = meta.get("codigo", "").strip()
    if not codigo:
        raise ErrorAgente("La portada no tiene «Código»: use la plantilla PIMS (PIMS-PR-01).")
    sugerido = lista_esperada(proyecto).get(codigo, (meta.get("titulo") or codigo, [], [], ""))
    requisitos = [r.strip() for r in (requisitos or sugerido[1]) if r and r.strip()]
    if not requisitos:
        raise ErrorAgente("Indique qué cláusulas o controles respalda %s." % codigo)
    expedientes = expedientes or sugerido[2]
    agente_autor = agente_autor or sugerido[3] or "Sin indicar"
    control = verificar_control(meta)
    datos = open(ruta, "rb").read()
    sha = hashlib.sha256(datos).hexdigest()
    secciones = secciones_docx(ruta)
    titulo = meta.get("titulo") or sugerido[0] or codigo
    p = nucleo.proyecto(proyecto)
    cx = _cx()
    with cx.cursor() as cur:
        cur.execute("""SELECT dp.id, dp.codigo, dp.version FROM documentos_pims dp
                       JOIN documentos d ON d.id = dp.documento_id
                       WHERE d.proyecto = %s AND d.sha256 = %s""", (proyecto, sha))
        previo = cur.fetchone()
    if previo:
        cx.close()
        return dict(obtener(previo["id"]), ya_registrado=True)

    # 1) expediente de evidencias (SHA-256, cadena de custodia); el texto lo lee el RAG de la BD
    controles = [r for r in requisitos if r in catalogo_refs()]
    evidencia = next((e for e in nucleo.leer_indice(p.expediente)["evidencias"]
                      if e["sha256"] == sha), None)          # reintento tras un fallo previo
    if controles and evidencia is None:
        with p.bloqueo:
            evidencia = nucleo.registrar_evidencia(
                p.expediente, ruta, controles, TIPO_POR_PREFIJO.get(_prefijo(codigo), "procedimiento"),
                "%s %s (v%s)" % (codigo, titulo, meta.get("version") or "?"), registrado_por,
                fuente or "Documento PIMS – implementación simulada (%s)" % agente_autor,
                (pp.fecha_ddmmaaaa(meta.get("fecha_version", "")) or dt.date.today()).isoformat(),
                nombre_original=os.path.basename(ruta))
            p._rag_listo = False      # el indice FAISS se rehace al proximo uso
    with cx.transaction(), cx.cursor() as cur:
        cur.execute("""INSERT INTO documentos (proyecto, archivo, titulo, tipo_documento, url_origen,
                              fecha_documento, fecha_descarga, sha256, tamano_bytes, paginas,
                              metodo_texto, caracteres)
                       VALUES (%s,%s,%s,'documento_pims',%s,%s,CURRENT_DATE,%s,%s,%s,'texto',%s)
                       ON CONFLICT (proyecto, sha256) DO UPDATE SET tipo_documento = 'documento_pims'
                       RETURNING id""",
                    (proyecto, os.path.basename(ruta), "%s %s" % (codigo, titulo), fuente or None,
                     pp.fecha_ddmmaaaa(meta.get("fecha_version", "")), sha, len(datos), len(secciones),
                     sum(len(t) for _, t in secciones)))
        doc_id = cur.fetchone()["id"]
        cur.execute("DELETE FROM documento_paginas WHERE documento_id = %s", (doc_id,))
        for n, texto in secciones:
            cur.execute("INSERT INTO documento_paginas (documento_id, pagina, texto, metodo) "
                        "VALUES (%s,%s,%s,'texto')", (doc_id, n, texto.replace("\x00", "")))
        ev_id = None
        if evidencia:
            cur.execute("SELECT id FROM evidencias WHERE proyecto = %s AND codigo = %s",
                        (proyecto, evidencia["id"]))
            fila = cur.fetchone()
            ev_id = fila["id"] if fila else None
        cur.execute(
            """INSERT INTO documentos_pims (proyecto, documento_id, evidencia_id, codigo, titulo, tipo,
                   version, fecha_version, creado_por, aprobado_por, confidencialidad, propietario,
                   valido_hasta, historial, requisitos, expedientes, agente_autor, estado, control,
                   registrado_por)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
            (proyecto, doc_id, ev_id, codigo, titulo, TIPO_DOCUMENTO.get(_prefijo(codigo), "otro"),
             meta.get("version"), pp.fecha_ddmmaaaa(meta.get("fecha_version", "")),
             meta.get("creado_por"), meta.get("aprobado_por"), meta.get("confidencialidad"),
             meta.get("propietario"), pp.fecha_ddmmaaaa(meta.get("valido_hasta", "")),
             json.dumps(meta.get("historial") or [], ensure_ascii=False), requisitos, expedientes,
             agente_autor, control["estado"], json.dumps(control, ensure_ascii=False), registrado_por))
        nuevo = cur.fetchone()["id"]
        obsoletos = []
        if control["estado"] == "aprobado":
            cur.execute("""UPDATE documentos_pims SET estado = 'obsoleto'
                           WHERE proyecto = %s AND codigo = %s AND id <> %s AND estado = 'aprobado'
                           RETURNING id, version, evidencia_id""", (proyecto, codigo, nuevo))
            obsoletos = cur.fetchall()
            for o in obsoletos:
                if o["evidencia_id"]:
                    cur.execute("UPDATE evidencias SET estado = 'obsoleta' WHERE id = %s",
                                (o["evidencia_id"],))
        cur.execute("""INSERT INTO decisiones_humanas (fecha, flujo, proyecto, nodo, actor, origen,
                              decision, detalle)
                       VALUES (now(), 'documentos_pims', %s, 'registrar', %s, 'humano', %s, %s)""",
                    (proyecto, registrado_por, "documento PIMS registrado: %s v%s" % (codigo, meta.get("version")),
                     json.dumps({"sha256": sha, "resultado_control": control["resultado"],
                                 "requisitos": requisitos, "evidencia": evidencia and evidencia["id"],
                                 "obsoletos": [o["version"] for o in obsoletos]}, ensure_ascii=False)))
    cx.close()
    if obsoletos:
        nucleo.PROYECTOS._cache.clear()   # el indice del expediente cambio (evidencia obsoleta)
    return dict(obtener(nuevo), ya_registrado=False)


# ----------------------------------------------------------------------------- consultas
COLUMNAS = ("id, codigo, titulo, tipo, version, fecha_version, creado_por, aprobado_por, "
            "confidencialidad, propietario, valido_hasta, historial, requisitos, expedientes, "
            "agente_autor, estado, control, registrado_por, registrado, archivo, sha256, paginas, "
            "caracteres, vigente, evidencia_id, documento_id")


def _publico(fila):
    f = dict(fila)
    for k in ("fecha_version", "valido_hasta", "registrado"):
        if f.get(k) is not None:
            f[k] = f[k].isoformat()
    return f


def listar(proyecto="unsa"):
    with _cx() as cx, cx.cursor() as cur:
        cur.execute("SELECT %s FROM v_documentos_pims WHERE proyecto = %%s ORDER BY codigo, id DESC"
                    % COLUMNAS, (proyecto,))
        docs = [_publico(r) for r in cur.fetchall()]
        cur.execute("""SELECT e.codigo AS evidencia, d.id FROM documentos_pims d
                       JOIN evidencias e ON e.id = d.evidencia_id WHERE d.proyecto = %s""", (proyecto,))
        evid = {r["id"]: r["evidencia"] for r in cur.fetchall()}
    for d in docs:
        d["evidencia"] = evid.get(d["id"])
    return docs


def obtener(id_):
    with _cx() as cx, cx.cursor() as cur:
        cur.execute("SELECT %s FROM v_documentos_pims WHERE id = %%s" % COLUMNAS, (id_,))
        fila = cur.fetchone()
        if not fila:
            raise ErrorAgente("No existe el documento PIMS %s" % id_)
        cur.execute("SELECT pagina, texto FROM documento_paginas WHERE documento_id = %s "
                    "ORDER BY pagina", (fila["documento_id"],))
        secciones = [dict(r) for r in cur.fetchall()]
    d = _publico(fila)
    d["secciones"] = secciones
    return d


def lista_maestra(proyecto="unsa"):
    """Lista maestra PIMS-RG-01: cada codigo esperado con su version vigente (o pendiente)."""
    docs = listar(proyecto)
    por_codigo = {}
    for d in docs:
        if d["estado"] != "obsoleto":
            por_codigo.setdefault(d["codigo"], d)
    filas = []
    for codigo, (titulo, reqs, exps, agente) in lista_esperada(proyecto).items():
        d = por_codigo.pop(codigo, None)
        filas.append({"codigo": codigo, "titulo": d["titulo"] if d else titulo, "requisitos": reqs,
                      "expedientes": exps, "agente_autor": agente, "propio": agente == EQUIPO,
                      "documento": d and {k: d[k] for k in ("id", "version", "estado", "vigente",
                                                            "control", "evidencia")},
                      "situacion": ("Vigente" if d["vigente"] else "Borrador" if d["estado"] == "borrador"
                                    else "Vencido") if d else "Pendiente"})
    for codigo, d in por_codigo.items():     # documentos fuera de la lista acordada
        filas.append({"codigo": codigo, "titulo": d["titulo"], "requisitos": d["requisitos"],
                      "expedientes": d["expedientes"], "agente_autor": d["agente_autor"],
                      "propio": d["agente_autor"] == EQUIPO,
                      "documento": {k: d[k] for k in ("id", "version", "estado", "vigente",
                                                      "control", "evidencia")},
                      "situacion": "Vigente" if d["vigente"] else "Borrador", "fuera_de_lista": True})
    return filas


def reverificar(proyecto="unsa", hoy=None):
    """Vuelve a aplicar las reglas de PR-01 a todos los documentos no obsoletos (la validez
    vence con el tiempo). Devuelve la lista con el resultado nuevo."""
    salida = []
    with _cx() as cx:
        with cx.cursor() as cur:
            cur.execute("""SELECT dp.id, dp.codigo, d.sha256, d.archivo FROM documentos_pims dp
                           JOIN documentos d ON d.id = dp.documento_id
                           WHERE dp.proyecto = %s AND dp.estado <> 'obsoleto'""", (proyecto,))
            filas = cur.fetchall()
        p = nucleo.proyecto(proyecto)
        indice = nucleo.leer_indice(p.expediente)["evidencias"]
        rutas = {e["sha256"]: os.path.join(p.expediente, e["archivo"]) for e in indice}
        for f in filas:
            ruta = rutas.get(f["sha256"])
            if not ruta or not os.path.isfile(ruta):
                salida.append({"id": f["id"], "codigo": f["codigo"], "resultado": "sin_archivo"})
                continue
            control = verificar_control(pp.leer_metadatos(ruta), hoy)
            with cx.cursor() as cur:
                cur.execute("UPDATE documentos_pims SET control = %s WHERE id = %s",
                            (json.dumps(control, ensure_ascii=False), f["id"]))
            cx.commit()
            salida.append({"id": f["id"], "codigo": f["codigo"], "resultado": control["resultado"]})
    return salida


# ----------------------------------------------------------------------------- auditoria
def control_documental(proyecto="unsa", hoy=None):
    """Paso de la auditoria interna: aplica PR-01 a cada documento PIMS vigente o en borrador
    y resume lo que falta de la lista maestra. Devuelve {documentos, pendientes, resumen,
    hallazgo (o None)}: el hallazgo es uno solo, sobre la clausula 7.5."""
    try:
        reverificar(proyecto, hoy)
    except Exception:        # noqa: BLE001  (archivo fuera de disco: se usa el ultimo control)
        pass
    docs = [d for d in listar(proyecto) if d["estado"] != "obsoleto"]
    vistos = set()
    unicos = []
    for d in docs:                      # una fila por codigo (la mas reciente)
        if d["codigo"] not in vistos:
            vistos.add(d["codigo"])
            unicos.append(d)
    revisados = []
    for d in unicos:
        c = d.get("control") or {}
        fallas = [r for r in c.get("reglas", []) if not r["ok"]]
        revisados.append({"codigo": d["codigo"], "titulo": d["titulo"], "version": d["version"],
                          "estado": d["estado"], "agente_autor": d["agente_autor"],
                          "resultado": c.get("resultado", "sin_verificar"),
                          "fallas": [{"regla": r["regla"], "gravedad": r["gravedad"],
                                      "detalle": r["detalle"], "requisito": r["requisito"]}
                                     for r in fallas]})
    esperada = lista_esperada(proyecto)
    pendientes = [c for c in esperada if c not in vistos]
    con_falla = [r for r in revisados if r["resultado"] != "conforme"]
    resumen = {"documentos": len(revisados),
               "conformes": sum(1 for r in revisados if r["resultado"] == "conforme"),
               "con_observaciones": sum(1 for r in revisados if r["resultado"] == "observaciones"),
               "no_conformes": sum(1 for r in revisados if r["resultado"] == "no_conforme"),
               "pendientes_lista_maestra": len(pendientes)}
    hallazgo = None
    if con_falla or pendientes:
        mayor = any(r["resultado"] == "no_conforme" for r in con_falla) or bool(pendientes)
        clas = "No conformidad menor" if mayor else "Observacion"
        lineas = []
        for r in con_falla:
            lineas.append("%s v%s (%s): %s" % (r["codigo"], r["version"] or "?", r["agente_autor"],
                                              "; ".join("%s – %s" % (f["regla"], f["detalle"])
                                                        for f in r["fallas"])))
        for c in pendientes:
            lineas.append("%s %s (%s): no está registrado en el repositorio documental"
                          % (c, esperada[c][0], esperada[c][3]))
        partes = []
        if con_falla:
            partes.append("%d de %d documentos PIMS no cumplen PIMS-PR-01" % (len(con_falla), len(revisados)))
        if pendientes:
            partes.append("%d documentos de la lista maestra PIMS-RG-01 sin registrar" % len(pendientes))
        hallazgo = {
            "ref": "7.5", "grupo": "clausula", "titulo": "Información documentada",
            "estado": "Control documental", "evidencias": [], "clasificacion": clas,
            "nivel": 2 if mayor else 1,
            "nota": "; ".join(partes) + ".",
            "documentos": con_falla, "pendientes": pendientes,
            "texto": "\n".join([
                "**Clasificacion propuesta:** %s" % clas,
                "- **Criterio:** ISO/IEC 27701:2025, 7.5.1, 7.5.2 y 7.5.3; PIMS-PR-01 Procedimiento "
                "de control de la información documentada y de los registros; lista maestra PIMS-RG-01.",
                "- **Condicion:** %s:" % "; ".join(partes)] +
                ["  - %s" % x for x in lineas] + [
                "- **Causa (preliminar):** Los documentos se registraron sin completar la portada de "
                "control o sin pasar por revisión y aprobación.",
                "- **Efecto:** Un documento en borrador, vencido o con campos de plantilla no sirve "
                "como evidencia de cumplimiento ante el auditor externo.",
                "- **Recomendacion:** Completar la portada, aprobar la versión 1.0 según la tabla de "
                "aprobación de PIMS-PR-01 y registrar en el repositorio cada documento de la lista "
                "maestra que falte.",
                "", "_Hallazgo determinista del control documental (PIMS-PR-01); requiere "
                "validacion del auditor._"]),
            "origen": "determinista (control documental)",
        }
    return {"documentos": revisados, "pendientes": pendientes, "resumen": resumen,
            "hallazgo": hallazgo}


def programa_auditoria(proyecto="unsa"):
    """Documento PIMS-PR-03 vigente (programa de auditoria) y PR-02 (plazos), si existen."""
    vigentes = {d["codigo"]: d for d in listar(proyecto) if d["vigente"]}
    return {c: ("%s v%s" % (c, vigentes[c]["version"])) if c in vigentes else None
            for c in ("PIMS-PR-01", "PIMS-PR-02", "PIMS-PR-03", "PIMS-PR-04", "PIMS-RG-01")}
