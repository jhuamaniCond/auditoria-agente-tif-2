# Conocimiento y despliegue de AUDITA-PIMS

## 1. Base de conocimiento

| Archivo | Ubicación | Para qué lo usa el asistente |
|---|---|---|
| `SKILL.md` | `02-skill/evidencia-auditoria-pims/` | Procedimiento de 6 pasos y reglas duras |
| `controles_27701.json` | `02-skill/.../references/` | Qué controles existen, qué evidencia espera cada uno y cuántas |
| `criterios_evidencia.md` | `02-skill/.../references/` | Pertinencia, suficiencia, fiabilidad, vigencia; clasificación de hallazgos |
| `plantilla_hallazgo.md` | `02-skill/.../assets/` | Formato obligatorio de cada hallazgo |
| `glosario_pims.md` | `03-asistente/` | Vocabulario común con el usuario |
| `evidencia.py` | `02-skill/.../scripts/` | Herramienta: registrar, verificar, cobertura, listar |

No se carga el texto de la norma ISO/IEC 27701:2025 porque es material con
derechos de autor; el catálogo resume solo lo necesario para auditar. Si el
grupo dispone de la norma licenciada, puede añadirse como conocimiento privado.

## 2. Opción A — Claude Code (skill + herramienta ejecutable) — recomendada

Es la única opción en la que el asistente ejecuta `evidencia.py` por sí mismo.

```bash
# en la carpeta del proyecto donde se auditará
mkdir -p .claude/skills
cp -r "02-skill/evidencia-auditoria-pims" .claude/skills/
```

Claude Code lee la `description` del SKILL.md y activa la skill cuando el
usuario pide algo como "prepara la auditoría interna del PIMS". La identidad se
fija copiando `instrucciones_sistema.md` en el `CLAUDE.md` del proyecto.

## 3. Opción B — Claude Project (claude.ai)

1. Crear un proyecto "AUDITA-PIMS".
2. Pegar `instrucciones_sistema.md` en *Project instructions*.
3. Subir como *Project knowledge*: SKILL.md, controles_27701.json,
   criterios_evidencia.md, plantilla_hallazgo.md, glosario_pims.md y evidencia.py.
4. Si la cuenta tiene habilitadas las Skills, subir la carpeta
   `evidencia-auditoria-pims` comprimida en *Settings → Capabilities → Skills*.
   Si no, el asistente pide al usuario ejecutar el script y pegar la salida.

## 4. Opción C — Gem de Gemini / GPT personalizado

Mismo contenido: instrucciones en el campo de instrucciones, los cinco archivos
como conocimiento. Con intérprete de código activado puede ejecutar
`evidencia.py` sobre archivos subidos a la conversación, pero el expediente no
persiste entre conversaciones: hay que descargarlo al final de cada sesión.

## 5. Requisitos

- Python 3.8 o superior (solo biblioteca estándar).
- El script no usa claves de API ni servicios externos: el expediente es una
  carpeta local.
- **Ojo:** en las opciones A, B y C el modelo corre en la nube. Lo que el
  asistente lee (el contenido de las evidencias) se envía al proveedor del
  modelo. Por eso conviene archivar evidencias seudonimizadas. Para que nada
  salga de la organización hay que usar un modelo local (Ollama + Qwen/Llama)
  conectado al script; eso es parte del Entregable 2.
