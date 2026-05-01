---
name: gradio-qa-ui
description: "DEPRECADO: esta skill fue reemplazada por react-vite-qa-ui. El frontend del proyecto ahora usa React 19 + Vite 7 + shadcn/ui. Ver .cursor/skills/react-vite-qa-ui/SKILL.md. La implementacion Gradio vive en src/app/legacy/app_gradio.py."
deprecated: true
replaced_by: react-vite-qa-ui
---

> **DEPRECADO**: esta skill fue reemplazada por **`react-vite-qa-ui`** al migrar el frontend de Gradio a React 19 + Vite 7 + shadcn/ui. No usar para codigo nuevo. Ver `.cursor/skills/react-vite-qa-ui/SKILL.md`.
>
> El codigo Gradio original vive en `src/app/legacy/app_gradio.py` como referencia historica.

# Interfaz de prueba Q&A con Gradio

> Mantener el mismo contenido en `.cursor/skills/gradio-qa-ui/` y `.claude/skills/gradio-qa-ui/`.

## Patron recomendado (`gr.Blocks`)

- `gr.Blocks()` como contenedor principal.
- `gr.Textbox` para la **pregunta** del usuario (entrada).
- `gr.Textbox` o `gr.Markdown` para la **respuesta** (salida); indicar si el texto proviene solo del contexto recuperado.
- `gr.Radio` para elegir **modelo** o modo cuando el pipeline lo permita.
- `gr.Accordion` para opciones avanzadas (por ejemplo **prompt del sistema** editable) sin saturar la vista principal.
- Boton **Enviar** con `gr.Button` que dispare la funcion que llama al pipeline Q&A.

## Ejecucion

- Entrypoint documentado del proyecto: `uv run python -m src.app.app_gradio` (ajustar modulo si el equipo define otra ruta).

## Textos de UI

- Etiquetas y mensajes al usuario en **espanol latinoamericano** (pueden llevar tildes en strings).
- Nombres de variables en codigo en espanol **ASCII** (`texto_pregunta`, `boton_enviar`).

## Demo

- La sustentacion es en vivo con la app; evitar depender de diapositivas segun la guia de la actividad.
