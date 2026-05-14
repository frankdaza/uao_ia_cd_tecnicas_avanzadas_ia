"""Pruebas del comparador de reportes JSONL (scripts.eval_metricas_rag)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.eval_metricas_rag import comparar_resultados_jsonl


def _escribir_jsonl(tmp: Path, nombre: str, filas: list[dict]) -> Path:
    ruta = tmp / nombre
    ruta.write_text("\n".join(json.dumps(f, ensure_ascii=False) for f in filas) + "\n", encoding="utf-8")
    return ruta


def test_comparar_sin_regresion_critica(tmp_path: Path) -> None:
    factual_a = [
        {
            "qid": "Q1",
            "tipo": "factual",
            "k_evaluacion": 5,
            "listado_na": False,
            "hit@5": 1,
            "precision@5": 0.2,
            "recall@5": 1.0,
            "mrr": 1.0,
            "ndcg@5": 0.5,
        },
        {
            "qid": "Q2",
            "tipo": "factual",
            "k_evaluacion": 5,
            "listado_na": False,
            "hit@5": 0,
            "precision@5": 0.0,
            "recall@5": 0.0,
            "mrr": 0.0,
            "ndcg@5": 0.0,
        },
    ]
    factual_b = [
        {**factual_a[0], "mrr": 1.0, "ndcg@5": 0.6},
        {**factual_a[1], "mrr": 0.2, "hit@5": 1},
    ]
    pa = _escribir_jsonl(tmp_path, "a.jsonl", factual_a)
    pb = _escribir_jsonl(tmp_path, "b.jsonl", factual_b)
    texto, regresion = comparar_resultados_jsonl(pa, pb, umbral_regresion_mrr=0.05)
    assert "Delta agregado" in texto
    assert regresion is False


def test_comparar_regresion_mrr_dispara_exit(tmp_path: Path) -> None:
    factual_a = [
        {
            "qid": "Q1",
            "tipo": "factual",
            "k_evaluacion": 5,
            "listado_na": False,
            "hit@5": 1,
            "precision@5": 0.4,
            "recall@5": 1.0,
            "mrr": 0.8,
            "ndcg@5": 0.9,
        },
    ]
    factual_b = [{**factual_a[0], "mrr": 0.2}]
    pa = _escribir_jsonl(tmp_path, "a2.jsonl", factual_a)
    pb = _escribir_jsonl(tmp_path, "b2.jsonl", factual_b)
    _, regresion = comparar_resultados_jsonl(pa, pb, umbral_regresion_mrr=0.05)
    assert regresion is True


def test_comparar_ignora_listado_na(tmp_path: Path) -> None:
    mix_a = [
        {
            "qid": "Q1",
            "tipo": "factual",
            "k_evaluacion": 5,
            "listado_na": False,
            "hit@5": 1,
            "precision@5": 0.2,
            "recall@5": 1.0,
            "mrr": 0.5,
            "ndcg@5": 0.3,
        },
        {"qid": "Q9", "tipo": "listado", "k_evaluacion": 5, "listado_na": True, "mrr": None},
    ]
    mix_b = [mix_a[0], mix_a[1]]
    pa = _escribir_jsonl(tmp_path, "m1.jsonl", mix_a)
    pb = _escribir_jsonl(tmp_path, "m2.jsonl", mix_b)
    texto, regresion = comparar_resultados_jsonl(pa, pb, umbral_regresion_mrr=0.05)
    parte = texto.split("## Delta por consulta", 1)[-1]
    assert "Q9" not in parte
    assert regresion is False


def test_comparar_delta_por_consulta_detecta_cambio(tmp_path: Path) -> None:
    base = {
        "qid": "Q1",
        "tipo": "factual",
        "k_evaluacion": 4,
        "listado_na": False,
        "hit@4": 0,
        "precision@4": 0.0,
        "recall@4": 0.0,
        "mrr": 0.0,
        "ndcg@4": 0.0,
    }
    mejor = {**base, "hit@4": 1, "mrr": 1.0}
    pa = _escribir_jsonl(tmp_path, "d1.jsonl", [base])
    pb = _escribir_jsonl(tmp_path, "d2.jsonl", [mejor])
    texto, _ = comparar_resultados_jsonl(pa, pb, umbral_regresion_mrr=0.05)
    assert "Q1" in texto
    assert "hit:" in texto or "mrr:" in texto
