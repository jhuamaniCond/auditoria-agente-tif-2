# -*- coding: utf-8 -*-
"""
Automatizacion del Agente de Evidencia (clausula 9.1, seguimiento continuo).

    vigilar(intervalo=10)        hilo daemon: archivo nuevo en datos/bandeja_entrada
                                 -> orquestador.iniciar("bandeja")
    verificar_periodica(horas=24) hilo daemon: herramientas.verificar_integridad y, si algo
                                 se altero, evento 'integridad.alterada' en el bus
    iniciar_automatizacion()     arranca ambos y suscribe el agente al bus (idempotente)
    estado_automatizacion()      para el panel web
"""

import datetime as dt
import os
import threading
import time

import nucleo
import coordinacion
import herramientas
import orquestador

IGNORAR = orquestador.IGNORAR
_CANDADO = threading.Lock()
_PARAR = threading.Event()
_HILOS = {}
_ESTADO = {"vigilancia": None, "verificacion": None}


def _ahora():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def archivos_nuevos(estable=2.0):
    """Archivos de primer nivel de la bandeja que ya no se estan copiando."""
    salida = []
    for n in sorted(os.listdir(nucleo.BANDEJA)):
        ruta = os.path.join(nucleo.BANDEJA, n)
        if (not os.path.isfile(ruta) or n.startswith((".", "~$"))
                or n.lower().endswith(IGNORAR)):
            continue
        try:
            if time.time() - os.path.getmtime(ruta) < estable:
                continue
        except OSError:
            continue
        salida.append(n)
    return salida


def revisar_bandeja(proyecto="unsa", parametros=None, _lanzados=None):
    """Una pasada: si hay archivos nuevos lanza una ejecucion 'bandeja'. Devuelve la ejecucion
    o None. El primer nodo del grafo mueve los archivos a en_proceso/ (no se duplican)."""
    lanzados = _lanzados if _lanzados is not None else {}
    ahora = time.time()
    nuevos = [n for n in archivos_nuevos() if ahora - lanzados.get(n, 0) > 120]
    if not nuevos:
        return None
    for n in nuevos:
        lanzados[n] = ahora
    par = dict(parametros or {}, archivos=nuevos, solicitado_por="automatizacion-bandeja")
    return orquestador.iniciar("bandeja", proyecto, par)


def vigilar(intervalo=10, proyecto="unsa", parametros=None):
    """Arranca el hilo daemon que vigila la bandeja. Devuelve el hilo."""
    with _CANDADO:
        if _HILOS.get("vigilancia") and _HILOS["vigilancia"].is_alive():
            return _HILOS["vigilancia"]
        lanzados = {}

        def bucle():
            while not _PARAR.is_set():
                try:
                    ej = revisar_bandeja(proyecto, parametros, lanzados)
                    _ESTADO["vigilancia"] = {"ultima_revision": _ahora(), "intervalo": intervalo,
                                             "proyecto": proyecto,
                                             "ultima_ejecucion": ej["id"] if ej else
                                             (_ESTADO["vigilancia"] or {}).get("ultima_ejecucion")}
                except Exception as e:      # noqa: BLE001
                    _ESTADO["vigilancia"] = {"ultima_revision": _ahora(), "error": str(e)}
                _PARAR.wait(intervalo)

        hilo = threading.Thread(target=bucle, name="vigilar-bandeja", daemon=True)
        _HILOS["vigilancia"] = hilo
        hilo.start()
        return hilo


def verificar_ahora(proyecto="unsa"):
    """Verificacion de integridad programada; publica alerta si algo se altero."""
    r = herramientas.verificar_integridad(proyecto, responsable="automatizacion-integridad")
    resumen = {"fecha": _ahora(), "proyecto": proyecto, "integro": r["integro"],
               "total": r["total"], "alteradas": r["resultados"]["ALTERADA"],
               "faltantes": r["resultados"]["FALTANTE"], "problemas_cadena": r["problemas_cadena"]}
    orquestador.registrar_decision(None, "verificacion_periodica",
                                   "integro" if r["integro"] else "integridad fallida",
                                   actor="automatizacion-integridad", proyecto=proyecto,
                                   detalle=resumen)
    if not r["integro"]:
        resumen["evento"] = coordinacion.publicar(dict(
            resumen, tipo="integridad.alterada", origen="automatizacion-integridad",
            nivel="critica"))["id"]
    _ESTADO["verificacion"] = resumen
    return resumen


def verificar_periodica(horas=24, proyecto="unsa", inmediata=True):
    """Arranca el hilo daemon de verificacion de integridad cada `horas`."""
    with _CANDADO:
        if _HILOS.get("verificacion") and _HILOS["verificacion"].is_alive():
            return _HILOS["verificacion"]

        def bucle():
            if not inmediata and _PARAR.wait(horas * 3600):
                return
            while not _PARAR.is_set():
                try:
                    verificar_ahora(proyecto)
                except Exception as e:      # noqa: BLE001
                    _ESTADO["verificacion"] = {"fecha": _ahora(), "error": str(e)}
                if _PARAR.wait(horas * 3600):
                    return

        hilo = threading.Thread(target=bucle, name="verificar-integridad", daemon=True)
        _HILOS["verificacion"] = hilo
        hilo.start()
        return hilo


def iniciar_automatizacion(proyecto="unsa", intervalo=10, horas=24, parametros=None,
                           verificar_al_inicio=True):
    """Suscribe el agente al bus y arranca vigilancia + verificacion (idempotente)."""
    _PARAR.clear()
    coordinacion.registrar_agente_evidencia()
    vigilar(intervalo, proyecto, parametros)
    verificar_periodica(horas, proyecto, inmediata=verificar_al_inicio)
    return estado_automatizacion()


def detener():
    """Para los hilos (pruebas)."""
    _PARAR.set()
    for h in list(_HILOS.values()):
        h.join(timeout=5)
    _HILOS.clear()


def estado_automatizacion():
    return {"vigilancia_activa": bool(_HILOS.get("vigilancia") and _HILOS["vigilancia"].is_alive()),
            "verificacion_activa": bool(_HILOS.get("verificacion")
                                        and _HILOS["verificacion"].is_alive()),
            "bandeja": nucleo.BANDEJA, "pendientes": archivos_nuevos(estable=0),
            "suscripciones": coordinacion.suscripciones(), **_ESTADO}
