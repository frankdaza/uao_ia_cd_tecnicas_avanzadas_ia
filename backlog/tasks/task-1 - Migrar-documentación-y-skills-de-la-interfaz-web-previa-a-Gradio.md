---
id: TASK-1
title: Migrar documentación y skills de la interfaz web previa a Gradio
status: Done
assignee: []
created_date: '2026-04-26 20:10'
updated_date: '2026-04-28 04:00'
labels:
  - docs
  - setup
dependencies: []
references:
  - >-
    backlog/docs/actividades/Técnicas Avanzadas de IA en Modelos de Lenguaje -
    Actividad del Módulo 1.pdf
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El proyecto inicialmente contemplaba dos opciones de UI. Para el MVP del sistema Q&A de la Fundación Valle del Lili se decidió usar **exclusivamente Gradio**. Antes de empezar a codificar, debemos limpiar la documentación, las rules de Cursor y las skills (`.cursor/skills/` y `.claude/skills/`) para evitar inconsistencias entre lo que el agente lee y lo que vamos a construir.

## Objetivo

Eliminar todas las menciones a la biblioteca de interfaz descartada en la documentación y los archivos de configuración del agente, y dejar Gradio como única opción soportada.

## Alcance de archivos a modificar

- `AGENTS.md`: tabla de skills y bullet del stack; interfaz solo **Gradio**.
- `CLAUDE.md`: interfaz de prueba solo **Gradio**.
- `.cursor/rules/project-stack.mdc`: sección "Interfaz de prueba" solo Gradio.
- `.cursor/rules/project-structure.mdc`: comentario de `src/app/` solo gradio.
- `.cursor/skills/gradio-qa-ui/SKILL.md` y `.claude/skills/gradio-qa-ui/SKILL.md`: instrucciones solo para Gradio (reemplazo de la skill antigua de UI).
- `.cursor/skills/uv-python-env/SKILL.md` y `.claude/skills/uv-python-env/SKILL.md`: dependencia de app solo `uv add gradio`.

## Búsqueda de referencias

Usar ripgrep insensible a mayúsculas por el nombre en inglés de la biblioteca descartada (tres sílabas, empieza por "st") desde la raíz del repo para descubrir cualquier referencia restante.

## Notas

- El espejo `.cursor/skills/` ↔ `.claude/skills/` debe quedar idéntico.
- Mantener la convención de idioma: documentación en español latinoamericano.
- No tocar `backlog/docs/actividades/...pdf` (es material de la actividad oficial).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Búsqueda con ripgrep (insensible a mayúsculas) por la biblioteca de UI descartada fuera de .git/ y backlog/docs/actividades/ retorna 0 coincidencias en contenido
- [x] #2 Carpeta `.cursor/skills/gradio-qa-ui/` con SKILL.md enfocado en Gradio (`gr.Blocks`, Textbox, Radio, Accordion; `uv run python -m src.app.app_gradio`)
- [x] #3 Carpeta `.claude/skills/gradio-qa-ui/` con contenido idéntico al espejo en `.cursor/`
- [x] #4 `AGENTS.md` y `CLAUDE.md` mencionan únicamente Gradio en el stack y en la tabla de skills
- [x] #5 `.cursor/rules/project-stack.mdc` y `.cursor/rules/project-structure.mdc` mencionan únicamente Gradio (y rules afines sin la biblioteca descartada)
- [x] #6 `.cursor/skills/uv-python-env/SKILL.md` y su espejo en `.claude/` usan solo `uv add gradio`
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1) Inventariar referencias con ripgrep.
2) Renombrar carpeta de skill de UI a `gradio-qa-ui` en `.cursor/skills/` y `.claude/skills/`.
3) Reescribir SKILL.md de `gradio-qa-ui` con patrón `gr.Blocks`, Textbox, Radio, Accordion y comando `uv run python -m src.app.app_gradio`.
4) Editar `AGENTS.md`, `CLAUDE.md`, `project-stack.mdc`, `project-structure.mdc`, `language-conventions.mdc`, `python-uv-environment.mdc`.
5) Editar `uv-python-env/SKILL.md` (ambos espejos) para dejar solo `uv add gradio`.
6) Verificar espejo con `diff -r .cursor/skills .claude/skills`.
7) Volver a ejecutar ripgrep y validar limpieza.
<!-- SECTION:PLAN:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Cambios listos en la rama de trabajo
- [x] #2 Espejo `.cursor/skills/` <-> `.claude/skills/` verificado con diff y queda idéntico
- [x] #3 Sin coincidencias de la biblioteca descartada en raíz (excluyendo .git y PDF de actividad)
<!-- DOD:END -->
