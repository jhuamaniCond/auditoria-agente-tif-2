# TIF Auditoría de Sistemas — Entregable 1 — Grupo 6: Agente de Evidencia y Auditoría

Resultado: la **skill funcional especializada** `evidencia-auditoria-pims` y el
asistente **AUDITA-PIMS**, una aplicación web local que da soporte al PIMS
basado en ISO/IEC 27701:2025.

**Tecnologías:** Python · Flask · HTML · CSS · JavaScript puro · FAISS ·
modelo local de embeddings (`nomic-embed-text`) · LLM local (`qwen2.5:7b`)
servidos con Ollama. Todo se ejecuta en la máquina del auditor.

| Tarea del TIF | Dónde está |
|---|---|
| De Prompt a Skill — transformar la tarea en un proceso reutilizable | `01-de-prompt-a-skill/de_prompt_a_skill.md` |
| Creación de Skill — activación, estructura y pasos | `02-skill/evidencia-auditoria-pims/` (empezar por `SKILL.md`) |
| Construcción de Asistente — identidad, instrucciones y conocimiento | `03-asistente/` (identidad e instrucciones, glosario, RAG, casos de prueba) |
| Asistente funcionando (aplicación web) | `04-aplicacion/` |
| Informe | `informe/Informe_Entregable_1.docx` (se regenera con `python informe/generar_informe.py`) |

## Puesta en marcha

```bash
# Modelos locales (una vez)
ollama pull nomic-embed-text
ollama pull qwen2.5:7b

# Aplicación
cd 04-aplicacion
pip install -r requirements.txt
python cargar_demo.py        # opcional: caso de estudio ClinData S.A.C.
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
