"""Pipeline completo del recuperador denso: MMR y reranker (mocks, Qdrant :memory:)."""

from __future__ import annotations

import math
from typing import Any

import pytest
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.api.configuracion import Configuracion
from src.rag.qdrant_store import reiniciar_cliente_qdrant
from src.rag.recuperador_denso import RecuperadorDenso


class _EmbFijo:
    def __init__(self, v: list[float]) -> None:
        self._v = v

    def get_query_embedding(self, texto: str) -> list[float]:
        return list(self._v)


class _RerankFijo:
    def puntuar(self, consulta: str, textos: list[str]) -> list[float]:
        # Invierte la preferencia por longitud para alterar el orden respecto a similitud.
        return [float(100 - len(t)) for t in textos]


def _payload(**kwargs: Any) -> dict[str, Any]:
    return {
        "archivo": kwargs["archivo"],
        "titulo": kwargs["titulo"],
        "source_url": kwargs.get("source_url", ""),
        "chunk_index": kwargs.get("chunk_index", 0),
        "texto": kwargs["texto"],
    }


@pytest.fixture
def limpiar_qdrant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QDRANT_URL", ":memory:")
    reiniciar_cliente_qdrant()
    from src.api.configuracion import obtener_configuracion

    obtener_configuracion.cache_clear()
    yield
    reiniciar_cliente_qdrant()
    obtener_configuracion.cache_clear()


def _coleccion_y_vs(limpiar_qdrant: None) -> QdrantVectorStore:
    cliente = QdrantClient(location=":memory:")
    nombre = "col_pipe"
    cliente.create_collection(
        nombre,
        vectors_config=VectorParams(size=4, distance=Distance.COSINE),
    )
    v_alto = [1.0, 0.0, 0.0, 0.0]
    v_dup = [0.99, 0.01, 0.0, 0.0]
    v_medio = [0.87, math.sqrt(1 - 0.87**2), 0.0, 0.0]
    cliente.upsert(
        collection_name=nombre,
        points=[
            PointStruct(
                id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                vector=v_alto,
                payload=_payload(archivo="a.md", titulo="A", texto="corto"),
            ),
            PointStruct(
                id="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                vector=v_dup,
                payload=_payload(archivo="b.md", titulo="B", texto="mediano"),
            ),
            PointStruct(
                id="cccccccc-cccc-4ccc-8ccc-cccccccccccc",
                vector=v_medio,
                payload=_payload(archivo="m.md", titulo="M", texto="muy largo texto"),
            ),
        ],
    )
    return QdrantVectorStore(collection_name=nombre, client=cliente, text_key="texto")


def test_pipeline_baseline_sin_mmr_ni_reranker(limpiar_qdrant: None) -> None:
    vs = _coleccion_y_vs(limpiar_qdrant)
    rec = RecuperadorDenso(
        vs,
        _EmbFijo([1.0, 0.0, 0.0, 0.0]),
        top_k=2,
        score_minimo=0.5,
        mmr_habilitado=False,
        reranker_habilitado=False,
    )
    out = rec.consultar("x")
    assert len(out.fuentes) == 2
    assert out.fuentes[0].archivo == "a.md"


def test_pipeline_solo_mmr(limpiar_qdrant: None) -> None:
    vs = _coleccion_y_vs(limpiar_qdrant)
    rec = RecuperadorDenso(
        vs,
        _EmbFijo([1.0, 0.0, 0.0, 0.0]),
        top_k=2,
        score_minimo=0.5,
        top_k_inicial=10,
        mmr_habilitado=True,
        mmr_lambda=0.02,
        reranker_habilitado=False,
    )
    out = rec.consultar("x")
    assert len(out.fuentes) == 2


def test_pipeline_solo_reranker(limpiar_qdrant: None) -> None:
    vs = _coleccion_y_vs(limpiar_qdrant)
    rec = RecuperadorDenso(
        vs,
        _EmbFijo([1.0, 0.0, 0.0, 0.0]),
        top_k=2,
        score_minimo=0.5,
        top_k_inicial=10,
        mmr_habilitado=False,
        reranker_habilitado=True,
        reranker_top_n_entrada=3,
        reranker_instancia=_RerankFijo(),
    )
    out = rec.consultar("x")
    assert len(out.fuentes) == 2
    # El mock favorece textos cortos: "corto" gana sobre "muy largo texto"
    assert out.fuentes[0].archivo == "a.md"


def test_pipeline_mmr_y_reranker(limpiar_qdrant: None) -> None:
    vs = _coleccion_y_vs(limpiar_qdrant)
    rec = RecuperadorDenso(
        vs,
        _EmbFijo([1.0, 0.0, 0.0, 0.0]),
        top_k=2,
        score_minimo=0.5,
        top_k_inicial=10,
        mmr_habilitado=True,
        mmr_lambda=0.02,
        reranker_habilitado=True,
        reranker_top_n_entrada=3,
        reranker_instancia=_RerankFijo(),
    )
    out = rec.consultar("x")
    assert len(out.fuentes) == 2


def test_reranker_falla_degrada_sin_excepcion(monkeypatch: pytest.MonkeyPatch, limpiar_qdrant: None) -> None:
    vs = _coleccion_y_vs(limpiar_qdrant)

    class _Mal:
        def puntuar(self, *a: object, **k: object) -> list[float]:
            raise RuntimeError("offline")

    rec = RecuperadorDenso(
        vs,
        _EmbFijo([1.0, 0.0, 0.0, 0.0]),
        top_k=2,
        score_minimo=0.5,
        top_k_inicial=10,
        mmr_habilitado=True,
        mmr_lambda=0.02,
        reranker_habilitado=True,
        reranker_instancia=_Mal(),
    )
    out = rec.consultar("x")
    assert len(out.fuentes) == 2


def test_desde_configuracion_respeta_flags(limpiar_qdrant: None) -> None:
    vs = _coleccion_y_vs(limpiar_qdrant)
    cfg = Configuracion(
        qdrant_url=":memory:",
        rag_top_k=2,
        rag_score_minimo=0.5,
        rag_mmr_habilitado=False,
        rag_reranker_habilitado=False,
    )
    rec = RecuperadorDenso.desde_configuracion(cfg, vector_store=vs, embeddings=_EmbFijo([1.0, 0.0, 0.0, 0.0]))
    out = rec.consultar("x")
    assert out.fuentes[0].archivo == "a.md"
