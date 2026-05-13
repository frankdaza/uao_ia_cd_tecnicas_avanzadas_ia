"""
Configuracion compartida de pytest para todo el arbol ``tests/``.

Markers (ver tambien ``[tool.pytest.ini_options]`` en ``pyproject.toml``):

- ``network``: requiere ``EJECUTAR_TESTS_CON_RED=1`` (los tests lo comprueban inline).
- ``integration_ollama``: contra servidor Ollama local; skip si no hay servicio.
- ``integration_postgres``: contra PostgreSQL real; activar con
  ``EJECUTAR_INTEGRACION_POSTGRES=1`` (los tests suelen validar el env inline).
- ``integration_qdrant``: contra un Qdrant accesible por URL (no ``:memory:``);
  activar con ``EJECUTAR_INTEGRACION_QDRANT=1``. Sin esa variable, los tests
  marcados se omiten para no bloquear desarrollo sin Docker.
- ``e2e_modulo2``: contra la API HTTP real (docker-compose); activar con
  ``EJECUTAR_E2E_MODULO2=1`` (ver ``scripts/README.md`` y ``tests/e2e/``).
- ``legacy``: app Gradio u otras piezas deprecadas conservadas como referencia.
- ``legacy_bm25``: pipeline M1 con recuperador BM25 bajo ``src/legacy/``; se puede
  excluir con ``pytest -m "not legacy_bm25"``.

Ejemplos::

    uv run pytest
    uv run pytest -m "not legacy_bm25"
    EJECUTAR_INTEGRACION_POSTGRES=1 uv run pytest -m integration_postgres
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi import FastAPI, Request

from src.api.dependencias import obtener_sesion_db
from src.api.main import crear_app


async def sesion_db_falsa(_request: Request) -> AsyncGenerator[AsyncMock, None]:
    """Replica el contrato de ``obtener_sesion_db`` sin PostgreSQL."""
    sesion = AsyncMock()
    try:
        yield sesion
        await sesion.commit()
    except Exception:
        await sesion.rollback()
        raise


def grafo_agente_minimo_mock() -> MagicMock:
    """Grafo LangGraph sustituido por un mock que no emite eventos."""
    grafo = MagicMock()

    async def _stream_vacio(*_a: object, **_k: object):
        if False:
            yield {}

    grafo.astream_events = MagicMock(side_effect=lambda *a, **k: _stream_vacio())
    return grafo


@pytest_asyncio.fixture
async def fastapi_app_sesion_mock() -> AsyncGenerator[FastAPI, None]:
    """App FastAPI con ``obtener_sesion_db`` sobrescrito (sin Postgres real)."""
    app = crear_app()
    app.state.grafo_agente = grafo_agente_minimo_mock()
    app.dependency_overrides[obtener_sesion_db] = sesion_db_falsa
    yield app
    app.dependency_overrides.clear()


def pytest_runtest_setup(item: pytest.Item) -> None:
    if "integration_qdrant" in item.keywords:
        if os.environ.get("EJECUTAR_INTEGRACION_QDRANT", "").strip() != "1":
            pytest.skip(
                "Marcador integration_qdrant: definir EJECUTAR_INTEGRACION_QDRANT=1 "
                "y un QDRANT_URL accesible (p. ej. contenedor Docker)."
            )
    if "e2e_modulo2" in item.keywords:
        if os.environ.get("EJECUTAR_E2E_MODULO2", "").strip() != "1":
            pytest.skip(
                "Marcador e2e_modulo2: definir EJECUTAR_E2E_MODULO2=1, levantar la API "
                "(p. ej. docker compose) y revisar scripts/README.md (BASE_URL / MOCK_LLM)."
            )
