"""Validacion del dataset YAML de preguntas (sin script de evaluacion batch)."""

from __future__ import annotations

from pathlib import Path

import yaml

_DATASET = Path(__file__).resolve().parent / "preguntas_evaluacion.yml"


def _cargar_preguntas(ruta: Path) -> list[dict[str, object]]:
    with ruta.open(encoding="utf-8") as f:
        raiz = yaml.safe_load(f)
    assert isinstance(raiz, dict)
    items = raiz.get("preguntas")
    assert isinstance(items, list)
    return items


def test_dataset_yaml_cumple_cantidad_y_schema() -> None:
    p = _cargar_preguntas(_DATASET)
    assert len(p) >= 20
    for fila in p:
        assert "id" in fila
        assert "texto" in fila
        assert "categoria" in fila
        assert "archivo_esperado" in fila
        assert isinstance(fila["texto"], str)
        assert isinstance(fila["categoria"], str)


def test_dataset_incluye_fuera_de_alcance() -> None:
    p = _cargar_preguntas(_DATASET)
    out = [x for x in p if str(x.get("categoria", "")) == "fuera-de-alcance"]
    assert len(out) >= 1
    assert out[0].get("archivo_esperado") is None


def test_dataset_categorias_solicitadas() -> None:
    p = _cargar_preguntas(_DATASET)
    cats = {str(x["categoria"]) for x in p}
    for esperada in (
        "institucional",
        "servicios",
        "contacto",
        "procesos",
        "fuera-de-alcance",
    ):
        assert esperada in cats
