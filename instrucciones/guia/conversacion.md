Hablemos de IA agéntica e IA multiagéntica

Perfecto, hablemos. Es uno de los temas más interesantes ahora mismo, porque toca el paso de “modelos que responden” a “sistemas que actúan”.

**IA agéntica** es un paradigma en el que un modelo —normalmente un LLM— no solo genera texto, sino que tiene un objetivo, planifica, usa herramientas, toma decisiones, ejecuta acciones y aprende de la retroalimentación. La idea central es el bucle:

**percibir → razonar/planificar → actuar → observar → ajustar**

Un agente suele tener:
- **Objetivo**: “organiza este viaje”, “corrige este bug”, “investiga este mercado”.
- **Planificación**: descompone el problema en pasos.
- **Memoria**: a corto plazo (contexto) y largo plazo (base de datos, vectores, notas).
- **Herramientas**: APIs, navegador, código, correo, calendario, bases de datos.
- **Autonomía**: decide cuándo y cómo actuar, no solo responde a un prompt.
- **Reflexión**: evalúa su propio resultado y se corrige.

Ejemplo simple: un agente de viajes que busca vuelos, compara precios, revisa hoteles, reserva y, si cancelan un vuelo, replanifica.

**IA multiagéntica** es la extensión: varios agentes interactúan entre sí. Cada uno puede tener un rol, herramientas y objetivos distintos. Pueden cooperar, competir o coordinarse jerárquicamente.

Ejemplo típico:
- Agente investigador: busca información.
- Agente analista: extrae datos y patrones.
- Agente redactor: escribe el informe.
- Agente crítico: revisa, detecta errores y pide cambios.
- Agente coordinador: asigna tareas y decide cuándo terminar.

Ventajas de lo multiagéntico:
- **Especialización**: cada agente es mejor en su rol.
- **Paralelismo**: varias tareas a la vez.
- **Verificación cruzada**: un agente revisa a otro.
- **Escalabilidad modular**: añades agentes según necesidad.

Retos:
- **Coordinación**: ¿quién decide? ¿cómo evitan bucles?
- **Comunicación**: protocolos, formato, ambigüedad.
- **Coste**: más llamadas, más tokens, más latencia.
- **Errores en cascada**: si un agente falla, contamina a los demás.
- **Evaluación**: medir si el sistema mejora o solo se complica.
- **Seguridad**: permisos, acciones irreversibles, alineación.

Patrones comunes:
- **Orquestador-trabajador**: un coordinador reparte tareas.
- **Pipeline**: agentes en cadena, cada uno pasa el resultado al siguiente.
- **Debate**: dos o más agentes defienden posturas y un juez decide.
- **Reflexión**: el agente genera, critica y mejora su propia salida.
- **Enjambre**: muchos agentes simples con reglas locales.
- **Subasta/mercado**: los agentes pujan por tareas.

Frameworks populares: LangGraph, AutoGen, CrewAI, MetaGPT, Swarm, Semantic Kernel. Muchos permiten definir roles, herramientas, memoria y flujos.

Una idea clave: **más agentes no siempre es mejor**. Un solo agente con buenas herramientas y un buen bucle de reflexión puede superar a un sistema multiagéntico mal coordinado. Lo multiagéntico brilla cuando la tarea es divisible, requiere roles muy distintos, paralelismo o verificación independiente.

¿Qué te interesa más: arquitecturas, frameworks, casos de uso reales, cómo diseñar uno desde cero, o los límites y riesgos actuales?


¿Cuál es la arquitectura de un sistema multiagente (Multi Agent System)?

No existe **una única arquitectura** de sistema multiagente (MAS). Depende de si hablamos de MAS clásicos (agentes reactivos/deliberativos, FIPA, BDI) o de MAS modernos basados en LLM. Pero sí hay una **arquitectura de referencia** que se repite: agentes especializados, un mecanismo de coordinación, un canal de comunicación, memoria compartida, herramientas y un entorno.

## 1. Componentes básicos de un MAS

En un MAS clásico:

- **Agentes**: entidades autónomas con objetivos, estado interno y capacidades.
- **Entorno**: el mundo donde actúan (sensores, APIs, usuarios, otros sistemas).
- **Comunicación**: mensajes entre agentes (FIPA-ACL, pub/sub, colas, JSON-RPC).
- **Organización**: roles, normas, jerarquías, permisos.
- **Coordinación**: planificación, asignación de tareas, negociación, consenso.

En un MAS con LLM se añaden capas:

- **Orquestador/planificador**
- **Memoria** (corto y largo plazo, vectorial, compartida)
- **Herramientas** (RAG, navegador, código, bases de datos, APIs)
- **Observabilidad y seguridad**
- **Evaluación y control de costes**

## 2. Arquitectura de referencia por capas

```
[Usuario / Evento / API]
          |
[Interfaz de entrada/salida]
          |
[Orquestador / Planificador / Router]
          |
   +------+------+------+
   |      |      |      |
[Agente][Agente][Agente][Agente]
   |      |      |      |
   +------+------+------+
          |
[Bus de comunicación / Protocolos]
          |
[Memoria compartida + Memoria individual]
          |
[Herramientas: APIs, RAG, Código, Navegador, DB]
          |
[Entorno externo: sistemas, sensores, actuadores]
          |
[Observabilidad, Seguridad, Gobernanza, Costes]
```

### Capas clave

1. **Interacción**: recibe el objetivo del usuario o de otro sistema.
2. **Orquestación**: descompone el objetivo, decide qué agente actúa, en qué orden y con qué herramientas.
3. **Agentes**: cada uno tiene rol, prompt, herramientas, memoria y criterios de éxito.
4. **Comunicación**: mensajes directos, pizarra compartida, pub/sub o protocolos como MCP/A2A.
5. **Memoria**:
   - Corto plazo: contexto de la conversación.
   - Largo plazo: base vectorial, documentos, historial.
   - Compartida: hechos, decisiones, estado global.
6. **Herramientas/Acciones**: lo que permite pasar de “decir” a “hacer”.
7. **Entorno**: el mundo real o simulado donde las acciones tienen efecto.
8. **Gobernanza**: trazas, permisos, límites de iteraciones, presupuestos, auditoría.

## 3. Topologías de coordinación

| Topología | Cómo funciona | Ventajas | Riesgos |
|---|---|---|---|
| **Centralizada** | Un orquestador asigna tareas a agentes trabajadores. | Control, trazabilidad, fácil de depurar. | Cuello de botella, punto único de fallo. |
| **Jerárquica** | Coordinadores por capas; cada uno gestiona subagentes. | Escalable, modular. | Complejidad, latencia. |
| **Descentralizada / P2P** | Los agentes negocian directamente. | Resiliencia, autonomía. | Difícil coordinación, bucles. |
| **Pipeline** | Agentes en cadena: A → B → C. | Simple, predecible. | Rígido, errores en cascada. |
| **Blackboard / Pizarra** | Todos leen/escriben en un espacio compartido. | Bueno para problemas abiertos. | Condiciones de carrera, ruido. |
| **Enjambre** | Muchos agentes simples con reglas locales. | Emergencia, paralelismo. | Poco control, difícil evaluar. |
| **Federada** | Varios MAS autónomos interoperan. | Escala organizacional. | Interoperabilidad, confianza. |

## 4. Mecanismos internos de coordinación

- **Planificación**: descomposición de tareas (Plan-and-Execute, ReAct, HTN).
- **Asignación**: subasta, Contract Net, roles fijos, colas de tareas.
- **Negociación**: votación, consenso, debate, crítico-juez.
- **Reflexión**: el agente genera, se critica y mejora.
- **Verificación cruzada**: un agente revisa el trabajo de otro.
- **Protocolos**: MCP para herramientas, A2A para agentes, FIPA-ACL en MAS clásicos.

## 5. Ejemplo típico: investigación y redacción

1. Usuario pide un informe.
2. Orquestador planifica: buscar → analizar → redactar → revisar.
3. Agente buscador usa navegador/RAG.
4. Agente analista extrae datos y patrones.
5. Agente redactor escribe el borrador.
6. Agente crítico detecta errores y pide cambios.
7. Orquestador consolida y devuelve el resultado.
8. Memoria compartida guarda fuentes, decisiones y versiones.

## 6. Principios de diseño

- **Empieza simple**: un solo agente con buenas herramientas suele bastar.
- **Añade agentes solo si hay** especialización real, paralelismo o verificación independiente.
- **Define contratos claros**: entrada, salida, herramientas, límites.
- **Controla iteraciones y costes**: máximo de rondas, presupuesto de tokens.
- **Traza todo**: logs, estados, decisiones, herramientas usadas.
- **Seguridad**: permisos mínimos, acciones irreversibles con confirmación humana.
- **Evalúa**: métricas de éxito, calidad, latencia, coste y alucinación.

En resumen: la arquitectura de un MAS es **agentes + entorno + comunicación + coordinación + organización**, y en la versión moderna se implementa como **capas de orquestación, agentes especializados, memoria compartida, herramientas y gobernanza**. La clave no es cuántos agentes hay, sino cómo se coordinan y cómo se controla el bucle.


Y n8n ¿Es un orquestador? , ¿Con cuáles otros compite?

Sí, **n8n es un orquestador**, pero con un matiz importante: es un **orquestador de flujos de trabajo (workflow orchestrator)** con capacidades nativas de IA, no un framework de agentes puro como LangGraph o AutoGen. Su función principal es coordinar pasos, integrar APIs y, en los últimos años, enrutar tareas hacia agentes de IA dentro de un flujo más amplio.

### 🧩 ¿Por qué n8n es un orquestador?

n8n permite construir flujos donde un nodo raíz (un agente principal) puede **supervisar y delegar trabajo a otros agentes especializados** usando el nodo *AI Agent Tool*. Esto habilita la orquestación multiagéntica sin la complejidad de gestionar sub-flujos manualmente. Además, su modelo de ejecución basado en nodos, lógica condicional (IF, Switch, Loop) y conexión con cientos de servicios lo convierte en una capa de orquestación que envuelve a los agentes, no en el agente en sí.

La distinción clave la resumen bien desde el ecosistema: *"Make / n8n no intentan ser frameworks de agentes; orquestan todo lo que rodea a los agentes"*. Es decir, n8n brilla cuando necesitas **conectar agentes con sistemas reales** (CRM, bases de datos, correo, APIs) dentro de un proceso de negocio.

### ⚔️ ¿Con quiénes compite n8n?

Sus competidores se dividen en varias categorías según el enfoque. Esta tabla comparativa rápida puede ayudarte a ubicarlos:

| Categoría | Herramientas principales | Enfoque principal |
|---|---|---|
| **Automatización no-code / low-code** | Zapier, Make, Power Automate | Conectar apps SaaS con mínima fricción técnica |
| **Automatización open-source** | Activepieces, Windmill, Node-RED | Self-hosting, control de datos, flexibilidad |
| **Frameworks de orquestación de agentes** | LangGraph, AutoGen, CrewAI, Semantic Kernel | Construir y coordinar agentes a nivel de código |
| **Plataformas de desarrollo de agentes/LLM** | Dify, Coze, Langflow, Flowise | Crear aplicaciones de IA visualmente, a menudo con menos foco en integración empresarial |
| **Motores de workflow duraderos** | Temporal, Prefect, Dagster | Garantizar ejecución fiable y persistente de procesos críticos |

#### 🔹 Frente a las plataformas de automatización clásicas

- **Zapier**: Es el líder en integraciones (más de 9.000 apps) y facilidad de uso para perfiles no técnicos. n8n compite ofreciendo **self-hosting, control de datos y precios más predecibles** (cobro por ejecución completa en lugar de por paso).
- **Make**: Similar a Zapier pero con un constructor visual más potente. n8n se diferencia por su **mayor flexibilidad para inyectar código personalizado** y su modelo open-source.
- **Power Automate**: Su gran ventaja es la integración nativa con el ecosistema Microsoft (M365, Azure, Dynamics). n8n compite apelando a **equipos que quieren independencia del proveedor, control sobre los modelos de IA y capacidad de self-hosting**.

#### 🔹 Frente a las alternativas open-source

- **Activepieces**: Es quizás el competidor open-source más directo. Ofrece una experiencia similar pero con una **licencia más permisiva (MIT)** y un constructor más amigable para no técnicos.
- **Windmill**: Se posiciona para equipos que prefieren **escribir código (Python/TypeScript) en lugar de arrastrar nodos**, con mayor fiabilidad y capacidades de reintento.
- **Node-RED**: Nacido del mundo IoT, es excelente para **enrutamiento de eventos de bajo nivel y hardware**. n8n está más orientado a **flujos de negocio y APIs SaaS**.

#### 🔹 Frente a los frameworks de agentes puros

Aquí la comparación es diferente, porque no compiten directamente, sino que **se complementan**. Los frameworks como **LangGraph, AutoGen, CrewAI o Semantic Kernel** están diseñados para construir la lógica interna de los agentes (planificación, memoria, diálogo). n8n, en cambio, **orquesta el entorno** donde esos agentes operan: los activa, les pasa datos, recoge sus resultados y los conecta con el resto del sistema. De hecho, un patrón común en producción es usar un framework de agentes *dentro* de un motor de workflow como n8n o Temporal.

#### 🔹 Frente a plataformas como Dify o Coze

- **Dify**: Es una plataforma low-code **enfocada en construir y desplegar aplicaciones LLM** (RAG, chatbots, agentes) de forma rápida. n8n es más fuerte en **automatización e integración de sistemas empresariales**, aunque Dify puede ser suficiente si tu objetivo es solo empaquetar una capacidad de IA como API.
- **Coze**: Plataforma cerrada de ByteDance, optimizada para **crear bots y asistentes rápidamente** para canales como Telegram o Discord. n8n ofrece **mucho más control, personalización y capacidad de integración profunda**.

En resumen, n8n no compite de tú a tú con los frameworks de agentes, sino que **compensa sus carencias naturales** (memoria a largo plazo, orquestación multiagéntica compleja) actuando como la capa de pegamento que conecta agentes, APIs y sistemas de negocio en un flujo automatizado.

¿Te gustaría profundizar en cómo encajaría n8n en una arquitectura multiagéntica concreta, o prefieres que exploremos uno de estos competidores en detalle?

¿Qué es y que hacen Ollama, RAG y MCP?

Ollama, RAG y MCP son tres tecnologías que, aunque distintas, se complementan muy bien en el ecosistema de la IA moderna. Podría decirse que **Ollama** es el motor, **RAG** es la forma de darle conocimiento actualizado y **MCP** es el conector universal hacia el mundo exterior.

### 🦙 Ollama: Tu motor de IA local

Ollama es una aplicación que te permite **ejecutar modelos de lenguaje grandes (LLMs) directamente en tu ordenador**, sin depender de servicios en la nube como OpenAI o Anthropic. Está disponible para Windows, macOS y Linux, y es software libre.

¿Qué hace exactamente?
- **Descarga y gestiona modelos**: Desde su biblioteca puedes obtener modelos como Llama, DeepSeek, Mistral, Gemma o Qwen con un simple comando.
- **Ejecución local y privada**: Todo el procesamiento ocurre en tu máquina, por lo que tus datos **no se envían a ningún servidor externo**. Puedes usarlo incluso sin conexión a internet.
- **Interfaz de terminal y API**: Se maneja desde la línea de comandos, pero también ofrece una API y librerías para Python y JavaScript, lo que permite integrarlo en tus propias aplicaciones.

En resumen, Ollama es la puerta de entrada para tener IA generativa de forma **local, privada y gratuita**, ideal para desarrollo, experimentación o proyectos donde la confidencialidad es clave.

### 📚 RAG: La biblioteca externa del modelo

RAG (Retrieval-Augmented Generation) es una técnica que **conecta un LLM con una base de conocimiento externa** para que pueda responder con información actualizada, específica o propietaria sin necesidad de reentrenar el modelo.

El problema que resuelve es doble: los modelos tienen un conocimiento "congelado" en su fecha de entrenamiento y, además, a veces "alucinan" (inventan) datos cuando no saben algo. RAG soluciona esto dándole al modelo una **"biblioteca de consulta"** antes de responder.

Su flujo de trabajo típico sigue estos pasos:
1. **Preparación**: Tus documentos (manuales, PDFs, bases de datos) se convierten en *embeddings* (representaciones numéricas) y se almacenan en una base de datos vectorial.
2. **Consulta**: El usuario hace una pregunta.
3. **Recuperación**: El sistema busca en esa base vectorial los fragmentos más relevantes para la pregunta.
4. **Generación aumentada**: Esos fragmentos se añaden como contexto al *prompt* original, y el LLM genera una respuesta basada en esa información real y verificable.

Gracias a RAG, un modelo de propósito general puede responder con precisión sobre **tus datos privados o información de última hora**, y además cada respuesta puede rastrearse hasta su fuente.

### 🔌 MCP: El conector universal

MCP (Model Context Protocol) es un **protocolo abierto** creado por Anthropic en noviembre de 2024 que **estandariza la forma en que las aplicaciones de IA se conectan con herramientas y fuentes de datos externas**. La analogía más común es la de un **"USB-C para la IA"**: así como ese conector unificó los cables, MCP unifica las integraciones.

Antes de MCP, conectar un modelo con *N* herramientas requería programar *N* integraciones distintas (el llamado "problema M×N"). Con MCP, cada herramienta expone un **servidor MCP** que cualquier modelo compatible puede usar automáticamente.

Su arquitectura tiene tres piezas:
- **Host**: La aplicación de IA que necesita los datos (por ejemplo, Claude Desktop, Cursor o tu propio agente).
- **Cliente MCP**: El componente dentro del host que se conecta a los servidores.
- **Servidor MCP**: El servicio que expone una herramienta o fuente de datos (una API REST, una base de datos local, un calendario, etc.).

Gracias a MCP, un agente de IA puede **leer tus archivos, consultar tu base de datos, usar tu calendario o ejecutar acciones** en sistemas externos de forma estandarizada y segura. Es la pieza que permite que los agentes dejen de estar aislados y pasen a **actuar sobre el mundo real**.

---

En conjunto, estas tres tecnologías forman una pila muy potente: **Ollama** te da el modelo, **RAG** le da el conocimiento y **MCP** le da las manos para actuar. ¿Te gustaría que veamos cómo se integran las tres en un flujo de trabajo concreto?

Si

Perfecto. Vamos a montar un flujo concreto donde **Ollama + RAG + MCP** trabajan juntos. El ejemplo será un **asistente corporativo local** que responde preguntas sobre documentación interna y además ejecuta acciones en sistemas reales.

---

## Escenario: Asistente interno para una empresa

**Pregunta del usuario:**
> "¿Cuántos días de vacaciones me quedan y puedes agendarme una reunión con el equipo el viernes a las 10?"

Esta sola frase requiere:
- **RAG** → consultar la política de vacaciones en los documentos de la empresa.
- **MCP** → consultar la base de datos de RRHH y el calendario, y crear el evento.
- **Ollama** → entender la petición, orquestar las herramientas y redactar la respuesta.

---

## Arquitectura del sistema

```
┌─────────────────────────────────────────────────────────┐
│                    USUARIO                              │
│         "¿Cuántos días de vacaciones me quedan          │
│          y agenda reunión el viernes a las 10?"         │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              HOST (tu aplicación)                       │
│  ┌───────────────────────────────────────────────────┐  │
│  │         AGENTE PRINCIPAL (orquestador)            │  │
│  │         LLM: Ollama (Llama 3.1 / Qwen)            │  │
│  └───────┬───────────────────────────┬───────────────┘  │
│          │                           │                  │
│          ▼                           ▼                  │
│  ┌───────────────┐          ┌────────────────────┐      │
│  │  CLIENTE RAG  │          │  CLIENTE MCP       │      │
│  │  (retriever)  │          │  (varias conexiones)│     │
│  └───────┬───────┘          └─────────┬──────────┘      │
└──────────┼────────────────────────────┼─────────────────┘
           │                            │
           ▼                            ▼
┌─────────────────────┐    ┌─────────────────────────────┐
│ BASE VECTORIAL      │    │  SERVIDORES MCP             │
│ (Chroma, Qdrant,    │    │  ┌─────────────────────┐    │
│  pgvector, FAISS)   │    │  │ MCP RRHH (Postgres) │    │
│                     │    │  ├─────────────────────┤    │
│ - Política vacaciones│   │  │ MCP Calendario      │    │
│ - Manual empleado   │    │  │ (Google Calendar)   │    │
│ - Procedimientos    │    │  ├─────────────────────┤    │
│ - FAQs              │    │  │ MCP Correo (SMTP)   │    │
└─────────────────────┘    │  └─────────────────────┘    │
                           └─────────────────────────────┘
```

---

## Flujo paso a paso

### 1. El usuario envía la pregunta

La aplicación (host) recibe el texto y lo pasa al agente principal.

### 2. El agente (Ollama) planifica

El LLM local, ejecutándose vía Ollama, analiza la petición y decide que necesita:

- **Paso A**: Buscar en la documentación (RAG) → "política de vacaciones"
- **Paso B**: Consultar el saldo real del empleado (MCP → RRHH)
- **Paso C**: Consultar disponibilidad del equipo (MCP → Calendario)
- **Paso D**: Crear el evento (MCP → Calendario)
- **Paso E**: Redactar la respuesta final

Esto se hace con un patrón tipo **ReAct** o **function calling**: el modelo genera llamadas estructuradas a herramientas.

### 3. RAG recupera la política

El cliente RAG convierte la pregunta en un embedding y busca en la base vectorial:

```python
# Pseudocódigo
query = "política de vacaciones días correspondientes"
resultados = vector_db.search(embed(query), top_k=3)
# Devuelve fragmentos del manual del empleado
```

Fragmento recuperado:
> "Todos los empleados tienen derecho a 22 días laborables de vacaciones al año. Los días no disfrutados se acumulan hasta un máximo de 5 días al año siguiente."

Ese texto se inyecta como contexto en el prompt del LLM.

### 4. MCP consulta los sistemas reales

El agente invoca herramientas expuestas por servidores MCP. Cada servidor MCP declara qué herramientas ofrece:

**Servidor MCP de RRHH** (conectado a PostgreSQL):
```json
{
  "tools": [
    {
      "name": "consultar_dias_vacaciones",
      "description": "Devuelve los días de vacaciones restantes de un empleado",
      "input_schema": {
        "empleado_id": "string"
      }
    }
  ]
}
```

**Servidor MCP de Calendario** (conectado a Google Calendar):
```json
{
  "tools": [
    {
      "name": "consultar_disponibilidad",
      "description": "Consulta huecos libres de un grupo",
      "input_schema": {
        "personas": ["string"],
        "fecha": "string"
      }
    },
    {
      "name": "crear_evento",
      "description": "Crea un evento en el calendario",
      "input_schema": {
        "titulo": "string",
        "fecha": "string",
        "hora": "string",
        "invitados": ["string"]
      }
    }
  ]
}
```

El agente, vía Ollama, genera llamadas como:
```json
{"tool": "consultar_dias_vacaciones", "args": {"empleado_id": "emp_1234"}}
{"tool": "consultar_disponibilidad", "args": {"personas": ["equipo"], "fecha": "2026-10-02"}}
{"tool": "crear_evento", "args": {...}}
```

El host ejecuta esas llamadas contra los servidores MCP y devuelve los resultados al LLM.

### 5. El agente compone la respuesta

Con toda la información (política + saldo real + confirmación del evento), Ollama redacta:

> "Te quedan **8 días de vacaciones** según el sistema de RRHH (tenías 22, has usado 14). Según la política, puedes acumular hasta 5 días para el año que viene.
>
> He agendado la reunión del equipo para el **viernes 2 de octubre a las 10:00** y he invitado a los 6 miembros. Ya está en el calendario compartido."

---

## Cómo encaja cada pieza

| Tecnología | Rol en el flujo | Por qué es clave |
|---|---|---|
| **Ollama** | Ejecuta el LLM local que entiende, planifica y redacta. | Privacidad total: los datos de la empresa nunca salen de tu infraestructura. |
| **RAG** | Recupera conocimiento estático (políticas, manuales). | El LLM no necesita haber sido entrenado con tus documentos. |
| **MCP** | Ejecuta acciones y consulta datos vivos (RRHH, calendario). | Estandariza las integraciones: un solo protocolo para todas las herramientas. |

---

## Diagrama de secuencia

```
Usuario        Host/Agente        RAG          MCP-RRHH      MCP-Calendario
   │               │               │               │               │
   │──pregunta────▶│               │               │               │
   │               │──buscar──────▶│               │               │
   │               │◀─fragmentos───│               │               │
   │               │──consultar días────────────────▶│               │
   │               │◀─8 días─────────────────────────│               │
   │               │──ver disponibilidad─────────────────────────────▶│
   │               │◀─viernes 10:00 libre─────────────────────────────│
   │               │──crear evento───────────────────────────────────▶│
   │               │◀─evento creado───────────────────────────────────│
   │               │               │               │               │
   │◀─respuesta────│               │               │               │
```

---

## Stack técnico mínimo para replicarlo

- **LLM local**: Ollama con `llama3.1:8b` o `qwen2.5:7b` (buenos para function calling).
- **Framework de agente**: LangChain, LangGraph o LlamaIndex.
- **Base vectorial**: Chroma o Qdrant (locales, fáciles de levantar).
- **Embeddings**: `nomic-embed-text` vía Ollama (todo local).
- **Servidores MCP**: SDK oficial de MCP (Python o TypeScript).
- **Host**: una app FastAPI o Streamlit que conecte todo.

---

## Consideraciones prácticas

- **Permisos**: el servidor MCP de RRHH solo debe exponer lo necesario. El agente no debería poder modificar nóminas, por ejemplo.
- **Confirmación humana**: acciones irreversibles (enviar correo, crear evento) pueden requerir un paso de aprobación.
- **Límite de iteraciones**: evitar que el agente entre en bucles infinitos llamando herramientas.
- **Trazabilidad**: registrar cada llamada a herramienta, con input/output, para auditar.
- **Fallback**: si un servidor MCP falla, el agente debe saber degradar (ej: "no pude consultar tu saldo, pero según la política te corresponden 22 días").

---

¿Quieres que profundicemos en alguna parte concreta? Por ejemplo:
- Cómo montar un **servidor MCP** desde cero.
- Cómo implementar el **bucle ReAct** con Ollama.
- Cómo diseñar la **base vectorial** para RAG.
- Cómo **orquestar todo con LangGraph** o n8n.

Vamos a hablar sobre un sistema de gestión de privacidad de información basado en el  ISO 27701:2025

La norma **ISO/IEC 27701:2025** representa un cambio de paradigma en la gestión de la privacidad. Su segunda edición, publicada en octubre de 2025, transforma lo que antes era un apéndice de ISO 27001 en un **sistema de gestión de privacidad de la información (PIMS) completamente autónomo** y certificable por sí mismo.

A continuación, te explico en qué consiste este sistema y cómo se estructura.

### 🔄 El cambio clave: de extensión a estándar independiente

La edición de 2019 era una extensión que requería obligatoriamente tener implementado ISO 27001 (Seguridad de la Información) para poder certificarse. La versión 2025 elimina esa dependencia. Ahora, cualquier organización puede implementar y certificar su PIMS sin necesidad de un sistema de gestión de seguridad de la información previo.

Esto es especialmente relevante para organizaciones cuyo foco principal es la privacidad (como despachos de abogados, consultoras de protección de datos o empresas de servicios cloud) y que no necesitan un SGSI completo, pero sí un marco robusto para gestionar la información personal (PII).

### 🏗️ Estructura del sistema: Cláusulas 4 a 10

La norma sigue la **Estructura Armonizada (Harmonized Structure)** común a todos los estándares de sistemas de gestión ISO, lo que facilita su integración con otros como ISO 9001 o ISO 42001. Los requisitos obligatorios se organizan en siete cláusulas que siguen el ciclo de mejora continua **Plan-Do-Check-Act**:

| Cláusula | Título | Fase PDCA | Requisitos principales |
|---|---|---|---|
| **4** | Contexto de la organización | Plan | Determinar cuestiones internas/externas, partes interesadas, el rol (responsable o encargado) y el alcance del PIMS. Incluye una **novedad**: evaluar si el cambio climático es un tema relevante. |
| **5** | Liderazgo | Plan | Compromiso de la alta dirección, establecimiento de la política de privacidad y asignación de roles y responsabilidades. |
| **6** | Planificación | Plan | Acciones para abordar riesgos y oportunidades, **evaluación de riesgos de privacidad**, tratamiento de riesgos, objetivos de privacidad y planificación de cambios. |
| **7** | Apoyo | Do | Provisión de recursos, competencia, concienciación, comunicación e información documentada. |
| **8** | Operación | Do | Planificación y control operacional, ejecución de las evaluaciones de riesgos y del plan de tratamiento. |
| **9** | Evaluación del desempeño | Check | Seguimiento, medición, análisis, **auditoría interna** y revisión por la dirección. |
| **10** | Mejora | Act | Mejora continua y tratamiento de no conformidades con acciones correctivas. |

### 📋 El corazón normativo: Anexo A (Controles)

El Anexo A es el conjunto de controles obligatorios (normativos). La revisión de 2025 lo ha reestructurado por completo, pasando de estar disperso en las cláusulas 6, 7 y 8 de la versión anterior a una **organización clara en tres tablas según el rol de la organización**.

| Tabla | Aplica a | Nº de Controles | Enfoque principal |
|---|---|---|---|
| **A.1** | Responsables del tratamiento (PII Controllers) | 31 | Base jurídica, consentimiento, derechos de los interesados, privacidad desde el diseño, transferencias de datos. |
| **A.2** | Encargados del tratamiento (PII Processors) | 18 | Acuerdos con clientes, propósitos del tratamiento, gestión de subcontratistas, notificación de brechas. |
| **A.3** | Ambos roles (Controles compartidos) | 29 | Políticas de seguridad, control de acceso, gestión de incidentes, criptografía, desarrollo seguro. |

Cada control del Anexo A tiene su correspondiente **guía de implementación** en el **Anexo B** (también normativo), lo que proporciona un marco práctico para su aplicación.

### 🗺️ Anexos informativos: Mapeos y transición

Además de los anexos normativos (A y B), la norma incluye varios anexos informativos que facilitan la interpretación y el cumplimiento:

*   **Anexo C:** Mapeo con los principios de privacidad de ISO/IEC 29100.
*   **Anexo D:** Mapeo con el **RGPD**. Relaciona las cláusulas y controles con los artículos 5 a 35 y 44 a 49 (excluyendo los artículos 36-43). Es una guía indicativa, no una garantía automática de cumplimiento legal.
*   **Anexo E:** Mapeo con ISO/IEC 27018 y ISO/IEC 29151.
*   **Anexo F:** **Correspondencia con ISO 27701:2019**. Fundamental para las organizaciones que ya están certificadas y necesitan planificar su transición.

### 🚀 Implementación y certificación: Un proceso de 5 fases

La implementación de un PIMS bajo esta norma sigue un proceso lógico y estructurado que, típicamente, se desarrolla en cinco fases:

1.  **Análisis de brechas (2-4 semanas):** Evaluar las prácticas de privacidad actuales frente a los requisitos de la norma (cláusulas 4-10 y controles del Anexo A aplicables) para identificar deficiencias y priorizar acciones.
2.  **Planificación (2-4 semanas):** Definir el alcance, elaborar la **Declaración de Aplicabilidad (SoA)** —documento clave que justifica la inclusión o exclusión de cada control del Anexo A— y crear el plan de implementación.
3.  **Implementación (2-6 meses):** Desarrollar políticas, implementar los controles seleccionados, configurar procesos y capacitar al personal.
4.  **Auditoría interna (2-4 semanas):** Realizar auditorías para verificar la conformidad, abordar las no conformidades y llevar a cabo la revisión por la dirección.
5.  **Auditoría de certificación (2-6 semanas):** Proceso en dos etapas por un organismo certificador: revisión de documentación (Etapa 1) y evaluación de la implementación (Etapa 2).

Un aspecto destacado de la versión 2025 es que **la certificación puede ser independiente o combinada con ISO 27001**, a elección de la organización.

### 💎 En resumen

ISO/IEC 27701:2025 ofrece un marco **autónomo, flexible y alineado con el RGPD** para gestionar los riesgos de privacidad. Su estructura de controles por roles y su guía de implementación detallada lo convierten en una herramienta práctica tanto para responsables como para encargados del tratamiento.

Si quieres profundizar en algún aspecto concreto, como el detalle de los controles del Anexo A para un rol específico, el mapeo con el RGPD o las implicaciones de la certificación independiente, no dudes en indicármelo.

Quiero desarrollar un Privacy Information Management System (PIMS) multiagente basado en el ISO 27701:2025

Diseñar un PIMS multiagente basado en ISO 27701:2025 es un paso natural hacia la automatización inteligente del cumplimiento. A continuación, te presento una arquitectura de referencia y un plan de implementación detallado.

---

## 🎯 Principios de diseño y contexto normativo

Antes de diseñar la arquitectura, es crucial alinear el sistema con los **tres pilares normativos** que gobiernan la IA agéntica:

| Estándar | Rol en el sistema | Qué aporta al PIMS multiagente |
|---|---|---|
| **ISO 27001** | Base de seguridad | Protege los sistemas, APIs y credenciales que los agentes utilizan |
| **ISO 27701:2025** | Capa de privacidad | Gobierna cómo se procesan los datos personales, con controles y trazas de auditoría |
| **ISO 42001** | Gobernanza de IA | Añade responsabilidad y supervisión específicas para sistemas de IA |

El sistema debe operar bajo el principio de **"human-in-the-loop" (HILT)**: los agentes ejecutan tareas de forma autónoma, pero las decisiones críticas requieren aprobación humana. Esto es esencial porque los agentes actúan de forma continua y su "radio de acción" cruza múltiples fronteras de seguridad y privacidad.

---

## 🏗️ Arquitectura de referencia: PIMS Multiagente

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CAPA DE GOBERNANZA                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Orquestador  │  │  Registro de │  │  Panel de Aprobación     │  │
│  │ (Supervisor) │  │  Decisiones  │  │  Humana (HITL)           │  │
│  └──────┬───────┘  └──────────────┘  └──────────────────────────┘  │
└─────────┼───────────────────────────────────────────────────────────┘
          │
┌─────────▼───────────────────────────────────────────────────────────┐
│                    BUS DE COMUNICACIÓN (MCP)                        │
│         Protocolo estandarizado para conectar agentes               │
│         con herramientas, datos y otros agentes                     │
└─────────┬───────────────────────────────────────────────────────────┘
          │
┌─────────▼───────────────────────────────────────────────────────────┐
│                      CAPA DE AGENTES ESPECIALIZADOS                 │
│                                                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────┐  │
│  │  Agente de  │ │  Agente de  │ │  Agente de  │ │  Agente de   │  │
│  │  Inventario │ │  Evaluación │ │  Controles  │ │  Evidencia   │  │
│  │  de Datos   │ │  de Riesgos │ │  y SoA      │ │  y Auditoría │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └──────────────┘  │
│                                                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────┐  │
│  │  Agente de  │ │  Agente de  │ │  Agente de  │ │  Agente de   │  │
│  │  Derechos   │ │  Incidentes │ │  Terceros   │ │  Formación   │  │
│  │  (DSAR)     │ │  y Brechas  │ │  (DPAs)     │ │  y Conciencia│  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └──────────────┘  │
└─────────┬───────────────────────────────────────────────────────────┘
          │
┌─────────▼───────────────────────────────────────────────────────────┐
│                      CAPA DE HERRAMIENTAS (MCP Servers)             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │  Bases   │ │  APIs de │ │  Sistemas│ │  Almacén │ │  Motores │ │
│  │  de Datos│ │  RRHH    │ │  de Tick │ │  Vectorial│ │  de LLM  │ │
│  │  (PII)   │ │  (HRIS)  │ │  (Jira)  │ │  (RAG)   │ │ (Ollama) │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Componentes clave

| Componente | Función | Tecnología sugerida |
|---|---|---|
| **Orquestador** | Descompone tareas, asigna agentes, supervisa el flujo | LangGraph, CrewAI o AutoGen |
| **Bus MCP** | Comunicación estandarizada entre agentes y herramientas | Model Context Protocol |
| **Agentes especializados** | Ejecutan tareas específicas del PIMS | LLMs locales (Ollama + Qwen/Llama) |
| **Memoria compartida** | Almacena hallazgos, decisiones y evidencias | Redis + base vectorial (Chroma) |
| **Panel HITL** | Aprobación humana para acciones críticas | Interfaz web (FastAPI + Streamlit) |

---

## 🤖 Agentes especializados y su mapeo a ISO 27701:2025

Cada agente se mapea a un conjunto de controles del Anexo A de la norma. La siguiente tabla detalla la correspondencia:

| Agente | Rol | Controles ISO 27701:2025 (Anexo A) | Herramientas MCP |
|---|---|---|---|
| **Agente de Inventario** | Descubre y cataloga sistemas de IA, endpoints, categorías de PII y propósitos de negocio | A.1.2.2 (Identificar propósito), A.1.2.9 (Registros de tratamiento) | Escaneo de red, APIs de inventario, registros de proveedores |
| **Agente de Riesgos** | Ejecuta evaluaciones de impacto de privacidad (DPIA) y análisis de riesgos | A.1.2.6 (DPIA), Cláusula 6.1.2 (Evaluación de riesgos) | Formularios DPIA, bases de datos de riesgos, RAG normativo |
| **Agente de Controles** | Genera la Declaración de Aplicabilidad (SoA) y verifica la implementación de controles | Todos los controles del Anexo A; Cláusula 6.1.3 (Tratamiento de riesgos) | Repositorio de políticas, motor de reglas, mapeo de controles |
| **Agente de Evidencia** | Recopila y organiza evidencias de auditoría de forma automática | Cláusula 9.1 (Seguimiento), Cláusula 9.2 (Auditoría interna) | APIs de GRC (Vanta, Scrut), almacenamiento de evidencias |
| **Agente de Derechos (DSAR)** | Gestiona solicitudes de acceso, rectificación y supresión de datos | A.1.3.7 (Acceso, corrección o supresión), A.1.3.9 (Copia de PII) | Sistemas de ticketing, bases de datos de PII, plantillas de respuesta |
| **Agente de Incidentes** | Detecta, clasifica y notifica brechas de privacidad | A.3.11 (Planificación de incidentes), A.3.12 (Respuesta a incidentes) | SIEM, sistemas de alertas, canales de notificación |
| **Agente de Terceros** | Gestiona DPAs, subencargados y evaluaciones de proveedores | A.1.2.7 (Contratos con encargados), A.2.5.7 (Divulgación de subcontratistas) | Repositorio de contratos, APIs de proveedores, scoring de riesgo |
| **Agente de Formación** | Programa y verifica la concienciación y formación en privacidad | A.3.17 (Concienciación y formación) | LMS, registros de asistencia, cuestionarios |

---

## 🔄 Flujos de trabajo multiagente

### Flujo 1: Evaluación de impacto de privacidad (DPIA) automatizada

```
Usuario solicita DPIA
       │
       ▼
┌──────────────┐
│ Orquestador  │ → Descompone la tarea
└──────┬───────┘
       │
       ├──▶ Agente de Inventario: identifica sistemas, PII y propósitos
       │
       ├──▶ Agente de Riesgos: analiza amenazas y vulnerabilidades
       │
       ├──▶ Agente de Controles: verifica controles existentes
       │
       ├──▶ Agente de Evidencia: recopila documentación de soporte
       │
       ▼
┌──────────────┐
│ Panel HITL   │ → DPO revisa y aprueba el DPIA
└──────┬───────┘
       │
       ▼
Informe DPIA firmado y archivado
```

### Flujo 2: Gestión de una brecha de privacidad

```
Alerta de SIEM (acceso no autorizado a PII)
       │
       ▼
┌──────────────┐
│ Orquestador  │ → Activa protocolo de incidentes
└──────┬───────┘
       │
       ├──▶ Agente de Incidentes: clasifica la brecha (gravedad, alcance)
       │
       ├──▶ Agente de Inventario: identifica PII afectada y titulares
       │
       ├──▶ Agente de Terceros: verifica si hay encargados implicados
       │
       ├──▶ Agente de Evidencia: documenta el incidente y las acciones
       │
       ▼
┌──────────────┐
│ Panel HITL   │ → DPO aprueba notificación a autoridad y afectados
└──────┬───────┘
       │
       ▼
Notificación enviada en plazo legal (72h RGPD)
```

---

## 🛠️ Plan de implementación en 5 fases

### Fase 1: Análisis de brechas y preparación (2-4 semanas)

- **Actividad**: Ejecutar el **Agente de Controles** para evaluar el estado actual frente a los requisitos de ISO 27701:2025.
- **Entregable**: Informe de brechas con priorización de acciones.
- **Herramienta**: Toolkit de PIMS con scripts de evaluación automatizada.

### Fase 2: Diseño de la arquitectura multiagente (2-3 semanas)

- **Actividad**: Definir roles de agentes, mapeo a controles y flujos de trabajo.
- **Entregable**: Documento de arquitectura + SoA preliminar.
- **Decisión clave**: ¿Usar un framework de agentes (LangGraph, CrewAI) o una plataforma de orquestación (n8n, Temporal)?

### Fase 3: Desarrollo e integración (2-4 meses)

- **Actividad**: Implementar agentes, conectar herramientas vía MCP y configurar la memoria compartida.
- **Entregable**: Sistema multiagente operativo en entorno de pruebas.
- **Consideración**: Priorizar agentes de alto impacto (Riesgos, Evidencia) y bajo riesgo de automatización.

### Fase 4: Pruebas y validación (1-2 meses)

- **Actividad**: Ejecutar escenarios de prueba (DPIA, DSAR, brecha) y validar con el DPO.
- **Entregable**: Informe de validación + ajustes de configuración.
- **Métrica**: Tasa de acierto en la clasificación de controles y generación de evidencias.

### Fase 5: Auditoría interna y certificación (2-4 semanas)

- **Actividad**: Realizar auditoría interna con el **Agente de Evidencia** y preparar la certificación.
- **Entregable**: Paquete de evidencias listo para el auditor externo.
- **Beneficio**: Reducción de hasta un 80-85% en el esfuerzo de preparación de auditorías.

---

## ⚠️ Consideraciones críticas de diseño

| Desafío | Estrategia de mitigación |
|---|---|
| **Autonomía excesiva** | Implementar puertas de aprobación humana (HITL) para acciones irreversibles: notificaciones de brechas, transferencias internacionales, modificaciones de DPAs |
| **Propósito limitado** | Cada agente debe operar con un propósito declarado y registrado. Los valores de propósito deben ser evaluables por máquina y registrarse en cada solicitud |
| **Eliminación de datos** | Definir procesos para localizar y eliminar datos en documentos originales, índices vectoriales, logs de prompts y datos de fine-tuning |
| **Radio de acción** | Delimitar estrictamente los permisos de cada agente. Un agente con acceso amplio es una superficie de ataque |
| **Deriva del modelo** | Monitorear el comportamiento de los agentes a lo largo del tiempo; el sistema puede comportarse diferente en el mes 3 que en el día 1 |
| **Trazabilidad** | Registrar cada decisión, herramienta usada y evidencia generada. Los logs deben ser inmutables y auditables. |

---

## 📊 Stack tecnológico recomendado

| Capa | Opción open-source | Opción comercial |
|---|---|---|
| **LLM local** | Ollama + Qwen/Llama | Azure OpenAI, AWS Bedrock |
| **Framework de agentes** | LangGraph, CrewAI, AutoGen | — |
| **Bus de comunicación** | MCP (Model Context Protocol) | — |
| **Memoria** | Redis + Chroma/Qdrant | Pinecone, Weaviate |
| **Base de conocimiento (RAG)** | LlamaIndex + documentos normativos | — |
| **Orquestación de flujos** | n8n, Temporal | Zapier, Make |
| **GRC / Evidencias** | Toolkit PIMS (GitHub) | Vanta, Scrut, OneTrust |
| **Panel HITL** | FastAPI + Streamlit | Retool, Appsmith |

---

## 💎 En resumen

Un PIMS multiagente basado en ISO 27701:2025 combina lo mejor de tres mundos: la **seguridad de ISO 27001**, la **privacidad de ISO 27701** y la **gobernanza de IA de ISO 42001**. La clave del éxito está en:

1. **Mapear cada agente a controles específicos** del Anexo A de la norma.
2. **Mantener el control humano** en decisiones críticas (HILT).
3. **Automatizar la evidencia** para reducir el esfuerzo de auditoría.
4. **Diseñar para la trazabilidad** desde el primer día.
5. **Empezar simple** y escalar según madurez.

¿Quieres que profundice en algún agente específico, en el diseño del bus MCP, o en cómo integrar el toolkit de PIMS con tu arquitectura?

Profundiza en los 8 agentes, profundiza en el diseño del bus MCP y en cómo integrar el toolkit de PIMS en una arquitectura todo en la nube con herramientas gratuitas y sobre una base de datos de PII en Postgres.


## 🧩 Profundización en los 8 agentes del PIMS multiagente

Cada agente se especializa en un dominio de control del Anexo A de ISO 27701:2025. La siguiente tabla detalla su diseño operativo.

| Agente | Controles ISO 27701:2025 | Herramientas MCP | Entradas | Salidas | Puerta HITL |
|---|---|---|---|---|---|
| **1. Inventario de Datos** | A.1.2.2 (Propósito), A.1.2.9 (Registros de tratamiento), A.1.5.4 (Transferencias) | Escaneo de red, API de metadatos, lector de esquemas PostgreSQL, catálogo de proveedores | Consultas SQL a `information_schema`, logs de aplicaciones, configuraciones de sistemas | Inventario de actividades de tratamiento (RoPA), mapa de flujos de PII, catálogo de propósitos | Aprobación del DPO para registrar nuevas actividades de tratamiento |
| **2. Evaluación de Riesgos** | A.1.2.6 (DPIA), Cláusula 6.1.2 (Evaluación de riesgos) | Calculadora DPIA (script `dpia_risk_scorer.py` del toolkit), RAG normativo, base de datos de amenazas | Descripción de la actividad de tratamiento del Agente 1, categorías de PII, contexto organizacional | Informe DPIA con puntuación de riesgo, recomendaciones de mitigación | Revisión y firma del DPO antes de aprobar el DPIA |
| **3. Controles y SoA** | Todos los controles del Anexo A, Cláusula 6.1.3 (Tratamiento de riesgos) | Repositorio de políticas, motor de reglas, tracker SoA (script `pims_soa_tracker.py`) | Resultados del DPIA, estado actual de controles, requisitos legales aplicables | Declaración de Aplicabilidad (SoA) actualizada, plan de tratamiento de riesgos | Aprobación del CISO/DPO para la versión final del SoA |
| **4. Evidencia y Auditoría** | Cláusula 9.1 (Seguimiento), Cláusula 9.2 (Auditoría interna), A.3.14 (Protección de registros) | APIs de GRC, almacenamiento de evidencias, generador de informes, gap checker (script `pims_gap_checker.py`) | Logs de sistemas, capturas de configuración, registros de formación, resultados de auditorías previas | Paquete de evidencias organizado por cláusula/control, informe de brechas de madurez | Validación del auditor interno antes de la auditoría de certificación |
| **5. Derechos (DSAR)** | A.1.3.7 (Acceso, corrección o supresión), A.1.3.9 (Copia de PII), A.1.3.10 (Gestión de solicitudes) | MCP server DSAR (open source), bases de datos de PII, sistema de ticketing, generador de respuestas | Solicitudes entrantes (email, formulario web), identidad del titular, bases de datos a consultar | Respuesta al titular con datos solicitados, registro de la solicitud y acciones tomadas | Aprobación del DPO para respuestas con datos sensibles o disputas |
| **6. Incidentes y Brechas** | A.3.11 (Planificación de incidentes), A.3.12 (Respuesta a incidentes), A.2.5.5 (Notificación de solicitudes de divulgación) | SIEM (Wazuh), sistema de alertas, canales de notificación, MCP server de incidentes | Alertas de seguridad, logs de acceso a PII, informes de empleados | Clasificación de la brecha, registro del incidente, notificaciones (autoridad, titulares) | Aprobación del DPO para notificar a la autoridad de control (plazo 72h RGPD) |
| **7. Terceros (DPAs)** | A.1.2.7 (Contratos con encargados), A.2.5.7 (Divulgación de subcontratistas), A.2.5.8 (Contratación de subencargados) | Repositorio de contratos, APIs de proveedores, scoring de riesgo, MCP server de gestión de proveedores | Contratos existentes, lista de proveedores, evaluaciones de seguridad, cambios en subcontratistas | Registro de DPAs vigentes, alertas de renovación, evaluación de riesgo de proveedores | Aprobación legal para nuevos DPAs o cambios de subcontratistas |
| **8. Formación y Conciencia** | A.3.17 (Concienciación, educación y formación), A.3.18 (Acuerdos de confidencialidad) | LMS (Moodle), generador de cuestionarios, sistema de notificaciones, registro de asistencia | Plantilla de empleados, roles y responsabilidades, resultados de evaluaciones previas | Programas de formación personalizados, registros de finalización, informes de concienciación | Aprobación del DPO para el contenido de la formación en privacidad |

---

## 🔌 Diseño del bus MCP (Model Context Protocol)

MCP sigue una arquitectura **cliente-host-servidor** donde el host actúa como contenedor y coordinador. Cada servidor MCP expone capacidades específicas que los agentes pueden invocar de forma estandarizada.

### Arquitectura del bus MCP

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HOST (Orquestador del PIMS)                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  LangGraph / CrewAI / AutoGen                                          ││
│  │  - Crea y gestiona instancias de clientes MCP                          ││
│  │  - Controla permisos y ciclo de vida de conexiones                     ││
│  │  - Aplica políticas de seguridad y requisitos de consentimiento        ││
│  │  - Coordina la integración con el LLM (Ollama/OpenAI)                  ││
│  │  - Agrega contexto de múltiples servidores                              ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│ Cliente MCP 1 │         │ Cliente MCP 2 │         │ Cliente MCP 3 │
│ (1:1 con      │         │ (1:1 con      │         │ (1:1 con      │
│  Server 1)    │         │  Server 2)    │         │  Server 3)    │
└───────┬───────┘         └───────┬───────┘         └───────┬───────┘
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│ Server MCP 1  │         │ Server MCP 2  │         │ Server MCP 3  │
│ PostgreSQL    │         │ DSAR Manager  │         │ Evidence Store│
│ (PII Database)│         │ (Derechos)    │         │ (Evidencias)  │
└───────────────┘         └───────────────┘         └───────────────┘
```

### Servidores MCP necesarios para el PIMS

| Servidor MCP | Propósito | Herramientas expuestas | Tecnología |
|---|---|---|---|
| **MCP PostgreSQL** | Acceso controlado a la base de datos de PII | `query_pii`, `anonymize_record`, `export_consent`, `audit_query` | Python + `psycopg2` + PostgreSQL Anonymizer |
| **MCP DSAR** | Gestión de solicitudes de derechos | `create_request`, `verify_identity`, `fulfill_request`, `track_status` | MCP server open-source para DSAR |
| **MCP Evidencias** | Almacenamiento y recuperación de evidencias | `store_evidence`, `retrieve_evidence`, `generate_audit_report` | Almacenamiento S3-compatible + metadatos en PostgreSQL |
| **MCP Riesgos** | Evaluación de riesgos de privacidad | `run_dpia`, `score_risk`, `suggest_mitigation` | Scripts del toolkit PIMS + LLM |
| **MCP SoA** | Generación y seguimiento del SoA | `update_soa`, `check_control_status`, `generate_soa_report` | Tracker SoA del toolkit + PostgreSQL |
| **MCP Terceros** | Gestión de DPAs y subencargados | `list_processors`, `check_dpa_status`, `evaluate_vendor` | APIs de proveedores + base de datos de contratos |
| **MCP Formación** | Gestión de concienciación | `assign_training`, `track_completion`, `generate_awareness_report` | LMS API (Moodle) + PostgreSQL |
| **MCP Incidentes** | Respuesta a brechas de privacidad | `classify_breach`, `notify_authority`, `notify_principals`, `log_incident` | SIEM (Wazuh) + canales de notificación |

### Principios de diseño del bus MCP

1. **Aislamiento estricto**: Cada servidor MCP opera de forma independiente y solo recibe el contexto necesario para su función. No puede leer la conversación completa ni "ver" otros servidores.
2. **Composición modular**: Los servidores son altamente componibles; el host puede combinarlos según las necesidades del flujo de trabajo.
3. **Negociación de capacidades**: Clientes y servidores declaran sus capacidades soportadas en cada solicitud, permitiendo evolución independiente.
4. **Seguridad por diseño**: El host aplica políticas de seguridad y consentimiento, manejando las decisiones de autorización del usuario.
5. **Protocolo JSON-RPC**: Toda comunicación usa JSON-RPC 2.0 sobre stdio o HTTP streamable, garantizando interoperabilidad.

---

## 🚀 Integración del toolkit PIMS en arquitectura cloud gratuita con PostgreSQL

El **ISO/IEC 27701:2025 PIMS Toolkit** de Ankit-Uniyal en GitHub es un conjunto de scripts de automatización GRC de calidad production-ready que se ejecutan con la biblioteca estándar de Python 3.8+ sin dependencias externas. Incluye tres scripts principales: `pims_gap_checker.py` (evaluación de brechas), `dpia_risk_scorer.py` (calculadora de riesgos DPIA) y `pims_soa_tracker.py` (tracker de SoA).

### Arquitectura cloud completa (todas las herramientas gratuitas)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CAPA DE APLICACIÓN (GRATUITA)                        │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Streamlit Community Cloud (hosting gratuito de la UI del PIMS)       │  │
│  │  - Panel de control del DPO                                            │  │
│  │  - Visualización del SoA y brechas                                     │  │
│  │  - Aprobaciones HITL                                                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Railway / Render (free tier para el orquestador)                     │  │
│  │  - LangGraph / CrewAI ejecutando los 8 agentes                        │  │
│  │  - Servidores MCP como procesos locales o contenedores                │  │
│  │  - Ollama (LLM local en el servidor o vía API gratuita)               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  GitHub Actions (CI/CD gratuito)                                       │  │
│  │  - Ejecución programada del gap checker                                │  │
│  │  - Generación de informes de evidencia                                 │  │
│  │  - Notificaciones al DPO                                              │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CAPA DE DATOS (GRATUITA)                             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Aiven for PostgreSQL (free tier: 1 CPU, 1GB RAM, 1GB disco)         │  │
│  │  - Base de datos principal de PII                                     │  │
│  │  - PostgreSQL Anonymizer instalado para enmascaramiento dinámico      │  │
│  │  - Tablas: pii_records, consent_log, processing_activities,           │  │
│  │           dsar_requests, incidents, evidence_store, soa_controls      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  ChromaDB (embeddings locales) o Aiven OpenSearch free tier           │  │
│  │  - Base vectorial para RAG normativo (ISO 27701, RGPD, guías)        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  AWS S3 Free Tier (5GB) o Cloudflare R2 (10GB gratis)                │  │
│  │  - Almacenamiento de evidencias de auditoría                          │  │
│  │  - Documentos DPIA, SoA, informes                                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Opciones gratuitas de PostgreSQL en la nube

| Proveedor | Recursos gratuitos | Ideal para |
|---|---|---|
| **Aiven** | 1 CPU, 1 GB RAM, 1 GB disco, backups diarios | Base de datos principal del PIMS (recomendado) |
| **AWS Aurora PostgreSQL Serverless** | Hasta 4 ACU, 1 GiB almacenamiento por clúster | Prototipos con escalabilidad automática |
| **Supabase** | 500 MB PostgreSQL | Proyectos pequeños con autenticación integrada |
| **Neon** | PostgreSQL serverless con ramificación | Desarrollo y pruebas con entornos efímeros |

### Esquema de la base de datos PII en PostgreSQL

```sql
-- Tabla principal de PII (con enmascaramiento dinámico)
CREATE TABLE pii_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    principal_id UUID NOT NULL,
    data_category TEXT NOT NULL,  -- 'identificadores', 'financiero', 'salud', etc.
    data_value TEXT,  -- valor real (enmascarado por PostgreSQL Anonymizer)
    purpose TEXT NOT NULL,
    lawful_basis TEXT NOT NULL,
    retention_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Registro de consentimiento
CREATE TABLE consent_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    principal_id UUID NOT NULL,
    purpose TEXT NOT NULL,
    consent_given BOOLEAN NOT NULL,
    consent_date TIMESTAMPTZ DEFAULT NOW(),
    withdrawal_date TIMESTAMPTZ,
    mechanism TEXT  -- 'email', 'web', 'api'
);

-- Actividades de tratamiento (RoPA)
CREATE TABLE processing_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_name TEXT NOT NULL,
    purpose TEXT NOT NULL,
    pii_categories TEXT[],
    recipients TEXT[],
    transfers_countries TEXT[],
    dpia_required BOOLEAN DEFAULT FALSE,
    dpia_completed BOOLEAN DEFAULT FALSE,
    soa_controls TEXT[]  -- controles del Anexo A aplicables
);

-- Solicitudes DSAR
CREATE TABLE dsar_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    principal_id UUID NOT NULL,
    request_type TEXT NOT NULL,  -- 'access', 'rectification', 'erasure', 'portability'
    status TEXT DEFAULT 'pending',
    received_at TIMESTAMPTZ DEFAULT NOW(),
    deadline_at TIMESTAMPTZ,  -- 30 días según RGPD
    completed_at TIMESTAMPTZ,
    response_data JSONB
);

-- Incidentes de privacidad
CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    description TEXT NOT NULL,
    severity TEXT NOT NULL,
    pii_affected TEXT[],
    principals_affected INTEGER,
    notified_authority BOOLEAN DEFAULT FALSE,
    notified_principals BOOLEAN DEFAULT FALSE,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- Evidencias de auditoría
CREATE TABLE evidence_store (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    control_ref TEXT NOT NULL,  -- 'A.1.2.2', 'Cláusula 6.1.2', etc.
    evidence_type TEXT NOT NULL,  -- 'policy', 'log', 'screenshot', 'record'
    file_path TEXT,
    hash_sha256 TEXT NOT NULL,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    collected_by TEXT
);

-- SoA (Declaración de Aplicabilidad)
CREATE TABLE soa_controls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    control_ref TEXT UNIQUE NOT NULL,
    control_title TEXT NOT NULL,
    applicable BOOLEAN NOT NULL,
    justification TEXT,
    implemented BOOLEAN DEFAULT FALSE,
    evidence_id UUID REFERENCES evidence_store(id)
);
```

### Integración del toolkit PIMS con PostgreSQL

Los scripts del toolkit se ejecutan de forma independiente y generan informes que se almacenan en PostgreSQL y S3:

```python
# Ejemplo de integración del gap checker con PostgreSQL
import subprocess
import psycopg2
from datetime import datetime

def run_gap_checker_and_store():
    """Ejecuta el gap checker y almacena los resultados en PostgreSQL."""
    
    # 1. Ejecutar el script del toolkit
    result = subprocess.run(
        ["python3", "iso-27701-pims-toolkit/13-SCRIPTS/pims_gap_checker.py", 
         "--input", "gap_scores.csv", "--output", "gap_report.txt"],
        capture_output=True, text=True
    )
    
    # 2. Parsear el resultado y almacenar en PostgreSQL
    conn = psycopg2.connect(
        "postgresql://user:pass@aiven-postgres-pims:12345/pims_db"
    )
    cursor = conn.cursor()
    
    # Insertar puntuaciones de madurez por cláusula
    cursor.execute("""
        INSERT INTO gap_assessments (clause, score, assessed_at)
        VALUES (%s, %s, %s)
    """, ("6.1", 2, datetime.now()))
    
    # 3. Si el score es bajo, crear una tarea de remediación
    if score < 3:
        cursor.execute("""
            INSERT INTO remediation_tasks (control_ref, description, priority, created_at)
            VALUES (%s, %s, %s, %s)
        """, ("6.1.2", "Implementar evaluación de riesgos de privacidad", "high", datetime.now()))
    
    conn.commit()
    conn.close()
    
    # 4. Subir el informe a S3/R2
    # ...
```

### Flujo completo con PostgreSQL y el toolkit

1. **Agente de Inventario** consulta PostgreSQL vía MCP para descubrir tablas con PII y sus propósitos.
2. **Agente de Riesgos** ejecuta `dpia_risk_scorer.py` con los datos extraídos y almacena el resultado en `processing_activities.dpia_completed`.
3. **Agente de Controles** ejecuta `pims_soa_tracker.py` y actualiza la tabla `soa_controls`.
4. **Agente de Evidencia** ejecuta `pims_gap_checker.py` periódicamente vía GitHub Actions y almacena los informes en S3.
5. **Agente de DSAR** usa el MCP server de PostgreSQL con PostgreSQL Anonymizer para enmascarar datos sensibles antes de responder al titular.
6. **Agente de Incidentes** consulta `pii_records` para determinar qué titulares fueron afectados por una brecha.

---

## 💎 Resumen ejecutivo

| Componente | Implementación gratuita | Rol en el PIMS |
|---|---|---|
| **8 agentes** | LangGraph + Ollama (local) | Automatización de controles del Anexo A |
| **Bus MCP** | Servidores MCP en Python | Comunicación estandarizada entre agentes y herramientas |
| **PostgreSQL** | Aiven free tier (1GB) | Base de datos central de PII con enmascaramiento |
| **Toolkit PIMS** | Scripts de Ankit-Uniyal en GitHub | Gap checker, DPIA scorer, SoA tracker |
| **Hosting UI** | Streamlit Community Cloud | Panel de control para el DPO |
| **Hosting agentes** | Railway/Render free tier | Ejecución del orquestador |
| **Evidencias** | AWS S3 Free Tier / Cloudflare R2 | Almacenamiento de artefactos de auditoría |
| **RAG normativo** | ChromaDB local / Aiven OpenSearch | Base vectorial para consultas normativas |

La arquitectura es completamente funcional con herramientas gratuitas, escalable según crezca la organización, y cumple con los requisitos de ISO 27701:2025 al mantener trazabilidad, puertas de aprobación humana y evidencia auditable en cada paso.

¿Quieres que profundice en el código de algún servidor MCP específico, en la configuración de PostgreSQL Anonymizer para el enmascaramiento de PII, o en el flujo de trabajo detallado de uno de los 8 agentes?