# TIF Auditoría de Sistemas — Entregable 1 — Grupo 6: Agente de Evidencia y Auditoría

Resultado: **skill funcional especializada** `evidencia-auditoria-pims` y el
asistente **AUDITA-PIMS**, que da soporte al PIMS basado en ISO/IEC 27701:2025.

| Tarea del TIF | Dónde está |
|---|---|
| De Prompt a Skill — transformar la tarea en un proceso reutilizable | `01-de-prompt-a-skill/de_prompt_a_skill.md` |
| Creación de Skill — activación, estructura y pasos | `02-skill/evidencia-auditoria-pims/` (empezar por `SKILL.md`) |
| Construcción de Asistente — identidad, instrucciones y conocimiento | `03-asistente/` |
| Informe | `informe/Informe_Entregable_1.docx` (se regenera con `python informe/generar_informe.py`) |

## Probar la skill en 10 segundos

```bash
cd 02-skill/evidencia-auditoria-pims/assets/demo
python ejecutar_demo.py
```

Registra 8 evidencias de una clínica ficticia, altera una a propósito, detecta
la alteración y genera `salida/informe_cobertura.md`. Los hallazgos que redacta
el asistente sobre ese resultado están en `salida/hallazgos_preliminares.md`.

Requisito: Python 3.8+ (solo biblioteca estándar). Para el informe: `pip install python-docx`.

## Pendiente antes de entregar (marcado en rojo en el informe)

- Figuras 1 y 2: `python informe/figuras/dibujar_figuras.py` (requiere matplotlib).
- Casos de prueba: `bash 03-asistente/pruebas/correr_casos.sh` (usa tu cuenta
  de Claude); anotar Pasa / No pasa en `generar_informe.py`, sección 8.4.
- Figura 4: captura del asistente desplegado (pasos junto a la figura).
- Luego regenerar: `python informe/generar_informe.py`.
