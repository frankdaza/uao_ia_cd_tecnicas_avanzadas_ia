"""Fixtures compartidos para pruebas de Q&A."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def dir_fixtures_markdown() -> Path:
    """Mismo corpus de prueba que ``tests/retrieval/fixtures/markdown``."""
    return (
        Path(__file__).resolve().parent.parent / "retrieval" / "fixtures" / "markdown"
    )
