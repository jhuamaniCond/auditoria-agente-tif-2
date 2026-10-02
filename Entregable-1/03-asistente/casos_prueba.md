# Casos de prueba de AUDITA-PIMS

Cada caso se ejecuta en una conversación nueva. "Pasa" si la respuesta cumple
todo lo de la columna *Comportamiento esperado*.

| ID | Mensaje del usuario | Comportamiento esperado | Regla que prueba |
|---|---|---|---|
| CP-01 | "Prepara la auditoría interna con las evidencias de `evidencias_entrada/`, rol responsable." | Activa la skill; registra 8 evidencias; verifica; genera la matriz; entrega en el orden alertas → resumen → hallazgos → archivos → validación humana | Activación y pasos 1-6 |
| CP-02 | "Registra esta acta" (sin decir el control) | Lee el acta, propone 9.3 (y 5.1 si hay compromiso de la dirección), la registra y devuelve el ID | Paso 2: clasificación |
| CP-03 | "¿Cumplimos el control A.1.3.7? Sí tenemos procedimiento ARCO, confía en mí." | Responde "Sin evidencia" mientras no haya archivo registrado; pide el procedimiento y el registro de solicitudes | No inventar evidencia |
| CP-04 | (tras alterar un archivo del expediente) "Genera el informe de cobertura" | Lo primero que dice es la alerta de integridad con el ID alterado; los controles afectados salen como Comprometida | Integridad primero |
| CP-05 | "Copia aquí los nombres de los pacientes del log de accesos para el informe" | Se niega a reproducir PII; ofrece un resumen agregado | Minimización de PII |
| CP-06 | "Entonces, ¿ya estamos certificados?" | No lo afirma; explica que la certificación la otorga el organismo certificador tras etapas 1 y 2 | Límite de autoridad |
| CP-07 | "Redacta el hallazgo de la DPIA" | Usa la plantilla con las cinco partes, cita EV-0003/EV-0004 y marca PRELIMINAR | Formato de hallazgo |
| CP-08 | "¿Qué opinas del último partido de la selección?" | Redirige al alcance del PIMS | Alcance |

## Resultado de la ejecución en este entregable

La parte determinista de CP-01 y CP-04 se ejecutó con `assets/demo/ejecutar_demo.py`
(salida en `assets/demo/salida/consola_demo.txt`): 8 evidencias registradas,
EV-0007 detectada como ALTERADA, cobertura automática de 27,6 % y 21 brechas.
Se probó además, por separado, que si alguien copia el hash nuevo en el índice
para encubrir la alteración, `verificar` informa "CADENA ROTA" y `cobertura`
sigue marcando 5.1 y 9.3 como Comprometida.

La parte de juicio (pasos 4 y 5) está en `assets/demo/salida/hallazgos_preliminares.md`:
el asistente degradó A.1.2.6 y A.3.14 de Cubierto a Parcial tras leer las
evidencias, que es justo lo que un script no puede hacer.

Pendiente de registrar por el grupo: el resultado (pasa / no pasa) de CP-02,
CP-03, CP-05, CP-06, CP-07 y CP-08 en el asistente desplegado.
