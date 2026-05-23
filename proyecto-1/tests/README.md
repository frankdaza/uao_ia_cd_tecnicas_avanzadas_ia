# Suite de pruebas (pytest)

Este directorio agrupa pruebas automatizadas del backend (FastAPI, agente M2, RAG, scripts).

## Entorno sin LLM real (recomendado en CI y laptops)

El agente puede ejecutarse en modo determinista sin llamadas a OpenAI para el router ni el compositor:

```bash
export MOCK_LLM=1
uv run pytest tests/ -v
```

Solo RAG / subconjuntos:

```bash
export MOCK_LLM=1
uv run pytest tests/rag/ -v
uv run pytest tests/api/ tests/agentes/ tests/scripts/ -v
```

## Cobertura (RAG, agente y API)

```bash
export MOCK_LLM=1
uv run pytest tests/ --cov=src.rag --cov=src.agentes --cov=src.api --cov-report=term
```

## Tiempo de ejecucion de referencia

En MacBook Apple Silicon (M1) o runner Linux comparable, la suma de `tests/rag/`, `tests/api/`, `tests/agentes/` y `tests/scripts/` con `MOCK_LLM=1` y sin servicios externos obligatorios debe permanecer **por debajo de 60 s**. Si alguna prueba marcada como lenta supera ese presupuesto en hardware modesto, conviene aislarla con `@pytest.mark.slow` y excluirla del comando por defecto.

## Marcadores utiles

Ver comentarios en `tests/conftest.py` y `[tool.pytest.ini_options]` en `pyproject.toml` para `integration_postgres`, `integration_qdrant`, `e2e_modulo2`, etc.
