"""Pruebas del lifespan FastAPI (warmup reranker, sin cargar modelos reales)."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from src.api.configuracion import Configuracion, obtener_configuracion
from src.api.main import crear_app


@pytest.fixture(autouse=True)
def limpiar_cache_config() -> None:
    obtener_configuracion.cache_clear()
    yield
    obtener_configuracion.cache_clear()


def test_lifespan_warmup_reranker_si_habilitado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RAG_RERANKER_HABILITADO", "1")
    monkeypatch.setenv("RAG_RERANKER_MODELO", "modelo-falso-warmup")
    obtener_configuracion.cache_clear()
    vistos: list[str] = []

    def _fake_warmup(cfg: Configuracion) -> None:
        vistos.append(str(cfg.rag_reranker_modelo))

    import src.api.main as main_mod

    monkeypatch.setattr(main_mod, "_warmup_reranker", _fake_warmup)
    app = crear_app()
    with TestClient(app, raise_server_exceptions=True) as client:
        r = client.get("/api/salud")
    assert r.status_code == 200
    assert vistos == ["modelo-falso-warmup"]


def test_lifespan_sin_warmup_si_reranker_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAG_RERANKER_HABILITADO", "0")
    obtener_configuracion.cache_clear()
    vistos: list[str] = []

    def _fake_warmup(cfg: Configuracion) -> None:
        vistos.append("no_deberia")

    import src.api.main as main_mod

    monkeypatch.setattr(main_mod, "_warmup_reranker", _fake_warmup)
    app = crear_app()
    with TestClient(app, raise_server_exceptions=True) as client:
        r = client.get("/api/salud")
    assert r.status_code == 200
    assert vistos == []
