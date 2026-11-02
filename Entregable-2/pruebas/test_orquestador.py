# -*- coding: utf-8 -*-
"""
Pruebas del orquestador (modo_rapido: sin LLM ni embeddings).

    python -m unittest Entregable-2/pruebas/test_orquestador.py -v

Trabaja en un proyecto aparte ('Pruebas Orquestador') que se borra al final;
nunca escribe en el expediente 'unsa'.
"""

import datetime as dt
import os
import shutil
import sys
import tempfile
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "agente"))

import nucleo  # noqa: E402
import orquestador  # noqa: E402
import coordinacion  # noqa: E402
import bandeja  # noqa: E402

ESPERA = 120
RAPIDO = {"modo_rapido": True}


class PruebasOrquestador(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.p = nucleo.PROYECTOS.crear("Pruebas Orquestador", "responsable",
                                       "Proyecto temporal de las pruebas del orquestador")
        cls.pid = cls.p.id
        cls.tmp = tempfile.mkdtemp(prefix="orq_")
        cls.ejecuciones = []
        hoy = dt.date.today().isoformat()
        docs = [("politica_privacidad.md", ["5.2"], "politica", "Politica de privacidad"),
                ("procedimiento_incidentes.md", ["A.3.11"], "procedimiento",
                 "Procedimiento de gestion de incidentes con PII"),
                ("programa_auditoria.md", ["9.2"], "informe", "Programa de auditoria interna")]
        cls.evidencias = []
        for nombre, ctrl, tipo, titulo in docs:
            ruta = os.path.join(cls.tmp, nombre)
            with open(ruta, "w", encoding="utf-8") as f:
                f.write("# %s\n\nDocumento de prueba aprobado el %s.\n" % (titulo, hoy))
            cls.evidencias.append(nucleo.registrar_evidencia(
                cls.p.expediente, ruta, ctrl, tipo, titulo, "pruebas", "", hoy,
                nombre_original=nombre))

    @classmethod
    def tearDownClass(cls):
        bandeja.detener()
        for id_ in cls.ejecuciones:
            for ruta in (os.path.join(nucleo.EJECUCIONES, id_ + ".json"),
                         os.path.join(orquestador.INSTANTANEAS, id_ + ".json")):
                if os.path.exists(ruta):
                    os.remove(ruta)
        for carpeta in (nucleo.SALIDAS, orquestador.INCIDENTES):
            for n in os.listdir(carpeta):
                if cls.pid in n or n.startswith("INC-PRUEBA"):
                    os.remove(os.path.join(carpeta, n))
        shutil.rmtree(cls.p.carpeta, ignore_errors=True)
        nucleo.PROYECTOS._cache.pop(cls.pid, None)
        shutil.rmtree(cls.tmp, ignore_errors=True)
        if nucleo.ALMACEN is not None:      # PostgreSQL: borra proyecto, custodia, ejecuciones...
            nucleo.ALMACEN.borrar_proyecto(cls.pid)
            for ruta in getattr(cls, "excel", []):
                if os.path.exists(ruta):
                    os.remove(ruta)

    # ------------------------------------------------------------ utilidades
    def _iniciar(self, tipo, parametros=None):
        ej = orquestador.iniciar(tipo, self.pid, dict(RAPIDO, **(parametros or {})))
        self.ejecuciones.append(ej["id"])
        return ej

    def _esperar(self, id_):
        ej = orquestador.esperar(id_, timeout=ESPERA, intervalo=0.2)
        self.assertNotEqual(ej["estado"], "en_curso", "la ejecucion no avanzo a tiempo")
        self.assertIsNone(ej.get("error"), ej.get("error"))
        return ej

    # ------------------------------------------------------------ pruebas
    def test_1_auditoria_aprobada(self):
        ej = self._iniciar("auditoria_interna", {"max_hallazgos": 2})
        self.assertEqual(ej["estado"], "en_curso")
        self.assertEqual([p["nodo"] for p in ej["pasos"]][0], "planificar")
        ej = self._esperar(ej["id"])
        self.assertEqual(ej["estado"], "esperando_aprobacion")
        a = ej["aprobacion"]
        self.assertTrue(a["pendiente"])
        self.assertTrue(a["hallazgos"])
        self.assertTrue(all({"ref", "estado", "texto"} <= set(h) for h in a["hallazgos"]))
        self.assertTrue(a["propuestas"])
        self.assertTrue(all({"ref", "veredicto", "justificacion"} <= set(x)
                            for x in a["propuestas"]))
        self.assertLessEqual(len(a["propuestas"]), 3)
        pasos = {p["nodo"]: p["estado"] for p in ej["pasos"]}
        self.assertEqual(pasos["alerta_integridad"], "omitido")
        self.assertEqual(pasos["redactar_hallazgos"], "ok")
        # El estado sobrevive fuera del proceso (PostgreSQL o disco)
        if nucleo.ALMACEN is not None:
            self.assertEqual(nucleo.ALMACEN.obtener_ejecucion(ej["id"])["estado"], "esperando_aprobacion")
            self.assertEqual(orquestador.TIPO_CHECKPOINTER, "PostgresSaver")
        else:
            self.assertTrue(os.path.exists(os.path.join(nucleo.EJECUCIONES, ej["id"] + ".json")))

        ref = a["propuestas"][0]["ref"]
        orquestador.aprobar(ej["id"], "aprobada", "Auditor de Prueba", "Conforme",
                            {ref: "aceptada"})
        ej = self._esperar(ej["id"])
        self.assertEqual(ej["estado"], "completada")
        self.assertFalse(ej["aprobacion"]["pendiente"])
        informe = ej["resultado"]["informe"]
        self.assertTrue(os.path.isfile(informe))
        with open(informe, encoding="utf-8") as f:
            texto = f.read()
        self.assertIn("Validado por el auditor:** Auditor de Prueba", texto)
        self.assertIn("Plan de accion correctiva", texto)
        self.assertTrue(ej["resultado"]["plan_accion"])
        self.assertTrue(all(x["responsable"] and x["plazo_dias"]
                            for x in ej["resultado"]["plan_accion"]))
        self.assertTrue(all(p["estado"] in ("ok", "omitido") for p in ej["pasos"]))
        decision = [x for x in orquestador.leer_bitacora(ej["id"]) if x["origen"] == "humano"]
        self.assertEqual(decision[0]["actor"], "Auditor de Prueba")
        self.assertEqual(nucleo.revisiones.leer(self.p.expediente)[ref]["decision"], "aceptada")
        self.assertIn(ej["id"], [e["id"] for e in orquestador.listar(self.pid)])

    def test_2_auditoria_rechazada(self):
        ej = self._esperar(self._iniciar("auditoria_interna", {"max_pertinencia": 0})["id"])
        self.assertEqual(ej["estado"], "esperando_aprobacion")
        self.assertEqual(ej["aprobacion"]["propuestas"], [])
        with self.assertRaises(nucleo.ErrorAgente):
            orquestador.aprobar(ej["id"], "talvez", "X")
        orquestador.aprobar(ej["id"], "rechazada", "Auditor de Prueba", "Faltan pruebas")
        ej = self._esperar(ej["id"])
        self.assertEqual(ej["estado"], "rechazada")
        self.assertNotIn("informe", ej["resultado"])
        pasos = {p["nodo"]: p["estado"] for p in ej["pasos"]}
        self.assertEqual(pasos["generar_informe"], "omitido")
        with self.assertRaises(nucleo.ErrorAgente):     # ya no espera aprobacion
            orquestador.aprobar(ej["id"], "aprobada", "X")

    def test_3_incidente_desde_bus(self):
        evt = coordinacion.simular_agente_incidentes(proyecto=self.pid, parametros=RAPIDO)
        entrega = evt["entregas"][0]
        self.assertEqual(entrega["suscriptor"], "agente-evidencia")
        id_ = entrega["resultado"]["ejecucion"]
        self.ejecuciones.append(id_)
        ej = self._esperar(id_)
        self.assertEqual(ej["estado"], "esperando_aprobacion")
        ev = ej["resultado"]["evidencia"]
        self.assertEqual(ev["controles"], ["A.3.11", "A.3.12"])
        self.assertEqual(ev["tipo"], "registro")
        self.assertTrue(ej["resultado"]["integridad"]["integro"])
        orquestador.aprobar(id_, "aprobada", "DPO de Prueba", "Notificar a la ANPD",
                            {ej["aprobacion"]["propuestas"][0]["ref"]: "aceptada"})
        ej = self._esperar(id_)
        self.assertEqual(ej["estado"], "completada")
        self.assertTrue(os.path.isfile(ej["resultado"]["informe"]))
        ids = [e["id"] for e in nucleo.leer_indice(self.p.expediente)["evidencias"]]
        self.assertIn(ev["id"], ids)
        self.assertIn(evt["id"], [e["id"] for e in coordinacion.leer_eventos(20)])

    def test_4_bandeja_auto_registrar(self):
        nombre = "prueba_orq_%s_politica_privacidad.md" % dt.datetime.now().strftime("%H%M%S%f")
        with open(os.path.join(nucleo.BANDEJA, nombre), "w", encoding="utf-8") as f:
            f.write("Politica de privacidad aprobada, versionada y comunicada. 2026-01-15\n")
        try:
            ej = self._esperar(self._iniciar("bandeja", {"archivos": [nombre],
                                                         "auto_registrar": True})["id"])
            self.assertEqual(ej["estado"], "completada")
            reg = ej["resultado"]["registradas"]
            self.assertEqual(len(reg), 1)
            self.assertTrue(reg[0]["controles"])
            self.assertFalse(os.path.exists(os.path.join(nucleo.BANDEJA, nombre)))
            self.assertTrue(os.path.exists(os.path.join(nucleo.BANDEJA, "procesados", nombre)))
        finally:
            for sub in ("", "procesados", "rechazados"):
                ruta = os.path.join(nucleo.BANDEJA, sub, nombre)
                if os.path.exists(ruta):
                    os.remove(ruta)

    def test_5_integridad_alterada(self):
        ruta = os.path.join(self.p.expediente, self.evidencias[0]["archivo"])
        with open(ruta, encoding="utf-8") as f:
            original = f.read()
        with open(ruta, "a", encoding="utf-8") as f:
            f.write("manipulado\n")
        try:
            ej = self._esperar(self._iniciar("auditoria_interna", {"max_pertinencia": 1})["id"])
            pasos = {p["nodo"]: p["estado"] for p in ej["pasos"]}
            self.assertEqual(pasos["alerta_integridad"], "ok")
            self.assertIn(self.evidencias[0]["id"],
                          ej["resultado"]["alertas"][0]["alteradas"])
            estados = {h["ref"]: h["estado"] for h in ej["aprobacion"]["hallazgos"]}
            self.assertEqual(estados.get("5.2"), "Comprometida")
            self.assertEqual(ej["aprobacion"]["hallazgos"][0]["ref"], "5.2")   # priorizada
            orquestador.aprobar(ej["id"], "rechazada", "Auditor de Prueba")
            self._esperar(ej["id"])
        finally:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(original)

    def test_6_api_y_grafo(self):
        self.assertIsNone(orquestador.obtener("NO-EXISTE"))
        self.assertIsNone(orquestador.obtener("../x"))
        with self.assertRaises(nucleo.ErrorAgente):
            orquestador.iniciar("desconocido", self.pid)
        d = orquestador.describir("auditoria_interna")
        self.assertIn("aprobacion_auditor", d["nodos"])
        lista = orquestador.listar()
        self.assertEqual(lista, sorted(lista, key=lambda e: (e["creado"], e["id"]), reverse=True))

    def test_8_cancelar_auditoria(self):
        # 1) Cancelar en la puerta HITL: se descarta sin informe y ya no admite aprobacion
        ej = self._esperar(self._iniciar("auditoria_interna", {"max_pertinencia": 0})["id"])
        self.assertEqual(ej["estado"], "esperando_aprobacion")
        with self.assertRaises(nucleo.ErrorAgente):
            orquestador.cancelar(ej["id"], "  ")                 # quien cancela es obligatorio
        ej = orquestador.cancelar(ej["id"], "Auditor de Prueba", "Prueba de cancelacion")
        self.assertEqual(ej["estado"], "cancelada")
        self.assertEqual(ej["cancelacion"]["estado_previo"], "esperando_aprobacion")
        self.assertFalse(ej["aprobacion"]["pendiente"])
        self.assertNotIn("informe", ej["resultado"])
        with self.assertRaises(nucleo.ErrorAgente):
            orquestador.aprobar(ej["id"], "aprobada", "Auditor de Prueba")
        with self.assertRaises(nucleo.ErrorAgente):
            orquestador.cancelar(ej["id"], "Auditor de Prueba")  # ya cerrada
        dec = [x for x in orquestador.leer_bitacora(ej["id"]) if x["decision"] == "cancelada"]
        self.assertEqual(dec[0]["actor"], "Auditor de Prueba")
        self.assertEqual(dec[0]["origen"], "humano")

        # 2) Cancelar mientras el hilo trabaja: se detiene y el estado no se sobrescribe
        ej = self._iniciar("auditoria_interna", {"max_pertinencia": 0})
        orquestador.cancelar(ej["id"], "Auditor de Prueba", "Cancelada en curso")
        hilo = orquestador._HILOS.get(ej["id"])
        if hilo:
            hilo.join(ESPERA)
        final = orquestador.obtener(ej["id"])
        self.assertEqual(final["estado"], "cancelada")
        self.assertIsNone(final.get("aprobacion"))
        self.assertTrue(all(p["estado"] in ("ok", "omitido", "cancelado") for p in final["pasos"]))
        if nucleo.ALMACEN is not None:      # una auditoria cancelada no se vuelca a GESTITEL
            self.assertEqual(nucleo.ALMACEN.filas_export_auditorias(ej["id"], self.pid), [])

    @unittest.skipIf(nucleo.ALMACEN is None, "solo con PIMS_BACKEND=postgres")
    def test_7_postgres_auditoria_y_excel_gestitel(self):
        import herramientas
        import openpyxl
        almacen = nucleo.ALMACEN
        # La cadena de custodia guardada en la BD valida con el codigo de la skill
        r = herramientas.verificar_integridad(self.pid)
        self.assertEqual(r["problemas_cadena"], [])
        # Una auditoria completada queda en las tablas del modulo Auditorias de GESTITEL
        completadas = [e for e in orquestador.listar(self.pid)
                       if e["tipo"] == "auditoria_interna" and e["estado"] == "completada"]
        self.assertTrue(completadas, "test_1 debe dejar una auditoria completada")
        cod = completadas[0]["id"]
        filas = almacen.filas_export_auditorias(cod, self.pid)
        self.assertEqual(len(filas), len(completadas[0]["aprobacion"]["hallazgos"]))
        # Estados con el codigo de una letra de GESTITEL (N = No conformidad, C = Cerrada, I = Interna)
        self.assertTrue(all(f["Clasificación (hallazgo)"] in
                            ("N", "Observación", "Oportunidad de mejora") for f in filas))
        self.assertTrue(all(f["Estado"] == "C" and f["Tipo"] == "I" for f in filas))
        # El codigo cabe en audit_code (20) y el requisito de origen en source_requirement_code (10)
        cod_gestitel = filas[0]["Código de auditoría"]
        self.assertRegex(cod_gestitel, r"^AUD-\d{4}-\d{3}$")
        self.assertTrue(all(len(f["Requisito de origen (checklist)"] or "") <= 10 for f in filas))
        # Excel con el formato de GESTITEL
        x = herramientas.exportar_gestitel(self.pid, cod)
        self.__class__.excel = [x["ruta"]]
        ws = openpyxl.load_workbook(x["ruta"]).active
        self.assertEqual(ws.title, "Auditorías")
        self.assertEqual(ws["A1"].value, "REPORTE AUDITORÍAS")
        self.assertEqual(ws["A6"].value, "Código de auditoría")
        self.assertEqual(ws.cell(6, 25).value, "Avance (acción)")
        self.assertEqual(ws.max_row, 6 + len(filas))
        self.assertEqual(ws["A7"].value, cod_gestitel)


if __name__ == "__main__":
    unittest.main(verbosity=2)
