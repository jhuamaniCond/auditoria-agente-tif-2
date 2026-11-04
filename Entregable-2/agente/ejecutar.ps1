<#
.SYNOPSIS
  Levanta todo lo necesario para usar el Agente de Evidencia y Auditoria (Grupo 6).

.DESCRIPTION
  1. Comprueba Python y las dependencias (las instala si faltan).
  2. Arranca Docker Desktop si esta apagado y levanta PostgreSQL + pgAdmin (BD/docker-compose.yml).
  3. Aplica el esquema, carga el catalogo y migra los datos de la UNSA si aun no estan en la BD.
  4. Arranca Ollama y prepara los modelos:
       - nomic-embed-text (embeddings): lo descarga si falta.
       - qwen (chat): si hay un solo modelo qwen lo usa; si hay varios pregunta cual;
         si no hay ninguno descarga qwen2.5:3b.
  5. Inicia la web (http://127.0.0.1:5000/agente) y abre en el navegador la web y
     pgAdmin (http://localhost:5050) para ver las tablas de la BD.
  Ctrl+C detiene la web. Los contenedores siguen activos (detenerlos: docker compose stop en BD/).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\ejecutar.ps1
  powershell -ExecutionPolicy Bypass -File .\ejecutar.ps1 -Puerto 5050 -SinNavegador
  powershell -ExecutionPolicy Bypass -File .\ejecutar.ps1 -SoloPreparar
#>
param(
    [int]$Puerto = 5000,
    [switch]$SinNavegador,   # no abrir el navegador (ni la web ni pgAdmin)
    [switch]$SinIA,          # no arrancar Ollama (la web funciona; las funciones con IA no)
    [switch]$SoloPreparar    # deja todo listo pero no inicia la web
)

# Los comandos nativos (docker, ollama, pip) escriben avisos en stderr: no deben cortar el script.
$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"

$Agente = $PSScriptRoot
$Entregable2 = Split-Path $Agente -Parent
$Repo = Split-Path $Entregable2 -Parent
$BD = Join-Path $Repo "BD"
$Contenedor = "pims_g6_postgres"
$OllamaUrl = if ($env:OLLAMA_URL) { $env:OLLAMA_URL } else { "http://localhost:11434" }

function Paso($texto)  { Write-Host ""; Write-Host "==> $texto" -ForegroundColor Cyan }
function Bien($texto)  { Write-Host "    [ok] $texto" -ForegroundColor Green }
function Aviso($texto) { Write-Host "    [!]  $texto" -ForegroundColor Yellow }
function Detener($texto) {
    Write-Host ""
    Write-Host "ERROR: $texto" -ForegroundColor Red
    exit 1
}

function Esperar($descripcion, $segundos, [scriptblock]$condicion) {
    $limite = (Get-Date).AddSeconds($segundos)
    while ((Get-Date) -lt $limite) {
        if (& $condicion) { return $true }
        Start-Sleep -Seconds 2
    }
    Aviso "Tiempo agotado esperando: $descripcion"
    return $false
}

function Consultar-BD($sql) {
    # Devuelve la primera celda del resultado, o $null si la consulta falla.
    $salida = & docker exec $Contenedor psql -U agente -d pims_auditoria -Atc $sql 2>$null
    if ($LASTEXITCODE -ne 0 -or $null -eq $salida) { return $null }
    return ([string]($salida | Select-Object -First 1)).Trim()
}

function Web-Responde($url) {
    try {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3
        return $r.StatusCode -eq 200
    } catch { return $false }
}

function Ollama-Responde {
    try { $null = Invoke-RestMethod -Uri "$OllamaUrl/api/tags" -TimeoutSec 3; return $true }
    catch { return $false }
}

function Modelos-Ollama {
    try { return @((Invoke-RestMethod -Uri "$OllamaUrl/api/tags" -TimeoutSec 5).models | ForEach-Object { $_.name }) }
    catch { return @() }
}

Write-Host "Agente de Evidencia y Auditoria - PIMS ISO/IEC 27701:2025 (Grupo 6)" -ForegroundColor White

# ------------------------------------------------------------------ 1. Python
Paso "Python y dependencias"
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { Detener "No se encontro 'python'. Instale Python 3.10 o superior y vuelva a ejecutar." }
$version = & python -c "import sys; print('%d.%d' % sys.version_info[:2])"
if ([version]$version -lt [version]"3.10") { Detener "Se necesita Python 3.10 o superior (encontrado $version)." }
Bien "Python $version"

& python -c "import flask, numpy, faiss, pypdf, requests, langgraph, mcp, psycopg, psycopg_pool, openpyxl, langgraph.checkpoint.postgres" 2>$null
if ($LASTEXITCODE -ne 0) {
    Aviso "Faltan dependencias: instalando Entregable-2/requirements.txt (puede tardar unos minutos)..."
    & python -m pip install -r (Join-Path $Entregable2 "requirements.txt")
    & python -c "import flask, numpy, faiss, pypdf, requests, langgraph, mcp, psycopg, psycopg_pool, openpyxl, langgraph.checkpoint.postgres" 2>$null
    if ($LASTEXITCODE -ne 0) { Detener "No se pudieron instalar las dependencias de Python." }
}
Bien "Dependencias instaladas"

# ------------------------------------------------------------------ 2. Docker
Paso "Docker y contenedores (PostgreSQL + pgAdmin)"
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Detener "No se encontro Docker. Instale Docker Desktop: https://www.docker.com/products/docker-desktop/"
}
$null = & docker info 2>$null
if ($LASTEXITCODE -ne 0) {
    $candidatos = @(
        (Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\Docker Desktop.exe"),
        (Join-Path $env:LOCALAPPDATA "Docker\Docker Desktop.exe")
    )
    $exe = $candidatos | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $exe) { Detener "Docker esta instalado pero apagado y no encontre Docker Desktop. Abralo a mano y reintente." }
    Aviso "Docker esta apagado: iniciando Docker Desktop..."
    Start-Process -FilePath $exe | Out-Null
    $listo = Esperar "Docker Desktop" 180 { $null = & docker info 2>$null; $LASTEXITCODE -eq 0 }
    if (-not $listo) { Detener "Docker Desktop no termino de arrancar." }
}
Bien "Docker activo"

Push-Location $BD
& docker compose up -d
$codigo = $LASTEXITCODE
Pop-Location
if ($codigo -ne 0) { Detener "docker compose up fallo (revise que el puerto 5432 o 5050 no este ocupado)." }
$sano = Esperar "PostgreSQL" 120 { (& docker inspect -f "{{.State.Health.Status}}" $Contenedor 2>$null) -eq "healthy" }
if (-not $sano) { Detener "PostgreSQL no quedo listo. Revise: docker logs $Contenedor" }
Bien "PostgreSQL en localhost:5432 | pgAdmin en http://localhost:5050"

# ------------------------------------------------------------------ 3. BD: esquema, catalogo, migracion
Paso "Base de datos pims_auditoria"
$catalogo = Consultar-BD "SELECT count(*) FROM requisitos"
if ($null -eq $catalogo) {
    Aviso "No existe el esquema: aplicando BD/schema.sql..."
    & docker cp (Join-Path $BD "schema.sql") "${Contenedor}:/tmp/schema.sql"
    & docker exec $Contenedor psql -U agente -d pims_auditoria -v ON_ERROR_STOP=1 -q -f /tmp/schema.sql
    if ($LASTEXITCODE -ne 0) { Detener "No se pudo aplicar schema.sql." }
    $catalogo = "0"
}
Push-Location $BD
if ([int]$catalogo -eq 0) {
    Aviso "Catalogo vacio: ejecutando cargar_catalogo.py..."
    & python cargar_catalogo.py
    if ($LASTEXITCODE -ne 0) { Pop-Location; Detener "Fallo cargar_catalogo.py." }
} else {
    Bien "Catalogo cargado ($catalogo requisitos)"
}
$unsa = Consultar-BD "SELECT count(*) FROM proyectos WHERE id = 'unsa'"
if ([int]$unsa -eq 0) {
    Aviso "El proyecto 'unsa' no esta en la BD: ejecutando migrar_datos_agente.py..."
    & python migrar_datos_agente.py
    if ($LASTEXITCODE -ne 0) { Pop-Location; Detener "Fallo migrar_datos_agente.py." }
} else {
    $n = Consultar-BD "SELECT count(*) FROM evidencias WHERE proyecto = 'unsa'"
    Bien "Datos de la UNSA ya migrados ($n evidencias)"
}
Pop-Location

# ------------------------------------------------------------------ 4. Ollama y modelos
if ($SinIA) {
    Paso "Ollama omitido (-SinIA): las funciones con IA no estaran disponibles"
} else {
    Paso "Ollama y modelos locales"
    if (-not (Ollama-Responde)) {
        $ollama = Get-Command ollama -ErrorAction SilentlyContinue
        $exeOllama = if ($ollama) { $ollama.Source } else { Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe" }
        if (-not (Test-Path $exeOllama)) {
            Aviso "Ollama no esta instalado (https://ollama.com/download). La web funcionara sin IA."
            $SinIA = $true
        } else {
            Aviso "Ollama no responde: iniciando 'ollama serve'..."
            Start-Process -FilePath $exeOllama -ArgumentList "serve" -WindowStyle Hidden | Out-Null
            if (-not (Esperar "Ollama" 60 { Ollama-Responde })) {
                Aviso "Ollama no arranco. La web funcionara sin IA."
                $SinIA = $true
            }
        }
    }
}

if (-not $SinIA) {
    Bien "Ollama en $OllamaUrl"
    $modelos = Modelos-Ollama

    # Embeddings
    $embed = if ($env:AUDITA_MODELO_EMBEDDINGS) { $env:AUDITA_MODELO_EMBEDDINGS } else { "nomic-embed-text" }
    if (-not ($modelos | Where-Object { $_ -eq $embed -or $_ -eq "${embed}:latest" })) {
        Aviso "Descargando el modelo de embeddings $embed..."
        & ollama pull $embed
    }
    Bien "Embeddings: $embed"

    # Chat (qwen)
    $qwen = @($modelos | Where-Object { $_ -like "qwen*" } | Sort-Object)
    if ($env:AUDITA_MODELO_CHAT -and ($modelos -contains $env:AUDITA_MODELO_CHAT)) {
        $chat = $env:AUDITA_MODELO_CHAT
    } elseif ($qwen.Count -eq 0) {
        Aviso "No hay ningun modelo qwen: descargando qwen2.5:3b (unos 2 GB)..."
        & ollama pull qwen2.5:3b
        $chat = "qwen2.5:3b"
    } elseif ($qwen.Count -eq 1) {
        $chat = $qwen[0]
    } else {
        Write-Host "    Hay varios modelos qwen instalados:" -ForegroundColor White
        for ($i = 0; $i -lt $qwen.Count; $i++) { Write-Host ("      {0}) {1}" -f ($i + 1), $qwen[$i]) }
        do {
            $eleccion = Read-Host "    Cual quiere usar? (1-$($qwen.Count))"
            $num = 0
            $valido = [int]::TryParse($eleccion, [ref]$num) -and $num -ge 1 -and $num -le $qwen.Count
            if (-not $valido) { Aviso "Escriba un numero entre 1 y $($qwen.Count)." }
        } until ($valido)
        $chat = $qwen[$num - 1]
    }
    $env:AUDITA_MODELO_CHAT = $chat
    Bien "Chat: $chat"
}

# ------------------------------------------------------------------ 5. Web
$url = "http://127.0.0.1:$Puerto/agente"
$urlPgAdmin = "http://localhost:5050"

function Abrir-Navegador {
    # Web del agente y pgAdmin (ver las tablas de la BD), cada uno en su pestana
    Start-Process $url
    if (Web-Responde $urlPgAdmin) { Start-Process $urlPgAdmin }
    else { Aviso "pgAdmin aun no responde en $urlPgAdmin; abralo en unos segundos." }
}

if ($SoloPreparar) {
    Paso "Todo listo (-SoloPreparar). Para iniciar la web: python servidor_web.py en $Agente"
    exit 0
}

Paso "Web del agente"
if (Web-Responde $url) {
    Aviso "Ya hay una web respondiendo en $url (no se inicia otra)."
    if (-not $SinNavegador) { Abrir-Navegador }
    exit 0
}

$env:PORT = "$Puerto"
if (-not $env:AGENTE_CLAVE_HASH -and -not $env:AGENTE_CLAVE -and -not $env:AGENTE_LOGIN) {
    # En la PC local (solo 127.0.0.1) el login es opcional; en la VPS se define AGENTE_CLAVE_HASH.
    $env:AGENTE_LOGIN = "0"
    Aviso "Login desactivado en local (defina AGENTE_CLAVE o AGENTE_CLAVE_HASH para activarlo)."
}
$web =Start-Process -FilePath "python" -ArgumentList "servidor_web.py" -WorkingDirectory $Agente -NoNewWindow -PassThru
try {
    $lista = Esperar "la web" 240 { (Web-Responde $url) -or $web.HasExited }
    if ($web.HasExited) { Detener "La web se cerro al arrancar (vea los mensajes de arriba)." }
    if (-not $lista) { Detener "La web no respondio en $url." }
    Write-Host ""
    Write-Host "  Web del agente:  $url" -ForegroundColor Green
    Write-Host "  App AUDITA-PIMS: http://127.0.0.1:$Puerto/" -ForegroundColor Green
    Write-Host "  pgAdmin (BD):    $urlPgAdmin" -ForegroundColor Green
    Write-Host "  Ctrl+C para detener la web." -ForegroundColor Gray
    if (-not $SinNavegador) { Abrir-Navegador }
    Wait-Process -Id $web.Id
} finally {
    if (-not $web.HasExited) {
        Stop-Process -Id $web.Id -Force -ErrorAction SilentlyContinue
        Write-Host "Web detenida. Los contenedores siguen activos (docker compose stop en BD/ para apagarlos)."
    }
}
