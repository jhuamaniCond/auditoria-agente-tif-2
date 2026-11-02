# -*- coding: utf-8 -*-
"""Genera el Excel de Auditorias con el formato de GESTITEL (https://unsa.27k.pe).

Copia la estructura del archivo que produce "Exportar Excel" en el modulo
Auditorias (ver datos/formato_auditorias_gestitel.xlsx): hoja "Auditorías",
cuatro lineas de cabecera, una linea en blanco, los 25 encabezados y una fila por
auditoria + item de checklist + hallazgo + accion. Ese archivo es el que se sube
con "Importar Excel" en la plataforma.

Los estados van con el codigo de una letra de GESTITEL (I, C, N, O...; tabla
gestitel_codigos). Los que aun no estan confirmados salen como texto y se avisa.

Uso:
  python exportar_gestitel.py                         # todas las auditorias del proyecto unsa
  python exportar_gestitel.py --auditoria AUD-2026-001 --salida mi.xlsx
  (--auditoria acepta el codigo GESTITEL o el id de la ejecucion del agente)
"""

import argparse
import datetime as dt
import os

import openpyxl
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDAS = os.path.join(os.path.dirname(AQUI), "Entregable-2", "datos", "salidas")

COLUMNAS = [
    "Código de auditoría", "Tipo", "Nombre", "Alcance", "Objetivo", "Fecha de inicio", "Fecha de fin",
    "Líder de auditoría", "Equipo auditor", "Áreas involucradas", "Estado", "Avance (%)",
    "Requisito de origen (checklist)", "Proceso (checklist)", "Norma (checklist)", "Requisito (checklist)",
    "Evidencia textual (checklist)", "Clasificación (hallazgo)", "Descripción (hallazgo)",
    "Evidencia (hallazgo)", "Plan de acción", "Responsable (acción)", "Fecha compromiso (acción)",
    "Estado (acción)", "Avance (acción)",
]

# Columnas que GESTITEL guarda como codigo de una letra
COLUMNAS_CODIGO = ["Tipo", "Estado", "Clasificación (hallazgo)", "Estado (acción)"]


def sin_codigo(filas):
    """Valores de las columnas de estado que no se pudieron pasar a codigo de GESTITEL."""
    return sorted({"%s=%s" % (col, f[col]) for f in filas for col in COLUMNAS_CODIGO
                   if f.get(col) is not None and len(str(f[col])) > 1})


def exportar(almacen, ruta=None, auditoria=None, proyecto="unsa", empresa="UNSA",
             generado_por="agente-evidencia"):
    """Escribe el .xlsx y devuelve {"ruta", "filas", "auditorias"}."""
    filas = almacen.filas_export_auditorias(auditoria, proyecto)
    ahora = dt.datetime.now()
    if not ruta:
        os.makedirs(SALIDAS, exist_ok=True)
        ruta = os.path.join(SALIDAS, "audits_gestitel_%s.xlsx" % ahora.strftime("%Y%m%d_%H%M%S"))

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Auditorías"
    ws.append(["REPORTE AUDITORÍAS"])
    ws.append(["Empresa: %s" % empresa])
    ws.append(["Generado por: %s" % generado_por])
    ws.append(["Fecha de generación: %s" % ahora.strftime("%d/%m/%Y %H:%M:%S")])
    ws.append([])
    ws.append(COLUMNAS)
    ws["A1"].font = Font(bold=True, size=14)
    for c in ws[6]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F3A5F")
    for f in filas:
        ws.append([f.get(col) for col in COLUMNAS])
    for i, col in enumerate(COLUMNAS, 1):
        ancho = max([len(col)] + [min(len(str(f.get(col) or "")), 60) for f in filas])
        ws.column_dimensions[get_column_letter(i)].width = max(12, ancho + 2)
    ws.freeze_panes = "A7"
    wb.save(ruta)
    return {"ruta": ruta, "filas": len(filas),
            "auditorias": sorted({f["Código de auditoría"] for f in filas}),
            "sin_codigo_gestitel": sin_codigo(filas)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--auditoria", help="código de una auditoría (por defecto, todas)")
    ap.add_argument("--proyecto", default="unsa")
    ap.add_argument("--salida", help="ruta del .xlsx (por defecto Entregable-2/datos/salidas/)")
    args = ap.parse_args()

    from almacen_pg import AlmacenPG
    r = exportar(AlmacenPG(), args.salida, args.auditoria, args.proyecto)
    print("Excel GESTITEL: %s (%d filas, auditorías: %s)"
          % (r["ruta"], r["filas"], ", ".join(r["auditorias"]) or "ninguna"))
    if r["sin_codigo_gestitel"]:
        print("AVISO: sin código GESTITEL confirmado (salen como texto; confirmar con el ingeniero y "
              "completar la tabla gestitel_codigos): %s" % ", ".join(r["sin_codigo_gestitel"]))


if __name__ == "__main__":
    main()
