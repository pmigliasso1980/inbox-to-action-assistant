# Inbox-to-Action Assistant

Convierte correos, mensajes o notas en un resumen, tareas, fechas, prioridad y un borrador revisado. La primera version usa texto pegado manualmente y guarda los resultados en SQLite; no envia mensajes ni ejecuta acciones externas.

## Objetivo de producto

El asistente debe ser útil todos los días: reducir el tiempo necesario para revisar entradas, evitar que
se pierdan compromisos y preparar respuestas confiables sin ejecutar acciones externas sin aprobación.
El éxito se medirá por tiempo ahorrado, precisión de las acciones extraídas, cantidad de correcciones
humanas y uso recurrente; no solamente por funcionalidades implementadas.

## Flujo

```text
Mensaje -> Analysis Agent -> Draft Agent -> Review Agent -> SQLite
```

El Draft Agent se omite cuando el analisis determina que no hace falta responder.

## Instalacion

```bash
cd ~/code/inbox-to-action-assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
export OPENAI_API_KEY="tu-clave"
```

## Procesar un mensaje

```bash
python3 -m src.inbox_action ingest \
  --sender "ana@example.com" \
  --subject "Propuesta y reunion" \
  "Pablo, revisa la propuesta antes del viernes y confirma si participas el lunes."
```

La aplicacion intenta varios modelos y reutiliza el primero autorizado. El resultado incluye el modelo elegido, el analisis, las tareas, el borrador y la revision.

Las fechas relativas se conservan en `date_text`; las expresiones inequívocas se resuelven desde la
fecha de referencia y las ambiguas quedan como `needs_confirmation`. La prioridad urgente requiere
evidencia explícita. Los compromisos futuros reciben `requires_human_approval`, pero no invalidan por sí
solos una revisión automática favorable. Todo resultado queda en `pending_human_review`.

Las solicitudes explícitas de confirmar, responder o avisar fuerzan `needs_reply=true`. La urgencia
textual establece prioridad `urgent`; un vencimiento verificado para hoy o mañana establece `high`;
sin esas señales, una prioridad propuesta como `high` o `urgent` se reduce. Si hace falta responder y
no existe borrador, la revisión se rechaza por política.

## Listar mensajes

```bash
python3 -m src.inbox_action list
```

## Revisar resultados

```bash
# Ver el resultado completo y su historial de auditoría
python3 -m src.inbox_action show 1
python3 -m src.inbox_action history 1

# Aprobar o rechazar con una nota humana
python3 -m src.inbox_action approve 1 --note "Verificado antes de responder"
python3 -m src.inbox_action reject 1 --note "La fecha propuesta es incorrecta"
```

Para corregir el análisis o borrador, exporta el objeto JSON correspondiente, edítalo y ejecuta:

```bash
python3 -m src.inbox_action revise 1 \
  --analysis-file analysis.json \
  --draft-file draft.json \
  --note "Corregí responsable y fecha"
```

También puede eliminarse un borrador con `--clear-draft`. Cada corrección y decisión queda registrada
en `review_events`, incluyendo las versiones anterior y posterior. Las correcciones vuelven el mensaje
a `pending_human_review`.

## Pruebas

```bash
python3 -m unittest discover -s tests -v
```

Los escenarios cotidianos anonimizados viven en `evals/daily_cases.json` y pueden ejecutarse de forma
aislada, sin API ni escrituras en SQLite:

```bash
python3 -m unittest tests.test_evaluation_cases -v
```

Esta evaluación comprueba las políticas sobre salidas estructuradas conocidas. No sustituye una
evaluación contra modelos reales, cuyas respuestas pueden variar y consumir API.

Con `OPENAI_API_KEY` configurada, la evaluación real ejecuta el flujo completo sin guardar mensajes en
SQLite:

```bash
# Empezar con un único caso para controlar costo y revisar el reporte
python3 -m src.inbox_action eval-live --case informativo_sin_accion

# Ejecutar los siete casos
python3 -m src.inbox_action eval-live
```

Puede repetirse `--case` para seleccionar varios escenarios. El comando imprime JSON con cada criterio,
dimensiones separadas (`extraction`, `dates`, `priority`, `response`, `draft_quality`, `review` y
`safety`), la salida real y un resumen; finaliza con código `1` cuando al menos un caso falla. La batería completa
puede realizar hasta 17 llamadas al modelo porque los casos con respuesta ejecutan análisis, borrador y
revisión, mientras los demás ejecutan análisis y revisión.

Las evaluaciones reales también comprueban que cada `date_text` provenga literalmente del mensaje. Los
casos pueden aceptar más de una prioridad cuando varias clasificaciones sean razonables; esta
flexibilidad se declara explícitamente en el fixture y no omite controles de seguridad.
Todo borrador se evalúa además por placeholders sin resolver, como `[Tu Nombre]`. Los escenarios pueden
declarar afirmaciones o acciones prohibidas específicas cuando el mensaje no las respalda.
Cada acción real debe conservar evidencia textual verificable y confianza mínima de `0.7`; diferencias
de puntuación o comillas envolventes no invalidan una cita correcta.

## Memoria del proyecto

Las decisiones, avances y próximos pasos de cada sesión se conservan en
[`docs/SESSION_LOG.md`](docs/SESSION_LOG.md). La bitácora contiene resúmenes operativos y no debe
incluir secretos ni contenido privado de los mensajes procesados.

## Proximos incrementos

1. Convertir los ensayos reales en pruebas de regresión y corregir citas, fechas, prioridad y borradores.
2. Evaluaciones con mensajes anonimizados: acciones omitidas, falsos positivos y tiempo ahorrado.
3. Bandeja diaria con detalle, corrección y aprobación/rechazo de resultados.
4. Interfaz web simple y rápida para completar el flujo sin depender de la terminal.
5. Ingesta de Gmail en modo lectura.
6. Creación de borradores y recordatorios únicamente con aprobación humana.
7. Seguimiento de calidad, costo, latencia y uso recurrente.
