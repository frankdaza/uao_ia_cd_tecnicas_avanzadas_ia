"""RAG denso: embeddings (LlamaIndex) y almacen vectorial Qdrant.

Reexporta simbolos usados por ingesta y tests desde ``src.rag.runtime`` (decision-6).
Nuevos modulos deben importarse preferentemente desde ``src.rag.runtime`` o
``src.rag.evaluacion``; este paquete mantiene solo estos nombres por compatibilidad.
"""

from src.rag.runtime.embeddings import obtener_embeddings
from src.rag.runtime.qdrant_store import (
    asegurar_coleccion,
    obtener_qdrant_client,
    obtener_vector_store,
    reiniciar_cliente_qdrant,
)
from src.rag.runtime.recuperador_denso import RecuperadorDenso

__all__ = [
    "RecuperadorDenso",
    "asegurar_coleccion",
    "obtener_embeddings",
    "obtener_qdrant_client",
    "obtener_vector_store",
    "reiniciar_cliente_qdrant",
]
