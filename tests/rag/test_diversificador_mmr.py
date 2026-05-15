"""Pruebas de MMR con embeddings sinteticos."""

from __future__ import annotations

import math

import numpy as np
import pytest
from llama_index.core.schema import NodeWithScore, TextNode

from src.rag.diversificador_mmr import aplicar_mmr


def _nodo_con_emb(texto: str, vec: list[float]) -> NodeWithScore:
    n = TextNode(text=texto, embedding=list(vec))
    return NodeWithScore(node=n, score=0.0)


def test_mmr_lambda_uno_respeta_orden_por_similitud() -> None:
    q = [1.0, 0.0, 0.0]
    bajo = _nodo_con_emb("bajo", [0.5, math.sqrt(0.75), 0.0])
    alto = _nodo_con_emb("alto", [1.0, 0.0, 0.0])
    pool = [bajo, alto]
    for c in pool:
        v = np.asarray(c.node.embedding, dtype=float)
        qn = np.asarray(q, dtype=float)
        c.score = float(np.dot(v, qn) / (np.linalg.norm(v) * np.linalg.norm(qn) + 1e-12))
    pool.sort(key=lambda x: x.score, reverse=True)
    out = aplicar_mmr(pool, q, lambda_mult=1.0, k_final=2)
    assert [c.node.text for c in out] == ["alto", "bajo"]


def test_mmr_penaliza_casi_duplicados_y_prioriza_diverso() -> None:
    q = [1.0, 0.0, 0.0]
    dup1 = _nodo_con_emb("d1", [1.0, 0.01, 0.0])
    dup2 = _nodo_con_emb("d2", [0.99, 0.01, 0.0])
    unico = _nodo_con_emb("u", [0.0, 1.0, 0.0])
    pool = [dup1, dup2, unico]
    for c in pool:
        emb = np.asarray(c.node.embedding, dtype=float)
        qn = np.asarray(q, dtype=float)
        c.score = float(np.dot(emb, qn) / (np.linalg.norm(emb) * np.linalg.norm(qn) + 1e-9))
    pool.sort(key=lambda x: x.score, reverse=True)
    out = aplicar_mmr(pool, q, lambda_mult=0.02, k_final=2)
    textos = {c.node.text for c in out}
    assert "u" in textos
    assert len(out) == 2


def test_mmr_lambda_cero_segunda_eleccion_maximiza_diversidad() -> None:
    q = [1.0, 0.0, 0.0]
    v1 = [1.0, 0.0, 0.0]
    v2 = [0.99, 0.01, 0.0]
    v3 = [0.0, 1.0, 0.0]
    pool = [_nodo_con_emb("a", v1), _nodo_con_emb("b", v2), _nodo_con_emb("c", v3)]
    out = aplicar_mmr(pool, q, lambda_mult=0.0, k_final=2)
    assert len(out) == 2
    assert "c" in {c.node.text for c in out}


def test_mmr_k_final_mayor_que_pool_devuelve_todos() -> None:
    q = [1.0, 0.0]
    pool = [_nodo_con_emb("a", [1.0, 0.0]), _nodo_con_emb("b", [0.0, 1.0])]
    out = aplicar_mmr(pool, q, lambda_mult=0.5, k_final=10)
    assert len(out) == 2


def test_aplicar_mmr_pool_unico_con_k_mayor() -> None:
    q = [1.0, 0.0]
    solo = _nodo_con_emb("solo", [1.0, 0.0])
    out = aplicar_mmr([solo], q, lambda_mult=0.5, k_final=3)
    assert len(out) == 1
    assert out[0].node.text == "solo"


def test_aplicar_mmr_dim_mismatch_levanta() -> None:
    q = [1.0, 0.0, 0.0, 0.0]
    ok = _nodo_con_emb("ok", [1.0, 0.0, 0.0, 0.0])
    mal = _nodo_con_emb("mal", [1.0, 0.0, 0.0])
    with pytest.raises(ValueError, match="mmr_dim_mismatch"):
        aplicar_mmr([ok, mal], q, lambda_mult=0.5, k_final=2)


def test_aplicar_mmr_norma_casi_cero_omite_candidato() -> None:
    q = [1.0, 0.0, 0.0]
    casi_nulo = _nodo_con_emb("n", [1e-15, 0.0, 0.0])
    a = _nodo_con_emb("a", [1.0, 0.0, 0.0])
    b = _nodo_con_emb("b", [0.0, 1.0, 0.0])
    out = aplicar_mmr([casi_nulo, a, b], q, lambda_mult=0.5, k_final=2)
    assert len(out) == 2
    assert {c.node.text for c in out} == {"a", "b"}


def test_aplicar_mmr_lambda_extremos() -> None:
    """Lambda 1.0 = orden por similitud a q; lambda 0.0 = diversidad pura en el top-k."""
    q = [1.0, 0.0, 0.0]
    pool_desordenado = [
        _nodo_con_emb("z", [0.0, 0.0, 1.0]),
        _nodo_con_emb("y", [0.0, 1.0, 0.0]),
        _nodo_con_emb("x", [1.0, 0.0, 0.0]),
    ]
    out_uno = aplicar_mmr(pool_desordenado, q, lambda_mult=1.0, k_final=3)
    assert out_uno[0].node.text == "x"
    assert {c.node.text for c in out_uno} == {"x", "y", "z"}

    dup1 = _nodo_con_emb("d1", [1.0, 0.01, 0.0])
    dup2 = _nodo_con_emb("d2", [0.99, 0.01, 0.0])
    ort = _nodo_con_emb("ort", [0.0, 1.0, 0.0])
    pool_dup = [dup1, dup2, ort]
    out_cero = aplicar_mmr(pool_dup, q, lambda_mult=0.0, k_final=2)
    assert len(out_cero) == 2
    assert out_cero[0].node.text in {"d1", "d2"}
    assert "ort" in {c.node.text for c in out_cero}


def test_mmr_sin_embedding_lanza() -> None:
    n = TextNode(text="sin", embedding=None)
    c = NodeWithScore(node=n, score=1.0)
    with pytest.raises(ValueError, match="embedding"):
        aplicar_mmr([c], [1.0, 0.0], 0.5, 1)


def test_mmr_orden_cambia_con_duplicados_vs_similitud_pura() -> None:
    """Cinco copias casi paralelas y un vector ortogonal: MMR (lambda 0.5) incluye el ortogonal en el top-2."""
    q = np.array([1.0, 0.0, 0.0])
    casi = [[0.995, 0.01 * i, 0.0] for i in range(5)]
    pool = [_nodo_con_emb(f"c{i}", v) for i, v in enumerate(casi)]
    pool.append(_nodo_con_emb("ort", [0.0, 1.0, 0.0]))
    out_mmr = aplicar_mmr(pool, q.tolist(), lambda_mult=0.03, k_final=3)
    textos_mmr = [c.node.text for c in out_mmr]
    out_greedy = aplicar_mmr(pool, q.tolist(), lambda_mult=1.0, k_final=3)
    textos_greedy = [c.node.text for c in out_greedy]
    assert "ort" in textos_mmr
    assert not any(t == "ort" for t in textos_greedy)
