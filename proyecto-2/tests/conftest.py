"""Fixtures compartidas entre paquetes de tests en proyecto-2."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.configuracion import obtener_configuracion


@pytest.fixture(autouse=True)
def limpiar_cache_config() -> None:
    obtener_configuracion.cache_clear()
    yield
    obtener_configuracion.cache_clear()


@pytest.fixture
def workspace_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Workspace aislado con carpeta data/taam para PDFs de prueba."""
    raiz = tmp_path / "workspace"
    (raiz / "data" / "taam").mkdir(parents=True)
    (raiz / "data" / "markdown").mkdir(parents=True)
    monkeypatch.setenv("UAO_WORKSPACE_ROOT", str(raiz))
    obtener_configuracion.cache_clear()
