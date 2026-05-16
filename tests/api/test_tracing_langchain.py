"""Pruebas del helper de tracing LangChain/LangSmith (sin red)."""

from __future__ import annotations

import os

import pytest

from src.api.configuracion import Configuracion, obtener_configuracion
from src.api.tracing_langchain import aplicar_tracing_langchain_desde_config


@pytest.fixture(autouse=True)
def limpiar_cache_configuracion() -> None:
    """Evita contaminacion entre casos por ``lru_cache``."""
    obtener_configuracion.cache_clear()
    yield
    obtener_configuracion.cache_clear()


def test_aplicar_tracing_no_escribe_si_desactivado(monkeypatch: pytest.MonkeyPatch) -> None:
    for clave in (
        "LANGCHAIN_TRACING_V2",
        "LANGCHAIN_API_KEY",
        "LANGCHAIN_PROJECT",
        "LANGCHAIN_ENDPOINT",
    ):
        monkeypatch.delenv(clave, raising=False)

    cfg = Configuracion.model_construct(trazas_langchain_activas=False)
    aplicar_tracing_langchain_desde_config(cfg)

    assert "LANGCHAIN_TRACING_V2" not in os.environ
    assert "LANGCHAIN_API_KEY" not in os.environ


def test_aplicar_tracing_no_escribe_si_falta_clave(monkeypatch: pytest.MonkeyPatch) -> None:
    for clave in (
        "LANGCHAIN_TRACING_V2",
        "LANGCHAIN_API_KEY",
        "LANGCHAIN_PROJECT",
        "LANGCHAIN_ENDPOINT",
    ):
        monkeypatch.delenv(clave, raising=False)

    cfg = Configuracion.model_construct(
        trazas_langchain_activas=True,
        clave_api_trazas_langchain=None,
    )
    aplicar_tracing_langchain_desde_config(cfg)

    assert os.environ.get("LANGCHAIN_TRACING_V2") != "true"


def test_aplicar_tracing_escribe_env_cuando_habilitado(monkeypatch: pytest.MonkeyPatch) -> None:
    for clave in (
        "LANGCHAIN_TRACING_V2",
        "LANGCHAIN_API_KEY",
        "LANGCHAIN_PROJECT",
        "LANGCHAIN_ENDPOINT",
    ):
        monkeypatch.delenv(clave, raising=False)

    cfg = Configuracion.model_construct(
        trazas_langchain_activas=True,
        clave_api_trazas_langchain="sk-prueba-local",
        proyecto_trazas_langchain="proyecto-pytest",
        url_endpoint_trazas_langchain="https://ejemplo.invalido",
    )
    aplicar_tracing_langchain_desde_config(cfg)

    assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
    assert os.environ.get("LANGCHAIN_API_KEY") == "sk-prueba-local"
    assert os.environ.get("LANGCHAIN_PROJECT") == "proyecto-pytest"
    assert os.environ.get("LANGCHAIN_ENDPOINT") == "https://ejemplo.invalido"


def test_tracing_con_prefijo_langsmith_en_configuracion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Alias LANGSMITH_* (guia LangSmith) mapean igual que LANGCHAIN_*."""
    for clave in (
        "LANGCHAIN_TRACING_V2",
        "LANGSMITH_TRACING",
        "LANGCHAIN_API_KEY",
        "LANGSMITH_API_KEY",
        "LANGCHAIN_PROJECT",
        "LANGSMITH_PROJECT",
        "LANGCHAIN_ENDPOINT",
        "LANGSMITH_ENDPOINT",
    ):
        monkeypatch.delenv(clave, raising=False)

    cfg = Configuracion.model_validate(
        {
            "LANGSMITH_TRACING": "true",
            "LANGSMITH_API_KEY": "lsv2_clave_prueba",
            "LANGSMITH_PROJECT": "proyecto-langsmith-pytest",
            "LANGSMITH_ENDPOINT": "https://api.smith.langchain.com",
        }
    )
    assert cfg.trazas_langchain_activas is True
    assert cfg.clave_api_trazas_langchain == "lsv2_clave_prueba"
    assert cfg.proyecto_trazas_langchain == "proyecto-langsmith-pytest"
    assert cfg.url_endpoint_trazas_langchain == "https://api.smith.langchain.com"

    aplicar_tracing_langchain_desde_config(cfg)

    assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
    assert os.environ.get("LANGCHAIN_API_KEY") == "lsv2_clave_prueba"
    assert os.environ.get("LANGCHAIN_PROJECT") == "proyecto-langsmith-pytest"
    assert os.environ.get("LANGCHAIN_ENDPOINT") == "https://api.smith.langchain.com"


def test_env_ignore_empty_langchain_tracing_v2_como_en_docker_compose(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Compose pasa `${VAR:-}` como cadena vacia si VAR no esta en el host; no debe fallar el bool."""
    for clave in (
        "LANGCHAIN_TRACING_V2",
        "LANGSMITH_TRACING",
        "LANGCHAIN_API_KEY",
        "LANGSMITH_API_KEY",
        "LANGCHAIN_PROJECT",
        "LANGSMITH_PROJECT",
        "LANGCHAIN_ENDPOINT",
        "LANGSMITH_ENDPOINT",
    ):
        monkeypatch.delenv(clave, raising=False)

    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "")
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGCHAIN_API_KEY", "clave-docker-compose")

    obtener_configuracion.cache_clear()
    cfg = Configuracion()
    assert cfg.trazas_langchain_activas is True
    assert cfg.clave_api_trazas_langchain == "clave-docker-compose"
