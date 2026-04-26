---
name: streamlit-qa-ui
description: Construye una interfaz web minima con Streamlit o Gradio para probar preguntas y respuestas. Usar al crear src/app o demos de sustentacion.
---

# Interfaz de prueba Q&A

> Mantener el mismo contenido en `.cursor/skills/streamlit-qa-ui/` y `.claude/skills/streamlit-qa-ui/`.

## Streamlit (patron)

- Entrada de texto para la **pregunta**.
- Boton o accion para **enviar**.
- Area para **respuesta** y, si aplica, nota de que el texto proviene solo del contexto cargado.
- Ejecutar: `uv run streamlit run src/app/app.py` (ajustar ruta si el equipo usa otra).

## Gradio (alternativa)

- `gr.Blocks()` con `Textbox` para pregunta y salida para respuesta; lanzar con `uv run python -m src.app` segun entrypoint definido.

## Textos de UI

- Etiquetas y mensajes al usuario en **espanol latinoamericano** (pueden llevar tildes en strings).
- Nombres de variables en codigo en espanol **ASCII** (`texto_pregunta`, `boton_enviar`).

## Demo

- La sustentacion es en vivo con la app; evitar depender de diapositivas segun la guia de la actividad.
