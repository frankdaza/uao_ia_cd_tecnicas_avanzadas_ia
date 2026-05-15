"""Regresiones sobre fixtures compartidos en ``tests/rag/conftest.py``."""

from __future__ import annotations

import math

import pytest

from tests.rag.conftest import (
    FakeEmbeddingsDeterministas,
    FakeRerankerDeterminista,
    FakeRerankerPromueveIndice,
)


def test_fake_embeddings_deterministas_normaliza_y_es_reproducible() -> None:
    emb = FakeEmbeddingsDeterministas(dimension=16)
    a = emb.get_query_embedding("misma consulta")
    b = emb.get_query_embedding("misma consulta")
    assert len(a) == 16
    assert a == b
    norma = math.sqrt(sum(x * x for x in a))
    assert norma == pytest.approx(1.0, abs=1e-5)


def test_fake_reranker_determinista_orden_por_indice() -> None:
    rnk = FakeRerankerDeterminista()
    scores = rnk.puntuar("q", ["a", "b", "c"])
    assert scores == [0.0, 1.0, 2.0]


def test_fake_reranker_promueve_indice_respetando_longitud() -> None:
    rnk = FakeRerankerPromueveIndice(2)
    scores = rnk.puntuar("q", ["x", "y", "z"])
    assert scores[2] == 100.0
    assert all(s == 1.0 for i, s in enumerate(scores) if i != 2)


def test_fake_vector_store_placeholder_exportado() -> None:
    from tests.rag import conftest as mod

    assert hasattr(mod, "FakeVectorStoreDocumentado")


def test_golden_minimo_incluye_token_e2e7001(golden_minimo: list) -> None:
    textos = " ".join(x["consulta"] for x in golden_minimo)
    assert "e2e7001" in textos
