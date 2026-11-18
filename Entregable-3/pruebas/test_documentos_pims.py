# -*- coding: utf-8 -*-
"""Control documental de los documentos PIMS (reglas de PIMS-PR-01) y lista maestra PIMS-RG-01.

    cd Entregable-3/agente && python ../pruebas/test_documentos_pims.py
"""
import datetime as dt
import glob
import os
import sys
import tempfile
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
E3 = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(E3, "agente"))

import plantillas_pims as pp  # noqa: E402
import documentos_pims as dp  # noqa: E402
import lista_maestra_pims as lm  # noqa: E402

GENERADOS = os.path.join(E3, "documentos-pims", "generados")
OTROS = os.path.join(E3, "documentos-pims", "otros-grupos")
ORIGINALES = os.path.join(E3, "documentos-pims", "plantillas-originales")


class ControlDocumental(unittest.TestCase):
    def test_1_documentos_del_grupo_6_son_conformes(self):
        archivos = glob.glob(os.path.join(GENERADOS, "PIMS-*.docx"))
        self.assertGreaterEqual(len(archivos), 5)
        for ruta in archivos:
            c = dp.verificar_control(pp.leer_metadatos(ruta), dt.date(2026, 11, 17))
            fallas = [r["regla"] for r in c["reglas"] if not r["ok"]]
            self.assertEqual(c["resultado"], "conforme", "%s: %s" % (os.path.basename(ruta), fallas))
            self.assertEqual(c["estado"], "aprobado")

    def test_2_plantillas_27001_del_docente_no_son_conformes(self):
        for ruta in glob.glob(os.path.join(ORIGINALES, "Procedimiento*.docx")):
            c = dp.verificar_control(pp.leer_metadatos(ruta))
            reglas = {r["regla"]: r for r in c["reglas"]}
            self.assertEqual(c["resultado"], "no_conforme")
            self.assertFalse(reglas["Sin campos de plantilla por llenar"]["ok"])
            self.assertFalse(reglas["Alineado a ISO/IEC 27701:2025 (sin restos de la plantilla 27001/22301)"]["ok"])

    def test_3_documento_vencido_se_detecta(self):
        ruta = glob.glob(os.path.join(GENERADOS, "PIMS-PR-01*.docx"))[0]
        c = dp.verificar_control(pp.leer_metadatos(ruta), dt.date(2028, 1, 1))
        validez = next(r for r in c["reglas"] if r["regla"] == "Validez vigente")
        self.assertFalse(validez["ok"])
        self.assertEqual(c["resultado"], "no_conforme")

    def test_4_formulario_fo01_con_registros(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = os.path.join(tmp, "fo01.docx")
            pp.formulario_no_conformidades(ruta, [{"numero": "AC-2026-001", "requisito": "9.2 Auditoria interna",
                                                   "clasificacion": "No conformidad mayor", "estado": "Abierta"}],
                                           fecha=dt.date(2026, 11, 17))
            m = pp.leer_metadatos(ruta)
            self.assertEqual(m["codigo"], "PIMS-FO-01")
            self.assertIn("AC-2026-001", m["texto"])
            self.assertEqual(dp.verificar_control(m, dt.date(2026, 11, 17))["resultado"], "conforme")

    def test_5_generacion_determinista(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = os.path.join(tmp, "a.docx"), os.path.join(tmp, "b.docx")
            for r in (a, b):
                pp.formulario_no_conformidades(r, fecha=dt.date(2026, 11, 17))
            with open(a, "rb") as fa, open(b, "rb") as fb:
                self.assertEqual(fa.read(), fb.read())

    def test_6_documentos_de_los_otros_equipos_son_conformes(self):
        archivos = glob.glob(os.path.join(OTROS, "PIMS-*.docx"))
        self.assertGreaterEqual(len(archivos), 17)
        for ruta in archivos:
            m = pp.leer_metadatos(ruta)
            c = dp.verificar_control(m, dt.date(2026, 11, 18))
            fallas = [r["regla"] for r in c["reglas"] if not r["ok"]]
            self.assertEqual(c["resultado"], "conforme", "%s: %s" % (os.path.basename(ruta), fallas))
            self.assertIn(m["codigo"], lm.por_codigo(), "%s no está en la lista maestra" % m["codigo"])


class ListaMaestra(unittest.TestCase):
    """Mensaje 3: la información documentada del PIMS con sus cláusulas y controles."""

    def test_1_toda_clausula_y_control_tiene_documento(self):
        por_req = lm.documentos_por_requisito()
        refs = list(lm.CLAUSULAS) + [c for c, _ in lm.CONTROLES_A1 + lm.CONTROLES_A3]
        self.assertEqual([r for r in refs if r not in por_req], [])
        catalogo = {c["ref"] for c in dp.nucleo.CATALOGO if c["grupo"] != "A.2"}
        self.assertEqual(sorted(catalogo - set(por_req)), [])

    def test_2_todo_expediente_de_la_guia_tiene_documento(self):
        cubiertos = set(lm.expedientes_cubiertos()) | set(lm.NO_APLICA)
        self.assertEqual([d for d in ("D%02d" % i for i in range(1, 38)) if d not in cubiertos], [])

    def test_3_cada_codigo_de_la_lista_tiene_su_docx(self):
        codigos = {pp.leer_metadatos(r)["codigo"] for carpeta in (GENERADOS, OTROS)
                   for r in glob.glob(os.path.join(carpeta, "PIMS-*.docx"))}
        self.assertEqual(sorted(set(lm.por_codigo()) - codigos), [])

    def test_4_un_documento_faltante_genera_hallazgo_7_5(self):
        doc = {"codigo": "PIMS-PR-01", "titulo": "Control documental", "version": "1.2",
               "estado": "aprobado", "agente_autor": lm.G6,
               "control": {"resultado": "conforme", "reglas": []}}
        originales = dp.reverificar, dp.listar, dp.lista_esperada
        dp.reverificar = lambda *a, **k: []
        dp.listar = lambda proyecto="unsa": [doc]
        dp.lista_esperada = lambda proyecto="unsa": {k: v for k, v in lm.por_codigo().items()
                                                     if k in ("PIMS-PR-01", "PIMS-RG-02")}
        try:
            cd = dp.control_documental("unsa", dt.date(2026, 11, 18))
        finally:
            dp.reverificar, dp.listar, dp.lista_esperada = originales
        self.assertEqual(cd["pendientes"], ["PIMS-RG-02"])
        self.assertEqual(cd["hallazgo"]["ref"], "7.5")
        self.assertIn("PIMS-RG-02", cd["hallazgo"]["texto"])
        self.assertIn(lm.A1, cd["hallazgo"]["texto"])


if __name__ == "__main__":
    unittest.main()
