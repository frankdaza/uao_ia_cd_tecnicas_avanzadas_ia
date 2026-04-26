---
id: TASK-13
title: App Gradio con selector de modelo y editor de prompt del sistema
status: Done
assignee: []
created_date: '2026-04-26 20:18'
updated_date: '2026-04-26 21:50'
labels:
  - ui
dependencies:
  - TASK-12
ordinal: 0.48828125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La UI es la cara del MVP. Debe permitir al usuario:
1. Escribir una pregunta y recibir respuesta.
2. Elegir el modelo (`llama3.1:8b` o `gemma4:e2b`).
3. **Leer y editar** el prompt del sistema (acordeón colapsable), con botón para restaurar el por defecto.
4. Ver el archivo fuente que respaldó la respuesta (trazabilidad para evaluación).

## Objetivo

Implementar `src/app/app_gradio.py` con `gr.Blocks`, lanzable con `uv run python -m src.app.app_gradio`.

## Diseño de la UI

```python
import gradio as gr
from src.qa.pipeline import construir_pipeline_por_defecto, PROMPT_SISTEMA_DEFECTO

pipeline = construir_pipeline_por_defecto()

with gr.Blocks(title="Q&A Fundación Valle del Lili") as demo:
    gr.Markdown("# Asistente Q&A — Fundación Valle del Lili")
    gr.Markdown(
        "Pregúntale lo que quieras sobre la información pública del sitio "
        "[valledellili.org](https://valledellili.org/). Las respuestas se basan "
        "exclusivamente en el contenido descargado."
    )

    with gr.Row():
        with gr.Column(scale=2):
            pregunta = gr.Textbox(
                label="Tu pregunta",
                placeholder="Ej: ¿Cómo puedo agendar una cita?",
                lines=3,
            )
            modelo = gr.Radio(
                choices=["llama3.1:8b", "gemma4:e2b"],
                value="llama3.1:8b",
                label="Modelo (Ollama)",
            )
            with gr.Accordion("Prompt del sistema (editable)", open=False):
                prompt_textbox = gr.Textbox(
                    value=PROMPT_SISTEMA_DEFECTO,
                    label="Edita el prompt y presiona Preguntar",
                    lines=14,
                )
                boton_restaurar = gr.Button("Restaurar prompt por defecto")
            boton_preguntar = gr.Button("Preguntar", variant="primary")
        with gr.Column(scale=3):
            respuesta = gr.Markdown(label="Respuesta")
            metadatos = gr.Markdown(label="Trazabilidad")

    def manejar_pregunta(texto_pregunta, modelo_elegido, prompt_actual):
        if not texto_pregunta.strip():
            return ("Por favor escribe una pregunta.", "")
        try:
            resultado = pipeline.responder(
                pregunta=texto_pregunta,
                modelo=modelo_elegido,
                prompt_sistema=prompt_actual,
            )
        except Exception as exc:
            return (f"⚠️ {exc}", "")
        meta = (
            f"**Archivo fuente:** `{resultado.archivo_fuente}`  \n"
            f"**URL origen:** [{resultado.source_url}]({resultado.source_url})  \n"
            f"**Score BM25:** {resultado.score_recuperacion:.2f}  \n"
            f"**Modelo:** `{resultado.modelo}` · **Latencia:** {resultado.latencia_ms} ms"
        )
        return (resultado.texto, meta)

    boton_preguntar.click(
        manejar_pregunta,
        inputs=[pregunta, modelo, prompt_textbox],
        outputs=[respuesta, metadatos],
    )
    boton_restaurar.click(
        lambda: PROMPT_SISTEMA_DEFECTO,
        outputs=[prompt_textbox],
    )

if __name__ == "__main__":
    demo.launch()
```

## Detalles técnicos

- **Persistencia del prompt**: durante la sesión, el textbox conserva ediciones del usuario. Al cerrar y reabrir la app, vuelve a `PROMPT_SISTEMA_DEFECTO`.
- **Manejo de errores**: capturar `OllamaNoAccesibleError` y `ModeloNoDisponibleError` y mostrar el mensaje amigable en `respuesta` (no romper la UI).
- **Estado global del pipeline**: instanciar **una sola vez** al cargar el módulo (índice BM25 cacheado).
- **Recarga del corpus**: opcional, agregar un botón "Recargar corpus" que llame `pipeline.recuperador.recargar()`.

## Identificadores ASCII

- `manejar_pregunta`, `restaurar_prompt`, `construir_demo`, `pregunta`, `modelo`, `prompt_textbox`, `boton_preguntar`, `boton_restaurar`, `respuesta`, `metadatos`.

## Dependencias a agregar

```bash
uv add gradio
```

## Tests

- Test funcional ligero (sin servidor): importar el módulo y verificar que `demo` es una instancia de `gr.Blocks` y que `manejar_pregunta` tiene la firma esperada.
- Smoke manual: `uv run python -m src.app.app_gradio`, abrir navegador, hacer 2-3 preguntas y validar que se muestra archivo fuente.

## Caso de negocio

La sustentación es en vivo (sin diapositivas). El evaluador hará preguntas en tiempo real y querrá ver:
1. La respuesta.
2. La trazabilidad (qué archivo se usó).
3. Cómo se ve afectado el comportamiento al editar el prompt (caso de uso del módulo de edición).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 src/app/app_gradio.py se ejecuta con 'uv run python -m src.app.app_gradio' y abre la UI en el navegador
- [x] #2 La UI tiene un Textbox para la pregunta, un Radio con 'llama3.1:8b' y 'gemma4:e2b', un Accordion con el prompt editable y un botón para restaurar el prompt por defecto
- [x] #3 Al presionar 'Preguntar', se muestra la respuesta del LLM y un bloque de trazabilidad con archivo_fuente, source_url, score y latencia
- [x] #4 Editar el textbox del prompt afecta la siguiente pregunta sin reiniciar la app
- [x] #5 Botón 'Restaurar prompt por defecto' reescribe el textbox al valor de PROMPT_SISTEMA_DEFECTO
- [x] #6 Cambiar el modelo en el Radio afecta la siguiente pregunta (verificar en metadatos)
- [x] #7 Si Ollama no está accesible o el modelo no existe, la UI muestra el mensaje en español sin crashear
- [x] #8 El pipeline se instancia una sola vez al cargar el módulo (no por cada pregunta)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1) uv add gradio
2) Crear src/app/app_gradio.py con gr.Blocks
3) Implementar manejar_pregunta() llamando pipeline.responder con override de prompt y modelo
4) Conectar botón restaurar al prompt por defecto
5) Manejar excepciones de Ollama mostrando mensaje en respuesta
6) Smoke test manual: levantar app y probar 3 preguntas
7) Documentar comando en README
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se agregó `gradio` e implementó `src/app/app_gradio.py` con `gr.Blocks`, pipeline único al importar, Radio de modelos, acordeón con prompt editable y restauración, trazabilidad en Markdown, manejo de OllamaNoAccesibleError/ModeloNoDisponibleError, botón opcional Recargar corpus (`pipeline.recuperador.recargar()`), property `recuperador` y reexport de `PROMPT_SISTEMA_DEFECTO` en el pipeline. Pruebas en `tests/app/test_app_gradio.py` y sección App Gradio en README.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 uv add gradio ejecutado y reflejado en pyproject.toml + uv.lock
- [x] #2 Comando documentado en README sección 'App Gradio'
- [x] #3 Smoke test manual con 3 preguntas distintas pasa (capturar evidencia en captura)
<!-- DOD:END -->
