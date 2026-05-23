"""Pruebas unitarias de metricas de evaluacion RAG (TASK-72)."""

from __future__ import annotations

import math

import pytest

from src.rag.evaluacion.metricas_eval import (
    archivos_desde_chunks_rankeados,
    conjunto_archivos_unicos_en_primeros_k,
    hit_at_k,
    hit_at_k_por_chunk,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    recall_conteo,
)

REL = {"data/markdown/a.md", "data/markdown/b.md"}


class TestHitAtK:
    def test_acierto_en_primera_posicion(self) -> None:
        assert hit_at_k(["data/markdown/a.md", "data/markdown/c.md"], REL, k=2) == 1

    def test_sin_acierto_en_topk(self) -> None:
        assert hit_at_k(["z.md", "w.md"], REL, k=2) == 0

    def test_acierto_en_ultimo_chunk_del_topk(self) -> None:
        assert hit_at_k(["z.md", "data/markdown/b.md"], REL, k=2) == 1

    def test_k_cero_siempre_cero(self) -> None:
        assert hit_at_k(["data/markdown/a.md"], REL, k=0) == 0

    def test_normaliza_rutas(self) -> None:
        assert hit_at_k(["data\\markdown\\a.md"], REL, k=1) == 1

    def test_equivale_hit_por_chunk_aux(self) -> None:
        chunks = ["x.md", "data/markdown/a.md"]
        assert hit_at_k_por_chunk(chunks, REL, 3) == hit_at_k(chunks, REL, 3)


class TestPrecisionAtK:
    def test_todos_relevantes_distintos(self) -> None:
        # 2 unicos relevantes de 4 ranuras -> 2/4
        arch = ["data/markdown/a.md", "data/markdown/b.md", "z.md", "z.md"]
        assert precision_at_k(arch, REL, k=4) == 0.5

    def test_ninguno_relevante(self) -> None:
        assert precision_at_k(["x.md", "y.md"], REL, k=2) == 0.0

    def test_duplicados_cuentan_una_vez_en_interseccion(self) -> None:
        arch = ["data/markdown/a.md", "data/markdown/a.md", "data/markdown/a.md"]
        assert precision_at_k(arch, REL, k=3) == pytest.approx(1.0 / 3.0)

    def test_k_denominador_fijo(self) -> None:
        arch = ["data/markdown/a.md"]
        assert precision_at_k(arch, REL, k=5) == pytest.approx(0.2)

    def test_k_cero_retorna_cero(self) -> None:
        assert precision_at_k(["data/markdown/a.md"], REL, k=0) == 0.0


class TestRecallAtK:
    def test_recupera_uno_de_dos_relevantes(self) -> None:
        rel = {"data/markdown/a.md", "data/markdown/b.md", "data/markdown/c.md"}
        arch = ["data/markdown/a.md", "x.md"]
        assert recall_at_k(arch, rel, k=2) == pytest.approx(1.0 / 3.0)

    def test_recupera_todos_en_topk(self) -> None:
        rel = {"data/markdown/a.md", "data/markdown/b.md"}
        arch = ["data/markdown/a.md", "data/markdown/b.md", "z.md"]
        assert recall_at_k(arch, rel, k=3) == 1.0

    def test_r_vacio(self) -> None:
        assert recall_at_k(["data/markdown/a.md"], set(), k=2) == 0.0

    def test_duplicados_en_chunks(self) -> None:
        rel = {"data/markdown/a.md"}
        arch = ["data/markdown/a.md", "data/markdown/a.md"]
        assert recall_at_k(arch, rel, k=2) == 1.0

    def test_sin_interseccion(self) -> None:
        assert recall_at_k(["z.md"], REL, k=5) == 0.0


class TestMrr:
    def test_primer_relevante_posicion_uno(self) -> None:
        assert mrr(["data/markdown/a.md", "z.md"], REL, k=3) == 1.0

    def test_primer_relevante_posicion_dos(self) -> None:
        assert mrr(["z.md", "data/markdown/b.md"], REL, k=3) == pytest.approx(0.5)

    def test_sin_relevantes(self) -> None:
        assert mrr(["z.md", "w.md"], REL, k=2) == 0.0

    def test_ignora_segundo_relevante(self) -> None:
        assert mrr(
            ["z.md", "data/markdown/a.md", "data/markdown/b.md"], REL, k=3
        ) == pytest.approx(0.5)

    def test_relevante_fuera_de_k(self) -> None:
        assert mrr(["z.md", "w.md", "data/markdown/a.md"], REL, k=2) == 0.0


class TestNdcgAtK:
    def test_perfecto_un_relevante_al_inicio(self) -> None:
        rel1 = {"data/markdown/a.md"}
        arch = ["data/markdown/a.md", "z.md"]
        dcg = 1.0 / math.log2(2.0)
        idcg = 1.0 / math.log2(2.0) + 1.0 / math.log2(3.0)
        assert ndcg_at_k(arch, rel1, k=2) == pytest.approx(dcg / idcg)

    def test_cero_relevancia(self) -> None:
        assert ndcg_at_k(["z.md", "w.md"], REL, k=2) == 0.0

    def test_coincide_con_formula_manual_un_chunk(self) -> None:
        arch = ["data/markdown/a.md"]
        dcg = 1.0 / math.log2(2.0)
        assert ndcg_at_k(arch, REL, k=1) == pytest.approx(dcg / dcg)

    def test_dos_relevantes_mejor_posicion(self) -> None:
        rel2 = {"a.md", "b.md"}
        arch = ["a.md", "b.md", "z.md"]
        dcg = 1.0 / math.log2(2) + 1.0 / math.log2(3)
        idcg = sum(1.0 / math.log2(i + 2) for i in range(3))
        assert ndcg_at_k(arch, rel2, k=3) == pytest.approx(dcg / idcg)

    def test_k_trunca(self) -> None:
        assert ndcg_at_k(["z.md", "data/markdown/a.md"], REL, k=1) == 0.0


@pytest.mark.parametrize(
    "archivos,relevantes,k,caso",
    [
        pytest.param(
            ["docs/mision.md"] * 3 + ["docs/otros.md", "docs/otros.md"],
            {"docs/mision.md"},
            5,
            "a",
            id="a_doc_relevante_repetido_en_varios_chunks",
        ),
        pytest.param(["a.md"], set(), 2, "b", id="b_relevantes_vacio"),
        pytest.param(["a.md"], {"a.md"}, 0, "c", id="c_k_cero"),
        pytest.param(["x.md", "y.md"], {"a.md"}, 3, "d", id="d_ningun_chunk_relevante"),
        pytest.param(
            ["a.md", "b.md"], {"a.md", "b.md"}, 2, "e", id="e_todos_chunks_relevantes"
        ),
        pytest.param(["a.md", "z.md"], {"a.md"}, 2, "f", id="f_mezcla_relevantes_y_no"),
    ],
)
def test_ndcg_at_k_regresion_parametrizado(
    archivos: list[str],
    relevantes: set[str],
    k: int,
    caso: str,
) -> None:
    """Cobertura TASK-74: nDCG acotado a [0, 1] y casos de borde."""
    valor = ndcg_at_k(archivos, relevantes, k)
    assert 0.0 <= valor <= 1.0
    if caso == "a":
        assert valor > 0.0
    elif caso == "e":
        assert valor == pytest.approx(1.0)
    elif caso == "f":
        assert 0.0 < valor < 1.0
    else:
        assert valor == pytest.approx(0.0)


class TestRecallConteo:
    def test_cobertura_completa(self) -> None:
        assert recall_conteo(100, 100) == 1.0

    def test_devuelve_mas_que_esperado(self) -> None:
        assert recall_conteo(120, 100) == 1.0

    def test_devuelve_menos(self) -> None:
        assert recall_conteo(50, 100) == 0.5

    def test_esperado_cero(self) -> None:
        assert recall_conteo(5, 0) == 0.0

    def test_cero_devuelto(self) -> None:
        assert recall_conteo(0, 10) == 0.0


class TestHelpers:
    def test_archivos_desde_chunks_respeta_k(self) -> None:
        assert archivos_desde_chunks_rankeados(["a", "b", "c"], 2) == ["a", "b"]

    def test_conjunto_unicos(self) -> None:
        s = conjunto_archivos_unicos_en_primeros_k(["a", "a", "b"], k=3)
        assert s == {"a", "b"}
