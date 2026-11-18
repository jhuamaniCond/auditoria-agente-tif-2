# Exporta a PDF cada documento PIMS (PIMS-PR-01: la version aprobada se publica tambien en PDF).
# Word trabaja sobre una copia temporal: el .docx original no se toca, para que su SHA-256 siga
# siendo el registrado en el expediente. El indice (campo TOC) se actualiza en la copia.
#
#   powershell -ExecutionPolicy Bypass -File Entregable-3\scripts\exportar_pdf.ps1
param(
    [string]$Carpeta = (Join-Path $PSScriptRoot "..\documentos-pims\generados"),
    [string]$Pdf = (Join-Path $PSScriptRoot "..\documentos-pims\pdf")
)
$Carpeta = (Resolve-Path $Carpeta).Path
New-Item -ItemType Directory -Force $Pdf | Out-Null
$Pdf = (Resolve-Path $Pdf).Path
$tmp = Join-Path $env:TEMP ("pims_pdf_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force $tmp | Out-Null
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    Get-ChildItem $Carpeta -Filter *.docx | Where-Object { $_.Name -notlike '~$*' } | ForEach-Object {
        $copia = Join-Path $tmp $_.Name
        Copy-Item $_.FullName $copia
        "abriendo " + $_.Name
        $doc = $word.Documents.Open($copia, $false, $false, $false)
        foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
        $destino = Join-Path $Pdf ($_.BaseName + ".pdf")
        "  exportando"
        $doc.SaveAs2([string]$destino, 17)      # 17 = wdFormatPDF
        $doc.Close(0)
        "  PDF: " + $destino
    }
} finally {
    $word.Quit()
    Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
}
