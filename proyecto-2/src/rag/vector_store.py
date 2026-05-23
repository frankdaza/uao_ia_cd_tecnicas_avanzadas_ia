"""Fabrica de ``QdrantVectorStore`` para la coleccion TAAM."""

from __future__ import annotations

from functools import lru_cache

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from src.configuracion import Configuracion, obtener_configuracion

_DIMS_EMBEDDING_OPENAI_SMALL = 1536


@lru_cache
def obtener_cliente_qdrant(url: str) -> QdrantClient:
    return QdrantClient(url=url)


def crear_embeddings(cfg: Configuracion) -> OpenAIEmbeddings:
    if not cfg.openai_api_key.strip():
        raise ValueError(
            "OPENAI_API_KEY no configurada; necesaria para embeddings de ingesta TAAM."
        )
    return OpenAIEmbeddings(
        model=cfg.embedding_model,
        api_key=cfg.openai_api_key,
    )


def asegurar_coleccion(
    cliente: QdrantClient,
    nombre: str,
    *,
    dimension: int = _DIMS_EMBEDDING_OPENAI_SMALL,
) -> None:
    """Crea la coleccion si no existe (distancia coseno)."""
    if cliente.collection_exists(nombre):
        return
    cliente.create_collection(
        collection_name=nombre,
        vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
    )


def crear_vector_store(
    cfg: Configuracion | None = None,
    *,
    cliente: QdrantClient | None = None,
    embedding: Embeddings | None = None,
) -> QdrantVectorStore:
    """``QdrantVectorStore`` listo para ingesta y consulta RAG TAAM."""
    conf = cfg or obtener_configuracion()
    cli = cliente or obtener_cliente_qdrant(conf.qdrant_url)
    emb = embedding or crear_embeddings(conf)
    asegurar_coleccion(cli, conf.taam_qdrant_collection)
    return QdrantVectorStore(
        client=cli,
        collection_name=conf.taam_qdrant_collection,
        embedding=emb,
        distance=Distance.COSINE,
    )
