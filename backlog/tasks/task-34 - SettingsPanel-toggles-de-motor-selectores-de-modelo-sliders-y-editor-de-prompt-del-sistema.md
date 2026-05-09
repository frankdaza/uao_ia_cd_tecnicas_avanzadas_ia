---
id: TASK-34
title: >-
  SettingsPanel: toggles de motor, selectores de modelo, sliders y editor de
  prompt del sistema
status: Done
assignee: []
created_date: '2026-04-30 05:45'
updated_date: '2026-05-01 01:19'
labels:
  - frontend
  - settings
  - ui
dependencies:
  - TASK-32
priority: high
ordinal: 7
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Objetivo

Implementar el panel de configuración en `frontend/src/features/settings/`:

- `SettingsPanel.tsx`: contenedor del panel lateral; usa hooks useModels para poblar opciones
- `ModelSelector.tsx`: checkbox Usar Ollama + dropdown de modelos Ollama; checkbox Usar OpenAI + dropdown de modelos OpenAI (solo visible si openai_disponible)
- Slider num_ctx Ollama (4096..16384, step 2048) con Slider de shadcn/ui
- Checkbox + slider max_completion_tokens OpenAI
- `SystemPromptEditor.tsx`: Accordion con Textarea editable del prompt del sistema; botón Restaurar prompt que llama GET /api/prompt-defecto (o lo pide al backend)
- Botón Recargar corpus que dispara useReloadCorpus
- Badge de estado: API online/offline (usa useQuery a GET /api/salud)
- Todo el estado de configuración se persiste en un Context (SettingsContext) o Zustand store para que Chat.tsx lo lea al enviar
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 SettingsPanel.tsx renderiza en el sidebar de AppShell
- [ ] #2 Dropdowns de modelos se pueblan desde GET /api/modelos
- [ ] #3 Toggle Usar Ollama oculta/muestra el dropdown de modelos Ollama y el slider num_ctx
- [ ] #4 Toggle Usar OpenAI oculta/muestra el dropdown de modelos OpenAI y controles de max_tokens
- [ ] #5 Sin openai_disponible: toggle OpenAI deshabilitado con tooltip explicativo
- [ ] #6 SystemPromptEditor.tsx permite editar el prompt y restaurarlo
- [ ] #7 Botón Recargar corpus muestra toast de éxito vía useReloadCorpus
- [ ] #8 Estado de configuración disponible en Chat.tsx vía Context o store
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
SettingsContext.tsx: Context con estado usarOllama/usarOpenai/modeloOllama/modeloOpenai/numCtx/maxTokensOpenai/promptSistema; toQaPeticion() serializa al formato del backend. SettingsPanel.tsx: badge API online/offline (useSalud), Switch Ollama+OpenAI, Select de modelos desde useModels, Slider numCtx (4096-16384), Accordion+Textarea para prompt+Restaurar, botón Recargar corpus, Tooltip para OpenAI sin API key.
<!-- SECTION:FINAL_SUMMARY:END -->
