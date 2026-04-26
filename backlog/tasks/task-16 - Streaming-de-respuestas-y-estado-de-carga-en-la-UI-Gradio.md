---
id: TASK-16
title: Streaming de respuestas y estado de carga en la UI Gradio
status: In Progress
assignee: []
created_date: '2026-04-26 22:31'
updated_date: '2026-04-26 22:31'
labels:
  - ui
  - ux
  - llm
dependencies:
  - TASK-13
references:
  - src/qa/cliente_ollama.py
  - src/qa/pipeline.py
  - src/qa/prompt.py
  - src/app/app_gradio.py
  - >-
    https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-chat-completion
  - 'https://www.gradio.app/guides/streaming-outputs'
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La app Gradio ya esta lista (TASK-13) y permite preguntar, elegir modelo y editar el prompt del sistema. Hoy `boton_preguntar.click(...)` invoca `manejar_pregunta` y este llama a `pipeline.responder`, que internamente usa `ClienteOllama.chat` con `"stream": False` (ver `src/qa/cliente_ollama.py`, metodo `chat`). El usuario no recibe ninguna senal mientras espera, y la respuesta aparece de golpe al final. Con preguntas largas (latencias > 30 s observadas en demo) la UI parece colgada y la experiencia es pobre.

Ademas, la respuesta llega como texto plano y no aprovecha que `respuesta` es un componente `gr.Markdown`: hoy no hay garantia de que el modelo entregue Markdown estructurado, asi que no se ven titulos, listas ni enlaces bien renderizados.

## Objetivo

Mejorar el UX del Asistente Q&A asi:

1. Mientras corre la consulta, el boton **Preguntar** queda **deshabilitado** y muestra un indicador de carga (texto tipo `Pensando...` o spinner). Al terminar, vuelve a estado normal.
2. La respuesta del LLM se renderiza **token a token** (streaming) en el componente `respuesta` de Markdown, en vez de aparecer toda al final.
3. La respuesta se muestra con **formato Markdown rico**: titulos (`##`), listas (`-`), negritas en terminos clave, codigo en linea (`` ` ``), enlaces como `[texto](url)`. El prompt del sistema instruye al modelo a usar este formato cuando aporte claridad, sin exagerarlo.
4. Los metadatos de trazabilidad siguen actualizandose al final con `archivo_fuente`, `source_url`, `score_recuperacion`, `modelo` y `latencia_ms`.

## Cambios principales

- **`src/qa/cliente_ollama.py`**: agregar `chat_stream(mensajes) -> Iterator[str]` que invoque `POST /api/chat` con `"stream": True`, parsee NDJSON con `response.iter_lines()` y haga `yield` de cada `message.content`. Conservar manejo existente de `OllamaNoAccesibleError` y `ModeloNoDisponibleError` con los mismos mensajes en espanol.
- **`src/qa/pipeline.py`**: agregar `responder_stream(...)` que devuelve un iterador. Patron sugerido: yield de strings parciales (texto acumulado o delta) y al final un `RespuestaQa` con metadatos. Mantener `responder` intacto para no romper tests existentes.
- **`src/qa/prompt.py`**: ajustar `PROMPT_SISTEMA_DEFECTO` para pedir respuestas en **Markdown estructurado** (titulos `##`, listas `-`, **negritas**, enlaces `[texto](url)`, codigo en linea) cuando aporte claridad. Incluir un ejemplo breve de salida esperada. Mantener el principio anti-alucinacion (responder solo con base en el contexto entregado).
- **`src/app/app_gradio.py`**:
  - Convertir `manejar_pregunta` en una **funcion generadora** (`manejar_pregunta_stream`) que `yield`-ea `(texto_acumulado, metadatos)` mientras llegan tokens.
  - Encadenar eventos de Gradio para deshabilitar/rehabilitar el boton:

```python
boton_preguntar.click(
    lambda: gr.update(interactive=False, value="Pensando..."),
    outputs=[boton_preguntar],
).then(
    manejar_pregunta_stream,
    inputs=[pregunta, modelo, prompt_textbox],
    outputs=[respuesta, metadatos],
).then(
    lambda: gr.update(interactive=True, value="Preguntar"),
    outputs=[boton_preguntar],
)
```

  - Mantener `respuesta` como `gr.Markdown` (renderiza tablas, listas, codigo, enlaces).
  - Aplicar **CSS minimo** via `gr.Blocks(css=...)` para mejorar tipografia, espaciado entre bloques (titulos, listas, parrafos) y aspecto del bloque de respuesta.

## Notas tecnicas

- **Ollama NDJSON**: cada linea trae `{"message": {"content": "..."}, "done": false, ...}`; el chunk final tiene `"done": true` con campos de evaluacion. No mezclar con `/api/generate` (es `/api/chat`).
- **Gradio streaming**: para `gr.Markdown` se hace acumulando texto en una variable y `yield`-eandolo en cada iteracion del generador.
- Mantener `temperature` y `num_ctx` desde `ConfiguracionLlm`.
- **Identificadores ASCII** (regla del repo): `chat_stream`, `responder_stream`, `manejar_pregunta_stream`, `iterar_tokens`, `acumulado`.
- Manejo de errores: si `OllamaNoAccesibleError` / `ModeloNoDisponibleError` ocurre durante el stream, capturar en la UI y mostrar mensaje en espanol; el `.then()` final debe ejecutarse igualmente para rehabilitar el boton (usar `js`/`postprocess` o un `try/except` que continue el generador).

## Caso de negocio

La sustentacion del modulo es en vivo. Con preguntas que tardan decenas de segundos, ver streaming y un boton bloqueado con `Pensando...` transmite al evaluador que la app esta funcionando. Ademas, una respuesta con formato Markdown bonito (titulos, listas, enlaces clicables al sitio fuente) demuestra mejor la calidad del MVP.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 ClienteOllama.chat_stream existe, devuelve un iterador de strings y reusa OllamaNoAccesibleError y ModeloNoDisponibleError con los mismos mensajes en espanol
- [ ] #2 PipelineQa.responder_stream emite tokens parciales en orden y al finalizar deja disponibles los metadatos archivo_fuente, source_url, score_recuperacion, latencia_ms y modelo equivalentes a responder
- [ ] #3 Al presionar Preguntar en la UI, el boton queda deshabilitado y muestra un indicador de carga visible (p. ej. texto 'Pensando...' o spinner) hasta que termina la respuesta, y luego vuelve a 'Preguntar' habilitado
- [ ] #4 La respuesta aparece progresivamente en el Markdown de respuesta mientras llegan los tokens (verificable en navegador con una pregunta larga)
- [ ] #5 Si Ollama no esta accesible o el modelo no existe, la UI muestra el mensaje de error en espanol sin crashear y el boton vuelve a su estado normal
- [ ] #6 PROMPT_SISTEMA_DEFECTO instruye al modelo a usar Markdown estructurado (titulos, listas, negritas, enlaces, codigo en linea) cuando aporte claridad, manteniendo la regla anti-alucinacion
- [ ] #7 Una pregunta de prueba que produzca lista o enlace se renderiza con formato Markdown correcto en la UI (lista con vinetas, enlace clicable, etc.)
- [ ] #8 Se agregan tests unitarios para chat_stream que simulan NDJSON de Ollama y para responder_stream verificando concatenacion de tokens y metadatos finales
- [ ] #9 Tests existentes (responder, app smoke, prompt) siguen pasando con uv run pytest, ajustando expectativas del prompt si fuese estrictamente necesario
- [ ] #10 README seccion 'App Gradio' actualizado mencionando streaming, indicador de carga y formato Markdown rico de la respuesta
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 uv run pytest pasa en local
- [ ] #2 Demo manual: con Ollama corriendo, una pregunta larga muestra streaming visible token a token y el boton queda bloqueado con indicador de carga durante la espera
- [ ] #3 Captura o video corto adjuntado en finalSummary mostrando el streaming y el formato Markdown de la respuesta
<!-- DOD:END -->
