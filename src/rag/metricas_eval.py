"""
Metricas puras de evaluacion de recuperacion (IR) para el golden set RAG.

Referencias utiles: BEIR (Thakur et al.), MTEB. Las funciones operan sobre listas
de rutas de archivo (chunks rankeados) y conjuntos de ground truth, sin efectos
secundarios ni I/O.
"""

from __future__ import annotations

import math
from typing import Iterable


def _normalizar_ruta(archivo: str) -> str:
    """Normaliza separadores y espacios para comparar con el golden set."""
    s = (archivo or "").strip().replace("\\", "/")
    while s.startswith("./"):
        s = s[2:]
    return s


def archivos_desde_chunks_rankeados(archivos_por_chunk: list[str], k: int) -> list[str]:
    """
    Primeros ``k`` fragmentos en orden de ranking; un archivo puede repetirse
    si varios chunks del mismo documento aparecen en el top.
    """
    if k <= 0:
        return []
    return [_normalizar_ruta(a) for a in archivos_por_chunk[:k]]


def conjunto_archivos_unicos_en_primeros_k(archivos_por_chunk: list[str], k: int) -> set[str]:
    """
    Conjunto de archivos distintos entre los primeros ``k`` chunks (orden no importa).

    Se usa como ``T_q^k`` en precision/recall a nivel documento con deduplicacion
    dentro del top-k (ver TASK-72).
    """
    return set(archivos_desde_chunks_rankeados(archivos_por_chunk, k))


def hit_at_k(archivos_por_chunk: list[str], relevantes: Iterable[str], k: int) -> int:
    """
    ``hit@k``: 1 si algun chunk entre los primeros ``k`` pertenece a un documento
    relevante; 0 en caso contrario.
    """
    rel = {_normalizar_ruta(r) for r in relevantes}
    for a in archivos_desde_chunks_rankeados(archivos_por_chunk, k):
        if a in rel:
            return 1
    return 0


def precision_at_k(archivos_por_chunk: list[str], relevantes: Iterable[str], k: int) -> float:
    """
    ``precision@k`` a nivel documento deduplicado: ``|T ∩ R| / k`` donde ``T`` es el
    conjunto de archivos unicos en los primeros ``k`` chunks y ``R`` el ground truth.

    El denominador sigue siendo ``k`` (ranuras del ranking), no ``|T|``.
    """
    if k <= 0:
        return 0.0
    rel = {_normalizar_ruta(r) for r in relevantes}
    t = conjunto_archivos_unicos_en_primeros_k(archivos_por_chunk, k)
    return len(t & rel) / float(k)


def recall_at_k(archivos_por_chunk: list[str], relevantes: Iterable[str], k: int) -> float:
    """
    ``recall@k`` a nivel documento: ``|T ∩ R| / |R|`` con ``T`` deduplicado en el top-k.
    Si ``R`` es vacio, retorna 0.0.
    """
    rel = {_normalizar_ruta(r) for r in relevantes}
    if not rel:
        return 0.0
    t = conjunto_archivos_unicos_en_primeros_k(archivos_por_chunk, k)
    return len(t & rel) / float(len(rel))


def mrr(archivos_por_chunk: list[str], relevantes: Iterable[str], k: int) -> float:
    """
    ``MRR`` truncado a ``k``: ``1 / rank`` del primer chunk cuyo archivo esta en ``R``;
    0 si no hay acierto en el top-k. El rank es 1-indexado.
    """
    rel = {_normalizar_ruta(r) for r in relevantes}
    for i, a in enumerate(archivos_desde_chunks_rankeados(archivos_por_chunk, k), start=1):
        if a in rel:
            return 1.0 / float(i)
    return 0.0


def ndcg_at_k(archivos_por_chunk: list[str], relevantes: Iterable[str], k: int) -> float:
    """
    ``nDCG@k`` con relevancia binaria por chunk: ganancia 1 si el archivo del chunk
    pertenece a ``R`` en esa posicion. El iDCG asume que las ``k`` primeras ranuras
    del ranking son todas relevantes (``sum(1/log2(i+2), i=0..k-1)``), de modo que
    ``0 <= nDCG <= 1`` aunque un mismo documento relevante ocupe varias posiciones.
    """
    if k <= 0:
        return 0.0
    rel = {_normalizar_ruta(r) for r in relevantes}
    if not rel:
        return 0.0
    ranked = archivos_desde_chunks_rankeados(archivos_por_chunk, k)
    dcg = sum(
        1.0 / math.log2(i + 2.0)
        for i, a in enumerate(ranked)
        if a in rel
    )
    idcg = sum(1.0 / math.log2(i + 2.0) for i in range(k))
    if idcg <= 0.0:
        return 0.0
    return dcg / idcg


def recall_conteo(conteo_devuelto: int, conteo_esperado: int) -> float:
    """
    Cobertura de conteo/listado: ``min(conteo_devuelto, conteo_esperado) / conteo_esperado``.

    Tolerancia documentada (TASK-72): al interpretar resultados reales, se puede
    considerar satisfecho un conteo dentro de ±10 % de ``conteo_esperado`` sin cambiar
    la formula numerica (la metrica sigue siendo la fraccion anterior).
    """
    if conteo_esperado <= 0:
        return 0.0
    return min(float(conteo_devuelto), float(conteo_esperado)) / float(conteo_esperado)


def hit_at_k_por_chunk(archivos_por_chunk: list[str], relevantes: Iterable[str], k: int) -> int:
    """
    Metrica auxiliar: mismo criterio que ``hit_at_k`` pero explicita semantica por chunk
    (equivale a ``hit_at_k`` con la misma entrada).
    """
    return hit_at_k(archivos_por_chunk, relevantes, k)
