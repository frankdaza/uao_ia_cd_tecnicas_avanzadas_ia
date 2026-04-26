"""Pruebas del script de evaluación y el dataset YAML."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from scripts import evaluar_qa
from src.qa.pipeline import RespuestaQa

_DATASET = Path(__file__).resolve().parent / "preguntas_evaluacion.yml"


def test_dataset_yaml_cumple_cantidad_y_schema() -> None:
    p = evaluar_qa.cargar_dataset(_DATASET)
    assert len(p) >= 20
    for fila in p:
        assert "id" in fila
        assert "texto" in fila
        assert "categoria" in fila
        assert "archivo_esperado" in fila
        assert isinstance(fila["texto"], str)
        assert isinstance(fila["categoria"], str)


def test_dataset_incluye_fuera_de_alcance() -> None:
    p = evaluar_qa.cargar_dataset(_DATASET)
    out = [x for x in p if str(x.get("categoria", "")) == "fuera-de-alcance"]
    assert len(out) >= 1
    assert out[0].get("archivo_esperado") is None


def test_dataset_categorias_solicitadas() -> None:
    p = evaluar_qa.cargar_dataset(_DATASET)
    cats = {str(x["categoria"]) for x in p}
    for esperada in (
        "institucional",
        "servicios",
        "contacto",
        "procesos",
        "fuera-de-alcance",
    ):
        assert esperada in cats


def test_modelo_a_slug() -> None:
    assert "llama3" in evaluar_qa._modelo_a_slug("llama3.1:8b")
    assert evaluar_qa._modelo_a_slug("a/b::c") == "a-b-c"


def test_escribir_reporte_incluye_tabla_y_preguntas(tmp_path: Path) -> None:
    r = RespuestaQa(
        texto="No tengo información suficiente",
        archivo_fuente=Path("nuestra-institucion.md"),
        source_url="u",
        titulo="t",
        modelo="m1",
        score_recuperacion=3.0,
        latencia_ms=10,
        prompt_sistema_usado="p",
    )
    reg = evaluar_qa.RegistroEvaluacion(
        pregunta_id=1,
        texto_pregunta="Hola",
        categoria="institucional",
        archivo_esperado="nuestra-institucion.md",
        respuesta=r,
        indice_muestra=1,
    )
    res = evaluar_qa.ResultadoModelo(modelo="m1", registros=[reg])
    dest = tmp_path / "r.md"
    evaluar_qa.escribir_reporte(res, dest, date(2026, 4, 26))
    t = dest.read_text(encoding="utf-8")
    assert "Resumen tabular" in t
    assert "Aciertos en archivo" in t
    assert "No tengo información suficiente" in t
    assert "coincide" in t
    assert "10 ms" in t
