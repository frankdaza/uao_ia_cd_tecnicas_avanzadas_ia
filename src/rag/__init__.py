"""RAG denso: embeddings (LlamaIndex) y almacen vectorial Qdrant."""

from src.rag.embeddings import obtener_embeddings
from src.rag.qdrant_store import (
    asegurar_coleccion,
    obtener_qdrant_client,
    obtener_vector_store,
    reiniciar_cliente_qdrant,
)

__all__ = [
    "asegurar_coleccion",
    "obtener_embeddings",
    "obtener_qdrant_client",
    "obtener_vector_store",
    "reiniciar_cliente_qdrant",
]
