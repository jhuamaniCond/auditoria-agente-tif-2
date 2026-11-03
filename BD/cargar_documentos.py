# -*- coding: utf-8 -*-
"""
Carga en PostgreSQL los documentos oficiales descargados en docs-unsa/.

    python cargar_documentos.py [--carpeta ../docs-unsa] [--proyecto unsa] [--sin-ocr]

Para cada PDF de fuentes.json: calcula su SHA-256, extrae el texto pagina por pagina
(capa de texto del PDF y, cuando la pagina es una imagen escaneada, OCR de Windows en
espanol) y lo guarda en `documentos` y `documento_paginas`. Es idempotente: un documento
con el mismo SHA-256 en el proyecto no se vuelve a cargar.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

import pymupdf

from db import conectar

AQUI = os.path.dirname(os.path.abspath(__file__))
DPI = 200
MIN_CARACTERES = 40         # una pagina con menos texto que esto se trata como imagen

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
$motor = $null
foreach ($idioma in 'es-ES', 'es-MX', 'en-US') {
  $motor = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new($idioma))
  if ($null -ne $motor) { break }
}
if ($null -eq $motor) { throw 'Windows no tiene ningun reconocedor OCR instalado' }
[Console]::OutputEncoding = [Text.Encoding]::UTF8
Get-ChildItem $Carpeta -Filter *.png | Sort-Object Name | ForEach-Object {
  $f = Esperar ([Windows.Storage.StorageFile]::GetFileFromPathAsync($_.FullName)) ([Windows.Storage.StorageFile])
  $s = Esperar ($f.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
  $dec = Esperar ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($s)) ([Windows.Graphics.Imaging.BitmapDecoder])
  $bmp = Esperar ($dec.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
  $r = Esperar ($motor.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
  "@@PAGINA " + $_.BaseName
  foreach ($l in $r.Lines) { "" + [int]($l.Words | Select-Object -First 1).BoundingRect.Y + "|" + [int]($l.Words | Select-Object -First 1).BoundingRect.X + "|" + $l.Text }
  $s.Dispose()
}
"""


def ocr_paginas(doc, paginas):
    """{pagina: texto} leyendo con el OCR de Windows las paginas indicadas (base 1)."""
    if not paginas:
        return {}
    with tempfile.TemporaryDirectory() as tmp:
        for n in paginas:
            doc[n - 1].get_pixmap(dpi=DPI).save(os.path.join(tmp, "p%04d.png" % n))
        script = os.path.join(tmp, "ocr.ps1")
        with open(script, "w", encoding="utf-8-sig") as f:
            f.write(OCR_PS1)
        proceso = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script, tmp],
            capture_output=True)
    if proceso.returncode != 0:
        raise RuntimeError(proceso.stderr.decode("utf-8", "replace")[:300])
    salida, actual = {}, None
    for linea in proceso.stdout.decode("utf-8", "replace").splitlines():
        if linea.startswith("@@PAGINA p"):
            actual = salida.setdefault(int(linea[10:]), [])
        elif actual is not None and linea.count("|") >= 2:
            y, x, texto = linea.split("|", 2)
            actual.append((int(y), int(x), texto.strip()))
    return {n: "\n".join(t for _, _, t in sorted(ls)) for n, ls in salida.items()}


def extraer(ruta, con_ocr=True):
    """[(pagina, texto, metodo)] de un PDF: texto del PDF y, si la pagina es imagen, OCR."""
    if ruta.lower().endswith((".txt", ".md")):     # texto plano: una sola "pagina"
        with open(ruta, encoding="utf-8", errors="replace") as f:
            texto = f.read().strip()
        return 1, ([(1, texto, "texto")] if texto else [])
    doc = pymupdf.open(ruta)
    paginas = {}
    for i, pagina in enumerate(doc, 1):
        texto = pagina.get_text().strip()
        if len(texto) >= MIN_CARACTERES:
            paginas[i] = (texto, "texto")
    if con_ocr:
        pendientes = [n for n in range(1, len(doc) + 1) if n not in paginas]
        for n, texto in ocr_paginas(doc, pendientes).items():
            if texto.strip():
                paginas[n] = (texto.strip(), "ocr")
    return len(doc), [(n, t, m) for n, (t, m) in sorted(paginas.items())]


def tipo_documento(nombre):
    n = nombre.upper()
    if "RCU" in n:
        return "resolucion_rcu"
    if re.search(r"\bRR[-_ ]", n):
        return "resolucion_rr"
    if "INF" in n:
        return "informe"
    if "DIRECTIVA" in n:
        return "directiva"
    return "otro"


def fecha(texto):
    try:
        return dt.date.fromisoformat(texto[:10]) if texto else None
    except ValueError:
        return None     # p. ej. '2018' (solo el anio)


def asegurar_proyecto(cx, id_):
    with cx.cursor() as cur:
        cur.execute("SELECT 1 FROM proyectos WHERE id = %s", (id_,))
        if cur.fetchone():
            return
        if id_ != "unsa":
            sys.exit("No existe el proyecto %r" % id_)
        cur.execute("""INSERT INTO proyectos (id, nombre, rol, descripcion, creado) VALUES
                       ('unsa', 'Universidad Nacional de San Agustin de Arequipa (UNSA)', 'responsable',
                        'Universidad publica peruana. Responsable del tratamiento de datos personales (Ley N.o 29733).',
                        now())""")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--carpeta", default=os.path.join(AQUI, "..", "docs-unsa"))
    ap.add_argument("--proyecto", default="unsa")
    ap.add_argument("--sin-ocr", action="store_true", help="solo la capa de texto de los PDF")
    a = ap.parse_args()
    carpeta = os.path.abspath(a.carpeta)
    fuentes = json.load(open(os.path.join(carpeta, "fuentes.json"), encoding="utf-8"))

    cx = conectar()
    cx.autocommit = True
    asegurar_proyecto(cx, a.proyecto)
    nuevos = repetidos = 0
    for i, f in enumerate(fuentes, 1):
        ruta = os.path.join(carpeta, f["archivo"])
        datos = open(ruta, "rb").read()
        sha = hashlib.sha256(datos).hexdigest()
        with cx.cursor() as cur:
            cur.execute("SELECT id FROM documentos WHERE proyecto = %s AND sha256 = %s", (a.proyecto, sha))
            if cur.fetchone():
                repetidos += 1
                print("[%d/%d] ya cargado: %s" % (i, len(fuentes), f["archivo"]))
                continue
        try:
            total, paginas = extraer(ruta, not a.sin_ocr)
        except Exception as e:  # noqa: BLE001  (PDF danado u OCR no disponible)
            print("[%d/%d] ERROR %s: %s" % (i, len(fuentes), f["archivo"], e))
            continue
        metodos = {m for _, _, m in paginas}
        metodo = "sin_texto" if not paginas else ("mixto" if len(metodos) > 1 else metodos.pop())
        with cx.transaction(), cx.cursor() as cur:
            cur.execute(
                """INSERT INTO documentos (proyecto, handle, archivo, titulo, tipo_documento, url_origen,
                          fecha_documento, fecha_descarga, sha256, tamano_bytes, paginas, metodo_texto, caracteres)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                (a.proyecto, f.get("handle"), f["archivo"], f["titulo"].replace("�", ""),
                 tipo_documento(f["archivo"]), f.get("url_origen"), fecha(f.get("fecha_documento")),
                 fecha(f.get("fecha_descarga") or f.get("fecha_consulta")), sha, len(datos), total, metodo,
                 sum(len(t) for _, t, _ in paginas)))
            id_doc = cur.fetchone()["id"]
            for n, texto, m in paginas:
                cur.execute("INSERT INTO documento_paginas (documento_id, pagina, texto, metodo) VALUES (%s,%s,%s,%s)",
                            (id_doc, n, texto.replace("\x00", ""), m))
        nuevos += 1
        print("[%d/%d] %s: %d pag, texto en %d (%s)" % (i, len(fuentes), f["archivo"], total, len(paginas), metodo))
    with cx.cursor() as cur:
        cur.execute("""SELECT count(*) AS d, coalesce(sum(paginas),0) AS p, coalesce(sum(caracteres),0) AS c
                       FROM documentos WHERE proyecto = %s""", (a.proyecto,))
        r = cur.fetchone()
    print("Cargados %d nuevos (%d ya estaban). En la BD: %d documentos, %d paginas, %d caracteres."
          % (nuevos, repetidos, r["d"], r["p"], r["c"]))


if __name__ == "__main__":
    main()
