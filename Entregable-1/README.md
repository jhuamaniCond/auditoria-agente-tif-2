# TIF Auditoría de Sistemas — Entregable 1 — Grupo 6: Agente de Evidencia y Auditoría

Resultado: la **skill funcional especializada** `evidencia-auditoria-pims` y el
asistente **AUDITA-PIMS**, una aplicación web local que da soporte al PIMS
basado en ISO/IEC 27701:2025.

En la pestaña **Cobertura**, la IA lee el contenido de las evidencias y propone
si cada control se cumple (*cumple / cumple parcialmente / no cumple*, con
justificación y citas). El auditor acepta o rechaza cada propuesta; solo una
propuesta aceptada baja un control de *Cubierto* a *Parcial*.

El criterio de auditoría es el **texto de ISO/IEC 27701:2025** que está en
`ISOS/`: el PDF (`ISOS/pdf/`) se convierte por OCR a `ISOS/texto/` y se indexa
en el RAG. El asistente lo cita con referencia y página al responder, evaluar
pertinencia y redactar el *Criterio* de los hallazgos; en la pestaña Cobertura,
al pulsar un control se abre su requisito (Anexo A o cláusula) y su guía (Anexo B).

Cada organización auditada es un **proyecto** (selector y botón «Nuevo
proyecto» en la cabecera) con su propio expediente, cobertura, revisiones y
chat; ClinData S.A.C. es el proyecto de ejemplo. Los datos están en
`04-aplicacion/datos/proyectos/<id>/`.

**Tecnologías:** Python · Flask · HTML · CSS · JavaScript puro · FAISS ·
modelo local de embeddings (`nomic-embed-text`) · LLM local (`qwen2.5:7b`)
servidos con Ollama. Todo se ejecuta en la máquina del auditor.

| Tarea del TIF | Dónde está |
|---|---|
| De Prompt a Skill — transformar la tarea en un proceso reutilizable | `01-de-prompt-a-skill/de_prompt_a_skill.md` |
| Creación de Skill — activación, estructura y pasos | `02-skill/evidencia-auditoria-pims/` (empezar por `SKILL.md`) |
| Construcción de Asistente — identidad, instrucciones y conocimiento | `03-asistente/` (identidad e instrucciones, glosario, RAG, casos de prueba) |
| Asistente funcionando (aplicación web) | `04-aplicacion/` |
| Norma ISO/IEC 27701:2025 (fuente de conocimiento) | `ISOS/pdf/` (original) y `ISOS/texto/` (texto por OCR, generado con `04-aplicacion/extraer_norma.py`) |
| Informe | `informe/Informe_Entregable_1.docx` (se regenera con `python informe/generar_informe.py`) |

## Puesta en marcha

```bash
# Modelos locales (una vez)
ollama pull nomic-embed-text
ollama pull qwen2.5:7b

# Aplicación
cd 04-aplicacion
pip install -r requirements.txt
python extraer_norma.py      # solo si cambia el PDF de ISOS/pdf (pide pymupdf; OCR de Windows)
python cargar_demo.py        # opcional: (re)carga el proyecto ClinData S.A.C.
python app.py                # http://127.0.0.1:5000
```

## Pruebas

```bash
# Parte determinista de la skill (sin IA): registra 8 evidencias, altera una,
# la detecta y genera la matriz de cobertura
cd 02-skill/evidencia-auditoria-pims/assets/demo && python ejecutar_demo.py

# Casos de prueba del asistente (con la aplicación en marcha)
python 03-asistente/pruebas/correr_casos.py
```

## Regenerar el informe

```bash
pip install python-docx matplotlib pillow
python informe/figuras/dibujar_figuras.py
python informe/generar_informe.py
```
