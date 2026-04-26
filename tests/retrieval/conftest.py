"""Fixtures compartidos para pruebas de recuperacion."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def dir_fixtures_markdown() -> Path:
    """Directorio con archivos .md de prueba (fundacion ficticia)."""
    return Path(__file__).resolve().parent / "fixtures" / "markdown"
