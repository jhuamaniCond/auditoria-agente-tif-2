# Conocimiento y despliegue de AUDITA-PIMS

## 1. Base de conocimiento (RAG local)

El asistente no recibe la base de conocimiento completa en cada consulta. La
aplicación la divide en fragmentos, los convierte en vectores con el modelo
local de embeddings `nomic-embed-text` y los guarda en un índice **FAISS**
(`04-aplicacion/datos/indice.faiss`). En cada pregunta recupera los 6
fragmentos más parecidos por similitud coseno y se los entrega al modelo en el
bloque CONTEXTO, junto con el estado del expediente calculado por `evidencia.py`.

| Fuente indexada | Fragmentos | Para qué la usa el asistente |
|---|---|---|
| `controles_27701.json` | 1 por control (33) | Qué exige cada control, qué evidencia espera, cuántas |
| `criterios_evidencia.md` | por sección | Pertinencia, suficiencia, vigencia; clasificación de hallazgos |
| `plantilla_hallazgo.md` | 1 | Formato obligatorio del hallazgo |
| `SKILL.md` | por sección | Reglas no negociables y pasos |
| `glosario_pims.md` | por sección | Vocabulario: PII, SoA, RoPA, DPIA, ARCO, HITL |
| Norma ISO/IEC 27701:2025 (`ISOS/texto/`) | 238, por cláusula, control del Anexo A y guía del Anexo B | Criterio de auditoría: qué exige exactamente cada requisito, con referencia y página |
| Evidencias del expediente | por párrafos, con su ID | Leer qué dice cada evidencia al valorar o redactar |

### La norma como fuente de conocimiento

El PDF de la norma está en `ISOS/pdf/`. Es un escaneo sin capa de texto, así
que `04-aplicacion/extraer_norma.py` lo convierte una sola vez con el OCR que
trae Windows (Windows.Media.Ocr, sin instalar Tesseract) en
`ISOS/texto/ISO 27701-2025.md`: introducción, cláusulas 1-10, los 78 controles
del Anexo A (31 + 18 + 29, reconstruidos de las tablas) y su guía del Anexo B.
Los Anexos C-F son tablas de correspondencia y no se incluyen.
`04-aplicacion/norma.py` separa ese texto por secciones y relaciona cada control
del catálogo con su requisito (cláusula o A.x) y su guía (B.x).

La norma está en inglés y las preguntas llegan en español, y
`nomic-embed-text` cruza mal de idioma. Por eso cada fragmento de la norma
lleva también el título en español del catálogo, y el chat busca en la norma
dos veces: con la pregunta original y con su traducción al inglés hecha por el
modelo local (unos 2-3 s más por pregunta).

Dónde la usa el asistente:

- **Chat**: además de los 5 fragmentos más parecidos de toda la base, recibe
  hasta 6 de la norma; si la pregunta nombra un control o una cláusula
  (p. ej. `A.3.11`), se adjunta su requisito y su guía. Cita así:
  `[ISO 27701-2025 §A.3.11 (p. 25)]`.
- **Revisión de pertinencia**: el modelo compara las evidencias con el
  requisito exacto del control (lo que dice *shall*), no solo con la evidencia
  esperada del catálogo.
- **Hallazgo**: el campo *Criterio* se redacta a partir del requisito de la
  norma, con referencia y página.
- **Interfaz**: en la pestaña Cobertura, al pulsar la referencia de un control
  se abre el texto de la norma (requisito + guía).

Si se añade otra norma, basta con dejar su PDF en `ISOS/pdf/` y volver a
ejecutar `python extraer_norma.py` (las páginas de cada parte están definidas
al inicio del script para ISO/IEC 27701:2025).

La **revisión de pertinencia** (botón *Evaluar pertinencia con IA*) no usa
fragmentos sueltos: entrega al modelo el texto completo de las evidencias del
control (hasta 10 000 caracteres en total; si un documento es más largo se
avisa de que solo se leyó el inicio), el requisito y la guía del control en
ISO/IEC 27701:2025 (hasta 3 000 caracteres), la evidencia esperada del catálogo
y la sección 1 de `criterios_evidencia.md`. Las propuestas y las decisiones del
auditor se guardan en `datos/expediente/revisiones_pertinencia.json`.

El índice se reconstruye solo si cambia alguna fuente (se compara una huella
SHA-256 de todo lo indexado); las evidencias nuevas se añaden al registrarlas.

La norma está protegida por derechos de autor: el PDF y su texto extraído se
usan solo dentro de la máquina del auditor (nada se envía fuera) y no deben
publicarse en un repositorio público.

## 2. Modelos locales (Ollama)

| Modelo | Tamaño | Función | Por qué este |
|---|---|---|---|
| `nomic-embed-text` | 274 MB | Embeddings del RAG | Ligero, multilingüe, ventana de 2 048 tokens, distingue documento/consulta |
| `qwen2.5:7b` (Q4_K_M) | 4,7 GB | Redactar respuestas, clasificar, hallazgos | Buen español, sigue instrucciones y produce JSON; cabe en una GPU de 8 GB |

Probado en un portátil con RTX 4060 (8 GB) y 16 GB de RAM: unos 24 tokens/s;
una respuesta del chat tarda entre 6 y 14 s y un hallazgo unos 12 s. Con menos
memoria se puede usar `qwen2.5:3b` cambiando la variable `AUDITA_MODELO_CHAT`.

## 3. Instalación

```bash
# 1. Ollama (https://ollama.com) y los dos modelos
winget install Ollama.Ollama          # o el instalador de la web
ollama pull nomic-embed-text
ollama pull qwen2.5:7b

# 2. Dependencias de Python
cd 04-aplicacion
pip install -r requirements.txt       # flask, faiss-cpu, numpy

# 3. Texto de la norma (solo si cambia el PDF de ISOS/pdf; ya viene generado)
pip install pymupdf
python extraer_norma.py               # -> ISOS/texto/ISO 27701-2025.md

# 4. (Opcional) cargar el caso de estudio ClinData S.A.C.
python cargar_demo.py

# 5. Arrancar
python app.py                         # http://127.0.0.1:5000
```

La primera vez construye el índice FAISS (unos segundos). El servidor escucha
solo en `127.0.0.1`: no queda expuesto a la red.

## 4. Privacidad del despliegue

Todo se ejecuta en la máquina del auditor: el servidor Flask, los dos modelos y
el índice. Ninguna evidencia ni pregunta sale a un servicio externo, lo que es
coherente con un sistema que gestiona datos personales.

## 5. Uso de la skill fuera de la aplicación

La carpeta `02-skill/evidencia-auditoria-pims` sigue el formato de Agent Skills
(SKILL.md con encabezado YAML + scripts + referencias), así que también puede
copiarse en `.claude/skills/` y usarse desde Claude Code con el mismo script.
