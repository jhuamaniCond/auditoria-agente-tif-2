# -*- coding: utf-8 -*-
"""
Convierte las normas escaneadas de ISOS/pdf/ en texto que el RAG puede indexar.

    python extraer_norma.py            # procesa todos los PDF de ISOS/pdf/

El PDF de ISO/IEC 27701:2025 es un escaneo (no tiene capa de texto), asi que
cada pagina se rasteriza con PyMuPDF y se lee con el OCR que trae Windows 10/11
(Windows.Media.Ocr, idioma en-US) a traves de PowerShell: no hace falta
instalar Tesseract ni modelos adicionales. Solo se ejecuta una vez; la app lee
el resultado, ISOS/texto/<nombre>.md, con una seccion "## <ref> <titulo>" por
clausula, control del Anexo A y guia del Anexo B.

Paginas que se convierten: introduccion, clausulas 1-10, Anexo A y Anexo B.
Los Anexos C-F son tablas de correspondencia (29100, RGPD, 27018, edicion 2019)
y la bibliografia: el OCR de tablas no conserva las filas, asi que se omiten.
"""

import os
import re
import subprocess
import sys
import tempfile

import pymupdf

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_PDF = os.path.join(RAIZ, "ISOS", "pdf")
CARPETA_TEXTO = os.path.join(RAIZ, "ISOS", "texto")
DPI = 250

# Paginas del PDF (base 1) de ISO/IEC 27701:2025 por tipo de contenido.
PAGINAS_TEXTO = range(6, 21)      # Introduccion y clausulas 1-10
PAGINAS_ANEXO_A = range(21, 27)   # Tablas A.1, A.2 y A.3 (tres columnas)
PAGINAS_ANEXO_B = range(27, 57)   # Guia de implementacion

OCR_PS1 = r"""
param([string]$Carpeta)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]
$asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
  $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
  $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
function Esperar($op, [Type]$t) {
  $task = $asTask.MakeGenericMethod($t).Invoke($null, @($op)); $task.Wait(); $task.Result }
$motor = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new('en-US'))
if ($null -eq $motor) { throw 'Windows no tiene el reconocedor OCR en-US instalado' }
[Console]::OutputEncoding = [Text.Encoding]::UTF8
Get-ChildItem $Carpeta -Filter *.png | Sort-Object Name | ForEach-Object {
  $f = Esperar ([Windows.Storage.StorageFile]::GetFileFromPathAsync($_.FullName)) ([Windows.Storage.StorageFile])
  $s = Esperar ($f.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
  $dec = Esperar ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($s)) ([Windows.Graphics.Imaging.BitmapDecoder])
  $bmp = Esperar ($dec.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
  $r = Esperar ($motor.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
  "@@PAGINA " + $_.BaseName
  foreach ($l in $r.Lines) {
    $w = ($l.Words | Select-Object -First 1).BoundingRect
    "" + [int]$w.X + "|" + [int]$w.Y + "|" + $l.Text }
  $s.Dispose()
}
"""


# ------------------------------------------------------------------ OCR
def ocr_pdf(ruta_pdf, paginas):
    """{pagina: [(x, y, texto)]} con las lineas que reconoce Windows OCR."""
    with tempfile.TemporaryDirectory() as tmp:
        doc = pymupdf.open(ruta_pdf)
        for n in paginas:
            doc[n - 1].get_pixmap(dpi=DPI).save(os.path.join(tmp, "p%03d.png" % n))
        script = os.path.join(tmp, "ocr.ps1")
        with open(script, "w", encoding="utf-8-sig") as f:
            f.write(OCR_PS1)
        salida = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script, tmp],
            capture_output=True, check=True).stdout.decode("utf-8", "replace")
    paginas_ocr, actual = {}, None
    for linea in salida.splitlines():
        if linea.startswith("@@PAGINA p"):
            actual = paginas_ocr.setdefault(int(linea[10:]), [])
        elif actual is not None and linea.count("|") >= 2:
            x, y, texto = linea.split("|", 2)
            actual.append((int(x), int(y), texto.strip()))
    return paginas_ocr


# ------------------------------------------------------- limpieza de OCR
_REF = re.compile(r"^([A-F])\s?\.\s?([0-9Il|]+(?:\s?[.,:]\s?[0-9Il|]+)*)")


def normalizar_ref(texto):
    """'B.I.3.2 Titulo' -> 'B.1.3.2 Titulo' (el OCR confunde 1 con I o l)."""
    m = _REF.match(texto)
    if not m:
        return texto
    numeros = re.sub(r"\s", "", m.group(2)).replace(",", ".").replace(":", ".")
    numeros = numeros.replace("I", "1").replace("l", "1").replace("|", "1")
    return "%s.%s%s" % (m.group(1), numeros, texto[m.end():])


def limpiar(texto):
    texto = re.sub(r"\bPI[Il1L]\b", "PII", texto)
    texto = re.sub(r"\b(of|If|if|in|to)(the|any)\b", r"\1 \2", texto)
    return texto.replace("Table A.I", "Table A.1")


def dentro_de_caja(linea):
    """Descarta la cabecera 'ISO/IEC 27701:2025(en)' y el pie de copyright."""
    return 170 < linea[1] < 2600 and "rights reserved" not in linea[2]


def filas(lineas):
    """Agrupa en una fila las lineas con la misma altura (p. ej. 'd)' + texto)."""
    lineas = sorted((l for l in lineas if dentro_de_caja(l)), key=lambda l: (l[1], l[0]))
    salida = []
    for x, y, t in lineas:
        if salida and abs(salida[-1][1] - y) <= 12:
            px, py, pt = salida[-1]
            salida[-1] = (min(px, x), py, pt + " " + t if px <= x else t + " " + pt)
        else:
            salida.append((x, y, t))
    return salida


ES_TITULO = re.compile(r"^(?:[A-F]\.)?\d{1,2}(?:\.\d{1,2}){0,4}\s+[A-Z][^.;:]{2,95}$")
SUBTITULOS = ("Control", "Implementation guidance", "Objective", "Other information")


def parrafos(paginas_ocr, paginas):
    """Texto corrido: [(pagina, 'titulo'|'parrafo', texto)]."""
    bloques = []
    for n in paginas:
        previa = None
        for x, y, t in filas(paginas_ocr.get(n, [])):
            t = limpiar(normalizar_ref(t))
            # Una sangria mayor solo abre parrafo si lo anterior cerro la frase o el
            # item; si no, es la segunda linea del mismo item de una lista.
            cerrado = bool(bloques) and bloques[-1][2].rstrip().endswith((".", ";", ":"))
            item = re.match(r"^([a-z]|\d)\)\s", t)
            nuevo = previa is None or y - previa[1] > 55 or (x > previa[0] + 40 and cerrado) \
                or item or t.startswith("NOTE")
            if ES_TITULO.match(t) and (previa is None or y - previa[1] > 55):
                bloques.append([n, "titulo", t])
            elif t.startswith(SUBTITULOS) and len(t) < 60:
                bloques.append([n, "subtitulo", t])
            elif nuevo or not bloques or bloques[-1][1] != "parrafo":
                sangria = "   " if item and x > 280 else ("- " if x > 280 else "")
                bloques.append([n, "parrafo", sangria + t])
            elif bloques[-1][2].endswith("-"):
                bloques[-1][2] = bloques[-1][2][:-1] + t
            else:
                bloques[-1][2] += " " + t
            previa = (x, y)
    return bloques


# ----------------------------------------------------------- Anexo A
COLUMNA_CONTROL = 800   # x a partir de la cual empieza la columna "Control"
TITULO_TABLA = re.compile(r"^Table [A-F]\.\S+\s+(\(continued\)|—|-)")
ENCABEZADOS_TABLA = ("Control title", "Control", "reference", "Control reference")


def _siguiente(ref):
    """A.1.4.3 -> A.1.4.4 (para una fila cuyo numero no leyo el OCR)."""
    partes = ref.split(".")
    return ".".join(partes[:-1] + [str(int(partes[-1]) + 1)])


def _repartir_columna_control(lineas, refs, controles):
    """Asigna las lineas de la columna Control a su fila.

    Cada control empieza con una oracion nueva (la linea anterior acaba en punto o
    la linea empieza por 'The organization') un poco por encima de su referencia,
    que esta centrada en la fila. Lo que queda antes del primer inicio continua el
    ultimo control de la pagina anterior.
    """
    textos = [(y, t) for x, y, t in lineas if x >= COLUMNA_CONTROL]
    inicios = [k for k, (y, t) in enumerate(textos)
               if k == 0 or textos[k - 1][1].rstrip().endswith(".")
               or t.startswith("The organization")]
    elegidos = []
    for c in refs:
        candidatos = [k for k in inicios if textos[k][0] <= c["y"] + 10
                      and (not elegidos or k > elegidos[-1])]
        elegidos.append(candidatos[-1] if candidatos else (elegidos[-1] if elegidos else 0))
    if refs and elegidos[0] > 0 and controles:
        controles[-1]["texto"].extend(textos[:elegidos[0]])
    for n, (c, k) in enumerate(zip(refs, elegidos)):
        fin = elegidos[n + 1] if n + 1 < len(elegidos) else len(textos)
        c["texto"].extend(textos[k:fin])


def anexo_a(paginas_ocr, paginas):
    """Tablas A.1-A.3: columnas referencia (x<400), titulo y control (x>=800)."""
    controles = []
    for n in paginas:
        lineas = filas_columnas(paginas_ocr.get(n, []))
        refs = [{"ref": normalizar_ref(t).split()[0], "pagina": n, "y": y, "titulo": [], "texto": []}
                for x, y, t in lineas if x < 400 and _REF.match(t) and len(t) < 14]
        celdas = sorted(((x, y, t) for x, y, t in lineas if x >= 400), key=lambda c: c[1])
        # Celdas separadas por un hueco > 40 px = filas distintas de la tabla.
        bloques, bloque = [], []
        for celda in celdas:
            if bloque and celda[1] - bloque[-1][1] > 40:
                bloques.append(bloque)
                bloque = []
            bloque.append(celda)
        if bloque:
            bloques.append(bloque)
        for bloque in bloques:
            arriba, abajo = bloque[0][1] - 30, bloque[-1][1] + 30
            dentro = [c for c in refs if arriba <= c["y"] <= abajo]
            completa = any(x < COLUMNA_CONTROL for x, _, _ in bloque) and                 any(x >= COLUMNA_CONTROL for x, _, _ in bloque)
            if not dentro:
                previas = [c for c in refs if c["y"] < arriba]
                if previas and completa:         # fila entera sin numero legible
                    nueva = {"ref": _siguiente(previas[-1]["ref"]), "pagina": n,
                             "y": (arriba + abajo) // 2, "titulo": [], "texto": []}
                    refs.append(nueva)
                    refs.sort(key=lambda c: c["y"])
                    dentro = [nueva]
                elif previas:                    # trozo de la fila de arriba
                    dentro = [previas[-1]]
                elif controles:                  # fila que viene de la pagina anterior
                    dentro = [controles[-1]]
                else:
                    continue
            for x, y, t in bloque:
                if x < COLUMNA_CONTROL:
                    min(dentro, key=lambda c: abs(c["y"] - y))["titulo"].append((y, t))
        _repartir_columna_control(lineas, refs, controles)
        controles.extend(refs)
    return [(c["pagina"], c["ref"], unir(c["titulo"]), unir(c["texto"]), c["ref"][:3])
            for c in controles]


def filas_columnas(lineas):
    salida = []
    for x, y, t in sorted(lineas, key=lambda l: (l[1], l[0])):
        if not dentro_de_caja((x, y, t)) or TITULO_TABLA.match(t) or t in ENCABEZADOS_TABLA:
            continue
        # A veces el OCR une en una linea la celda del titulo y la del control.
        corte = t.find("The organization shall")
        if x < COLUMNA_CONTROL and corte > 0:
            salida.extend([(x, y, t[:corte].strip()), (COLUMNA_CONTROL, y, t[corte:])])
        else:
            salida.append((x, y, t))
    return salida


def unir(partes):
    texto = ""
    for _, t in sorted(partes):
        texto = texto[:-1] + t if texto.endswith("-") else (texto + " " + t).strip()
    return limpiar(texto)


# ------------------------------------------------------------ escritura
TABLAS = {"A.1": "Tabla A.1 - controles para responsables del tratamiento (PII controllers)",
          "A.2": "Tabla A.2 - controles para encargados del tratamiento (PII processors)",
          "A.3": "Tabla A.3 - controles de seguridad para responsables y encargados"}


def markdown(nombre, paginas_ocr):
    lineas = ["# %s" % nombre, "",
              "Texto extraido por OCR (Windows.Media.Ocr) de ISOS/pdf/%s.pdf con "
              "04-aplicacion/extraer_norma.py. Idioma original: ingles. Cada seccion indica la "
              "pagina del PDF de donde sale." % nombre, ""]

    def volcar(bloques):
        for n, tipo, t in bloques:
            if tipo == "titulo":
                lineas.extend(["", "## %s" % t, "", "_Pagina %d del PDF_" % n, ""])
            elif tipo == "subtitulo":
                lineas.extend(["**%s**" % t, ""])
            else:
                lineas.extend([t, ""])

    volcar(parrafos(paginas_ocr, PAGINAS_TEXTO))
    lineas.extend(["", "# Annex A (normative) - PIMS reference control objectives and controls", ""])
    controles = anexo_a(paginas_ocr, PAGINAS_ANEXO_A)
    for n, ref, titulo, texto, tabla in controles:
        lineas.extend(["## %s %s" % (ref, titulo), "", "_Pagina %d del PDF - %s_" % (n, TABLAS[tabla]),
                       "", "**Control (requisito, Anexo A):** %s" % texto, ""])
    lineas.extend(["", "# Annex B (normative) - Implementation guidance", ""])
    volcar(parrafos(paginas_ocr, PAGINAS_ANEXO_B))
    texto = "\n".join(lineas)
    return re.sub(r"\n{3,}", "\n\n", texto).strip() + "\n"


def main():
    os.makedirs(CARPETA_TEXTO, exist_ok=True)
    pdfs = [f for f in sorted(os.listdir(CARPETA_PDF)) if f.lower().endswith(".pdf")]
    if not pdfs:
        sys.exit("No hay PDF en %s" % CARPETA_PDF)
    for archivo in pdfs:
        nombre = os.path.splitext(archivo)[0]
        print("OCR de %s ..." % archivo)
        paginas = list(PAGINAS_TEXTO) + list(PAGINAS_ANEXO_A) + list(PAGINAS_ANEXO_B)
        texto = markdown(nombre, ocr_pdf(os.path.join(CARPETA_PDF, archivo), paginas))
        destino = os.path.join(CARPETA_TEXTO, nombre + ".md")
        with open(destino, "w", encoding="utf-8") as f:
            f.write(texto)
        print("  -> %s (%d secciones, %d caracteres)" % (
            os.path.relpath(destino, RAIZ), texto.count("\n## "), len(texto)))


if __name__ == "__main__":
    main()
