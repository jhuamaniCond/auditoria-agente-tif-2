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
| Evidencias del expediente | por párrafos, con su ID | Leer qué dice cada evidencia al valorar o redactar |

El índice se reconstruye solo si cambia alguna fuente (se compara una huella
SHA-256 de todo lo indexado); las evidencias nuevas se añaden al registrarlas.

No se indexa el texto de la norma ISO/IEC 27701:2025 por estar protegido por
derechos de autor; el catálogo resume lo necesario para auditar.

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

# 3. (Opcional) cargar el caso de estudio ClinData S.A.C.
python cargar_demo.py

# 4. Arrancar
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
