---
id: TASK-15
title: 'README final, guía de demo y documentación del informe del módulo'
status: Done
assignee: []
created_date: '2026-04-26 20:19'
updated_date: '2026-04-26 21:57'
labels:
  - docs
dependencies:
  - TASK-13
  - TASK-14
references:
  - >-
    backlog/docs/actividades/Técnicas Avanzadas de IA en Modelos de Lenguaje -
    Actividad del Módulo 1.pdf
ordinal: 26
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La actividad del módulo exige un **informe** con secciones específicas y una **sustentación en vivo** de 15 minutos sin diapositivas. El README es la pieza central que cualquier evaluador o miembro del equipo usará para reproducir y entender el MVP.

## Objetivo

Reescribir `README.md` con la estructura completa del informe y un mini-runbook para la demo. Adicionalmente, agregar el archivo de decisión en `backlog/decisions/` documentando la decisión arquitectónica clave del MVP (convención de nombre: `decision-1 - MVP-BM25-Archivo-Completo.md`).

## Estructura del README

1. **Título y resumen**
   - "Sistema Q&A sobre la Fundación Valle del Lili — MVP fase 1"
   - 2-3 líneas describiendo qué hace y qué NO hace.

2. **Descripción del problema**
   - "Necesidad de un canal de comunicación automatizado y preciso para la Fundación Valle del Lili."

3. **Planteamiento de la solución**
   - Q&A local con scraping → Markdown → BM25 a nivel archivo → Ollama (LLM local).
   - Decisiones explícitas: **sin** chunking, **sin** embeddings, **sin** vector DB en esta fase.

4. **Preparación de los datos**
   - `data/raw/`: HTML descargado del dominio `valledellili.org` respetando `robots.txt`.
   - `data/markdown/valledellili-org/`: 1 `.md` por página con front matter YAML.
   - Comandos:

     ```bash
     uv run python -m scripts.scrape --max-paginas 200
     uv run python -m scripts.export_markdown
     ```

5. **Modelado**
   - Recuperación: BM25 a nivel archivo (`rank-bm25`).
   - Modelos LLM: `llama3.1:8b` y `gemma4:e2b` vía Ollama.
   - Diseño del prompt: zero-shot con instrucción de "no inventar"; tono profesional, divertido y amable en español colombiano.

6. **Cómo correr la app**

   ```bash
   uv sync
   ollama pull llama3.1:8b
   ollama pull gemma4:e2b   # si no existe, anotar como limitación
   uv run python -m src.app.app_gradio
   ```

7. **Resultados**
   - Apuntar a `data/processed/evaluaciones/` (reportes generados por task-14).
   - Resumen tabular: # preguntas, # aciertos en archivo recuperado, # respuestas con "No tengo información suficiente", latencia promedio.

8. **Limitaciones conocidas**
   - Páginas que superen `num_ctx=8192`: el LLM podría truncar.
   - BM25 a nivel archivo puede recuperar la página equivocada cuando varias secciones comparten vocabulario.
   - `gemma4:e2b` puede no existir en el registro oficial de Ollama; si falla, usar solo `llama3.1:8b` y dejarlo documentado.

9. **Roadmap (Módulo 2)**
   - Chunking semántico.
   - Embeddings + base vectorial (Chroma o FAISS).
   - Re-ranking.

10. **Guía de demo (15 min)**
    - 3 minutos: motivación y pipeline.
    - 7 minutos: 4 preguntas en vivo cubriendo: institucional, servicios, contacto y una **fuera de alcance**.
    - 3 minutos: edición del prompt en la UI mostrando cambio de comportamiento.
    - 2 minutos: limitaciones y roadmap.

## ADR (Architectural Decision Record)

Crear `backlog/decisions/decision-1 - MVP-BM25-Archivo-Completo.md` con front matter YAML (`id`, `title`, `date`, `status`) y cuerpo alineado al estilo Backlog.md. Contenido equivalente al borrador siguiente:

```markdown
---
id: decision-1
title: MVP usa BM25 a nivel archivo (sin chunking ni embeddings)
date: '2026-04-26'
status: accepted
---

## Contexto
...

## Decisión
...

## Consecuencias
### Positivas
...
### Negativas / riesgos
...

## Alternativas consideradas
...
```

## Identificadores ASCII

- N/A (la task es de documentación; los archivos referenciados ya existen).

## Notas de revisión

- El README debe estar en español latinoamericano.
- Mantener los comandos `uv run` consistentes con el resto de la documentación.
- No mencionar en el README la biblioteca de interfaz que no forma parte del MVP (validar que solo aparece Gradio).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 README.md contiene las 10 secciones definidas (resumen, problema, solución, datos, modelado, cómo correr, resultados, limitaciones, roadmap, guía de demo)
- [x] #2 Todos los comandos de README ejecutan con uv run y son válidos en la estructura del repo
- [x] #3 README solo documenta Gradio como interfaz web
- [x] #4 README incluye apuntador explícito a data/processed/evaluaciones/ con resultados de task-14
- [x] #5 README documenta el pull de los modelos: 'ollama pull llama3.1:8b' y 'ollama pull gemma4:e2b' (con nota sobre posible no disponibilidad)
- [x] #6 Existe `backlog/decisions/decision-1 - MVP-BM25-Archivo-Completo.md` con front matter, Contexto, Decisión, Consecuencias y Alternativas
- [x] #7 La guía de demo del README cabe en 15 minutos con bloques de tiempo claros
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1) Reescribir README.md con las 10 secciones
2) Validar comandos uv run uno a uno
3) Crear backlog/decisions/decision-1 - MVP-BM25-Archivo-Completo.md
4) Validar que el README no documenta otras bibliotecas de interfaz
5) Lectura cruzada con un compañero para asegurar claridad
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
README.md reescrito con las 10 secciones del informe (resumen, problema, solución, datos, modelado, ejecución, resultados vía data/processed/evaluaciones/, limitaciones, roadmap y guía de demo 15 min). Comandos validados con uv run (--help en scrape/export_markdown; import de app_gradio). Decisión de arquitectura registrada como decision-1 en backlog/decisions/decision-1 - MVP-BM25-Archivo-Completo.md. Interfaz documentada: solo Gradio.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Un nuevo desarrollador puede levantar el proyecto siguiendo solo el README sin preguntas adicionales
- [x] #2 El README no contiene referencias a bibliotecas de interfaz distintas de Gradio
- [x] #3 El ADR 0001 está commiteado en backlog/decisions/
<!-- DOD:END -->
