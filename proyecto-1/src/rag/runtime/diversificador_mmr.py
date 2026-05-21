"""
Diversificacion MMR (Maximal Marginal Relevance) sobre candidatos con embeddings.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Sequence

import numpy as np
from llama_index.core.schema import NodeWithScore

logger = logging.getLogger(__name__)

EPS_NORM = 1e-12


def _vector_nodo_a_numpy(nodo: object) -> np.ndarray:
    emb = getattr(nodo, "embedding", None)
    if emb is None:
        msg = "Cada candidato MMR requiere ``node.embedding`` (vectores desde Qdrant)."
        raise ValueError(msg)
    arr = np.asarray(emb, dtype=np.float64).ravel()
    if arr.size == 0:
        msg = "Embedding de candidato vacio."
        raise ValueError(msg)
    return arr


def _normalizar_unidad(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if n < EPS_NORM:
        return v
    return v / n


def _similitud_coseno(a: np.ndarray, b: np.ndarray) -> float:
    """Coseno entre vectores ya normalizados (producto interno acotado)."""
    return float(np.clip(np.dot(a, b), -1.0, 1.0))


def aplicar_mmr(
    candidatos: list[NodeWithScore],
    embedding_consulta: Sequence[float],
    lambda_mult: float,
    k_final: int,
) -> list[NodeWithScore]:
    """
    Selecciona hasta ``k_final`` nodos maximizando relevancia frente a la consulta
    y penalizando redundancia respecto a los ya elegidos (MMR clasico).

    Contrato ``k_final``: si ``k_final`` es mayor que la cantidad de candidatos
    validos tras validar dimensiones y filtrar normas casi nulas, se devuelven
    todos los disponibles (a lo sumo ``len(pool)``). En ese caso se registra un
    mensaje ``INFO`` en el log.

    Args:
        candidatos: ``NodeWithScore`` con ``node.embedding`` poblado (misma dimension
            que ``embedding_consulta``).
        embedding_consulta: Vector de la consulta (no tiene que estar normalizado).
        lambda_mult: Peso de relevancia frente a diversidad; en 1.0 equivale a orden
            puramente por similitud con la consulta; en 0.0 solo se evita redundancia.
        k_final: Tamano deseado del conjunto de salida (puede superar al pool; se trunca).

    Returns:
        Lista ordenada por el orden de inclusion MMR (no por score original).
    """
    if k_final <= 0:
        return []
    if not candidatos:
        return []

    lam = float(np.clip(lambda_mult, 0.0, 1.0))
    q = np.asarray(list(embedding_consulta), dtype=np.float64).ravel()
    if q.size == 0:
        msg = "embedding_consulta vacio."
        raise ValueError(msg)
    dim_q = int(q.size)
    q = _normalizar_unidad(q)

    filtrados: list[NodeWithScore] = []
    vecs: list[np.ndarray] = []
    sims_q: list[float] = []

    for c in candidatos:
        raw = _vector_nodo_a_numpy(c.node)
        if int(raw.size) != dim_q:
            raise ValueError(
                "mmr_dim_mismatch: la consulta tiene "
                f"{dim_q} dimensiones y un candidato tiene {int(raw.size)}; "
                "revisa modelo de embedding y coleccion Qdrant."
            )
        n = float(np.linalg.norm(raw))
        if n < EPS_NORM:
            etiqueta = getattr(c.node, "id_", None) or getattr(c.node, "node_id", None)
            logger.warning(
                "MMR: se omite candidato con norma casi cero (< %.1e); nodo=%r",
                EPS_NORM,
                etiqueta,
            )
            continue
        v = raw / n
        filtrados.append(c)
        vecs.append(v)
        sims_q.append(_similitud_coseno(q, v))

    if not filtrados:
        return []

    pool_size = len(filtrados)
    if k_final > pool_size:
        logger.info(
            "MMR: k_final=%d supera candidatos validos (%d); se devuelven %d.",
            k_final,
            pool_size,
            pool_size,
        )

    indices_restantes: list[int] = list(range(pool_size))
    seleccion: list[int] = []

    while indices_restantes and len(seleccion) < k_final:
        mejor_i: int | None = None
        mejor_mmr = -math.inf
        mejor_sim_q = -math.inf
        for idx in indices_restantes:
            rel = sims_q[idx]
            if not seleccion:
                div = 0.0
            else:
                div = max(_similitud_coseno(vecs[idx], vecs[j]) for j in seleccion)
            mmr = lam * rel - (1.0 - lam) * div
            if mmr > mejor_mmr + 1e-15 or (
                abs(mmr - mejor_mmr) <= 1e-15 and rel > mejor_sim_q + 1e-15
            ):
                mejor_mmr = mmr
                mejor_sim_q = rel
                mejor_i = idx
        assert mejor_i is not None
        seleccion.append(mejor_i)
        indices_restantes.remove(mejor_i)

    return [filtrados[i] for i in seleccion]


def candidatos_desde_pares_similitud(
    pares: list[tuple[float, object]],
) -> list[NodeWithScore]:
    """
    Convierte pares (similitud, nodo LlamaIndex) a ``NodeWithScore`` para MMR.

    ``similitud`` se copia en ``NodeWithScore.score`` (score de Qdrant / coseno).
    """
    salida: list[NodeWithScore] = []
    for sim, nodo in pares:
        salida.append(NodeWithScore(node=nodo, score=float(sim)))  # type: ignore[arg-type]
    return salida


def pares_desde_candidatos_mmr(
    candidatos: list[NodeWithScore],
) -> list[tuple[float, object]]:
    """Convierte la salida de MMR a pares (score, nodo) para ``_salida_desde_pares``."""
    return [(float(c.score), c.node) for c in candidatos]
