# -*- coding: utf-8 -*-
"""
Demostracion de la skill evidencia-auditoria-pims con la empresa ficticia
ClinData S.A.C. (clinica que actua como responsable del tratamiento).

1. Crea un expediente limpio y registra ocho evidencias.
2. Altera a proposito una de ellas (simula que alguien edito el acta).
3. Verifica integridad y genera la matriz de cobertura al 2026-10-01.

Toda la salida de consola queda tambien en salida/consola_demo.txt.
"""

import contextlib
import io
import os
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "..", "scripts"))
import evidencia  # noqa: E402

# Rutas relativas a la carpeta de la demo para que la salida sea legible.
ENTRADA = "evidencias_entrada"
EXPEDIENTE = "expediente"
SALIDA = "salida"
RECOLECTOR = "Agente de Evidencia (demo)"

EVIDENCIAS = [
    ("politica_privacidad_v2.md", ["5.2"], "politica",
     "Politica de privacidad v2.0", "Gestor documental", "2026-02-10"),
    ("registro_formacion_2026.csv", ["A.3.17", "7.2"], "registro",
     "Registro de formacion en privacidad 2026", "LMS Moodle", "2026-06-30"),
    ("ropa_2026.csv", ["A.1.2.2", "A.1.2.9"], "registro",
     "Registro de actividades de tratamiento 2026", "PostgreSQL processing_activities", "2026-04-01"),
    ("dpia_telemedicina.md", ["A.1.2.6"], "informe",
     "DPIA del servicio de telemedicina", "Oficial de Privacidad", "2026-05-20"),
    ("procedimiento_incidentes.md", ["A.3.11"], "procedimiento",
     "PRO-SEG-004 Gestion de incidentes y brechas", "Gestor documental", "2026-01-15"),
    ("informe_auditoria_interna_2024.md", ["9.2"], "informe",
     "Informe de auditoria interna 2024", "Archivo de auditoria", "2024-11-20"),
    ("acta_revision_direccion_2026.md", ["9.3", "5.1"], "acta",
     "Acta de revision por la direccion 01-2026", "Gerencia General", "2026-07-10"),
    ("log_accesos_pii_sept2026.csv", ["A.3.14"], "log",
     "Log seudonimizado de accesos a PII, septiembre 2026", "PostgreSQL audit_query", "2026-09-30"),
]


def correr(*argumentos):
    """Ejecuta un subcomando de evidencia.py y no corta la demo si sale con 1."""
    print("\n$ python evidencia.py " + " ".join(argumentos))
    try:
        evidencia.main(list(argumentos))
    except SystemExit as fin:
        if fin.code not in (0, None):
            print("(codigo de salida %s)" % fin.code)


def demo():
    shutil.rmtree(EXPEDIENTE, ignore_errors=True)
    os.makedirs(EXPEDIENTE)
    os.makedirs(SALIDA, exist_ok=True)
    shutil.copy("soa.csv", EXPEDIENTE)

    print("== 1. Registro de evidencias ==")
    for archivo, controles, tipo, titulo, fuente, fecha in EVIDENCIAS:
        args = ["registrar", "--expediente", EXPEDIENTE,
                "--archivo", os.path.join(ENTRADA, archivo),
                "--tipo", tipo, "--titulo", titulo, "--responsable", RECOLECTOR,
                "--fuente", fuente, "--fecha-documento", fecha]
        for c in controles:
            args += ["--control", c]
        correr(*args)

    correr("listar", "--expediente", EXPEDIENTE)

    print("\n== 2. Se altera EV-0007 (alguien edita el acta despues de archivarla) ==")
    acta = os.path.join(EXPEDIENTE, "archivos", "EV-0007_acta_revision_direccion_2026.md")
    with open(acta, "a", encoding="utf-8") as f:
        f.write("Acuerdo (4): se da por cerrada la auditoria 2026.\n")

    print("\n== 3. Verificacion de integridad ==")
    correr("verificar", "--expediente", EXPEDIENTE)

    print("\n== 4. Matriz de cobertura (rol responsable, corte 2026-10-01) ==")
    correr("cobertura", "--expediente", EXPEDIENTE, "--rol", "responsable",
           "--vigencia-dias", "365", "--fecha-corte", "2026-10-01",
           "--salida", os.path.join(SALIDA, "informe_cobertura.md"))


if __name__ == "__main__":
    os.chdir(AQUI)
    evidencia._consola_utf8()
    buffer = io.StringIO()

    class Tee(io.TextIOBase):
        def write(self, s):
            sys.__stdout__.write(s)
            buffer.write(s)
            return len(s)

    with contextlib.redirect_stdout(Tee()):
        demo()
    texto = buffer.getvalue()
    with open(os.path.join(SALIDA, "consola_demo.txt"), "w", encoding="utf-8") as f:
        f.write(texto)
