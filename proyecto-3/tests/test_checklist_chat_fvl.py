"""Pruebas del checklist de chat FVL (documentacion, sin secretos)."""

from __future__ import annotations

import re
from pathlib import Path

_RUTA_DOC = Path(__file__).resolve().parents[1] / "docs" / "checklist-pruebas-chat-fvl.md"
_PATRON_TOKEN = re.compile(r"\d{9,}:[A-Za-z0-9_-]{25,}")


def test_checklist_existe() -> None:
    assert _RUTA_DOC.is_file()


def test_checklist_cinco_categorias_y_fuera_corpus() -> None:
    texto = _RUTA_DOC.read_text(encoding="utf-8").lower()
    for categoria in (
        "cuidados",
        "medicacion",
        "signos alarma",
        "dieta",
        "actividad",
        "fuera de corpus",
        "precio del dolar",
    ):
        assert categoria in texto, f"Falta categoria o pregunta: {categoria}"
    for id_prueba in ("fvl-01", "fvl-02", "fvl-03", "fvl-04", "fvl-05", "fvl-06"):
        assert id_prueba in texto


def test_checklist_menciona_jsonl_y_sessions() -> None:
    texto = _RUTA_DOC.read_text(encoding="utf-8").lower()
    assert "openfang sessions" in texto
    assert "jsonl" in texto


def test_checklist_prueba_negativa_sin_ingesta() -> None:
    texto = _RUTA_DOC.read_text(encoding="utf-8").lower()
    assert "sin ingesta" in texto or "prueba negativa" in texto
    assert "contar_memorias_semanticas" in texto


def test_checklist_sin_token_real() -> None:
    contenido = _RUTA_DOC.read_text(encoding="utf-8")
    assert not _PATRON_TOKEN.search(contenido)
