---
id: TASK-41
title: >-
  Actualizar informe LaTeX con migracion React+Vite+FastAPI+SSE y nuevo corpus
  de 1000 paginas
status: Done
assignee: []
created_date: '2026-05-01 04:19'
updated_date: '2026-05-01 16:20'
labels:
  - docs
  - informe
  - latex
  - arquitectura
dependencies:
  - TASK-23
  - TASK-24
  - TASK-39
references:
  - informe/Informe_Latex.tex
  - informe/Informe_Latex.pdf
  - >-
    backlog/decisions/decision-2 -
    Migracion-Frontend-React-Vite-Backend-FastAPI-SSE.md
  - backlog/docs/doc-002 - Migracion-Frontend-React-Vite-Backend-FastAPI.md
  - src/qa/cliente_openai.py
  - src/qa/cliente_ollama.py
  - scripts/scrape.py
  - scripts/export_markdown.py
documentation:
  - >-
    backlog/decisions/decision-2 -
    Migracion-Frontend-React-Vite-Backend-FastAPI-SSE.md
  - backlog/docs/doc-002 - Migracion-Frontend-React-Vite-Backend-FastAPI.md
priority: high
ordinal: 0.5
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El informe LaTeX en `informe/Informe_Latex.tex` describe la fase 1 del MVP (UI Gradio, crawler con 200 paginas y profundidad 5, corpus aproximado de 45 documentos, tabla de modelos incompleta donde aparece mal `gemma4:e2` y falta `gemma4:e4b`, y solo un modelo OpenAI listado). Esta desactualizado respecto a los cambios de arquitectura y de corpus hechos en fase 2.

La migracion arquitectonica esta registrada en:

- `backlog/decisions/decision-2 - Migracion-Frontend-React-Vite-Backend-FastAPI-SSE.md`.
- `backlog/docs/doc-002 - Migracion-Frontend-React-Vite-Backend-FastAPI.md`.

Adicionalmente, se ejecuto una nueva corrida de scraping no documentada en el informe:

```bash
uv run python -m scripts.scrape --max-paginas 1000 --profundidad-maxima 8
```

Resultados observados (ver capturas adjuntas del usuario):

- Scraping: 1000 descargas exitosas, 0 omitidas por robots, 0 omitidas por hash, 20 errores, duracion aproximada de 51 min.
- Conversion a Markdown (`uv run python -m scripts.export_markdown`): 1000 creados, 0 actualizados, 0 omitidos por hash, 0 errores, duracion aproximada de 32 s; salida en `data/markdown/valledellili-org/`.

Modelos realmente soportados en el backend:

- Ollama (`src/qa/cliente_ollama.py`): `llama3.1:8b`, `gemma4:e2b`, `gemma4:e4b`.
- OpenAI via API (`src/qa/cliente_openai.py`): `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `chatgpt-4o-latest`, `gpt-3.5-turbo`.

## Alcance

Reescribir a fondo `informe/Informe_Latex.tex` para reflejar la fase 2 del proyecto: backend FastAPI + Uvicorn + sse-starlette, frontend React 19 + Vite 7 + Tailwind v4 + shadcn/ui, streaming SSE token a token, modo dual (Ollama + OpenAI), conjunto completo de 3 modelos Ollama + 5 modelos OpenAI, corpus de 1000 documentos Markdown y nuevos parametros del crawler. Incluir en el informe las dos capturas que documentan la ultima ejecucion del scraping y la conversion a Markdown.

La tarea incluye:

- Crear `informe/figuras/` y copiar las dos capturas adjuntas como `scraping_resultado_1000.png` y `markdown_export_1000.png`.
- Actualizar el preambulo con `\graphicspath{{figuras/}}`.
- Reescribir abstract, palabras clave, diagrama de arquitectura, tabla de stack, parametros del crawler, resultados del scraping, resultados de la exportacion a Markdown, tabla de modelos, seccion de UI (reemplazando Gradio por FastAPI+SSE y React), evaluacion, discusion, conclusiones y bibliografia.
- Mover la cita `abid2019gradio` a una nota sobre el codigo legacy preservado en `src/app/legacy/app_gradio.py`.
- Validar la compilacion con `latexmk -pdf`.

## Entregables

- `informe/Informe_Latex.tex` actualizado y compilado a `informe/Informe_Latex.pdf`.
- `informe/figuras/scraping_resultado_1000.png`.
- `informe/figuras/markdown_export_1000.png`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Existe `informe/figuras/` con las dos capturas nombradas `scraping_resultado_1000.png` y `markdown_export_1000.png`.
- [x] #2 El preambulo de `Informe_Latex.tex` incluye `\graphicspath{{figuras/}}`.
- [x] #3 Abstract y palabras clave mencionan FastAPI+SSE, React 19+Vite 7+Tailwind+shadcn/ui, modo dual, corpus de 1000 paginas y el conjunto completo de 3 modelos Ollama + 5 modelos OpenAI.
- [x] #4 Figura tikz de arquitectura refleja los modulos Backend FastAPI+SSE y Frontend React 19 (Gradio queda como legacy).
- [x] #5 La tabla `tab:stack` incluye filas para FastAPI + Uvicorn + sse-starlette y React 19 + Vite 7 + Tailwind v4 + shadcn/ui + Vercel AI SDK.
- [x] #6 La tabla `tab:crawler` refleja `max_paginas = 1000` y `profundidad_max = 8`.
- [x] #7 Existe una subseccion `Resultados del scraping` con tabla (1000 exitosas, 0 omitidas robots, 0 omitidas hash, 20 errores, ~51 min) e imagen `scraping_resultado_1000.png`.
- [x] #8 Existe una subseccion `Resultados de la exportacion a Markdown` con cifras (1000 creados, 0 actualizados, 0 errores, ~32 s) e imagen `markdown_export_1000.png`.
- [x] #9 La tabla `tab:modelos` lista los 3 modelos Ollama (`llama3.1:8b`, `gemma4:e2b`, `gemma4:e4b`) y los 5 modelos OpenAI (`gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `chatgpt-4o-latest`, `gpt-3.5-turbo`).
- [x] #10 La antigua seccion de Interfaz Gradio queda reemplazada por una seccion `Backend FastAPI+SSE y Frontend React 19` con endpoints, streaming, modo dual, tokens de diseno institucional y menciones a prompt editable + trazabilidad BM25.
- [x] #11 Secciones Evaluacion, Discusion y Conclusiones reflejan corpus de 1000 documentos, los 8 modelos disponibles y la separacion backend/frontend.
- [x] #12 Bibliografia incluye entradas para FastAPI, sse-starlette, React 19, Vite, Tailwind v4, shadcn/ui y Vercel AI SDK.
- [x] #13 `latexmk -pdf informe/Informe_Latex.tex` compila sin errores y el PDF incluye ambas imagenes.
- [x] #14 La tarea queda con `status: Done` sin invocar `task_complete`.
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Resumen

Informe LaTeX `informe/Informe_Latex.tex` reescrito para reflejar la fase 2 del proyecto (migracion a React 19 + Vite 7 + FastAPI + SSE, nuevo corpus de 1000 documentos y los 8 modelos soportados). PDF regenerado con `latexmk -pdf` en 8 paginas (`informe/Informe_Latex.pdf`, ~393 KB) sin errores ni referencias sin resolver; solo persisten advertencias cosmeticas de fuente (`T1/ptm/m/scit`) inofensivas.

## Cambios realizados

- `informe/figuras/` creada con `scraping_resultado_1000.png` y `markdown_export_1000.png` copiadas desde las capturas adjuntas del usuario.
- Preambulo: `\graphicspath{{figuras/}}` para resolver rutas y ampliacion del estilo `estiloBase` de `listings` con `extendedchars`, `inputencoding=utf8` y mapeo `literate` de caracteres del espanol para que los ejemplos YAML con tildes compilen sin error de UTF-8.
- Abstract y palabras clave reescritos para describir la arquitectura de siete modulos, los 8 modelos (3 Ollama + 5 OpenAI), el backend FastAPI+SSE y el frontend React+Vite+Tailwind+shadcn/ui.
- Introduccion ajustada para explicar la separacion de capas y la reutilizacion del API.
- Figura `fig:arq` en TikZ actualizada con siete modulos: se reemplaza el modulo Gradio por `Backend HTTP FastAPI + SSE` y se agrega `Frontend SPA React 19 + Vite 7`.
- Tabla `tab:stack` ampliada con filas para FastAPI + Uvicorn + sse-starlette + pydantic-settings y React 19 + Vite 7 + TypeScript + Tailwind v4 + shadcn/ui + Vercel AI SDK. Nota explicita sobre la UI Gradio como legacy en `src/app/legacy/app_gradio.py` (citando `abid2019gradio`).
- Tabla `tab:crawler` actualizada con `max_paginas=1000` y `profundidad_max=8`.
- Nueva subseccion `Resultados de la ejecucion` en scraping con tabla (1000/0/0/20/~51 min), comando `uv run python -m scripts.scrape --max-paginas 1000 --profundidad-maxima 8` y figura `fig:scraping` (imagen `scraping_resultado_1000.png`).
- Nueva subseccion `Resultados de la exportacion a Markdown` con tabla (1000 creados / 0 actualizados / 0 omitidos / 0 errores / ~32 s) y figura `fig:markdown` (imagen `markdown_export_1000.png`).
- Referencia al tamano del corpus en la seccion BM25 pasa de '45+' a '1000 documentos', y se documenta `POST /api/recargar-corpus` para reindexar bajo demanda.
- Tabla `tab:modelos` reescrita con los 3 modelos Ollama (`llama3.1:8b`, `gemma4:e2b`, `gemma4:e4b`) y los 5 modelos OpenAI (`gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `chatgpt-4o-latest`, `gpt-3.5-turbo`). Subseccion OpenAI documenta el cliente `src/qa/cliente_openai.py`, el manejo de `RateLimitError` con `Retry-After` y el uso de `OLLAMA_NUM_CTX` para el contexto de Ollama.
- Seccion Gradio reemplazada por `Backend HTTP FastAPI + SSE y Frontend React 19` (`sec:api_ui`) con subsecciones de backend, streaming SSE, modo dual (una sola pasada BM25 con `preparar_contexto_inferencia`), frontend React, prompt editable + trazabilidad BM25 y comandos de despliegue. Incluye la tabla `tab:endpoints` y la tabla de vistas React en `tab:ui`.
- Secciones de Evaluacion (tabla con filas para los 8 modelos), Discusion (se agrega subseccion `Ventajas de la Separacion Backend / Frontend` y se actualiza la lista de limitaciones) y Conclusiones (cinco aportes refinados al nuevo alcance) ajustadas al stack fase 2.
- Bibliografia ampliada con entradas para FastAPI, Uvicorn, sse-starlette, React 19, Vite, Tailwind CSS v4, shadcn/ui, Vercel AI SDK y el ADR interno `decision-2`.

## Compilacion

```bash
cd informe && latexmk -pdf -interaction=nonstopmode -halt-on-error Informe_Latex.tex
```

Resultado: exit code 0, `Informe_Latex.pdf` de 8 paginas, sin referencias ni citas sin resolver.
<!-- SECTION:FINAL_SUMMARY:END -->
