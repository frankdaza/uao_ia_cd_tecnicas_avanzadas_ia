"""Pruebas de RecuperadorDenso y rag_denso (Qdrant en memoria, embeddings mock)."""

from __future__ import annotations

import math
from typing import Any

import pytest
from llama_index.vector_stores.qdrant import QdrantVectorStore
from pydantic import BaseModel, TypeAdapter
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.agentes.herramientas.rag_tool import crear_rag_tool
from src.api.configuracion import Configuracion
from src.rag.qdrant_store import reiniciar_cliente_qdrant
from src.rag.recuperador_denso import (
    MENSAJE_COLECCION_VACIA,
    MENSAJE_SIN_RESULTADOS,
    RecuperadorDenso,
    SalidaRecuperacionRagDenso,
)


class _EmbeddingsVecFijo:
    """Evita llamadas HTTP: siempre devuelve el mismo vector de consulta."""

    def __init__(self, vector: list[float]) -> None:
        self._vector = vector

    def get_query_embedding(self, texto: str) -> list[float]:
        return list(self._vector)


class _CargaFuenteRag(BaseModel):
    """
    Subconjunto alineado con RagChunk / evento fuentes del frontend (M2).

    ``chunk_index`` es extra para trazabilidad RAG; la UI puede ignorarlo.
    """

    archivo: str
    titulo: str
    source_url: str
    score: float
    score_denso: float
    score_final: float


@pytest.fixture
def limpiar_singletons_qdrant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QDRANT_URL", ":memory:")
    reiniciar_cliente_qdrant()
    from src.api.configuracion import obtener_configuracion

    obtener_configuracion.cache_clear()
    yield
    reiniciar_cliente_qdrant()
    obtener_configuracion.cache_clear()


def _payload(
    *,
    archivo: str,
    titulo: str,
    source_url: str,
    chunk_index: int,
    texto: str,
) -> dict[str, Any]:
    return {
        "archivo": archivo,
        "titulo": titulo,
        "source_url": source_url,
        "chunk_index": chunk_index,
        "texto": texto,
    }


def test_recuperador_coleccion_vacia(limpiar_singletons_qdrant: None) -> None:
    cliente = QdrantClient(location=":memory:")
    nombre = "col_vacia"
    cliente.create_collection(
        nombre,
        vectors_config=VectorParams(size=4, distance=Distance.COSINE),
    )
    vs = QdrantVectorStore(collection_name=nombre, client=cliente, text_key="texto")
    rec = RecuperadorDenso(
        vector_store=vs,
        embeddings=_EmbeddingsVecFijo([1.0, 0.0, 0.0, 0.0]),
        top_k=5,
        score_minimo=0.1,
    )
    out = rec.consultar("cualquier cosa")
    assert out.fuentes == []
    assert MENSAJE_COLECCION_VACIA in out.respuesta_contexto
    assert out.razon == "coleccion_vacia"


def test_recuperador_umbral_filtra_y_ordena_desc(limpiar_singletons_qdrant: None) -> None:
    cliente = QdrantClient(location=":memory:")
    nombre = "col_rag"
    cliente.create_collection(
        nombre,
        vectors_config=VectorParams(size=4, distance=Distance.COSINE),
    )
    # Ortogonal al query [1,0,0,0] -> score 0 con Cosine
    v_bajo = [0.0, 1.0, 0.0, 0.0]
    # ~0.87 de similitud coseno respecto a [1,0,0,0]
    v_medio = [0.87, math.sqrt(1 - 0.87**2), 0.0, 0.0]
    v_alto = [1.0, 0.0, 0.0, 0.0]
    cliente.upsert(
        collection_name=nombre,
        points=[
            PointStruct(
                id="11111111-1111-4111-8111-111111111111",
                vector=v_bajo,
                payload=_payload(
                    archivo="b.md",
                    titulo="B",
                    source_url="",
                    chunk_index=0,
                    texto="texto bajo",
                ),
            ),
            PointStruct(
                id="22222222-2222-4222-8222-222222222222",
                vector=v_medio,
                payload=_payload(
                    archivo="m.md",
                    titulo="M",
                    source_url="https://ejemplo.org/m",
                    chunk_index=1,
                    texto="texto medio",
                ),
            ),
            PointStruct(
                id="33333333-3333-4333-8333-333333333333",
                vector=v_alto,
                payload=_payload(
                    archivo="a.md",
                    titulo="A",
                    source_url="https://ejemplo.org/a",
                    chunk_index=2,
                    texto="texto alto",
                ),
            ),
        ],
    )
    vs = QdrantVectorStore(collection_name=nombre, client=cliente, text_key="texto")
    rec = RecuperadorDenso(
        vector_store=vs,
        embeddings=_EmbeddingsVecFijo([1.0, 0.0, 0.0, 0.0]),
        top_k=10,
        score_minimo=0.5,
    )
    out = rec.consultar("politicas de calidad")
    assert len(out.fuentes) == 2
    scores = [f.score_denso for f in out.fuentes]
    assert scores == sorted(scores, reverse=True)
    for f in out.fuentes:
        assert f.score == f.score_final
    assert out.fuentes[0].archivo == "a.md"
    assert out.fuentes[1].archivo == "m.md"
    assert "[CHUNK 1]" in out.respuesta_contexto
    assert "texto alto" in out.respuesta_contexto


def test_recuperador_sin_coincidencias_sobre_umbral(limpiar_singletons_qdrant: None) -> None:
    cliente = QdrantClient(location=":memory:")
    nombre = "col_umbral"
    cliente.create_collection(
        nombre,
        vectors_config=VectorParams(size=4, distance=Distance.COSINE),
    )
    cliente.upsert(
        collection_name=nombre,
        points=[
            PointStruct(
                id="44444444-4444-4444-8444-444444444444",
                vector=[0.0, 1.0, 0.0, 0.0],
                payload=_payload(
                    archivo="x.md",
                    titulo="X",
                    source_url="",
                    chunk_index=0,
                    texto="aislado",
                ),
            ),
        ],
    )
    vs = QdrantVectorStore(collection_name=nombre, client=cliente, text_key="texto")
    rec = RecuperadorDenso(
        vector_store=vs,
        embeddings=_EmbeddingsVecFijo([1.0, 0.0, 0.0, 0.0]),
        top_k=5,
        score_minimo=0.99,
    )
    out = rec.consultar("consulta")
    assert out.fuentes == []
    assert out.respuesta_contexto == MENSAJE_SIN_RESULTADOS


def test_recuperador_consulta_vacia(limpiar_singletons_qdrant: None) -> None:
    cliente = QdrantClient(location=":memory:")
    nombre = "col_x"
    cliente.create_collection(
        nombre,
        vectors_config=VectorParams(size=2, distance=Distance.COSINE),
    )
    vs = QdrantVectorStore(collection_name=nombre, client=cliente, text_key="texto")
    rec = RecuperadorDenso(
        vector_store=vs,
        embeddings=_EmbeddingsVecFijo([1.0, 0.0]),
        top_k=3,
        score_minimo=0.0,
    )
    out = rec.consultar("   ")
    assert out.fuentes == []
    assert out.respuesta_contexto == MENSAJE_SIN_RESULTADOS


def test_fuentes_compatibles_con_schema_ui_rag(
    limpiar_singletons_qdrant: None,
) -> None:
    """Valida archivo/titulo/source_url/score frente al contrato de la UI (chunks RAG)."""
    cliente = QdrantClient(location=":memory:")
    nombre = "col_schema"
    cliente.create_collection(
        nombre,
        vectors_config=VectorParams(size=4, distance=Distance.COSINE),
    )
    cliente.upsert(
        collection_name=nombre,
        points=[
            PointStruct(
                id="55555555-5555-4555-8555-555555555555",
                vector=[1.0, 0.0, 0.0, 0.0],
                payload=_payload(
                    archivo="doc.md",
                    titulo="Titulo",
                    source_url="https://fvl.org/x",
                    chunk_index=0,
                    texto="cuerpo",
                ),
            ),
        ],
    )
    vs = QdrantVectorStore(collection_name=nombre, client=cliente, text_key="texto")
    rec = RecuperadorDenso(
        vector_store=vs,
        embeddings=_EmbeddingsVecFijo([1.0, 0.0, 0.0, 0.0]),
        top_k=5,
        score_minimo=0.1,
    )
    out = rec.consultar("hola")
    TypeAdapter(list[_CargaFuenteRag]).validate_python(
        [f.model_dump() for f in out.fuentes]
    )
    for f in out.fuentes:
        assert isinstance(f.chunk_index, int)


def test_crear_rag_tool_structured_tool(limpiar_singletons_qdrant: None) -> None:
    cliente = QdrantClient(location=":memory:")
    nombre = "col_tool"
    cliente.create_collection(
        nombre,
        vectors_config=VectorParams(size=4, distance=Distance.COSINE),
    )
    cliente.upsert(
        collection_name=nombre,
        points=[
            PointStruct(
                id="66666666-6666-4666-8666-666666666666",
                vector=[1.0, 0.0, 0.0, 0.0],
                payload=_payload(
                    archivo="t.md",
                    titulo="T",
                    source_url="",
                    chunk_index=0,
                    texto="fragmento",
                ),
            ),
        ],
    )
    vs = QdrantVectorStore(collection_name=nombre, client=cliente, text_key="texto")
    rec = RecuperadorDenso(
        vector_store=vs,
        embeddings=_EmbeddingsVecFijo([1.0, 0.0, 0.0, 0.0]),
        top_k=3,
        score_minimo=0.2,
    )
    tool = crear_rag_tool(
        configuracion_motor=Configuracion(qdrant_url=":memory:"),
        recuperador=rec,
    )
    assert tool.name == "rag_denso"
    payload = tool.invoke({"consulta": "pregunta"})
    SalidaRecuperacionRagDenso.model_validate(payload)
    assert payload["fuentes"][0]["archivo"] == "t.md"
