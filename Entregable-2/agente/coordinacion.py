# -*- coding: utf-8 -*-
"""
Capa de coordinacion entre agentes del PIMS: bus de eventos simple.

    import coordinacion
    coordinacion.suscribir("incidente.detectado", mi_callback)
    coordinacion.publicar({"tipo": "incidente.detectado", "origen": "agente-incidentes", ...})

Cada evento se guarda (con las entregas a sus suscriptores) en
datos/eventos.jsonl. El Agente de Evidencia y Auditoria se suscribe con
registrar_agente_evidencia() a:

    incidente.detectado   -> orquestador.iniciar("incidente", ...)
    auditoria.solicitada  -> orquestador.iniciar("auditoria_interna", ...)
    evidencia.nueva       -> copia el archivo a la bandeja y orquestador.iniciar("bandeja", ...)

El propio agente publica: aprobacion.requerida, integridad.alterada,
auditoria.completada, incidente.documentado, evidencia.registrada.

simular_agente_incidentes() hace de Agente de Incidentes y Brechas para la demo.
"""

import datetime as dt
import json
import os
import random
import shutil
import string
import threading
from collections import defaultdict

import nucleo

EVENTOS = os.path.join(nucleo.DATOS, "eventos.jsonl")
AGENTE_EVIDENCIA = "agente-evidencia"

_SUSCRIPTORES = defaultdict(list)       # tipo -> [(nombre, callback)]
_CANDADO = threading.RLock()


def _ahora():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def _id():
    return "EVT-%s-%s" % (dt.datetime.now().strftime("%Y%m%d-%H%M%S"),
                          "".join(random.choices(string.ascii_lowercase + string.digits, k=4)))


def suscribir(tipo, callback, nombre=None):
    """Suscribe callback(evento) a un tipo de evento ('*' = todos). Idempotente por nombre."""
    nombre = nombre or getattr(callback, "__qualname__", repr(callback))
    with _CANDADO:
        lista = _SUSCRIPTORES[tipo]
        lista[:] = [(n, cb) for n, cb in lista if n != nombre]
        lista.append((nombre, callback))
    return nombre


def desuscribir(tipo, nombre):
    with _CANDADO:
        _SUSCRIPTORES[tipo] = [(n, cb) for n, cb in _SUSCRIPTORES[tipo] if n != nombre]


def suscripciones():
    with _CANDADO:
        return {t: [n for n, _ in l] for t, l in _SUSCRIPTORES.items() if l}


def publicar(evento):
    """Publica un evento (dict con 'tipo'), lo entrega a los suscriptores y lo guarda.

    Devuelve el evento con id, fecha y 'entregas' [{suscriptor, resultado | error}]."""
    if not isinstance(evento, dict) or not evento.get("tipo"):
        raise ValueError("El evento debe ser un dict con 'tipo'")
    evento = json.loads(json.dumps(evento, default=str))
    evento.setdefault("id", _id())
    evento.setdefault("fecha", _ahora())
    evento.setdefault("origen", "desconocido")
    with _CANDADO:
        destinos = list(_SUSCRIPTORES.get(evento["tipo"], [])) + list(_SUSCRIPTORES.get("*", []))
    entregas = []
    for nombre, cb in destinos:
        try:
            entregas.append({"suscriptor": nombre, "resultado": cb(json.loads(json.dumps(evento)))})
        except Exception as e:              # noqa: BLE001
            entregas.append({"suscriptor": nombre, "error": "%s: %s" % (type(e).__name__, e)})
    evento["entregas"] = json.loads(json.dumps(entregas, default=str))
    with _CANDADO:
        with open(EVENTOS, "a", encoding="utf-8") as f:
            f.write(json.dumps(evento, ensure_ascii=False) + "\n")
    return evento


def leer_eventos(n=50, tipo=None):
    """Ultimos n eventos (mas recientes primero)."""
    if not os.path.exists(EVENTOS):
        return []
    with open(EVENTOS, encoding="utf-8") as f:
        eventos = [json.loads(x) for x in f if x.strip()]
    if tipo:
        eventos = [e for e in eventos if e.get("tipo") == tipo]
    return list(reversed(eventos[-n:]))


# ------------------------------------------------------------ Agente de Evidencia
def _al_incidente(evento):
    import orquestador
    par = dict(evento.get("parametros") or {})
    par["evento"] = {k: v for k, v in evento.items() if k != "parametros"}
    par.setdefault("solicitado_por", evento.get("origen"))
    ej = orquestador.iniciar("incidente", evento.get("proyecto") or "unsa", par)
    return {"ejecucion": ej["id"]}


def _al_auditoria(evento):
    import orquestador
    par = dict(evento.get("parametros") or {})
    par.setdefault("solicitado_por", evento.get("origen"))
    ej = orquestador.iniciar("auditoria_interna", evento.get("proyecto") or "unsa", par)
    return {"ejecucion": ej["id"]}


def _al_evidencia(evento):
    import orquestador
    par = dict(evento.get("parametros") or {})
    ruta = evento.get("ruta")
    if ruta:
        if not os.path.isfile(ruta):
            raise ValueError("No existe el archivo %s" % ruta)
        destino = os.path.join(nucleo.BANDEJA, os.path.basename(ruta))
        if os.path.abspath(ruta) != os.path.abspath(destino):
            shutil.copy2(ruta, destino)
        par["archivos"] = [os.path.basename(ruta)]
    par.setdefault("solicitado_por", evento.get("origen"))
    ej = orquestador.iniciar("bandeja", evento.get("proyecto") or "unsa", par)
    return {"ejecucion": ej["id"]}


def registrar_agente_evidencia():
    """Suscribe el Agente de Evidencia y Auditoria a sus eventos (idempotente)."""
    suscribir("incidente.detectado", _al_incidente, AGENTE_EVIDENCIA)
    suscribir("auditoria.solicitada", _al_auditoria, AGENTE_EVIDENCIA)
    suscribir("evidencia.nueva", _al_evidencia, AGENTE_EVIDENCIA)
    return suscripciones()


DESCRIPCION_DEMO = (
    "El SIEM detecto entre las 01:12 y las 02:47 consultas masivas al banco de datos personales "
    "'Estudiantes' (Sistema Academico: matricula y notas) desde una IP externa, usando la cuenta "
    "de servicio del portal de matricula. Se exportaron aproximadamente 1 200 registros con "
    "nombres, DNI, codigo universitario, correo institucional, telefono y notas. La cuenta fue "
    "bloqueada a las 03:05 por el equipo de TI.")


def simular_agente_incidentes(descripcion=None, proyecto="unsa", parametros=None,
                              severidad="alta"):
    """Hace de Agente de Incidentes y Brechas: publica un 'incidente.detectado' realista."""
    registrar_agente_evidencia()
    ahora = dt.datetime.now().astimezone()
    evento = {
        "tipo": "incidente.detectado",
        "origen": "agente-incidentes-brechas",
        "proyecto": proyecto,
        "parametros": dict(parametros or {}),
        "incidente": {
            "id": "INC-UNSA-%s" % ahora.strftime("%Y%m%d-%H%M%S"),
            "titulo": "Acceso no autorizado al banco de datos personales 'Estudiantes'",
            "descripcion": descripcion or DESCRIPCION_DEMO,
            "severidad": severidad,
            "categoria": "confidencialidad (brecha de datos personales)",
            "banco_datos": "Estudiantes (Sistema Academico - matricula y notas)",
            "categorias_pii": ["nombres y apellidos", "DNI", "codigo universitario",
                               "correo institucional", "telefono", "notas"],
            "titulares_afectados_estimados": 1200,
            "deteccion": {
                "fecha": ahora.isoformat(timespec="seconds"),
                "fuente": "SIEM (Wazuh): regla de consultas masivas fuera de horario",
                "indicadores": ["IP de origen 203.0.113.45 (externa)",
                                "cuenta de servicio svc-portal-matricula",
                                "1 200 filas exportadas de la tabla estudiantes"]},
            "acciones_inmediatas": ["Bloqueo de la cuenta de servicio comprometida",
                                    "Rotacion de credenciales del portal de matricula",
                                    "Preservacion de los logs de acceso (A.3.14)"],
            "requiere_notificacion": True,
            "plazo_notificacion_horas": 48,
            "base_legal": "Ley N.o 29733 de Proteccion de Datos Personales y su Reglamento "
                          "(D.S. N.o 016-2024-JUS)",
        },
    }
    return publicar(evento)
