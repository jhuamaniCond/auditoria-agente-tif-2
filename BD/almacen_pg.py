# -*- coding: utf-8 -*-
"""
Almacen PostgreSQL del Agente de Evidencia y Auditoria.

Sustituye a los archivos con los que trabajaba el agente:

    registro_evidencias.json      -> evidencias + evidencia_requisito
    cadena_custodia.log           -> cadena_custodia
    soa.csv                       -> soa_evaluaciones (aplicable = false)
    revisiones_pertinencia.json   -> revisiones_pertinencia
    proyecto.json                 -> proyectos
    eventos.jsonl                 -> eventos_agentes
    bitacora_decisiones.jsonl     -> decisiones_humanas
    bitacora_mcp.jsonl            -> bitacora_mcp
    ejecuciones/*.json            -> ejecuciones (+ auditorias/hallazgos/acciones al completarse)
    ejecuciones/_estado/*.json    -> ejecucion_instantaneas

Todas las funciones reciben y devuelven los mismos diccionarios que antes se
guardaban en JSON, para que el codigo del agente no cambie de forma. Los
archivos de evidencia (PDF, TXT...) siguen en disco: la BD guarda ruta y SHA-256.

Se activa desde Entregable-2/agente/nucleo.py (PIMS_BACKEND=postgres, por defecto).
"""

import datetime as dt
import hashlib
import json
import os
import threading
import weakref

from psycopg.types.json import Jsonb

from db import conectar, dsn

GENESIS = "0" * 64

CLASIFICACION = {  # agente -> estados de GESTITEL
    "no conformidad mayor": "No conformidad",
    "no conformidad menor": "No conformidad",
    "no conformidad": "No conformidad",
    "observacion": "Observación",
    "observación": "Observación",
    "oportunidad de mejora": "Oportunidad de mejora",
}


def _iso(valor):
    """timestamptz/date de la BD -> texto ISO como el que escribia el agente."""
    if valor is None:
        return None
    if isinstance(valor, dt.datetime):
        return valor.astimezone().isoformat(timespec="seconds")
    return valor.isoformat()


def _json(valor):
    """Normaliza a tipos JSON (fechas a texto) antes de guardar en JSONB."""
    return json.loads(json.dumps(valor, ensure_ascii=False, default=str))


def proyecto_de(expediente):
    """datos/proyectos/<id>/expediente -> <id>."""
    return os.path.basename(os.path.dirname(os.path.abspath(expediente)))


class AlmacenPG(object):
    """Una conexion por hilo, en autocommit; las escrituras compuestas usan transaccion."""

    nombre = "PostgreSQL"

    def __init__(self):
        self._local = threading.local()
        with self._cx() as cur:          # falla pronto si la BD no esta disponible
            cur.execute("SELECT count(*) AS n FROM requisitos")
            if not cur.fetchone()["n"]:
                raise RuntimeError("El catalogo de la BD esta vacio: ejecute BD/cargar_catalogo.py")

    # ------------------------------------------------------------------ conexion
    def conexion(self):
        cx = getattr(self._local, "cx", None)
        if cx is None or cx.closed:
            cx = conectar()
            cx.autocommit = True
            self._local.cx = cx
            # El orquestador abre hilos: la conexion se cierra cuando termina el suyo
            weakref.finalize(threading.current_thread(), cx.close)
        return cx

    def _cx(self):
        return self.conexion().cursor()

    def descripcion(self):
        partes = dict(p.split("=", 1) for p in dsn().split() if "=" in p)
        return "PostgreSQL %s:%s/%s" % (partes.get("host", "?"), partes.get("port", "?"),
                                        partes.get("dbname", "?"))

    # ================================================================ PROYECTOS
    def leer_proyecto(self, id_):
        with self._cx() as cur:
            cur.execute("SELECT id, nombre, rol, descripcion, creado FROM proyectos WHERE id = %s", (id_,))
            r = cur.fetchone()
        return dict(r, creado=_iso(r["creado"])) if r else None

    def listar_proyectos(self):
        with self._cx() as cur:
            cur.execute("SELECT id FROM proyectos ORDER BY id")
            return [r["id"] for r in cur.fetchall()]

    def crear_proyecto(self, datos, excluidos=()):
        cx = self.conexion()
        with cx.transaction(), cx.cursor() as cur:
            cur.execute("""INSERT INTO proyectos (id, nombre, rol, descripcion, creado)
                           VALUES (%(id)s, %(nombre)s, %(rol)s, %(descripcion)s, %(creado)s)""", datos)
            for e in excluidos:
                cur.execute("""INSERT INTO soa_evaluaciones (proyecto, requisito, aplicable, justificacion, estado)
                               VALUES (%s, %s, false, %s, 'No aplica')""",
                            (datos["id"], e["ref"], e["justificacion"].strip()))

    def borrar_proyecto(self, id_):
        """Solo para pruebas: elimina el proyecto y todo lo suyo (incluida su custodia)."""
        cx = self.conexion()
        with cx.transaction(), cx.cursor() as cur:
            cur.execute("ALTER TABLE cadena_custodia DISABLE TRIGGER tg_custodia_inmutable")
            cur.execute("DELETE FROM cadena_custodia WHERE proyecto = %s", (id_,))
            cur.execute("ALTER TABLE cadena_custodia ENABLE TRIGGER tg_custodia_inmutable")
            cur.execute("SELECT id FROM ejecuciones WHERE proyecto = %s", (id_,))
            ejecuciones = [r["id"] for r in cur.fetchall()]
            cur.execute("DELETE FROM ejecucion_instantaneas WHERE ejecucion = ANY(%s)", (ejecuciones,))
            # Estado de LangGraph (tablas de PostgresSaver, si ya se crearon)
            for tabla in ("checkpoint_writes", "checkpoint_blobs", "checkpoints"):
                cur.execute("SELECT to_regclass(%s) AS t", (tabla,))
                if cur.fetchone()["t"]:
                    cur.execute("DELETE FROM %s WHERE thread_id = ANY(%%s)" % tabla, (ejecuciones,))
            cur.execute("DELETE FROM decisiones_humanas WHERE proyecto = %s", (id_,))
            cur.execute("DELETE FROM eventos_agentes WHERE proyecto = %s", (id_,))
            cur.execute("DELETE FROM proyectos WHERE id = %s", (id_,))

    # =============================================================== EXPEDIENTE
    def leer_indice(self, expediente):
        pid = proyecto_de(expediente)
        with self._cx() as cur:
            cur.execute(
                """SELECT e.id AS pk, e.codigo, e.tipo, e.titulo, e.ruta_archivo, e.sha256, e.tamano_bytes,
                          e.fecha_documento, e.fecha_registro, e.responsable, e.fuente,
                          COALESCE(array_agg(er.requisito ORDER BY er.orden)
                                   FILTER (WHERE er.requisito IS NOT NULL), '{}') AS controles
                   FROM evidencias e LEFT JOIN evidencia_requisito er ON er.evidencia_id = e.id
                   WHERE e.proyecto = %s
                   GROUP BY e.id ORDER BY e.codigo""", (pid,))
            filas = cur.fetchall()
        return {"norma": "ISO/IEC 27701:2025", "evidencias": [{
            "id": f["codigo"], "controles": list(f["controles"]), "tipo": f["tipo"], "titulo": f["titulo"],
            "archivo": f["ruta_archivo"], "sha256": f["sha256"], "tamano_bytes": f["tamano_bytes"],
            "fecha_documento": _iso(f["fecha_documento"]), "fecha_registro": _iso(f["fecha_registro"]),
            "responsable": f["responsable"], "fuente": f["fuente"] or ""} for f in filas]}

    def guardar_indice(self, expediente, indice):
        """Inserta o actualiza cada evidencia del indice (no borra las que no vengan)."""
        pid = proyecto_de(expediente)
        cx = self.conexion()
        with cx.transaction(), cx.cursor() as cur:
            for ev in indice["evidencias"]:
                cur.execute(
                    """INSERT INTO evidencias (proyecto, codigo, tipo, titulo, ruta_archivo, sha256, tamano_bytes,
                                               fecha_documento, fecha_registro, responsable, fuente)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (proyecto, codigo) DO UPDATE SET
                         tipo = EXCLUDED.tipo, titulo = EXCLUDED.titulo, ruta_archivo = EXCLUDED.ruta_archivo,
                         sha256 = EXCLUDED.sha256, tamano_bytes = EXCLUDED.tamano_bytes,
                         fecha_documento = EXCLUDED.fecha_documento, responsable = EXCLUDED.responsable,
                         fuente = EXCLUDED.fuente
                       RETURNING id""",
                    (pid, ev["id"], ev["tipo"], ev["titulo"], ev["archivo"], ev["sha256"],
                     ev.get("tamano_bytes"), ev.get("fecha_documento"), ev["fecha_registro"],
                     ev["responsable"], ev.get("fuente") or None))
                pk = cur.fetchone()["id"]
                cur.execute("DELETE FROM evidencia_requisito WHERE evidencia_id = %s", (pk,))
                for orden, ref in enumerate(ev.get("controles", [])):
                    cur.execute("INSERT INTO evidencia_requisito VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                                (pk, ref, orden))

    def leer_cadena(self, expediente):
        with self._cx() as cur:
            cur.execute("""SELECT contenido, hash_anterior, hash_linea FROM cadena_custodia
                           WHERE proyecto = %s ORDER BY n""", (proyecto_de(expediente),))
            return [dict(r["contenido"], hash_anterior=r["hash_anterior"], hash_linea=r["hash_linea"])
                    for r in cur.fetchall()]

    def agregar_custodia(self, expediente, linea):
        pid = proyecto_de(expediente)
        contenido = {k: v for k, v in linea.items() if k not in ("hash_anterior", "hash_linea")}
        with self._cx() as cur:
            cur.execute(
                """INSERT INTO cadena_custodia (proyecto, n, fecha, accion, responsable, evidencia_id,
                                                contenido, hash_anterior, hash_linea)
                   VALUES (%s, %s, %s, %s, %s,
                           (SELECT id FROM evidencias WHERE proyecto = %s AND codigo = %s),
                           %s, %s, %s)""",
                (pid, linea["n"], linea["fecha"], linea["accion"], linea["responsable"],
                 pid, linea.get("evidencia"), Jsonb(_json(contenido)),
                 linea["hash_anterior"], linea["hash_linea"]))

    def leer_soa(self, expediente):
        with self._cx() as cur:
            cur.execute("""SELECT requisito, aplicable, justificacion FROM soa_evaluaciones
                           WHERE proyecto = %s""", (proyecto_de(expediente),))
            return {r["requisito"]: (r["aplicable"], r["justificacion"] or "") for r in cur.fetchall()}

    # ============================================================== REVISIONES
    def leer_revisiones(self, expediente):
        with self._cx() as cur:
            cur.execute("SELECT requisito, datos FROM revisiones_pertinencia WHERE proyecto = %s",
                        (proyecto_de(expediente),))
            return {r["requisito"]: r["datos"] for r in cur.fetchall()}

    def guardar_revision(self, expediente, ref, rev, cur=None):
        sql = """INSERT INTO revisiones_pertinencia (proyecto, requisito, veredicto, justificacion, falta,
                                                     huellas, modelo, decision, auditor, fecha_ia,
                                                     fecha_decision, datos)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                 ON CONFLICT (proyecto, requisito) DO UPDATE SET
                   veredicto = EXCLUDED.veredicto, justificacion = EXCLUDED.justificacion,
                   falta = EXCLUDED.falta, huellas = EXCLUDED.huellas, modelo = EXCLUDED.modelo,
                   decision = EXCLUDED.decision, auditor = EXCLUDED.auditor, fecha_ia = EXCLUDED.fecha_ia,
                   fecha_decision = EXCLUDED.fecha_decision, datos = EXCLUDED.datos"""
        args = (proyecto_de(expediente), ref, rev["veredicto"], rev.get("justificacion"), rev.get("falta"),
                Jsonb(_json(rev.get("huellas") or {})), rev.get("modelo"), rev.get("decision"),
                rev.get("auditor"), rev.get("fecha_ia"), rev.get("fecha_decision"), Jsonb(_json(rev)))
        if cur is not None:
            cur.execute(sql, args)
        else:
            with self._cx() as c:
                c.execute(sql, args)

    def guardar_revisiones(self, expediente, revisiones):
        cx = self.conexion()
        with cx.transaction(), cx.cursor() as cur:
            for ref, rev in revisiones.items():
                self.guardar_revision(expediente, ref, rev, cur)

    # ================================================================== EVENTOS
    _FIJOS_EVENTO = ("id", "fecha", "tipo", "origen", "proyecto", "ejecucion", "entregas")

    def guardar_evento(self, ev):
        with self._cx() as cur:
            cur.execute(
                """INSERT INTO eventos_agentes (id, fecha, tipo, origen, proyecto, ejecucion, payload, entregas)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING""",
                (ev["id"], ev["fecha"], ev["tipo"], ev.get("origen") or "desconocido", ev.get("proyecto"),
                 ev.get("ejecucion"),
                 Jsonb(_json({k: v for k, v in ev.items() if k not in self._FIJOS_EVENTO})),
                 Jsonb(_json(ev.get("entregas") or []))))

    def leer_eventos(self, n=50, tipo=None):
        """Ultimos n eventos, mas recientes primero."""
        with self._cx() as cur:
            cur.execute("""SELECT * FROM eventos_agentes WHERE (%(t)s::text IS NULL OR tipo = %(t)s)
                           ORDER BY fecha DESC, id DESC LIMIT %(n)s""", {"t": tipo, "n": n})
            salida = []
            for r in cur.fetchall():
                ev = dict(r["payload"])
                ev.update({"id": r["id"], "fecha": _iso(r["fecha"]), "tipo": r["tipo"], "origen": r["origen"],
                           "entregas": r["entregas"]})
                for k in ("proyecto", "ejecucion"):
                    if r[k] is not None:
                        ev[k] = r[k]
                salida.append(ev)
            return salida

    # ========================================================= DECISIONES (HITL)
    def guardar_decision(self, linea):
        with self._cx() as cur:
            cur.execute(
                """INSERT INTO decisiones_humanas (fecha, ejecucion, flujo, proyecto, nodo, actor, origen,
                                                   decision, detalle)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (linea["fecha"], linea.get("ejecucion"), linea.get("flujo"), linea.get("proyecto"),
                 linea.get("nodo"), linea.get("actor") or "desconocido", linea.get("origen"),
                 str(linea.get("decision")), Jsonb(_json(linea.get("detalle") or {}))))

    def leer_decisiones(self, ejecucion=None, n=500):
        """Ultimas n decisiones en orden cronologico (como la bitacora JSONL)."""
        with self._cx() as cur:
            cur.execute("""SELECT * FROM (
                             SELECT * FROM decisiones_humanas
                             WHERE (%(e)s::text IS NULL OR ejecucion = %(e)s)
                             ORDER BY id DESC LIMIT %(n)s) t ORDER BY id""", {"e": ejecucion, "n": n})
            return [{"fecha": _iso(r["fecha"]), "ejecucion": r["ejecucion"], "flujo": r["flujo"],
                     "proyecto": r["proyecto"], "nodo": r["nodo"], "actor": r["actor"], "origen": r["origen"],
                     "decision": r["decision"], "detalle": r["detalle"]} for r in cur.fetchall()]

    # ============================================================ BITACORA MCP
    @staticmethod
    def _hash_mcp(contenido, anterior):
        datos = json.dumps(contenido, ensure_ascii=False, sort_keys=True) + anterior
        return hashlib.sha256(datos.encode("utf-8")).hexdigest()

    def anotar_mcp(self, entrada):
        """Anade una entrada encadenada por SHA-256; un bloqueo de BD evita carreras entre procesos."""
        cx = self.conexion()
        with cx.transaction(), cx.cursor() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(hashtext('bitacora_mcp'))")
            cur.execute("SELECT n, hash FROM bitacora_mcp ORDER BY n DESC LIMIT 1")
            ultima = cur.fetchone()
            n, anterior = (ultima["n"], ultima["hash"]) if ultima else (0, GENESIS)
            contenido = _json(dict(n=n + 1, **entrada))
            h = self._hash_mcp(contenido, anterior)
            cur.execute(
                """INSERT INTO bitacora_mcp (n, fecha, tool, argumentos, transporte, pid, resultado,
                                             duracion_ms, contenido, hash_anterior, hash)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (contenido["n"], contenido.get("fecha"), contenido.get("tool"),
                 Jsonb(contenido.get("argumentos") or {}), contenido.get("transporte"), contenido.get("pid"),
                 str(contenido.get("resultado")), contenido.get("duracion_ms"), Jsonb(contenido),
                 anterior, h))
        return dict(contenido, hash_anterior=anterior, hash=h)

    def leer_mcp(self, n=None):
        """Entradas en orden (todas, o las ultimas n)."""
        with self._cx() as cur:
            if n:
                cur.execute("""SELECT * FROM (SELECT contenido, hash_anterior, hash, n FROM bitacora_mcp
                               ORDER BY n DESC LIMIT %s) t ORDER BY n""", (n,))
            else:
                cur.execute("SELECT contenido, hash_anterior, hash FROM bitacora_mcp ORDER BY n")
            return [dict(r["contenido"], hash_anterior=r["hash_anterior"], hash=r["hash"])
                    for r in cur.fetchall()]

    def verificar_mcp(self):
        problemas, anterior, total = [], GENESIS, 0
        for d in self.leer_mcp():
            total += 1
            contenido = {k: v for k, v in d.items() if k not in ("hash_anterior", "hash")}
            if d["hash_anterior"] != anterior:
                problemas.append("entrada %s: no enlaza con la anterior" % d.get("n"))
            if self._hash_mcp(contenido, d["hash_anterior"]) != d["hash"]:
                problemas.append("entrada %s: contenido modificado" % d.get("n"))
            anterior = d["hash"]
        return {"entradas": total, "problemas": problemas, "integra": not problemas}

    # ============================================================= EJECUCIONES
    def guardar_ejecucion(self, ej):
        datos = _json(ej)
        cx = self.conexion()
        with cx.transaction(), cx.cursor() as cur:
            cur.execute(
                """INSERT INTO ejecuciones (id, tipo, proyecto, estado, creado, actualizado, datos)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (id) DO UPDATE SET estado = EXCLUDED.estado,
                     actualizado = EXCLUDED.actualizado, datos = EXCLUDED.datos""",
                (datos["id"], datos.get("tipo"), datos.get("proyecto"), datos.get("estado"),
                 datos.get("creado"), datos.get("actualizado") or datos.get("creado"), Jsonb(datos)))
            if datos.get("tipo") == "auditoria_interna" and datos.get("estado") == "completada":
                self.volcar_auditoria(cur, datos)

    def obtener_ejecucion(self, id_):
        with self._cx() as cur:
            cur.execute("SELECT datos FROM ejecuciones WHERE id = %s", (id_,))
            r = cur.fetchone()
        return r["datos"] if r else None

    def listar_ejecuciones(self, proyecto=None):
        with self._cx() as cur:
            cur.execute("""SELECT datos FROM ejecuciones WHERE (%(p)s::text IS NULL OR proyecto = %(p)s)
                           ORDER BY creado DESC, id DESC""", {"p": proyecto})
            return [r["datos"] for r in cur.fetchall()]

    def guardar_instantanea(self, estado):
        with self._cx() as cur:
            cur.execute("""INSERT INTO ejecucion_instantaneas (ejecucion, estado) VALUES (%s, %s)
                           ON CONFLICT (ejecucion) DO UPDATE SET estado = EXCLUDED.estado, guardado = now()""",
                        (estado["ejecucion"], Jsonb(_json(estado))))

    def leer_instantanea(self, id_):
        with self._cx() as cur:
            cur.execute("SELECT estado FROM ejecucion_instantaneas WHERE ejecucion = %s", (id_,))
            r = cur.fetchone()
        return r["estado"] if r else None

    # ================================================= AUDITORIAS (D33 / D34)
    def volcar_auditoria(self, cur, ej):
        """Ejecucion 'auditoria_interna' completada -> auditorias, checklist, hallazgos y acciones
        (modelo del modulo Auditorias de GESTITEL). Idempotente: rehace la auditoria."""
        pid = ej["proyecto"]
        res = ej.get("resultado") or {}
        plan = res.get("plan") or {}
        aprob = res.get("aprobacion") or {}
        cur.execute("SELECT codigo FROM requisitos")
        catalogo = {r["codigo"] for r in cur.fetchall()}
        cur.execute("DELETE FROM auditorias WHERE codigo = %s", (ej["id"],))
        cur.execute(
            """INSERT INTO auditorias (proyecto, codigo, tipo, nombre, alcance, objetivo, fecha_inicio,
                                       fecha_fin, lider, equipo_auditor, areas, estado,
                                       ejecucion_agente, informe_ruta, creado)
               VALUES (%s, %s, 'Interna', %s, %s, %s, %s::timestamptz::date, %s::timestamptz::date,
                       %s, %s, %s, 'Cerrada', %s, %s, %s) RETURNING id""",
            (pid, ej["id"], "Auditoría interna PIMS - %s" % plan.get("organizacion", pid),
             plan.get("alcance"), plan.get("objetivo"), ej["creado"], ej.get("actualizado") or ej["creado"],
             aprob.get("auditor"), ["agente-evidencia"] + ([aprob["auditor"]] if aprob.get("auditor") else []),
             [], ej["id"], os.path.basename(res["informe"]) if res.get("informe") else None, ej["creado"]))
        aud_id = cur.fetchone()["id"]
        acciones = {a["ref"]: a for a in res.get("plan_accion") or []}
        n = 0
        for h in (ej.get("aprobacion") or {}).get("hallazgos") or []:
            ref = h["ref"] if h.get("ref") in catalogo else None
            cur.execute(
                """INSERT INTO checklist_items (auditoria_id, requisito, requisito_origen, norma,
                                                evidencia_textual, resultado)
                   VALUES (%s, %s, 'Matriz de cobertura del agente', 'ISO/IEC 27701:2025', %s, %s) RETURNING id""",
                (aud_id, ref, h.get("estado"), h.get("estado")))
            item = cur.fetchone()["id"]
            cur.execute(
                """INSERT INTO hallazgos (auditoria_id, checklist_item_id, requisito, clasificacion,
                                          descripcion, evidencia_texto, origen)
                   VALUES (%s, %s, %s, %s, %s, %s, 'agente') RETURNING id""",
                (aud_id, item, ref, CLASIFICACION.get(str(h.get("clasificacion", "")).lower(), "Observación"),
                 h.get("texto") or "", "Estado de cobertura: %s (%s)" % (h.get("estado"), h.get("clasificacion"))))
            hal = cur.fetchone()["id"]
            n += 1
            if ref:
                cur.execute("""INSERT INTO hallazgo_evidencia
                               SELECT %s, er.evidencia_id FROM evidencia_requisito er
                               JOIN evidencias e ON e.id = er.evidencia_id
                               WHERE e.proyecto = %s AND er.requisito = %s ON CONFLICT DO NOTHING""",
                            (hal, pid, ref))
            a = acciones.get(h.get("ref"))
            if a:
                cur.execute("""INSERT INTO acciones (hallazgo_id, descripcion, responsable, fecha_compromiso)
                               VALUES (%s, %s, %s, %s)""",
                            (hal, a.get("accion") or "", a.get("responsable"), a.get("fecha_limite")))
        return aud_id, n

    # ======================================================== EXPORTACION
    def filas_export_auditorias(self, codigo=None, proyecto=None):
        """Filas de v_export_auditorias_gestitel (columnas del Excel de GESTITEL)."""
        with self._cx() as cur:
            cur.execute("""SELECT v.* FROM v_export_auditorias_gestitel v
                           JOIN auditorias a ON a.codigo = v."Código de auditoría"
                           WHERE (%(c)s::text IS NULL OR a.codigo = %(c)s)
                             AND (%(p)s::text IS NULL OR a.proyecto = %(p)s)
                           ORDER BY a.creado, v."Requisito (checklist)" """, {"c": codigo, "p": proyecto})
            return [dict(r) for r in cur.fetchall()]
