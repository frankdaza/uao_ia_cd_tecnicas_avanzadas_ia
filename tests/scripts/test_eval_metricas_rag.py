"""Pruebas del comparador de reportes JSONL (scripts.eval_metricas_rag)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import eval_metricas_rag as mod
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


def test_comparar_umbral_recall_dispara_exit(tmp_path: Path) -> None:
    base = {
        "qid": "Q1",
        "tipo": "factual",
        "k_evaluacion": 5,
        "listado_na": False,
        "hit@5": 1,
        "precision@5": 0.2,
        "recall@5": 1.0,
        "mrr": 1.0,
        "ndcg@5": 0.5,
    }
    peor = {**base, "recall@5": 0.1, "mrr": 1.0}
    pa = _escribir_jsonl(tmp_path, "r1.jsonl", [base])
    pb = _escribir_jsonl(tmp_path, "r2.jsonl", [peor])
    _, regresion = comparar_resultados_jsonl(
        pa, pb, umbral_mrr=0.0, umbral_recall_k=0.0, umbral_ndcg_k=-1.0
    )
    assert regresion is True


def test_config_todas_produce_reporte_y_csv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raiz = tmp_path / "repo"
    (raiz / "data" / "eval" / "reportes").mkdir(parents=True)
    (raiz / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    repo_real = Path(__file__).resolve().parents[2]
    schema_src = repo_real / "data" / "eval" / "golden_set.schema.json"
    if not schema_src.is_file():
        pytest.skip("schema golden no presente")
    (raiz / "data" / "eval" / "golden_set.schema.json").write_text(
        schema_src.read_text(encoding="utf-8"), encoding="utf-8"
    )
    golden_abs = raiz / "data" / "eval" / "g.jsonl"
    golden_abs.write_text(
        json.dumps(
            {
                "id": "t1",
                "consulta": "hola",
                "tipo": "factual",
                "k_evaluacion": 3,
                "archivos_relevantes": ["a.md"],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    fila_res = {
        "qid": "t1",
        "consulta": "hola",
        "tipo": "factual",
        "k_evaluacion": 3,
        "archivos_relevantes": ["a.md"],
        "archivos_por_chunk": ["a.md"],
        "listado_na": False,
        "hit@3": 1,
        "precision@3": 0.33,
        "recall@3": 1.0,
        "mrr": 1.0,
        "ndcg@3": 0.5,
    }

    def fake_ejecutar(
        nombre: mod.TipoConfigEval,
        entradas: list,
        collection_cli: str | None,
    ) -> tuple[list, dict, object]:
        from types import SimpleNamespace

        cfg = SimpleNamespace(
            qdrant_collection="c",
            embedding_provider="p",
            embedding_model="m",
            embedding_dims=3,
            rag_score_minimo=0.0,
            rag_top_k=3,
            rag_top_k_inicial=9,
            rag_mmr_habilitado=False,
            rag_mmr_lambda=0.5,
            rag_reranker_habilitado=False,
            rag_reranker_modelo="x",
            rag_reranker_top_n_entrada=8,
        )
        return [fila_res], {"mrr": 1.0, "recall@3": 1.0, "hit@3": 1.0}, cfg

    monkeypatch.setattr(mod, "encontrar_raiz_repo", lambda inicio=None: raiz)
    monkeypatch.setattr(mod, "reiniciar_cliente_qdrant", lambda: None)
    monkeypatch.setattr(mod, "_ejecutar_un_preset", fake_ejecutar)
    monkeypatch.setattr(mod, "capturar_versiones_pip", lambda: "mock")

    out_md = raiz / "data" / "eval" / "reportes" / "salida.md"
    rc = mod.main(
        [
            "--golden",
            str(golden_abs.relative_to(raiz)),
            "--config",
            "todas",
            "--reporte-out",
            str(out_md.relative_to(raiz)),
        ]
    )
    assert rc == 0
    texto_md = out_md.read_text(encoding="utf-8")
    assert "## Preset: baseline" in texto_md
    assert "## Preset: mmr" in texto_md
    assert "## Preset: reranker" in texto_md
    assert "## Preset: combinado" in texto_md
    csv_path = out_md.with_suffix(".csv")
    assert csv_path.is_file()
    cuerpo_csv = csv_path.read_text(encoding="utf-8")
    assert "baseline" in cuerpo_csv and "mmr" in cuerpo_csv
    assert not cuerpo_csv.startswith("\ufeff")


def test_fail_if_empty_aborta(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mod, "reiniciar_cliente_qdrant", lambda: None)
    monkeypatch.setattr(mod, "contar_puntos_en_coleccion", lambda *a, **k: 0)
    monkeypatch.setattr(mod, "obtener_qdrant_client", lambda *a, **k: object())
    raiz = mod.encontrar_raiz_repo()
    golden = raiz / "data" / "eval" / "golden_set_rag.jsonl"
    if not golden.is_file():
        pytest.skip("golden no presente en este checkout")
    rc = mod.main(["--fail-if-empty", "--golden", str(golden)])
    assert rc == 1
