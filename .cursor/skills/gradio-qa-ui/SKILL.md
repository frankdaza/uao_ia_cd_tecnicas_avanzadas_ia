---
name: gradio-qa-ui
description: "DEPRECADO: el frontend del proyecto usa React 19 + Vite 8 (react-vite-qa-ui). La UI Gradio y el pipeline BM25 asociado fueron retirados del arbol de codigo; ver historial en git y ADRs."
deprecated: true
replaced_by: react-vite-qa-ui
---

> **DEPRECADO**: el producto y el laboratorio usan **`react-vite-qa-ui`** (React 19 + Vite 8 + shadcn/ui) y el agente M2 vía FastAPI. La aplicación Gradio y el recuperador BM25 ya **no** están en el repositorio; si necesitas el patron `gr.Blocks` como referencia académica, consulta commits anteriores o el informe del modulo 1.
>
> Para implementar o modificar la interfaz actual: `.cursor/skills/react-vite-qa-ui/SKILL.md` (espejo en `.claude/skills/react-vite-qa-ui/SKILL.md`).

## Mantenimiento del espejo

Mantener el mismo contenido en `.cursor/skills/gradio-qa-ui/` y `.claude/skills/gradio-qa-ui/`.
