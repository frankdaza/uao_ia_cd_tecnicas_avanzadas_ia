"""
Recuperacion densa sobre Qdrant usando LlamaIndex (sin BM25 ni lectura de Markdown).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from llama_index.core.vector_stores.types import VectorStoreQuery
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from llama_index.core.base.embeddings.base import BaseEmbedding
    from llama_index.vector_stores.qdrant import QdrantVectorStore

logger = logging.getLogger(__name__)

MENSAJE_SIN_RESULTADOS = (
    "No se recuperaron fragmentos del corpus institucional por encima del umbral "
    "de similitud configurado. No hay contexto RAG suficiente para responder con "
    "documentación de la Fundación Valle del Lili."
)

MENSAJE_COLECCION_VACIA = (
    "La colección vectorial no contiene documentos indexados todavía. "
    "No hay contexto RAG disponible."
)


class FuenteRagDenso(BaseModel):
    """Metadatos de un chunk devuelto al compositor o a la UI."""

    archivo: str = Field(description="Ruta relativa del Markdown de origen.")
    titulo: str = Field(description="Titulo declarado en front matter.")
    source_url: str = Field(description="URL publica asociada al documento, si existe.")
    score: float = Field(
        description=(
            "Score de similitud devuelto por Qdrant/LlamaIndex (mayor suele indicar "
            "mayor cercania cuando la metrica es Cosine o Dot; ajustar RAG_SCORE_MINIMO "
            "si se usa otra distancia en QDRANT_DISTANCE)."
        ),
    )
    chunk_index: int = Field(ge=0, description="Indice del fragmento dentro del archivo.")


class SalidaRecuperacionRagDenso(BaseModel):
    """Contrato estable hacia el LLM compositor."""

    respuesta_contexto: str = Field(
        description=(
            "Texto concatenado de fragmentos con cabeceras [CHUNK i] titulo / URL; "
            "vacío o mensaje explicito si no hubo coincidencias."
        ),
    )
    fuentes: list[FuenteRagDenso] = Field(default_factory=list)


class RecuperadorDenso:
    """
    Consulta Qdrant por similitud densa: embedding de la pregunta, top-k y filtro por score.

    No utiliza BM25 ni lee ``data/markdown/`` en tiempo de consulta.
    """

    def __init__(
        self,
        vector_store: QdrantVectorStore,
        embeddings: BaseEmbedding,
        top_k: int,
        score_minimo: float,
    ) -> None:
        self._vector_store = vector_store
        self._embeddings = embeddings
        self._top_k = top_k
        self._score_minimo = score_minimo

    def _contar_puntos(self) -> int:
        cliente = self._vector_store.client
        return int(
            cliente.count(
                collection_name=self._vector_store.collection_name, exact=True
            ).count
        )

    def _pares_filtrados(self, consulta_limpia: str) -> list[tuple[float, object]]:
        query_embedding = self._embeddings.get_query_embedding(consulta_limpia)
        consulta_vs = VectorStoreQuery(
            query_embedding=list(query_embedding),
            similarity_top_k=self._top_k,
        )
        resultado_vs = self._vector_store.query(consulta_vs)
        nodos = resultado_vs.nodes or []
        sims = resultado_vs.similarities or []
        pares: list[tuple[float, object]] = []
        for nodo, sim in zip(nodos, sims, strict=True):
            if sim is None:
                continue
            try:
                s = float(sim)
            except (TypeError, ValueError):
                continue
            if s >= self._score_minimo:
                pares.append((s, nodo))
        pares.sort(key=lambda t: t[0], reverse=True)
        return pares

    @staticmethod
    def _meta_chunk(nodo: object) -> tuple[str, str, str, int]:
        meta = getattr(nodo, "metadata", {}) or {}
        archivo = str(meta.get("archivo") or "")
        titulo = str(meta.get("titulo") or "")
        source_url = str(meta.get("source_url") or "")
        chunk_raw = meta.get("chunk_index", 0)
        try:
            chunk_index = int(chunk_raw)
        except (TypeError, ValueError):
            chunk_index = 0
        return archivo, titulo, source_url, chunk_index

    def _salida_desde_pares(self, pares: list[tuple[float, object]]) -> SalidaRecuperacionRagDenso:
        bloques: list[str] = []
        fuentes: list[FuenteRagDenso] = []
        for i, (score, nodo) in enumerate(pares, start=1):
            archivo, titulo, source_url, chunk_index = self._meta_chunk(nodo)
            texto = (nodo.get_content() or "").strip()
            ref_url = source_url if source_url else "(sin URL)"
            cabecera = f"[CHUNK {i}] {titulo} / {ref_url}"
            bloques.append(f"{cabecera}\n{texto}")
            fuentes.append(
                FuenteRagDenso(
                    archivo=archivo,
                    titulo=titulo,
                    source_url=source_url,
                    score=score,
                    chunk_index=chunk_index,
                )
            )
        return SalidaRecuperacionRagDenso(
            respuesta_contexto="\n\n".join(bloques),
            fuentes=fuentes,
        )

    def consultar(self, consulta: str) -> SalidaRecuperacionRagDenso:
        """
        Embedea ``consulta``, consulta el vector store y filtra por ``score_minimo``.

        Los resultados se ordenan por score descendente. Si la colección está vacía o
        ningún punto supera el umbral, se devuelve un mensaje claro y ``fuentes`` vacía.
        """
        consulta_limpia = consulta.strip()
        if not consulta_limpia:
            return SalidaRecuperacionRagDenso(
                respuesta_contexto=MENSAJE_SIN_RESULTADOS,
                fuentes=[],
            )

        if self._contar_puntos() == 0:
            logger.info(
                "RAG denso: coleccion %s vacia",
                self._vector_store.collection_name,
            )
            return SalidaRecuperacionRagDenso(
                respuesta_contexto=MENSAJE_COLECCION_VACIA,
                fuentes=[],
            )

        pares = self._pares_filtrados(consulta_limpia)
        if not pares:
            return SalidaRecuperacionRagDenso(
                respuesta_contexto=MENSAJE_SIN_RESULTADOS,
                fuentes=[],
            )
        return self._salida_desde_pares(pares)
