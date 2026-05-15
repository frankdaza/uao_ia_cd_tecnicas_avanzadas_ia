"""
Recuperacion densa sobre Qdrant usando LlamaIndex (sin BM25 ni lectura de Markdown).
"""

from __future__ import annotations

import hashlib
import logging
from typing import TYPE_CHECKING, cast

from llama_index.core.vector_stores.types import (
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
    VectorStoreQuery,
)
from pydantic import BaseModel, Field
from qdrant_client.http.models import Filter

from src.api.configuracion import Configuracion

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
    """
    Contrato estable hacia el LLM compositor.

    El campo ``razon`` es opcional: indica por que no hay fragmentos utiles cuando
    ``fuentes`` esta vacia. Valores posibles (snake_case): ``coleccion_vacia`` (sin
    puntos indexados en la consulta sin filtros), ``embeddings_fallo`` (proveedor de
    embeddings indisponible o error), ``qdrant_fallo`` (error al consultar el vector
    store) y ``qdrant_response_mismatch`` (cardinalidad inconsistente entre nodos y
    similitudes devueltas por el backend).
    """

    respuesta_contexto: str = Field(
        description=(
            "Texto concatenado de fragmentos con cabeceras [CHUNK i] titulo / URL; "
            "vacío o mensaje explicito si no hubo coincidencias."
        ),
    )
    fuentes: list[FuenteRagDenso] = Field(default_factory=list)
    razon: str | None = Field(
        default=None,
        description="Causa de degradacion cuando no hay fuentes recuperadas.",
    )


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
        *,
        top_k_inicial: int = 20,
        mmr_habilitado: bool = False,
        mmr_lambda: float = 0.5,
        reranker_habilitado: bool = False,
        reranker_modelo: str = "BAAI/bge-reranker-base",
        reranker_top_n_entrada: int = 10,
        reranker_instancia: object | None = None,
    ) -> None:
        self._vector_store = vector_store
        self._embeddings = embeddings
        self._top_k = top_k
        self._score_minimo = score_minimo
        self._top_k_inicial = max(1, int(top_k_inicial))
        self._mmr_habilitado = bool(mmr_habilitado)
        self._mmr_lambda = float(mmr_lambda)
        self._reranker_habilitado = bool(reranker_habilitado)
        self._reranker_modelo = str(reranker_modelo).strip() or "BAAI/bge-reranker-base"
        self._reranker_top_n_entrada = max(1, int(reranker_top_n_entrada))
        self._reranker_instancia = reranker_instancia
        self._coleccion_vacia: bool | None = None

    @classmethod
    def desde_configuracion(
        cls,
        cfg: Configuracion,
        *,
        vector_store: QdrantVectorStore | None = None,
        embeddings: BaseEmbedding | None = None,
        top_k: int | None = None,
        score_minimo: float | None = None,
        top_k_inicial: int | None = None,
        mmr_habilitado: bool | None = None,
        mmr_lambda: float | None = None,
        reranker_habilitado: bool | None = None,
        reranker_modelo: str | None = None,
        reranker_top_n_entrada: int | None = None,
    ) -> RecuperadorDenso:
        """Carga vector store y embeddings desde ``cfg`` salvo que se inyecten."""
        from src.rag.embeddings import obtener_embeddings
        from src.rag.qdrant_store import obtener_vector_store

        vs = vector_store or obtener_vector_store(cfg)
        emb = embeddings or obtener_embeddings(cfg)
        return cls(
            vector_store=vs,
            embeddings=emb,
            top_k=int(cfg.rag_top_k if top_k is None else top_k),
            score_minimo=float(cfg.rag_score_minimo if score_minimo is None else score_minimo),
            top_k_inicial=int(cfg.rag_top_k_inicial if top_k_inicial is None else top_k_inicial),
            mmr_habilitado=bool(cfg.rag_mmr_habilitado if mmr_habilitado is None else mmr_habilitado),
            mmr_lambda=float(cfg.rag_mmr_lambda if mmr_lambda is None else mmr_lambda),
            reranker_habilitado=bool(
                cfg.rag_reranker_habilitado if reranker_habilitado is None else reranker_habilitado
            ),
            reranker_modelo=str(cfg.rag_reranker_modelo if reranker_modelo is None else reranker_modelo).strip(),
            reranker_top_n_entrada=int(
                cfg.rag_reranker_top_n_entrada if reranker_top_n_entrada is None else reranker_top_n_entrada
            ),
        )

    def _necesita_vectores(self) -> bool:
        return self._mmr_habilitado

    def _limite_qdrant(self, top_efectivo: int) -> int:
        """Candidatos pedidos a Qdrant antes de MMR/rerank (retrocompatible si ambos off)."""
        te = max(1, int(top_efectivo))
        if not self._mmr_habilitado and not self._reranker_habilitado:
            return te
        n = max(self._top_k_inicial, te)
        if self._reranker_habilitado:
            n = max(n, self._reranker_top_n_entrada)
        return max(1, n)

    @staticmethod
    def _consulta_hash_truncada(consulta: str) -> str:
        return hashlib.sha256(consulta.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _filtros_tipo_pagina(
        filtros_tipo_pagina: list[str] | None,
    ) -> MetadataFilters | None:
        if not filtros_tipo_pagina:
            return None
        limpios = [str(x).strip() for x in filtros_tipo_pagina if str(x).strip()]
        if not limpios:
            return None
        return MetadataFilters(
            filters=[
                MetadataFilter(
                    key="tipo_pagina",
                    value=limpios,
                    operator=FilterOperator.IN,
                )
            ]
        )

    def _pares_filtrados(
        self,
        consulta: str,
        consulta_limpia: str,
        *,
        top_k: int | None = None,
        filtros_tipo_pagina: list[str] | None = None,
        query_embedding: list[float],
    ) -> tuple[list[tuple[float, object]], str | None]:
        k = self._limite_qdrant(self._top_k if top_k is None else max(1, int(top_k)))
        emb_consulta = list(query_embedding)
        filtros_meta = self._filtros_tipo_pagina(filtros_tipo_pagina)
        consulta_vs = VectorStoreQuery(
            query_embedding=emb_consulta,
            similarity_top_k=k,
            filters=filtros_meta,
        )
        try:
            if self._necesita_vectores():
                vs = self._vector_store
                query_filter = cast(Filter, vs._build_query_filter(consulta_vs))
                resp = vs.client.query_points(
                    collection_name=vs.collection_name,
                    query=emb_consulta,
                    using=vs.dense_vector_name,
                    limit=k,
                    query_filter=query_filter,
                    with_payload=True,
                    with_vectors=True,
                )
                resultado_vs = vs.parse_to_query_result(resp.points)
            else:
                resultado_vs = self._vector_store.query(consulta_vs)
        except Exception as exc:  # noqa: BLE001 — degradacion controlada hacia el agente
            logger.exception(
                "rag.consultar.qdrant_fallo",
                extra={
                    "categoria": "qdrant_fallo",
                    "consulta_hash": self._consulta_hash_truncada(consulta),
                    "exc_type": type(exc).__name__,
                },
            )
            return [], "qdrant_fallo"

        nodos = resultado_vs.nodes or []
        sims = resultado_vs.similarities or []
        if nodos:
            self._coleccion_vacia = False

        if not nodos and filtros_meta is None:
            return [], "coleccion_vacia_inferida"

        try:
            emparejados = list(zip(nodos, sims, strict=True))
        except ValueError:
            logger.exception(
                "rag.consultar.qdrant_response_mismatch",
                extra={
                    "categoria": "qdrant_response_mismatch",
                    "consulta_hash": self._consulta_hash_truncada(consulta),
                    "nodos": len(nodos),
                    "sims": len(sims),
                    "exc_type": "ValueError",
                },
            )
            return [], "qdrant_response_mismatch"

        pares: list[tuple[float, object]] = []
        for nodo, sim in emparejados:
            if sim is None:
                continue
            try:
                s = float(sim)
            except (TypeError, ValueError):
                continue
            if s >= self._score_minimo:
                pares.append((s, nodo))
        pares.sort(key=lambda t: t[0], reverse=True)
        return pares, None

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

    def _pipeline_post_filtrado(
        self,
        pares: list[tuple[float, object]],
        consulta_limpia: str,
        top_efectivo: int,
        query_embedding: list[float],
    ) -> list[tuple[float, object]]:
        """MMR opcional, reranker opcional; sin flags devuelve los ``top_efectivo`` mejores."""
        if not pares:
            return []

        if not self._mmr_habilitado and not self._reranker_habilitado:
            return pares[: max(1, int(top_efectivo))]

        from llama_index.core.schema import NodeWithScore

        from src.rag.diversificador_mmr import (
            aplicar_mmr,
            candidatos_desde_pares_similitud,
            pares_desde_candidatos_mmr,
        )

        candidatos_ns = candidatos_desde_pares_similitud(pares)
        if self._mmr_habilitado:
            try:
                mmr_sel = aplicar_mmr(
                    candidatos_ns,
                    query_embedding,
                    self._mmr_lambda,
                    max(1, int(top_efectivo)),
                )
            except ValueError as exc:
                logger.warning("MMR omitido (sin embeddings en nodos): %s", exc)
                mmr_sel = candidatos_ns[: max(1, int(top_efectivo))]
        else:
            # Sin MMR: se conserva el orden por similitud; el reranker opera sobre el prefijo.
            mmr_sel = candidatos_ns

        if not self._reranker_habilitado:
            return pares_desde_candidatos_mmr(mmr_sel)

        n_toma = min(self._reranker_top_n_entrada, len(mmr_sel))
        sub = mmr_sel[:n_toma]
        textos = [(c.node.get_content() or "").strip() for c in sub]
        try:
            rnk = self._reranker_instancia
            if rnk is None:
                from src.rag.reranker_cross_encoder import RerankerCrossEncoder

                rnk = RerankerCrossEncoder(self._reranker_modelo)
            scores_r = rnk.puntuar(consulta_limpia, textos)
        except Exception as exc:  # noqa: BLE001 — degradar sin tumbar la peticion
            logger.warning(
                "Reranker RAG no disponible (%s); se continua solo con orden post-MMR/similitud.",
                exc,
            )
            return pares_desde_candidatos_mmr(mmr_sel)

        ordenados = sorted(
            zip(scores_r, sub, strict=True),
            key=lambda t: t[0],
            reverse=True,
        )
        top_n = max(1, int(top_efectivo))
        salida_c: list[NodeWithScore] = []
        for scr, c in ordenados[:top_n]:
            salida_c.append(NodeWithScore(node=c.node, score=float(scr)))
        return pares_desde_candidatos_mmr(salida_c)

    def consultar(
        self,
        consulta: str,
        *,
        top_k: int | None = None,
        filtros_tipo_pagina: list[str] | None = None,
    ) -> SalidaRecuperacionRagDenso:
        """
        Embedea ``consulta``, consulta el vector store y filtra por ``score_minimo``.

        Los resultados se ordenan por score descendente. Si la colección está vacía o
        ningún punto supera el umbral, se devuelve un mensaje claro y ``fuentes`` vacía.
        Ante fallos de embeddings o de Qdrant, no se propaga la excepción: se devuelve
        ``fuentes`` vacía y el campo opcional ``razon`` indica la causa (snake_case).

        Args:
            consulta: Texto de la pregunta.
            top_k: Si se informa, sustituye el ``top_k`` del constructor solo en esta
                llamada (p. ej. evaluación con ``k_evaluacion`` distinto del producto).
        """
        consulta_limpia = consulta.strip()
        if not consulta_limpia:
            return SalidaRecuperacionRagDenso(
                respuesta_contexto=MENSAJE_SIN_RESULTADOS,
                fuentes=[],
            )

        top_efectivo = self._top_k if top_k is None else max(1, int(top_k))

        tiene_filtros = self._filtros_tipo_pagina(filtros_tipo_pagina) is not None
        if self._coleccion_vacia is True and not tiene_filtros:
            logger.info(
                "RAG denso: coleccion %s vacia (cache sin count)",
                self._vector_store.collection_name,
            )
            return SalidaRecuperacionRagDenso(
                respuesta_contexto=MENSAJE_COLECCION_VACIA,
                fuentes=[],
                razon="coleccion_vacia",
            )

        try:
            query_embedding = list(self._embeddings.get_query_embedding(consulta_limpia))
        except Exception as exc:  # noqa: BLE001 — degradacion controlada hacia el agente
            logger.exception(
                "rag.consultar.embeddings_fallo",
                extra={
                    "categoria": "embeddings_fallo",
                    "consulta_hash": self._consulta_hash_truncada(consulta),
                    "exc_type": type(exc).__name__,
                },
            )
            return SalidaRecuperacionRagDenso(
                respuesta_contexto=MENSAJE_SIN_RESULTADOS,
                fuentes=[],
                razon="embeddings_fallo",
            )

        pares, fatal = self._pares_filtrados(
            consulta,
            consulta_limpia,
            top_k=top_efectivo,
            filtros_tipo_pagina=filtros_tipo_pagina,
            query_embedding=query_embedding,
        )
        if fatal == "coleccion_vacia_inferida":
            self._coleccion_vacia = True
            logger.info(
                "RAG denso: coleccion %s vacia (inferida sin count)",
                self._vector_store.collection_name,
            )
            return SalidaRecuperacionRagDenso(
                respuesta_contexto=MENSAJE_COLECCION_VACIA,
                fuentes=[],
                razon="coleccion_vacia",
            )
        if fatal == "qdrant_response_mismatch":
            return SalidaRecuperacionRagDenso(
                respuesta_contexto=MENSAJE_SIN_RESULTADOS,
                fuentes=[],
                razon="qdrant_response_mismatch",
            )
        if fatal == "qdrant_fallo":
            return SalidaRecuperacionRagDenso(
                respuesta_contexto=MENSAJE_SIN_RESULTADOS,
                fuentes=[],
                razon="qdrant_fallo",
            )
        if not pares:
            return SalidaRecuperacionRagDenso(
                respuesta_contexto=MENSAJE_SIN_RESULTADOS,
                fuentes=[],
            )
        pares_finales = self._pipeline_post_filtrado(
            pares,
            consulta_limpia,
            top_efectivo,
            query_embedding,
        )
        return self._salida_desde_pares(pares_finales)
