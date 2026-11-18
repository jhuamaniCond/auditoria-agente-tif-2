# -*- coding: utf-8 -*-
"""
Plantillas PIMS (ISO/IEC 27701:2025) construidas sobre las plantillas de referencia
ISO/IEC 27001:2013 que entrego el docente (Mensaje 2).

Se abre la plantilla original para conservar su formato (estilos, encabezado, pie,
numeracion de titulos, portada y tablas de control), se corrige todo lo que era del
SGSI/SGCN y se reescribe el cuerpo. Lo usan:

  - Entregable-3/scripts/generar_documentos_pims.py  (los documentos del Grupo 6)
  - el agente, para emitir el formulario PIMS-FO-01 con las no conformidades de cada
    auditoria aprobada (formulario_no_conformidades()).

Metadatos de control (clausula 7.5.2): cada documento lleva en su portada la tabla
Codigo / Version / Fecha de la version / Creado por / Aprobado por / Nivel de
confidencialidad, que el agente vuelve a leer con leer_metadatos() para verificar el
control documental de cualquier documento PIMS que suban los otros grupos.
"""

import copy
import datetime as dt
import os
import re

import docx
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

AQUI = os.path.dirname(os.path.abspath(__file__))
PLANTILLAS = os.path.join(os.path.dirname(AQUI), "documentos-pims", "plantillas-originales")
PLANTILLA_PROCEDIMIENTO = os.path.join(PLANTILLAS, "Procedimiento_para_medidas_correctivas_ES.docx")
PLANTILLA_CONTROL_DOC = os.path.join(PLANTILLAS, "Procedimiento_para_control_de_documentos_y_registros_ES.docx")
PLANTILLA_FORMULARIO = os.path.join(PLANTILLAS, "Apendice_Formulario_para_medidas_correctivas_ES.docx")
# Plantillas del Mensaje 2 para los documentos de los otros equipos del PIMS
PLANTILLA_METODOLOGIA = os.path.join(PLANTILLAS, "Metodologia_de_evaluacion_y_tratamiento_de_riesgos_ES.docx")
PLANTILLA_INFORME_RIESGOS = os.path.join(PLANTILLAS, "Apendice_3_Informe_sobre_evaluacion_y_tratamiento_ES.docx")
PLANTILLA_PLAN_TRATAMIENTO = os.path.join(PLANTILLAS, "Plan_de_tratamiento_del_riesgo_ES.docx")
PLANTILLA_PLAN_CAPACITACION = os.path.join(PLANTILLAS, "Plan_de_capacitacion_y_concienciacion_ES.docx")
PLANTILLA_CUADRO_EVALUACION = os.path.join(PLANTILLAS, "Apendice_1_Cuadro_de_evaluacion_de_riesgos_ES.xlsx")
PLANTILLA_CUADRO_TRATAMIENTO = os.path.join(PLANTILLAS, "Apendice_2_Cuadro_de_tratamiento_de_riesgos_ES.xlsx")

ORGANIZACION = "Universidad Nacional de San Agustín de Arequipa (UNSA)"
SISTEMA = "Sistema de Gestión de Privacidad de la Información (PIMS) – ISO/IEC 27701:2025"
NOTA_SIMULACION = ("Documento elaborado con apoyo de IA para una implementación simulada del PIMS en "
                   "la UNSA, con fines académicos (TIF de Auditoría de Sistemas, Grupo 6). Los cargos "
                   "y unidades provienen de resoluciones públicas de la UNSA; las aprobaciones y "
                   "firmas son simuladas.")
CAMPOS_PORTADA = ("Código", "Versión", "Fecha de la versión", "Creado por", "Aprobado por",
                  "Nivel de confidencialidad")
GRIS = "D9D9D9"


# --------------------------------------------------------------------------- utilidades XML
def _texto_celda(celda, texto, negrita=None, tam=None):
    """Reemplaza el texto de una celda conservando el formato del primer run."""
    parrafos = celda.paragraphs
    p = parrafos[0]
    for extra in parrafos[1:]:
        extra._p.getparent().remove(extra._p)
    runs = p.runs
    if runs:
        runs[0].text = texto
        for r in runs[1:]:
            r._r.getparent().remove(r._r)
        r = runs[0]
    else:
        r = p.add_run(texto)
    if negrita is not None:
        r.bold = negrita
    if tam:
        r.font.size = Pt(tam)
    return r


def _texto_parrafo(p, texto):
    for enlace in p._p.findall(qn("w:hyperlink")):     # p.runs no incluye los hipervinculos
        p._p.remove(enlace)
    runs = p.runs
    if not runs:
        p.add_run(texto)
        return
    runs[0].text = texto
    for r in runs[1:]:
        r._r.getparent().remove(r._r)


def _sombrear(celda, color=GRIS):
    tcPr = celda._tc.get_or_add_tcPr()
    for viejo in tcPr.findall(qn("w:shd")):
        tcPr.remove(viejo)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def _bordes(tabla):
    tblPr = tabla._tbl.tblPr
    bordes = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b = OxmlElement("w:%s" % lado)
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "4")
        b.set(qn("w:space"), "0")
        b.set(qn("w:color"), "808080")
        bordes.append(b)
    # El esquema de Word exige este orden dentro de tblPr: ... tblInd, tblBorders, shd,
    # tblLayout, tblCellMar, tblLook ...; fuera de orden Word pide "reparar" el archivo.
    for viejo in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(viejo)
    posteriores = [tblPr.find(qn("w:%s" % n)) for n in
                   ("shd", "tblLayout", "tblCellMar", "tblLook", "tblCaption", "tblDescription")]
    posteriores = [e for e in posteriores if e is not None]
    if posteriores:
        posteriores[0].addprevious(bordes)
    else:
        tblPr.append(bordes)


def _campo_indice(parrafo):
    """Inserta el campo TOC de Word (se actualiza al abrir el documento)."""
    for tipo, instr in (("begin", None), (None, 'TOC \\o "1-3" \\h \\z \\u'), ("separate", None),
                        ("texto", None), ("end", None)):
        r = parrafo.add_run()
        if tipo == "texto":
            r.text = "Clic derecho → Actualizar campo para ver el índice."
            r.italic = True
            continue
        if instr:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = instr
            r._r.append(it)
            continue
        fc = OxmlElement("w:fldChar")
        fc.set(qn("w:fldCharType"), tipo)
        if tipo == "begin":
            fc.set(qn("w:dirty"), "true")
        r._r.append(fc)


def _actualizar_campos_al_abrir(documento):
    ajustes = documento.settings.element
    for viejo in ajustes.findall(qn("w:updateFields")):
        ajustes.remove(viejo)
    uf = OxmlElement("w:updateFields")
    uf.set(qn("w:val"), "true")
    ajustes.append(uf)


# --------------------------------------------------------------------------- documento
class DocumentoPIMS:
    """Documento PIMS construido sobre una plantilla original del docente."""

    def __init__(self, plantilla, codigo, titulo, version="1.0", fecha=None, creado_por="",
                 aprobado_por="", confidencialidad="Uso interno", historial=(), portada=True,
                 nota=NOTA_SIMULACION):
        self.doc = docx.Document(plantilla)
        self.codigo, self.titulo, self.version = codigo, titulo, version
        self.fecha = fecha or dt.date.today()
        self.creado_por, self.aprobado_por = creado_por, aprobado_por
        self.confidencialidad = confidencialidad
        self.nota = nota
        self._encabezado_y_pie()
        if portada == "simple":
            # Plantillas de una sola hoja (planes): sin portada propia, se arma una al inicio.
            self.vaciar_cuerpo()
            self._portada_simple(historial)
        elif portada:
            self._portada(historial)
        self._cuerpo = self.doc.element.body

    # ---- encabezado / pie
    def _encabezado_y_pie(self):
        """Corrige encabezados y pies de TODAS las variantes (primera pagina, pares e impares):
        la plantilla trae "©2015 Plantilla para clientes de EPPS..." en la portada y una tabla
        "nombre del documento | ver. [version] del [fecha] | Pagina X de Y" en el resto."""
        licencia = ("EPPS", "Plantilla para clientes", "iso27001standard")
        nota = "Implementación simulada del PIMS de la UNSA con fines académicos"
        version = "%s versión %s del %s" % (self.codigo, self.version, self.fecha.strftime("%d-%m-%Y"))
        for s in self.doc.sections:
            for parte in (s.header, s.first_page_header, s.even_page_header):
                for t in parte.tables:
                    celdas = t.rows[0].cells
                    _texto_celda(celdas[0], ORGANIZACION)
                    _texto_celda(celdas[-1], self.confidencialidad)
            for parte in (s.footer, s.first_page_footer, s.even_page_footer):
                for p in parte.paragraphs:
                    if any(x in p.text for x in licencia):
                        _texto_parrafo(p, nota)
                for t in parte.tables:
                    for fila in t.rows:
                        celdas = fila.cells
                        if celdas and "Página" not in celdas[0].text:
                            _texto_celda(celdas[0], self.titulo)
                        for c in celdas[1:]:
                            if "[versión]" in c.text or "[fecha]" in c.text or "ver." in c.text:
                                _texto_celda(c, version)

    # ---- portada (logo, nombre, titulo, tabla de control, historial, indice)
    def _portada(self, historial):
        cuerpo = self.doc.element.body
        hijos = list(cuerpo.iterchildren())
        parrafos = [docx.text.paragraph.Paragraph(e, self.doc) for e in hijos if e.tag == qn("w:p")]
        tablas = self.doc.tables
        con_titulo = False
        for p in parrafos:
            t = p.text.strip()
            if t == "[logo de la organización]":
                _texto_parrafo(p, SISTEMA)
            elif t == "[nombre de la organización]":
                _texto_parrafo(p, ORGANIZACION)
            elif t.isupper() and len(t) > 15:
                _texto_parrafo(p, self.titulo.upper())
                con_titulo = True
        if not con_titulo:
            # p. ej. «Apéndice 3: Formulario - Informe sobre evaluación...» (sin titulo en mayúsculas)
            primero = next((p for p in parrafos if p.text.strip()), None)
            if primero is not None:
                _texto_parrafo(primero, self.titulo.upper())
        valores = {"Código:": self.codigo, "Versión:": self.version,
                   "Fecha de la versión:": self.fecha.strftime("%d-%m-%Y"),
                   "Creado por:": self.creado_por, "Aprobado por:": self.aprobado_por,
                   "Nivel de confidencialidad:": self.confidencialidad}
        if tablas[0].rows[0].cells[0].text.strip() != "Código:":
            # La plantilla trae solo el historial: se agrega la tabla de control (PR-01, 7.5.2).
            control = self._tabla_control()
            ancla = tablas[0]._tbl
            previo = ancla.getprevious()
            if previo is not None and previo.tag == qn("w:p") and \
                    "Historial" in docx.text.paragraph.Paragraph(previo, self.doc).text:
                ancla = previo            # la tabla de control va antes del título del historial
            ancla.addprevious(control._tbl)
            ancla.addprevious(OxmlElement("w:p"))
            tablas = self.doc.tables
        control = tablas[0]
        for fila in control.rows:
            clave = fila.cells[0].text.strip()
            if clave in valores:
                _texto_celda(fila.cells[1], valores[clave])
        hist = tablas[1]
        filas = hist.rows[1:]
        for i, fila in enumerate(filas):
            datos = historial[i] if i < len(historial) else ("", "", "", "")
            for c, v in zip(fila.cells, datos):
                _texto_celda(c, v)
        # nota de simulacion bajo el titulo de la portada
        titulo_p = next((p for p in parrafos if p.text.strip() == self.titulo.upper()), None)
        if titulo_p is not None:
            nota = OxmlElement("w:p")
            titulo_p._p.addnext(nota)
            pn = docx.text.paragraph.Paragraph(nota, titulo_p._parent)
            r = pn.add_run(self.nota)
            r.italic, r.font.size = True, Pt(9)
            r.font.color.rgb = RGBColor(0x59, 0x59, 0x59)
        # todo lo que sigue a "Tabla de contenido" se reemplaza
        indice = next((p for p in parrafos if p.text.strip().startswith("Tabla de contenido")), None)
        if indice is None:
            return
        borrar, encontrado = [], False
        for e in cuerpo.iterchildren():
            if e is indice._p:
                encontrado = True
                continue
            if encontrado and e.tag != qn("w:sectPr"):
                borrar.append(e)
        for e in borrar:
            cuerpo.remove(e)
        p = self.doc.add_paragraph()
        _campo_indice(p)
        p.add_run().add_break(WD_BREAK.PAGE)
        # (sin w:updateFields: Word mostraria un aviso que bloquea la exportacion automatica)

    def vaciar_cuerpo(self):
        """Para plantillas sin portada (formulario): deja solo el sectPr."""
        cuerpo = self.doc.element.body
        for e in list(cuerpo.iterchildren()):
            if e.tag != qn("w:sectPr"):
                cuerpo.remove(e)

    def _tabla_control(self):
        """Tabla Código / Versión / ... / Nivel de confidencialidad (se llena en _portada)."""
        t = self.doc.add_table(rows=0, cols=2)
        _bordes(t)
        for k in CAMPOS_PORTADA:
            c = t.add_row().cells
            _texto_celda(c[0], k + ":", negrita=True, tam=9)
            _sombrear(c[0], "F2F2F2")
            _texto_celda(c[1], "", tam=9)
        return t

    def _portada_simple(self, historial):
        """Encabezado de control para plantillas de una hoja (Plan de tratamiento, Plan de
        capacitación): título, nota de simulación, tabla de control e historial."""
        cab = self.doc.add_paragraph()
        r = cab.add_run(self.titulo)
        r.bold, r.font.size = True, Pt(14)
        sub = self.doc.add_paragraph()
        r = sub.add_run("%s · %s" % (ORGANIZACION, SISTEMA))
        r.font.size = Pt(9)
        control = self.doc.add_table(rows=0, cols=2)
        _bordes(control)
        for k, v in (("Código:", self.codigo), ("Versión:", self.version),
                     ("Fecha de la versión:", self.fecha.strftime("%d-%m-%Y")),
                     ("Creado por:", self.creado_por), ("Aprobado por:", self.aprobado_por),
                     ("Nivel de confidencialidad:", self.confidencialidad)):
            c = control.add_row().cells
            _texto_celda(c[0], k, negrita=True, tam=9)
            _sombrear(c[0], "F2F2F2")
            _texto_celda(c[1], v, tam=9)
        self.doc.add_paragraph()
        cab_h = self.doc.add_paragraph()
        cab_h.add_run("Historial de modificaciones").bold = True
        hist = self.doc.add_table(rows=1, cols=4)
        _bordes(hist)
        for c, t in zip(hist.rows[0].cells, ("Fecha", "Versión", "Creado por",
                                              "Descripción de la modificación")):
            _texto_celda(c, t, negrita=True, tam=8)
            _sombrear(c)
        for fila in historial:
            for c, t in zip(hist.add_row().cells, fila):
                _texto_celda(c, t, tam=8)
        nota = self.doc.add_paragraph()
        rn = nota.add_run(self.nota)
        rn.italic, rn.font.size = True, Pt(8)
        rn.font.color.rgb = RGBColor(0x59, 0x59, 0x59)

    # ---- bloques de contenido
    def h1(self, texto):
        return self.doc.add_paragraph(texto, style="Heading 1")

    def h2(self, texto):
        return self.doc.add_paragraph(texto, style="Heading 2")

    def h3(self, texto):
        return self.doc.add_paragraph(texto, style="Heading 3")

    def p(self, texto, negrita=False, cursiva=False):
        par = self.doc.add_paragraph()
        self._con_negritas(par, texto, negrita, cursiva)
        return par

    @staticmethod
    def _con_negritas(par, texto, negrita=False, cursiva=False):
        """**texto** dentro del parrafo sale en negrita."""
        for i, trozo in enumerate(re.split(r"\*\*", texto)):
            if trozo:
                r = par.add_run(trozo)
                r.bold = negrita or bool(i % 2)
                r.italic = cursiva

    def vinetas(self, items, numerada=False):
        for it in items:
            par = self.doc.add_paragraph()
            pPr = par._p.get_or_add_pPr()
            numPr = OxmlElement("w:numPr")
            ilvl = OxmlElement("w:ilvl")
            ilvl.set(qn("w:val"), "0")
            numId = OxmlElement("w:numId")
            numId.set(qn("w:val"), "2")
            numPr.append(ilvl)
            numPr.append(numId)
            pPr.append(numPr)
            sp = OxmlElement("w:spacing")
            sp.set(qn("w:after"), "40")
            pPr.append(sp)
            self._con_negritas(par, it)

    def tabla(self, cabecera, filas, anchos=None, tam=9):
        t = self.doc.add_table(rows=1, cols=len(cabecera))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        _bordes(t)
        for c, texto in zip(t.rows[0].cells, cabecera):
            _texto_celda(c, texto, negrita=True, tam=tam)
            _sombrear(c)
        for fila in filas:
            celdas = t.add_row().cells
            for c, texto in zip(celdas, fila):
                c.paragraphs[0].text = ""
                self._con_negritas(c.paragraphs[0], str(texto))
                for r in c.paragraphs[0].runs:
                    r.font.size = Pt(tam)
        if anchos:
            from docx.shared import Cm
            for fila in t.rows:
                for c, a in zip(fila.cells, anchos):
                    c.width = Cm(a)
        self.doc.add_paragraph()
        return t

    def firmas(self, firmantes):
        """[(rol, cargo)] -> bloque de firmas simuladas."""
        self.doc.add_paragraph()
        t = self.doc.add_table(rows=3, cols=len(firmantes))
        for i, (rol, cargo) in enumerate(firmantes):
            _texto_celda(t.cell(0, i), rol, negrita=True, tam=9)
            _texto_celda(t.cell(1, i), "\n\n_____________________________", tam=9)
            _texto_celda(t.cell(2, i), cargo + "\n(firma simulada)", tam=9)

    def salto(self):
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def guardar(self, ruta):
        os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
        props = self.doc.core_properties
        props.title = "%s %s" % (self.codigo, self.titulo)
        props.subject = SISTEMA
        props.author = self.creado_por or "Grupo 6"
        props.keywords = "PIMS; ISO/IEC 27701:2025; UNSA; %s; v%s" % (self.codigo, self.version)
        props.comments = self.nota[:250]
        momento = dt.datetime(self.fecha.year, self.fecha.month, self.fecha.day, 12, 0, 0)
        props.created = props.modified = momento
        props.last_modified_by = props.author
        props.revision = 1
        self.doc.save(ruta)
        _zip_determinista(ruta, momento)
        return ruta


def _zip_determinista(ruta, momento):
    """Reescribe el .docx con fecha fija en cada entrada del zip: el mismo contenido da el
    mismo SHA-256, y volver a generar un documento no crea una version nueva en el expediente."""
    import zipfile
    with zipfile.ZipFile(ruta) as z:
        entradas = [(i.filename, z.read(i.filename)) for i in z.infolist()]
    with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as z:
        for nombre, datos in entradas:
            info = zipfile.ZipInfo(nombre, date_time=momento.timetuple()[:6])
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, datos)


# --------------------------------------------------------------------------- lectura (agente)
RE_CODIGO = re.compile(r"^PIMS-(POL|MA|PR|PL|MT|FO|RG|IN|AC)-\d{2}$")


def leer_metadatos(ruta):
    """Lee la tabla de control de la portada y la seccion "Validez" de un .docx PIMS.
    Devuelve {codigo, version, fecha_version, creado_por, aprobado_por, confidencialidad,
    propietario, valido_hasta, titulo, historial: [...], texto} (vacios si faltan)."""
    d = docx.Document(ruta)
    meta = {k: "" for k in ("codigo", "version", "fecha_version", "creado_por", "aprobado_por",
                            "confidencialidad", "propietario", "valido_hasta", "titulo")}
    claves = {"código": "codigo", "versión": "version", "fecha de la versión": "fecha_version",
              "creado por": "creado_por", "aprobado por": "aprobado_por",
              "nivel de confidencialidad": "confidencialidad"}
    historial = []
    for t in d.tables:
        for fila in t.rows:
            celdas = [c.text.strip() for c in fila.cells]
            if len(celdas) >= 2:
                k = celdas[0].rstrip(":").strip().lower()
                if k in claves and not meta[claves[k]]:
                    meta[claves[k]] = celdas[1]
            if len(celdas) >= 4 and re.match(r"^\d{2}-\d{2}-\d{4}$", celdas[0]) and \
                    re.match(r"^\d+\.\d+$", celdas[1]):
                historial.append({"fecha": celdas[0], "version": celdas[1], "autor": celdas[2],
                                  "descripcion": celdas[3]})
    titulo_props = (d.core_properties.title or "").strip()
    if titulo_props:
        meta["titulo"] = re.sub(r"^PIMS-[A-Z]+-\d+\s+", "", titulo_props)
    parrafos = [p.text.strip() for p in d.paragraphs]
    for i, t in enumerate(parrafos):
        if t.isupper() and len(t) > 15 and not meta["titulo"]:
            meta["titulo"] = t.capitalize()
        m = re.search(r"es válido hasta el (\d{2}-\d{2}-\d{4})", t)
        if m:
            meta["valido_hasta"] = m.group(1)
        m = re.search(r"propietario de este documento es (?:el |la )?(.+?)(?:,| que )", t)
        if m and not meta["propietario"]:
            meta["propietario"] = m.group(1).strip()
    texto = "\n".join(x for x in parrafos if x)
    for t in d.tables:
        for fila in t.rows:
            vistos = []
            for c in fila.cells:
                if c.text.strip() and c.text.strip() not in vistos:
                    vistos.append(c.text.strip())
            texto += "\n" + " | ".join(vistos)
    # Encabezados y pies (todas las variantes): ahi suelen quedar restos de la plantilla.
    for s in d.sections:
        for parte in (s.header, s.first_page_header, s.even_page_header,
                      s.footer, s.first_page_footer, s.even_page_footer):
            try:
                texto += "\n" + "\n".join(p.text for p in parte.paragraphs if p.text.strip())
                for t in parte.tables:
                    for fila in t.rows:
                        texto += "\n" + " | ".join(c.text.strip() for c in fila.cells if c.text.strip())
            except Exception:  # noqa: BLE001  (variante inexistente)
                pass
    meta["historial"] = historial
    meta["texto"] = texto
    return meta


def fecha_ddmmaaaa(texto):
    try:
        return dt.datetime.strptime(texto.strip(), "%d-%m-%Y").date()
    except (ValueError, AttributeError):
        return None


# --------------------------------------------------------------------------- formulario FO-01
FO01_FILAS = [
    ("numero", "N.° de acción correctiva"),
    ("origen", "Origen (auditoría, incidente, revisión por la dirección, queja de titular…)"),
    ("requisito", "Requisito ISO/IEC 27701:2025 / Ley N.° 29733"),
    ("clasificacion", "Clasificación"),
    ("detectado", "Fecha de detección y persona que la identificó"),
    ("descripcion", "a) Descripción de la no conformidad (condición y evidencia)"),
    ("correccion", "a) Corrección inmediata y tratamiento de las consecuencias (incluye efecto sobre titulares de datos personales)"),
    ("causa", "b) Causa(s) de la no conformidad (análisis de causa raíz)"),
    ("similares", "b) ¿Existen o pueden ocurrir no conformidades similares? (indique N.° de acción relacionada)"),
    ("necesaria", "b) ¿Es necesaria una acción correctiva? (Sí / No y justificación)"),
    ("accion", "c) Acción correctiva a implementar"),
    ("responsable", "c) Responsable de la implementación"),
    ("fecha_limite", "c) Fecha límite de implementación"),
    ("aprobado", "c) Aprobado por"),
    ("informar", "c) Personas o áreas a informar"),
    ("implementada", "d) Implementada el"),
    ("eficacia", "d) Revisión de la eficacia (fecha, método y resultado)"),
    ("cambios", "e) Cambios necesarios en el PIMS o en sus documentos"),
    ("estado", "Estado"),
]


def _formulario_base(fecha, version="1.0"):
    d = DocumentoPIMS(PLANTILLA_FORMULARIO, "PIMS-FO-01",
                      "Formulario de no conformidades y acciones correctivas",
                      version=version, fecha=fecha, portada=False)
    d.vaciar_cuerpo()
    return d


def _bloque_formulario(d, valores):
    t = d.doc.add_table(rows=0, cols=2)
    _bordes(t)
    from docx.shared import Cm
    for clave, etiqueta in FO01_FILAS:
        celdas = t.add_row().cells
        _texto_celda(celdas[0], etiqueta, negrita=True, tam=9)
        _sombrear(celdas[0], "F2F2F2")
        _texto_celda(celdas[1], valores.get(clave, ""), tam=9)
        celdas[0].width, celdas[1].width = Cm(6.0), Cm(10.5)
    fila = t.add_row().cells
    _texto_celda(fila[0], "Firmas", negrita=True, tam=9)
    _sombrear(fila[0], "F2F2F2")
    _texto_celda(fila[1], "Identificó: ____________   Responsable: ____________   "
                          "Verificó eficacia: ____________  (firmas simuladas)", tam=9)
    for f in t.rows:                    # ninguna fila se parte entre dos paginas
        trPr = f._tr.get_or_add_trPr()
        no_partir = OxmlElement("w:cantSplit")
        no_partir.set(qn("w:val"), "true")
        trPr.append(no_partir)


def formulario_no_conformidades(ruta, registros=None, fecha=None, titulo_extra="",
                                creado_por="Coordinador de Datos Personales – Grupo 6",
                                aprobado_por="Oficial de Datos Personales (aprobación simulada)",
                                historial=None, version="1.0"):
    """Genera PIMS-FO-01. `registros` es una lista de dicts con las claves de FO01_FILAS;
    sin registros se emite el formulario en blanco (2 bloques)."""
    fecha = fecha or dt.date.today()
    d = _formulario_base(fecha, version)
    cab = d.doc.add_paragraph()
    r = cab.add_run("Apéndice de PIMS-PR-02 — Formulario de no conformidades y acciones correctivas")
    r.bold, r.font.size = True, Pt(13)
    d.p("Registro exigido por la cláusula 10.2 de ISO/IEC 27701:2025: naturaleza de la no "
        "conformidad, acciones tomadas y resultados de la acción correctiva. Se completa un bloque "
        "por no conformidad; una vez verificada la eficacia el registro se bloquea (solo lectura).")
    control = d.doc.add_table(rows=0, cols=2)
    _bordes(control)
    for k, v in (("Código:", d.codigo), ("Versión:", d.version),
                 ("Fecha de la versión:", d.fecha.strftime("%d-%m-%Y")),
                 ("Creado por:", creado_por), ("Aprobado por:", aprobado_por),
                 ("Nivel de confidencialidad:", "Confidencial (una vez completado)")):
        c = control.add_row().cells
        _texto_celda(c[0], k, negrita=True, tam=9)
        _sombrear(c[0], "F2F2F2")
        _texto_celda(c[1], v, tam=9)
    d.doc.add_paragraph()
    hist = d.doc.add_table(rows=1, cols=4)
    _bordes(hist)
    for c, t in zip(hist.rows[0].cells, ("Fecha", "Versión", "Creado por", "Descripción de la modificación")):
        _texto_celda(c, t, negrita=True, tam=8)
        _sombrear(c)
    for fila in (historial or (
            ("03-11-2026", "0.1", "Grupo 6 – Agente de Evidencia y Auditoría",
             "Adaptación del formulario ISO/IEC 27001:2013 a la cláusula 10.2 de ISO/IEC 27701:2025"),
            (d.fecha.strftime("%d-%m-%Y"), d.version, "Oficial de Datos Personales",
             "Versión aprobada (aprobación simulada)"))):
        for c, t in zip(hist.add_row().cells, fila):
            _texto_celda(c, t, tam=8)
    d.doc.add_paragraph()
    if titulo_extra:
        d.p(titulo_extra, cursiva=True)
    nota = d.doc.add_paragraph()
    rn = nota.add_run(NOTA_SIMULACION)
    rn.italic, rn.font.size = True, Pt(8)
    filas = registros or [{}, {}]
    for i, valores in enumerate(filas):
        if i:
            d.doc.add_paragraph()     # sin salto de pagina: cada bloque cabe en ~media hoja
        _bloque_formulario(d, valores)
    d.doc.add_paragraph()
    hasta = dt.date(d.fecha.year + 1, d.fecha.month, min(d.fecha.day, 28)).strftime("%d-%m-%Y")
    d.p("Este documento es válido hasta el %s." % hasta)
    d.p("El propietario de este documento es el Coordinador de Datos Personales, que debe "
        "verificarlo y, si es necesario, actualizarlo junto con PIMS-PR-02 por lo menos una vez al año.")
    return d.guardar(ruta)
