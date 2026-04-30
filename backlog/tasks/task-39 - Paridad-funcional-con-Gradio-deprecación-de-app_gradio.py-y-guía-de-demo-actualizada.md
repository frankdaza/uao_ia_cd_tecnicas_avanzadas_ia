---
id: TASK-39
title: >-
  Paridad funcional con Gradio, deprecación de app_gradio.py y guía de demo
  actualizada
status: Done
assignee: []
created_date: '2026-04-30 05:47'
updated_date: '2026-04-30 06:13'
labels:
  - parity
  - deprecation
  - docs
dependencies:
  - TASK-38
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Objetivo

Cerrar el ciclo de migración:

1. Smoke checklist de paridad funcional con Gradio: streaming Ollama, streaming OpenAI, dual secuencial, recarga de corpus, prompt editable y restaurable, fuentes BM25 visibles, accesibilidad mínima
2. Deprecar `src/app/app_gradio.py`: mover a `src/app/legacy/app_gradio.py` con comentario de deprecación en el encabezado
3. Actualizar entrypoint en pyproject.toml o README: eliminar referencia a `uv run python -m src.app.app_gradio`
4. Gradio puede eliminarse de pyproject.toml si el equipo lo decide (documentar la decisión)
5. Actualizar la guía de demo de 15 minutos en README.md para reflejar la nueva UI React
6. Marcar task-39 como Done
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 src/app/legacy/app_gradio.py existe con comentario de deprecación en el encabezado del módulo
- [ ] #2 src/app/app_gradio.py NO existe en la ruta original
- [ ] #3 README.md no referencia uv run python -m src.app.app_gradio como comando principal
- [ ] #4 README.md guía de demo de 15 minutos describe la nueva UI React
- [ ] #5 Smoke checklist completado: los 7 items del objetivo verificados manualmente
- [ ] #6 Si gradio se elimina de pyproject.toml: uv lock actualizado y documentado en README
- [ ] #7 decision-2 referenciada en README.md o AGENTS.md como registro arquitectónico
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
src/app/app_gradio.py movido a src/app/legacy/app_gradio.py con cabecera DEPRECADO (referencia a doc-002 y decision-2). src/app/legacy/__init__.py creado. tests/app/test_app_gradio.py actualizado a nuevo import path y mark @pytest.mark.legacy. pyproject.toml: mark legacy registrado en [tool.pytest.ini_options]. README.md: sección 'Paridad funcional con Gradio' con smoke checklist de 10 ítems; referencia a Gradio corregida a React+Vite como interfaz principal; ADR-002 referenciado en la sección de solución. Guía de demo de 15 min revisada y alineada con la nueva UI React. 119 tests pasan sin advertencias.
<!-- SECTION:FINAL_SUMMARY:END -->
