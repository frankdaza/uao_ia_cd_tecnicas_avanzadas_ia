"""Pipeline completo del recuperador denso: MMR y reranker (mocks, Qdrant :memory:)."""

from __future__ import annotations

import math
from typing import Any
from unittest.mock import MagicMock

import pytest
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.api.configuracion import Configuracion
from src.rag.qdrant_store import reiniciar_cliente_qdrant
from src.rag.recuperador_denso import MENSAJE_SIN_RESULTADOS, RecuperadorDenso


class _EmbFijo:
    def __init__(self, v: list[float]) -> None:
        self._v = v

    def get_query_embedding(self, texto: str) -> list[float]:
        return list(self._v)


class _RerankFijo:
    def puntuar(self, consulta: str, textos: list[str]) -> list[float]:
        # Invierte la preferencia por longitud para alterar el orden respecto a similitud.
        return [float(100 - len(t)) for t in textos]


class _RerankIndiceAscendente:
    """Prefiere el ultimo texto del prefijo denso (orden de entrada = orden denso)."""

    def puntuar(self, consulta: str, textos: list[str]) -> list[float]:
        return [float(i) for i in range(len(textos))]


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


def _coleccion_cinco_angulos(limpiar_qdrant: None) -> QdrantVectorStore:
    """Cinco vectores en el plano XY con similitud coseno decreciente respecto a [1,0,0,0]."""
    cliente = QdrantClient(location=":memory:")
    nombre = "col_cinco"
    cliente.create_collection(
        nombre,
        vectors_config=VectorParams(size=4, distance=Distance.COSINE),
    )
    puntos: list[PointStruct] = []
    ids_uuid = (
        "00000001-0001-4001-8001-000000000001",
        "00000002-0002-4002-8002-000000000002",
        "00000003-0003-4003-8003-000000000003",
        "00000004-0004-4004-8004-000000000004",
        "00000005-0005-4005-8005-000000000005",
    )
    for i, ang in enumerate((0.0, 12.0, 24.0, 36.0, 48.0)):
        rad = math.radians(ang)
        v = [math.cos(rad), math.sin(rad), 0.0, 0.0]
        puntos.append(
            PointStruct(
                id=ids_uuid[i],
                vector=v,
                payload=_payload(
                    archivo=f"e{i}.md",
                    titulo=f"E{i}",
                    texto=f"t{i}",
                ),
            )
        )
    cliente.upsert(collection_name=nombre, points=puntos)
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


def test_consultar_embeddea_consulta_una_sola_vez(limpiar_qdrant: None) -> None:
    casos = [
        (False, {}),
        (True, {"top_k_inicial": 10, "mmr_lambda": 0.02}),
    ]
    for mmr_habilitado, extra in casos:
        vs = _coleccion_y_vs(limpiar_qdrant)
        emb = MagicMock()
        emb.get_query_embedding = MagicMock(return_value=[1.0, 0.0, 0.0, 0.0])
        rec = RecuperadorDenso(
            vs,
            emb,
            top_k=2,
            score_minimo=0.5,
            mmr_habilitado=mmr_habilitado,
            reranker_habilitado=False,
            **extra,
        )
        rec.consultar("que es la fundacion?")
        assert emb.get_query_embedding.call_count == 1, f"mmr_habilitado={mmr_habilitado}"


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
    for f in out.fuentes:
        assert f.score == f.score_final
    assert out.fuentes[0].score_final == pytest.approx(100.0 - len("corto"))
    assert out.fuentes[0].score_denso == pytest.approx(1.0, abs=0.02)


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


def test_consultar_qdrant_fallo() -> None:
    vs = MagicMock()
    vs.collection_name = "mock_col"
    vs.query.side_effect = RuntimeError("qdrant no disponible")
    rec = RecuperadorDenso(
        vs,
        _EmbFijo([1.0, 0.0, 0.0, 0.0]),
        top_k=2,
        score_minimo=0.5,
    )
    out = rec.consultar("pregunta")
    assert out.fuentes == []
    assert out.razon == "qdrant_fallo"
    assert MENSAJE_SIN_RESULTADOS in out.respuesta_contexto


def test_consultar_embeddings_fallo() -> None:
    vs = MagicMock()
    vs.collection_name = "mock_col"
    emb = MagicMock()
    emb.get_query_embedding = MagicMock(side_effect=ConnectionError("offline"))
    rec = RecuperadorDenso(vs, emb, top_k=2, score_minimo=0.5)
    out = rec.consultar("pregunta")
    assert out.fuentes == []
    assert out.razon == "embeddings_fallo"


def test_consultar_zip_mismatch() -> None:
    n_a = MagicMock()
    n_a.get_content = MagicMock(return_value="texto a")
    n_a.metadata = {"archivo": "a.md", "titulo": "A", "source_url": "", "chunk_index": 0}
    n_b = MagicMock()
    n_b.get_content = MagicMock(return_value="texto b")
    n_b.metadata = {"archivo": "b.md", "titulo": "B", "source_url": "", "chunk_index": 0}
    resultado = MagicMock()
    resultado.nodes = [n_a, n_b]
    resultado.similarities = [0.99]
    vs = MagicMock()
    vs.collection_name = "mock_col"
    vs.query = MagicMock(return_value=resultado)
    rec = RecuperadorDenso(
        vs,
        _EmbFijo([1.0, 0.0, 0.0, 0.0]),
        top_k=2,
        score_minimo=0.1,
    )
    out = rec.consultar("pregunta")
    assert out.fuentes == []
    assert out.razon == "qdrant_response_mismatch"


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


def test_pipeline_opcion_b_rerank_sobre_prefijo_denso_cinco_candidatos(limpiar_qdrant: None) -> None:
    """
    Cinco puntos; el reranker mock asigna score creciente con el indice del prefijo denso
    (orden de ``candidatos_ns``). El ganador es siempre el ultimo de ese prefijo.
    """
    vs = _coleccion_cinco_angulos(limpiar_qdrant)
    emb = _EmbFijo([1.0, 0.0, 0.0, 0.0])
    rec_denso = RecuperadorDenso(
        vs,
        emb,
        top_k=5,
        score_minimo=0.5,
        top_k_inicial=10,
        mmr_habilitado=False,
        reranker_habilitado=False,
    )
    orden_prefijo = [f.archivo for f in rec_denso.consultar("x").fuentes]
    assert len(orden_prefijo) == 5

    rec = RecuperadorDenso(
        vs,
        emb,
        top_k=3,
        score_minimo=0.5,
        top_k_inicial=10,
        mmr_habilitado=False,
        reranker_habilitado=True,
        reranker_top_n_entrada=5,
        reranker_instancia=_RerankIndiceAscendente(),
    )
    out = rec.consultar("x")
    esperado = [orden_prefijo[-1], orden_prefijo[-2], orden_prefijo[-3]]
    assert [f.archivo for f in out.fuentes] == esperado
    assert out.fuentes[0].score_final == pytest.approx(4.0)
    assert out.fuentes[0].score_denso < out.fuentes[1].score_denso


def test_pipeline_opcion_b_campos_score_mmr_y_rerank(limpiar_qdrant: None) -> None:
    """Con opcion B, score_denso conserva la similitud Qdrant y score_final el cross-encoder."""
    vs = _coleccion_y_vs(limpiar_qdrant)
    rec = RecuperadorDenso(
        vs,
        _EmbFijo([1.0, 0.0, 0.0, 0.0]),
        top_k=2,
        score_minimo=0.5,
        top_k_inicial=10,
        mmr_habilitado=True,
        mmr_lambda=0.5,
        reranker_habilitado=True,
        reranker_top_n_entrada=3,
        reranker_instancia=_RerankFijo(),
    )
    out = rec.consultar("x")
    assert len(out.fuentes) == 2
    for f in out.fuentes:
        assert f.score == f.score_final
        assert 0.5 <= f.score_denso <= 1.0
    # El reranker mock no devuelve similitud coseno; debe diferir del denso al menos en un tope
    assert any(abs(f.score_final - f.score_denso) > 0.05 for f in out.fuentes)
