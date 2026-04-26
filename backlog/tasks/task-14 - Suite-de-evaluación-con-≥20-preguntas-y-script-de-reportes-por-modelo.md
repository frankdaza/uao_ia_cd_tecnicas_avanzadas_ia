---
id: TASK-14
title: Suite de evaluación con ≥20 preguntas y script de reportes por modelo
status: To Do
assignee: []
created_date: '2026-04-26 20:18'
labels:
  - tests
  - llm
dependencies:
  - TASK-12
references:
  - .cursor/skills/qa-prompt-engineering/SKILL.md
  - >-
    backlog/docs/actividades/Técnicas Avanzadas de IA en Modelos de Lenguaje -
    Actividad del Módulo 1.pdf
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La actividad del módulo exige al menos **20 preguntas distintas** para evaluar precisión y coherencia (ver `backlog/docs/actividades/...pdf`). Necesitamos un set reproducible de preguntas y un script que genere reportes por modelo para anexar al informe.

## Objetivo

1. Definir un dataset de evaluación versionado en `tests/qa/preguntas_evaluacion.yml`.
2. Crear `scripts/evaluar_qa.py` que ejecute cada pregunta contra el `PipelineQa` con cada modelo y genere reportes en `data/processed/evaluaciones/`.

## Dataset propuesto (`tests/qa/preguntas_evaluacion.yml`)

```yaml
preguntas:
  - id: 1
    texto: "¿Qué es la Fundación Valle del Lili?"
    categoria: institucional
    archivo_esperado: quienes-somos.md
  - id: 2
    texto: "¿Dónde está ubicada la Fundación?"
    categoria: contacto
    archivo_esperado: contacto.md
  - id: 3
    texto: "¿Cuáles son los servicios de cardiología?"
    categoria: servicios
    archivo_esperado: ~ # opcional, dejar null si no se conoce el slug exacto
  # ... hasta al menos 20 entradas cubriendo:
  # - quiénes son / historia / misión / visión
  # - especialidades médicas (cardiología, oncología, pediatría, neurología, trasplantes)
  # - sedes / ubicación / horarios
  # - contacto (teléfonos, correos, formularios)
  # - procesos (citas, urgencias, hospitalización)
  # - sostenibilidad / responsabilidad social
  # - investigación / docencia
  # - una pregunta deliberadamente FUERA DE ALCANCE (debe responder "No tengo información suficiente")
```

## Comando del script

```bash
uv run python -m scripts.evaluar_qa --modelos llama3.1:8b gemma4:e2b
```

## Salida esperada

`data/processed/evaluaciones/<modelo_slug>__YYYY-MM-DD.md` con:

- Encabezado con: modelo, total de preguntas, fecha, resumen (latencia promedio, tasa de "No tengo información suficiente").
- Una sección por pregunta:

  ```markdown
  ### Pregunta 1 — ¿Qué es la Fundación Valle del Lili?

  - **Categoría:** institucional
  - **Archivo esperado:** quienes-somos.md
  - **Archivo recuperado:** quienes-somos.md (✅ coincide)
  - **Score BM25:** 12.34
  - **Latencia:** 4521 ms
  - **Respuesta:**

    > La Fundación Valle del Lili es una institución...
  ```

- Tabla resumen al final con: total, aciertos en archivo (cuando hay `archivo_esperado`), respuestas con "No tengo información suficiente".

## Detalles técnicos

- Cargar el YAML con `pyyaml`.
- Crear el pipeline una sola vez por modelo, iterar las preguntas.
- Escribir el reporte como Markdown.
- Si el modelo no está disponible (`ModeloNoDisponibleError`), abortar **solo** ese reporte y continuar con los demás modelos; reportar el error en stdout.
- Permitir `--solo-pregunta <id>` para depurar.

## Identificadores ASCII

- `cargar_dataset`, `evaluar_modelo`, `escribir_reporte`, `parsear_argumentos`, `RegistroEvaluacion`.

## Caso de negocio

El informe del módulo exige una sección de **Resultados** con ejemplos de preguntas y respuestas y discusión de limitaciones. Estos reportes son la fuente de verdad para esa sección.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 tests/qa/preguntas_evaluacion.yml contiene >= 20 preguntas con id, texto, categoria y archivo_esperado opcional
- [ ] #2 Al menos 1 pregunta del dataset es deliberadamente FUERA DE ALCANCE para validar la respuesta 'No tengo información suficiente'
- [ ] #3 Las categorías cubren al menos: institucional, servicios, contacto, procesos, fuera-de-alcance
- [ ] #4 uv run python -m scripts.evaluar_qa --modelos llama3.1:8b gemma4:e2b genera 2 archivos .md en data/processed/evaluaciones/
- [ ] #5 Cada reporte contiene una entrada por pregunta con archivo recuperado, score, latencia y respuesta del LLM
- [ ] #6 Cada reporte tiene una tabla resumen con total, aciertos en archivo y conteo de 'No tengo información suficiente'
- [ ] #7 Si un modelo no está disponible en Ollama, el script reporta el error y continúa con los demás modelos
- [ ] #8 --solo-pregunta <id> ejecuta solo esa pregunta y genera un reporte parcial
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1) Redactar tests/qa/preguntas_evaluacion.yml con 20+ preguntas alineadas al sitio
2) Crear scripts/evaluar_qa.py con argparse
3) Cargar el YAML y construir pipeline por modelo
4) Iterar preguntas y acumular RegistroEvaluacion
5) Escribir reporte Markdown por modelo en data/processed/evaluaciones/
6) Tabla resumen final
7) Smoke run con --solo-pregunta 1
8) Documentar en README
<!-- SECTION:PLAN:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 scripts/evaluar_qa.py es ejecutable con uv run python -m scripts.evaluar_qa
- [ ] #2 El YAML de preguntas está commiteado y validado contra un esquema mínimo
- [ ] #3 data/processed/evaluaciones/ existe y está commiteable (los .md de muestra se incluyen en el informe; el directorio puede estar en .gitignore para corridas grandes y agregar ejemplos manuales en docs/)
<!-- DOD:END -->
