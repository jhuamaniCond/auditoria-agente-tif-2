# Repartición: Exposición del Entregable 1 — Grupo 6 (Agente de Evidencia y Auditoría, PIMS ISO 27701:2025)

Cada integrante explica sus carpetas/archivos y la parte de la interfaz que se apoya en ellos, y hace su propia demo en vivo de esa parte.

Integrante1:
-hacer la explicación de `01-de-prompt-a-skill/` (cómo la tarea manual de recolectar evidencia se convirtió en un proceso reutilizable)
-hacer la explicación de `02-skill/evidencia-auditoria-pims/`: `SKILL.md` (activación y pasos), `scripts/evidencia.py` (registro con SHA-256 y cadena de custodia), `references/` (controles_27701.json, criterios_evidencia.md) y `assets/` (plantilla de hallazgo y demo con su salida)
-hacer la explicación y demo de la pestaña **Expediente** de la interfaz: tabla "Evidencias registradas", formulario "Registrar evidencia" → "Registrar con hash" y botón "Verificar integridad"

Integrante2:
-hacer la explicación de `03-asistente/`: identidad e `instrucciones_sistema.md`, `glosario_pims.md`, `conocimiento_y_despliegue.md`
-hacer la explicación de las pruebas del asistente: `casos_prueba.md`, `pruebas/correr_casos.py` y `pruebas/resultados/` (CP-01 a CP-10 y resumen: cuáles pasan, cuál tiene observación y cuál no pasa y por qué)
-hacer la explicación de la parte de chat de `04-aplicacion/asistente.py` (cómo arma la respuesta con el conocimiento recuperado)
-hacer la explicación y demo de la pestaña **Asistente** de la interfaz: preguntas sugeridas y chat libre con respuestas citadas

Integrante3:
-hacer la explicación de la estructura web de `04-aplicacion/`: `app.py` (rutas Flask `/api/...`), `proyectos.py` (multiproyecto, cabecera `X-Proyecto`), `evidencia_api.py`, `cargar_demo.py`, `requirements.txt`, `templates/index.html` y `static/` (app.js, estilos.css)
-hacer la explicación de `04-aplicacion/datos/proyectos/clindata/` (proyecto.json, expediente con archivos EV-xxxx, registro_evidencias.json, cadena_custodia.log, soa.csv) y de cómo se instala y ejecuta según `README.md`
-hacer la explicación y demo de la barra superior y navegación de la interfaz: selector de proyecto, "+ Nuevo proyecto" y pestañas
-hacer la explicación y demo de la pestaña **Cobertura** de la interfaz: "Calcular", matriz de cobertura por control (estados Cubierto/Parcial/Sin evidencia) y visor de evidencias

Integrante4:
-hacer la explicación de la capa de IA local de `04-aplicacion/`: `llm_local.py` (Ollama, qwen2.5:7b), `rag.py` (FAISS + nomic-embed-text) y los índices de `datos/` (indice_conocimiento.*, indice_evidencias.*)
-hacer la explicación de la norma como fuente: `ISOS/` (PDF escaneado y texto), `extraer_norma.py` (OCR) y `norma.py` (partición por secciones A.x ↔ B.x)
-hacer la explicación de `revisiones.py` y de las funciones de pertinencia y hallazgo de `asistente.py` (veredicto con citas verificadas, el auditor acepta o rechaza, solo degrada Cubierto→Parcial)
-hacer la explicación y demo de las funciones de IA en la interfaz: "Analizar con IA local" al registrar evidencia, "Evaluar pertinencia con IA" (progreso y aceptar/rechazar), panel "Hallazgo preliminar" y clic en la referencia de un control para ver el texto de la norma
