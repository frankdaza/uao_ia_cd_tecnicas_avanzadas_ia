"""Validación de data/structured/faqs.json contra faqs.schema.json (JSON Schema draft 2020-12)."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from src.rutas_workspace import encontrar_raiz_workspace

RAIZ_WORKSPACE = encontrar_raiz_workspace(Path(__file__).resolve())


def test_faqs_json_cumple_schema_y_utf8() -> None:
    ruta_schema = RAIZ_WORKSPACE / "data" / "structured" / "faqs.schema.json"
    ruta_datos = RAIZ_WORKSPACE / "data" / "structured" / "faqs.json"
    texto_schema = ruta_schema.read_text(encoding="utf-8")
    texto_datos = ruta_datos.read_text(encoding="utf-8")
    assert "\ufffd" not in texto_datos, (
        "El archivo faqs.json no debe contener caracteres de reemplazo UTF-8."
    )
    schema = json.loads(texto_schema)
    datos = json.loads(texto_datos)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(datos)
    assert len(datos["faqs"]) >= 5


def test_faqs_cubre_intents_contacto_horario_ubicacion() -> None:
    datos = json.loads(
        (RAIZ_WORKSPACE / "data" / "structured" / "faqs.json").read_text(
            encoding="utf-8"
        )
    )
    intents = {f["intent"] for f in datos["faqs"]}
    assert "linea_telefonica_pbx" in intents
    assert "horario_atencion_siau_pqrs" in intents
    assert "direccion_sede_principal" in intents
