"""Pruebas de reduccion t-SNE, KMeans y export Plotly (TASK-130)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.openfang.reduccion_tsne import (
    MIN_SESIONES_TSNE,
    SesionesInsuficientesTsne,
    cargar_artefactos_vectorizacion,
    contar_sesiones,
    ejecutar_pipeline_visual,
    elegir_k_clusters,
    exportar_plotly,
    perplejidad_adaptiva,
    reducir_tsne,
    resumen_clusters_por_etiqueta,
    sesiones_insuficientes,
)

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
_VECTORES_DEMO = _FIXTURES / "tsne_vectores_demo.npy"
_METADATOS_DEMO = _FIXTURES / "tsne_metadatos_demo.parquet"


def test_perplejidad_adaptiva_casos() -> None:
    assert perplejidad_adaptiva(10) == 9.0
    assert perplejidad_adaptiva(50) == 30.0
    assert perplejidad_adaptiva(3) == 2.0


def test_perplejidad_adaptiva_rechaza_muestra_unica() -> None:
    with pytest.raises(ValueError, match="al menos 2"):
        perplejidad_adaptiva(1)


def test_sesiones_insuficientes() -> None:
    assert sesiones_insuficientes(2) is True
    assert sesiones_insuficientes(3) is False
    assert sesiones_insuficientes(3, minimo=4) is True


def test_contar_sesiones() -> None:
    meta = pd.DataFrame(
        {
            "session_id": ["a", "a", "b"],
            "texto": ["x", "y", "z"],
        }
    )
    assert contar_sesiones(meta) == 2
    assert contar_sesiones(pd.DataFrame()) == 0


def test_elegir_k_clusters_datos_separables() -> None:
    rng = np.random.default_rng(0)
    grupos = [rng.normal(loc=i * 3, scale=0.2, size=(8, 4)) for i in range(3)]
    x = np.vstack(grupos)
    k = elegir_k_clusters(x, k_min=3, k_max=5)
    assert 3 <= k <= 5


def test_reducir_tsne_forma() -> None:
    rng = np.random.default_rng(1)
    x = rng.normal(size=(5, 8)).astype(np.float32)
    coords = reducir_tsne(x, n_components=2, perplexity=4.0, random_state=42)
    assert coords.shape == (5, 2)


def test_resumen_clusters_por_etiqueta() -> None:
    meta = pd.DataFrame({"texto": ["a uno", "b dos", "a tres"]})
    etiquetas = np.array([0, 1, 0])
    resumen = resumen_clusters_por_etiqueta(meta, etiquetas, max_ejemplos=2)
    assert 0 in resumen and 1 in resumen
    assert len(resumen[0]) <= 2


@pytest.mark.skipif(
    not _VECTORES_DEMO.is_file() or not _METADATOS_DEMO.is_file(),
    reason="fixtures demo no generados",
)
def test_cargar_artefactos_demo() -> None:
    x, meta = cargar_artefactos_vectorizacion(_VECTORES_DEMO, _METADATOS_DEMO)
    assert x.shape[0] == len(meta)
    assert contar_sesiones(meta) >= MIN_SESIONES_TSNE


@pytest.mark.skipif(
    not _VECTORES_DEMO.is_file() or not _METADATOS_DEMO.is_file(),
    reason="fixtures demo no generados",
)
def test_ejecutar_pipeline_visual_demo(tmp_path: Path) -> None:
    pytest.importorskip("kaleido")
    x, meta = cargar_artefactos_vectorizacion(_VECTORES_DEMO, _METADATOS_DEMO)
    resultado = ejecutar_pipeline_visual(x, meta, tmp_path, random_state=42)
    assert (tmp_path / "tsne_2d.png").is_file()
    assert (tmp_path / "tsne_3d.html").is_file()
    assert resultado.coords_2d.shape[0] == x.shape[0]
    assert resultado.coords_3d.shape[1] == 3
    assert resultado.n_clusters >= 3


def test_ejecutar_pipeline_lanza_si_pocas_sesiones(tmp_path: Path) -> None:
    x = np.random.randn(2, 4).astype(np.float32)
    meta = pd.DataFrame(
        {
            "session_id": ["s1", "s2"],
            "texto": ["a", "b"],
        }
    )
    with pytest.raises(SesionesInsuficientesTsne):
        ejecutar_pipeline_visual(x, meta, tmp_path)


def test_exportar_plotly_mock_sin_kaleido(tmp_path: Path) -> None:
    meta = pd.DataFrame(
        {
            "session_id": ["s1", "s2", "s3"],
            "texto": ["texto uno", "texto dos", "texto tres"],
        }
    )
    coords_2d = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 0.5]])
    coords_3d = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [2.0, 0.5, -1.0]])
    etiquetas = np.array([0, 1, 0])

    with patch("src.openfang.reduccion_tsne.px") as px_mock:
        fig = MagicMock()
        px_mock.scatter.return_value = fig
        px_mock.scatter_3d.return_value = fig
        png, html = exportar_plotly(
            coords_2d, coords_3d, etiquetas, meta, dir_salida=tmp_path
        )
        assert png.name == "tsne_2d.png"
        assert html.name == "tsne_3d.html"
        fig.write_image.assert_called_once()
        fig.write_html.assert_called_once()
