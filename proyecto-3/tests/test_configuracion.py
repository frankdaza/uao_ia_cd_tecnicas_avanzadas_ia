"""Pruebas de configuracion pydantic-settings (proyecto-3)."""

from __future__ import annotations

import pytest

from src.configuracion import Configuracion, obtener_configuracion


@pytest.fixture(autouse=True)
def limpiar_cache_configuracion() -> None:
    obtener_configuracion.cache_clear()
    yield
    obtener_configuracion.cache_clear()


def test_defaults_sin_env() -> None:
    cfg = Configuracion(_env_file=None)
    assert cfg.openai_model == "gpt-4o-mini"
    assert cfg.openai_embedding_model == "text-embedding-3-small"
    assert cfg.log_level == "INFO"
    assert cfg.ollama_base_url == "http://127.0.0.1:11434"
    assert cfg.openai_api_key == ""


def test_openfang_home_absoluto() -> None:
    cfg = Configuracion(_env_file=None)
    ruta = cfg.openfang_home_absoluto()
    assert ruta.name == "data"
    assert ruta.parent.name == "openfang"
    assert ruta.parent.parent == cfg.raiz_proyecto()


def test_raiz_workspace_detecta_monorepo() -> None:
    cfg = Configuracion(_env_file=None, uao_workspace_root="")
    raiz = cfg.raiz_workspace()
    proyecto = cfg.raiz_proyecto()
    if (proyecto.parent / "data" / "markdown").is_dir():
        assert raiz == proyecto.parent.resolve()
    else:
        assert raiz == proyecto.resolve()


def test_exigir_openai_api_key_vacio() -> None:
    cfg = Configuracion(_env_file=None, openai_api_key="")
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        cfg.exigir_openai_api_key()
