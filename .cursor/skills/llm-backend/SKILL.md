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

## Modulo 2 (anticipo)

- El informe puede mencionar embeddings y base vectorial futura; en codigo del modulo 1 priorizar prompt + contexto textual segun la actividad.
