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
from pydantic import BaseModel, ConfigDict, Field
from qdrant_client.http.models import Filter

from src.agentes.reglas import coercionar_top_k_final, coercionar_top_k_inicial
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

    model_config = ConfigDict(populate_by_name=True)

    archivo: str = Field(description="Ruta relativa del Markdown de origen.")
    titulo: str = Field(description="Titulo declarado en front matter.")
    source_url: str = Field(description="URL publica asociada al documento, si existe.")
    score_denso: float = Field(
        description=(
            "Similitud densa del vector store (Qdrant/LlamaIndex). Es el valor contra el que "
            "se aplica RAG_SCORE_MINIMO antes de MMR/rerank; no se sustituye por el reranker."
        ),
    )
    score_final: float = Field(
        description=(
            "Score visible al consumidor: igual a score_denso si no hubo reranker; "
            "valor del cross-encoder si hubo reranker."
        ),
    )
    chunk_index: int = Field(
        ge=0, description="Indice del fragmento dentro del archivo."
    )
    score: float = Field(
        description="Alias retrocompatible de score_final (mismo valor numerico).",
    )


class SalidaRecuperacionRagDenso(BaseModel):
    """
    Contrato estable hacia el LLM compositor.

    El campo ``razon`` es opcional: indica por que no hay fragmentos utiles cuando
    ``fuentes`` esta vacia. Valores posibles (snake_case): ``coleccion_vacia`` (sin
    puntos indexados en la consulta sin filtros), ``embeddings_fallo`` (proveedor de
    embeddings indisponible o error), ``qdrant_fallo`` (error al consultar el vector
    store), ``qdrant_response_mismatch`` (cardinalidad inconsistente entre nodos y
    similitudes devueltas por el backend) y ``mmr_sin_candidatos`` (hubo candidatos densos
    pero MMR o reranker descartaron todos los fragmentos).
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
        reranker_batch_size: int = 16,
        reranker_instancia: object | None = None,
    ) -> None:
        self._vector_store = vector_store
        self._embeddings = embeddings
        self._top_k = coercionar_top_k_final(int(top_k))
        self._score_minimo = score_minimo
        self._top_k_inicial = coercionar_top_k_inicial(int(top_k_inicial))
        self._mmr_habilitado = bool(mmr_habilitado)
        self._mmr_lambda = float(mmr_lambda)
        self._reranker_habilitado = bool(reranker_habilitado)
        self._reranker_modelo = str(reranker_modelo).strip() or "BAAI/bge-reranker-base"
        self._reranker_top_n_entrada = max(1, int(reranker_top_n_entrada))
        self._reranker_batch_size = max(1, min(256, int(reranker_batch_size)))
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
        reranker_batch_size: int | None = None,
    ) -> RecuperadorDenso:
        """Carga vector store y embeddings desde ``cfg`` salvo que se inyecten."""
        from src.rag.runtime.embeddings import obtener_embeddings
        from src.rag.runtime.qdrant_store import obtener_vector_store

        vs = vector_store or obtener_vector_store(cfg)
        emb = embeddings or obtener_embeddings(cfg)
        return cls(
            vector_store=vs,
            embeddings=emb,
            top_k=coercionar_top_k_final(
                int(cfg.rag_top_k if top_k is None else top_k)
            ),
            score_minimo=float(
                cfg.rag_score_minimo if score_minimo is None else score_minimo
            ),
            top_k_inicial=coercionar_top_k_inicial(
                int(cfg.rag_top_k_inicial if top_k_inicial is None else top_k_inicial)
            ),
            mmr_habilitado=bool(
                cfg.rag_mmr_habilitado if mmr_habilitado is None else mmr_habilitado
            ),
            mmr_lambda=float(cfg.rag_mmr_lambda if mmr_lambda is None else mmr_lambda),
            reranker_habilitado=bool(
                cfg.rag_reranker_habilitado
                if reranker_habilitado is None
                else reranker_habilitado
            ),
            reranker_modelo=str(
                cfg.rag_reranker_modelo if reranker_modelo is None else reranker_modelo
            ).strip(),
            reranker_top_n_entrada=int(
                cfg.rag_reranker_top_n_entrada
                if reranker_top_n_entrada is None
                else reranker_top_n_entrada
            ),
            reranker_batch_size=int(
                cfg.rag_reranker_batch_size
                if reranker_batch_size is None
                else reranker_batch_size
            ),
        )

    def _necesita_vectores(self) -> bool:
        return self._mmr_habilitado

    def _limite_qdrant(self, top_efectivo: int) -> int:
        """Candidatos pedidos a Qdrant antes de MMR/rerank (retrocompatible si ambos off)."""
        te = coercionar_top_k_final(int(top_efectivo))
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
        k = self._limite_qdrant(
            self._top_k if top_k is None else coercionar_top_k_final(int(top_k))
        )
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

    @staticmethod
    def _mapa_score_denso_por_nodo(
        pares: list[tuple[float, object]],
    ) -> dict[int, float]:
        return {id(nodo): float(sim) for sim, nodo in pares}

    def _salida_desde_triples(
        self,
        triples: list[tuple[float, float, object]],
    ) -> SalidaRecuperacionRagDenso:
        """Construye salida con score_denso / score_final y alias ``score``."""
        bloques: list[str] = []
        fuentes: list[FuenteRagDenso] = []
        for i, (score_denso, score_final, nodo) in enumerate(triples, start=1):
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
                    score_denso=score_denso,
                    score_final=score_final,
                    score=score_final,
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
    ) -> list[tuple[float, float, object]]:
        """
        Post-proceso tras filtrar por umbral denso.

        Orden implementado (TASK-78, opcion B si MMR y reranker activos):
        similitud densa -> reranker sobre prefijo amplio -> MMR final.
        Solo MMR: MMR sobre candidatos densos. Solo reranker: rerank sobre prefijo denso.
        """
        top_ef = coercionar_top_k_final(int(top_efectivo))
        mapa_denso = self._mapa_score_denso_por_nodo(pares)
        if not pares:
            return []

        if not self._mmr_habilitado and not self._reranker_habilitado:
            return [(float(s), float(s), n) for s, n in pares[:top_ef]]

        from llama_index.core.schema import NodeWithScore

        from src.rag.runtime.diversificador_mmr import (
            aplicar_mmr,
            candidatos_desde_pares_similitud,
            pares_desde_candidatos_mmr,
        )

        candidatos_ns = candidatos_desde_pares_similitud(pares)

        def triples_desde_pares_similitud(
            p: list[tuple[float, object]],
        ) -> list[tuple[float, float, object]]:
            return [(float(s), float(s), n) for s, n in p]

        def triples_desde_mmr_nodes(
            seleccion: list[NodeWithScore],
        ) -> list[tuple[float, float, object]]:
            salida: list[tuple[float, float, object]] = []
            for c in seleccion:
                n = c.node
                sd = mapa_denso.get(id(n), float(c.score))
                salida.append((sd, sd, n))
            return salida

        def mmr_sobre_candidatos(
            pool: list[NodeWithScore],
            *,
            k: int,
        ) -> list[NodeWithScore]:
            try:
                return aplicar_mmr(
                    pool,
                    query_embedding,
                    self._mmr_lambda,
                    k,
                )
            except ValueError as exc:
                logger.warning("MMR omitido (sin embeddings en nodos): %s", exc)
                return pool[:k]

        # Solo reranker: denso -> rerank -> top_k
        if self._reranker_habilitado and not self._mmr_habilitado:
            n_toma = min(max(self._reranker_top_n_entrada, top_ef), len(candidatos_ns))
            sub = candidatos_ns[:n_toma]
            textos = [(c.node.get_content() or "").strip() for c in sub]
            try:
                rnk = self._reranker_instancia
                if rnk is None:
                    from src.rag.runtime.reranker_cross_encoder import (
                        RerankerCrossEncoder,
                    )

                    rnk = RerankerCrossEncoder(self._reranker_modelo)
                scores_r = rnk.puntuar(
                    consulta_limpia, textos, batch_size=self._reranker_batch_size
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Reranker RAG no disponible (%s); se continua solo con similitud densa.",
                    exc,
                )
                return triples_desde_pares_similitud(
                    pares_desde_candidatos_mmr(sub)[:top_ef]
                )

            pares_sc = [
                (float(s), c)
                for s, c in zip(scores_r, sub, strict=True)
                if s is not None
            ]
            if not pares_sc:
                logger.warning(
                    "Reranker RAG: todos los scores fueron descartados; se continua con similitud densa."
                )
                return triples_desde_pares_similitud(
                    pares_desde_candidatos_mmr(sub)[:top_ef]
                )

            ordenados = sorted(
                pares_sc,
                key=lambda t: t[0],
                reverse=True,
            )
            salida: list[tuple[float, float, object]] = []
            for scr, c in ordenados[:top_ef]:
                n = c.node
                sd = mapa_denso.get(id(n), float(c.score))
                salida.append((sd, float(scr), n))
            return salida

        # Solo MMR
        if self._mmr_habilitado and not self._reranker_habilitado:
            mmr_sel = mmr_sobre_candidatos(candidatos_ns, k=top_ef)
            return triples_desde_mmr_nodes(mmr_sel)

        # MMR + reranker (B): rerank sobre prefijo denso, luego MMR
        n_toma = min(max(self._reranker_top_n_entrada, top_ef), len(candidatos_ns))
        sub = candidatos_ns[:n_toma]
        textos = [(c.node.get_content() or "").strip() for c in sub]
        try:
            rnk = self._reranker_instancia
            if rnk is None:
                from src.rag.runtime.reranker_cross_encoder import RerankerCrossEncoder

                rnk = RerankerCrossEncoder(self._reranker_modelo)
            scores_r = rnk.puntuar(
                consulta_limpia, textos, batch_size=self._reranker_batch_size
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Reranker RAG no disponible (%s); se continua con MMR sobre similitud densa.",
                exc,
            )
            mmr_sel = mmr_sobre_candidatos(candidatos_ns, k=top_ef)
            return triples_desde_mmr_nodes(mmr_sel)

        pares_sc = [
            (float(s), c) for s, c in zip(scores_r, sub, strict=True) if s is not None
        ]
        if not pares_sc:
            logger.warning(
                "Reranker RAG: todos los scores fueron descartados; se continua con MMR sobre similitud densa."
            )
            mmr_sel = mmr_sobre_candidatos(candidatos_ns, k=top_ef)
            return triples_desde_mmr_nodes(mmr_sel)

        ordenados = sorted(
            pares_sc,
            key=lambda t: t[0],
            reverse=True,
        )
        reranked: list[NodeWithScore] = [
            NodeWithScore(node=c.node, score=float(scr)) for scr, c in ordenados
        ]
        mmr_sel = mmr_sobre_candidatos(reranked, k=top_ef)
        salida_b: list[tuple[float, float, object]] = []
        for c in mmr_sel:
            n = c.node
            sd = mapa_denso.get(id(n), 0.0)
            salida_b.append((sd, float(c.score), n))
        return salida_b

    def consultar(
        self,
        consulta: str,
        *,
        top_k: int | None = None,
        filtros_tipo_pagina: list[str] | None = None,
    ) -> SalidaRecuperacionRagDenso:
        """
        Embedea ``consulta``, consulta el vector store y filtra por ``score_minimo`` **solo**
        sobre la similitud densa (Qdrant). Opcionalmente aplica reranker y/o MMR segun
        configuracion (orden B cuando ambos activos: denso -> rerank -> MMR).

        Los resultados exponen ``score_denso`` y ``score_final`` (y ``score`` como alias
        de ``score_final``). Si la colección está vacía o ningún punto supera el umbral
        denso, se devuelve un mensaje claro y ``fuentes`` vacía. Ante fallos de embeddings
        o de Qdrant, no se propaga la excepción: se devuelve ``fuentes`` vacía y el campo
        opcional ``razon`` indica la causa (snake_case).

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

        top_efectivo = (
            self._top_k if top_k is None else coercionar_top_k_final(int(top_k))
        )

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
            query_embedding = list(
                self._embeddings.get_query_embedding(consulta_limpia)
            )
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
        triples_finales = self._pipeline_post_filtrado(
            pares,
            consulta_limpia,
            top_efectivo,
            query_embedding,
        )
        if not triples_finales and pares:
            return SalidaRecuperacionRagDenso(
                respuesta_contexto=MENSAJE_SIN_RESULTADOS,
                fuentes=[],
                razon="mmr_sin_candidatos",
            )
        return self._salida_desde_triples(triples_finales)
