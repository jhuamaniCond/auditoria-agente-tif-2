# -*- coding: utf-8 -*-
"""Conexion a PostgreSQL compartida por los scripts de BD/ y por el agente.

Variables de entorno (valores por defecto = docker-compose.yml):
  PIMS_DB_HOST=localhost  PIMS_DB_PORT=5432  PIMS_DB_NAME=pims_auditoria
  PIMS_DB_USER=agente     PIMS_DB_PASSWORD=agente_local
o bien una sola PIMS_DATABASE_URL=postgresql://usuario:clave@host:puerto/base
"""

import os
import time

import psycopg
from psycopg.rows import dict_row


def dsn():
    url = os.environ.get("PIMS_DATABASE_URL")
    if url:
        return url
    return (
        f"host={os.environ.get('PIMS_DB_HOST', 'localhost')} "
        f"port={os.environ.get('PIMS_DB_PORT', '5432')} "
        f"dbname={os.environ.get('PIMS_DB_NAME', 'pims_auditoria')} "
        f"user={os.environ.get('PIMS_DB_USER', 'agente')} "
        f"password={os.environ.get('PIMS_DB_PASSWORD', 'agente_local')}"
    )


def conectar(intentos=4):
    """Conexion con filas como diccionarios. Usar con `with conectar() as cx:`.

    Reintenta unas veces: PostgreSQL en Docker puede tardar o cerrar conexiones un momento
    mientras escribe a disco (laptop sin GPU con el LLM local cargado)."""
    for n in range(1, intentos + 1):
        try:
            return psycopg.connect(dsn(), row_factory=dict_row, connect_timeout=10)
        except psycopg.OperationalError:
            if n == intentos:
                raise
            time.sleep(0.6 * n)
