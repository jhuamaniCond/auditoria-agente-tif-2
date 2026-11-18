# -*- coding: utf-8 -*-
"""Piezas comunes de los documentos PIMS de los otros equipos (generar_documentos_otros_grupos.py)."""

import datetime as dt
import os

import generar_documentos_pims as g6
import lista_maestra_pims as lm
import plantillas_pims as pp

E3 = g6.E3
SALIDA = os.path.join(E3, "documentos-pims", "otros-grupos")
FECHA = dt.date(2026, 11, 18)
VALIDO_HASTA = "18-11-2027"

# cargos (los mismos del Grupo 6)
CU, CGTD, ODP, CDP, OSCD, OTI, CSIRT, SG = g6.CU, g6.CGTD, g6.ODP_CORTO, g6.CDP, g6.OSCD_CORTO, g6.OTI, \
    g6.CSIRT, g6.SG
RRHH = "Jefe(a) de la Unidad de Recursos Humanos"
REF_COMUNES = g6.REF_COMUNES
APROBADO_CGTD = "Comité de Gobierno y Transformación Digital (sesión simulada del 18-11-2026)"
APROBADO_CU = "Consejo Universitario (Resolución de Consejo Universitario simulada del 18-11-2026)"

FICHA = {f["codigo"]: f for f in lm.filas()}


def nota(equipo):
    return ("Documento elaborado con apoyo de IA por el Grupo 6 en coordinación con el equipo «%s» del "
            "PIMS, para una implementación simulada del PIMS en la UNSA con fines académicos (TIF de "
            "Auditoría de Sistemas). Los cargos y unidades provienen de resoluciones públicas de la UNSA; "
            "las aprobaciones, firmas y cifras son simuladas." % equipo)


def nuevo(plantilla, codigo, titulo, descripcion, aprobado_por=APROBADO_CGTD, aprobador_corto=ODP,
          revisor=CDP, portada=True):
    """Documento con la portada de control completa (lo que verifica PIMS-PR-01)."""
    f = FICHA[codigo]
    historial = [
        ("10-11-2026", "0.1", "Equipo «%s» con el Grupo 6 (borrador asistido por IA)" % f["equipo"],
         descripcion),
        ("14-11-2026", "0.2", revisor, "Revisión de coherencia con la lista maestra PIMS-RG-01 y con los "
                                      "documentos de los demás equipos"),
        ("18-11-2026", "1.0", aprobador_corto, "Versión aprobada (aprobación simulada)"),
    ]
    return pp.DocumentoPIMS(plantilla, codigo, titulo, version="1.0", fecha=FECHA,
                            creado_por="%s – equipo «%s»" % (f["propietario"], f["equipo"]),
                            aprobado_por=aprobado_por, confidencialidad=f["confidencialidad"],
                            historial=historial, portada=portada, nota=nota(f["equipo"]))


def objetivo(d, objetivo_txt, alcance_txt, usuarios_txt):
    d.h1("Objetivo, alcance y usuarios")
    d.p(objetivo_txt)
    d.p(alcance_txt)
    d.p(usuarios_txt)


def referencias(d, extra):
    d.h1("Documentos de referencia")
    d.vinetas(REF_COMUNES + list(extra))


def registros(d, filas, tam=8):
    d.h1("Gestión de registros guardados en base a este documento")
    d.tabla(["Nombre del registro", "Ubicación de archivo", "Persona responsable del archivo",
             "Controles para la protección del registro", "Tiempo de retención"], filas,
            anchos=[3.6, 3.8, 2.6, 4, 2], tam=tam)


def validez(d, codigo, criterios):
    d.h1("Validez y gestión de documentos")
    d.p("Este documento es válido hasta el %s." % VALIDO_HASTA)
    d.p("El propietario de este documento es el %s, que debe verificar y, si es necesario, actualizar "
        "el documento por lo menos una vez al año, y además cuando cambien la norma, la Ley N.° 29733 o "
        "su reglamento, la estructura orgánica de la UNSA o los resultados de auditoría lo justifiquen."
        % FICHA[codigo]["propietario"])
    d.p("Al evaluar la eficacia y adecuación de este documento se tienen en cuenta los siguientes "
        "criterios (se miden según PIMS-PR-04):")
    d.vinetas(criterios)


def firmas(d, elabora, revisa, aprueba):
    d.firmas([("Elaborado por", elabora), ("Revisado por", revisa), ("Aprobado por", aprueba)])


def guardar(d, nombre):
    return d.guardar(os.path.join(SALIDA, nombre))
