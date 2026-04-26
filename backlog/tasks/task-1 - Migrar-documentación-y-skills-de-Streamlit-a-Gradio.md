---
id: TASK-1
title: Migrar documentación y skills de Streamlit a Gradio
status: To Do
assignee: []
created_date: '2026-04-26 20:10'
labels:
  - docs
  - setup
dependencies: []
references:
  - >-
    backlog/docs/actividades/Técnicas Avanzadas de IA en Modelos de Lenguaje -
    Actividad del Módulo 1.pdf
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El proyecto inicialmente contemplaba dos opciones de UI (Streamlit o Gradio). Para el MVP del sistema Q&A de la Fundación Valle del Lili se decidió usar **exclusivamente Gradio**. Antes de empezar a codificar, debemos limpiar la documentación, las rules de Cursor y las skills (`.cursor/skills/` y `.claude/skills/`) para evitar inconsistencias entre lo que el agente lee y lo que vamos a construir.

## Objetivo

Eliminar todas las menciones a Streamlit en la documentación y los archivos de configuración del agente, y dejar Gradio como única opción soportada.

## Alcance de archivos a modificar

- `AGENTS.md`: tabla de skills y bullet del stack ("Interfaz: **Streamlit** o **Gradio**" → "Interfaz: **Gradio**").
- `CLAUDE.md`: línea "Interfaz de prueba: **Streamlit** *o* **Gradio**" → "Interfaz de prueba: **Gradio**".
- `.cursor/rules/project-stack.mdc`: sección "Interfaz de prueba" debe quedar solo Gradio.
- `.cursor/rules/project-structure.mdc`: comentario de `src/app/` que dice "streamlit o gradio" → "gradio".
- `.cursor/skills/streamlit-qa-ui/SKILL.md` y `.claude/skills/streamlit-qa-ui/SKILL.md`: renombrar carpeta a `gradio-qa-ui` y reescribir el contenido enfocado solo en Gradio.
- `.cursor/skills/uv-python-env/SKILL.md` y `.claude/skills/uv-python-env/SKILL.md`: cambiar `uv add streamlit` o `uv add gradio` por solo `uv add gradio`.

## Búsqueda de referencias

Usar `rg -i streamlit` desde la raíz del repo para descubrir cualquier referencia restante.

## Notas

- El espejo `.cursor/skills/` ↔ `.claude/skills/` debe quedar idéntico.
- Mantener la convención de idioma: documentación en español latinoamericano.
- No tocar `backlog/docs/actividades/...pdf` (es material de la actividad oficial; las menciones a Streamlit ahí no aplican).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Búsqueda 'rg -i streamlit' fuera de .git/ y backlog/docs/actividades/ retorna 0 matches
- [ ] #2 Carpeta .cursor/skills/streamlit-qa-ui/ renombrada a .cursor/skills/gradio-qa-ui/ y su contenido reemplazado por instrucciones específicas de Gradio
- [ ] #3 Carpeta .claude/skills/streamlit-qa-ui/ renombrada a .claude/skills/gradio-qa-ui/ con contenido idéntico al espejo en .cursor/
- [ ] #4 AGENTS.md y CLAUDE.md mencionan únicamente Gradio en el stack y en la tabla de skills
- [ ] #5 .cursor/rules/project-stack.mdc y .cursor/rules/project-structure.mdc mencionan únicamente Gradio
- [ ] #6 .cursor/skills/uv-python-env/SKILL.md y su espejo en .claude/ usan solo 'uv add gradio'
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1) Ejecutar 'rg -i streamlit' para inventariar referencias\n2) Renombrar carpetas streamlit-qa-ui a gradio-qa-ui en .cursor/skills/ y .claude/skills/\n3) Reescribir SKILL.md de gradio-qa-ui con patrón gr.Blocks, Textbox, Radio, Accordion para prompt y comandos 'uv run python -m src.app.app_gradio'\n4) Editar AGENTS.md, CLAUDE.md, project-stack.mdc, project-structure.mdc para eliminar Streamlit\n5) Editar uv-python-env/SKILL.md (ambos espejos) para dejar solo 'uv add gradio'\n6) Verificar espejo con 'diff -r .cursor/skills .claude/skills'\n7) Re-ejecutar 'rg -i streamlit' para validar limpieza
<!-- SECTION:PLAN:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Cambios commiteados en una sola rama dedicada
- [ ] #2 Espejo .cursor/skills/ <-> .claude/skills/ verificado con diff y queda idéntico
- [ ] #3 rg -i streamlit en raíz (excluyendo .git y PDF de actividad) retorna 0
<!-- DOD:END -->
