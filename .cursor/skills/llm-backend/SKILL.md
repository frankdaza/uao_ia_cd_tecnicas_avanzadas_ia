---
name: llm-backend
description: Orquesta llamadas LLM con Ollama local o API OpenAI y un framework (LangChain o LlamaIndex). Usar al disenar src/qa o integracion con modelos.
---

# Backend LLM

> Mantener el mismo contenido en `.cursor/skills/llm-backend/` y `.claude/skills/llm-backend/`.

## Eleccion de modelo

- **Ollama**: modelo open source local; sin costo por token; requiere Ollama instalado y modelo descargado.
- **OpenAI (u otro API)**: requiere clave en `.env`; no commitear secretos.

## Framework

- Elegir **uno**: LangChain **o** LlamaIndex; envolver la llamada al modelo en funciones con interfaces claras (`generar_respuesta`, `invocar_modelo`).

## Configuracion

- Variables como `OLLAMA_BASE_URL`, `OPENAI_API_KEY`, `MODELO_LLM` en `.env.example` sin valores reales.
- Cargar con `pydantic-settings` o equivalente si el proyecto lo define.

## Identificadores

- Modulos y funciones en espanol ASCII; nombres de clases descriptivos (`ClienteLlm`, `ConfiguracionModelo`).

## Exposicion via HTTP y SSE (backend FastAPI)

El `PipelineQa` de `src/qa/pipeline.py` expone sus capacidades al frontend React a traves de `src/api/` (FastAPI + sse-starlette). Los metodos clave son:

- `responder(pregunta, modelo, prompt_sistema)` → sincrono, usado en `POST /api/qa`.
- `responder_stream(pregunta, modelo, prompt_sistema)` → `Iterator[(str, RespuestaQa|None)]`, usado en `POST /api/qa/stream` via SSE.
- `responder_openai_stream(pregunta, modelo_openai, ...)` → idem para OpenAI.
- `preparar_contexto_inferencia(pregunta, prompt_sistema)` → una sola pasada BM25; resultado compartido por ambos motores en modo dual.
- `stream_ollama_desde_contexto(ctx, modelo, t_inicio)` + `stream_openai_desde_contexto(ctx, modelo, t_inicio)` → streaming desde contexto pre-calculado; para el endpoint `POST /api/qa/dual/stream`.

**Regla clave**: en modo dual, `preparar_contexto_inferencia` se llama **UNA sola vez** por peticion; los dos streams consumen el mismo `ContextoInferencia`.

Ver skill `fastapi-sse-api` para patrones de implementacion SSE y tests.

## Modulo 2 (anticipo)

- El informe puede mencionar embeddings y base vectorial futura; en codigo del modulo 1 priorizar prompt + contexto textual segun la actividad.
