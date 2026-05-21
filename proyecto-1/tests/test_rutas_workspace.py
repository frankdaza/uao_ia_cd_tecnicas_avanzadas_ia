"""Pruebas de resolucion de raices workspace vs proyecto."""

from __future__ import annotations

from pathlib import Path

from src.rutas_workspace import (
    encontrar_raiz_proyecto,
    encontrar_raiz_workspace,
    resolver_ruta_workspace,
)


def test_raiz_proyecto_contiene_pyproject() -> None:
    raiz = encontrar_raiz_proyecto(Path(__file__).resolve())
    assert (raiz / "pyproject.toml").is_file()
    assert (raiz / "src" / "api").is_dir()


def test_raiz_workspace_contiene_data_markdown() -> None:
    ws = encontrar_raiz_workspace(Path(__file__).resolve())
    assert (ws / "data" / "markdown").is_dir()


def test_resolver_faqs_en_workspace() -> None:
    ruta = resolver_ruta_workspace("data/structured/faqs.json")
    assert ruta.is_file()
