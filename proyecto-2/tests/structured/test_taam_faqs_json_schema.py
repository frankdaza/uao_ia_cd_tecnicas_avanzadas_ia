"""Validacion de data/structured/taam_faqs.json contra taam_faqs.schema.json."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from src.rutas_workspace import encontrar_raiz_workspace

RAIZ_WORKSPACE = encontrar_raiz_workspace(Path(__file__).resolve())


def test_taam_faqs_json_cumple_schema_y_utf8() -> None:
    ruta_schema = RAIZ_WORKSPACE / "data" / "structured" / "taam_faqs.schema.json"
    ruta_datos = RAIZ_WORKSPACE / "data" / "structured" / "taam_faqs.json"
    texto_datos = ruta_datos.read_text(encoding="utf-8")
    assert "\ufffd" not in texto_datos, (
        "El archivo taam_faqs.json no debe contener caracteres de reemplazo UTF-8."
    )
    schema = json.loads(ruta_schema.read_text(encoding="utf-8"))
    datos = json.loads(texto_datos)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(datos)
    assert len(datos["faqs"]) >= 5


def test_taam_faqs_cubre_intents_demo_sustentacion() -> None:
    datos = json.loads(
        (RAIZ_WORKSPACE / "data" / "structured" / "taam_faqs.json").read_text(
            encoding="utf-8"
        )
    )
    intents = {f["intent"] for f in datos["faqs"]}
    assert "caminata_postoperatoria" in intents
    assert "signos_alarma" in intents
    assert "dolor_postoperatorio_leve" in intents
