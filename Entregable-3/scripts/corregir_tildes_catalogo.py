# -*- coding: utf-8 -*-
"""
Pone las tildes que faltan en los textos del catalogo de la BD (requisitos y expedientes).

    python Entregable-3/scripts/corregir_tildes_catalogo.py

Idempotente. Si se vuelve a ejecutar BD/cargar_catalogo.py, conviene correr este script despues.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
E3 = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(E3, "agente"))
sys.path.insert(0, os.path.join(os.path.dirname(E3), "BD"))

import tildes  # noqa: E402
from db import conectar  # noqa: E402

TABLAS = {
    "requisitos": ("codigo", ["nombre", "descripcion", "evidencia_esperada", "nombre_grupo", "ley29733_explicacion"]),
    "expedientes": ("codigo", ["nombre", "fase", "accion", "responsable_propuesto", "contenido", "se_revisa_cuando"]),
}


def main():
    cambios = 0
    with conectar() as cx:
        for tabla, (clave, campos) in TABLAS.items():
            with cx.cursor() as cur:
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (tabla,))
                existentes = {r["column_name"] for r in cur.fetchall()}
                campos = [c for c in campos if c in existentes]
                cur.execute("SELECT %s, %s FROM %s" % (clave, ", ".join(campos), tabla))
                filas = cur.fetchall()
            for f in filas:
                nuevos = {c: tildes.corregir(f[c]) for c in campos if isinstance(f[c], str)}
                nuevos = {c: v for c, v in nuevos.items() if v != f[c]}
                if not nuevos:
                    continue
                with cx.cursor() as cur:
                    cur.execute("UPDATE %s SET %s WHERE %s = %%s" % (
                        tabla, ", ".join("%s = %%s" % c for c in nuevos), clave),
                        list(nuevos.values()) + [f[clave]])
                cambios += 1
        cx.commit()
    print("Filas corregidas: %d" % cambios)


if __name__ == "__main__":
    main()
