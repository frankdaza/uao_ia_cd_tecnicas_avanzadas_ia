"""Integracion: ingesta con CHUNK_STRATEGY=markdown vs sentence (Qdrant :memory:)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

from scripts import indexar_corpus_qdrant as idx
from src.api.configuracion import obtener_configuracion
from src.rag.runtime.qdrant_store import obtener_qdrant_client, reiniciar_cliente_qdrant


@pytest.fixture
def corpus_tres_tipos(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Tres Markdown: ficha medico, servicio, sede."""
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'test'\nversion = '0'\n", encoding="utf-8"
    )
    md = tmp_path / "data" / "corp" / "md"
    md.mkdir(parents=True)

    (md / "directorio-medico-juan-perez.md").write_text(
        "---\n"
        "titulo: Juan Perez - Fundación Valle del Lili\n"
        "source_url: https://valledellili.org/directorio-medico/juan-perez/\n"
        "seccion: directorio-medico\n"
        "---\n\n"
        "## Pediatria\n\n"
        "### Sedes\n\n"
        "- Sede Alfaguara\n"
        "- Sede Valle del Lili\n\n"
        "### Formacion\n\n"
        "Texto de formacion.\n",
        encoding="utf-8",
    )

    (md / "servicios-gastroenterologia.md").write_text(
        "---\n"
        "titulo: Gastroenterologia\n"
        "source_url: https://valledellili.org/servicios/gastroenterologia/\n"
        "seccion: servicios\n"
        "---\n\n"
        "## Enfermedades que trata\n\n"
        "Parrafo largo sobre digestivo.\n\n"
        "## Procedimientos\n\n"
        "Lista breve.\n",
        encoding="utf-8",
    )

    (md / "sedes-sede-alfaguara.md").write_text(
        "---\n"
        "titulo: Sede Alfaguara\n"
        "source_url: https://valledellili.org/sedes/sede-alfaguara/\n"
        "seccion: sedes\n"
        "---\n\n"
        "## Servicios destacados\n\n"
        "### Alergologia\n\n"
        "Detalle alergologia.\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("QDRANT_URL", ":memory:")
    monkeypatch.setenv("EMBEDDING_DIMS", "8")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-prueba-local")
    monkeypatch.setenv("QDRANT_COLLECTION", "coleccion_md_chunk_test")
    reiniciar_cliente_qdrant()
    obtener_configuracion.cache_clear()
    return tmp_path


def _mock_embeddings(monkeypatch: pytest.MonkeyPatch, dims: int) -> MagicMock:
    mock = MagicMock()

    def batch(texts: list[str]) -> list[list[float]]:
        return [[0.02 * (k + 1) / max(len(t), 1) for k in range(dims)] for t in texts]

    mock.get_text_embedding_batch.side_effect = batch
    monkeypatch.setattr(idx, "obtener_embeddings", lambda _cfg=None: mock)
    return mock


def test_markdown_tres_archivos_payload_e_idempotencia(
    corpus_tres_tipos: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_embeddings(monkeypatch, 8)
    monkeypatch.setenv("CHUNK_STRATEGY", "markdown")
    obtener_configuracion.cache_clear()
    cfg = obtener_configuracion()
    assert cfg.chunk_strategy == "markdown"

    raiz = corpus_tres_tipos
    md_dir = raiz / "data" / "corp" / "md"

    s1 = idx.ejecutar_indexacion(
        raiz,
        cfg,
        md_dir,
        "**/*.md",
        purgar=False,
        limite_archivos=None,
        tam_lote_embed=8,
        tam_lote_retrieve=32,
    )
    assert s1.chunks_totales >= 3
    assert s1.chunks_upsert >= 1
    assert s1.chunks_por_tipo_pagina.get("ficha_medico", 0) >= 1

    cliente = obtener_qdrant_client(cfg)
    puntos, _ = cliente.scroll(
        collection_name=cfg.qdrant_collection,
        limit=64,
        with_payload=True,
        with_vectors=False,
    )
    assert len(puntos) >= 3
    muestra = next(
        p
        for p in puntos
        if isinstance(p.payload, dict)
        and p.payload.get("tipo_pagina") == "ficha_medico"
    )
    pl = muestra.payload
    assert isinstance(pl, dict)
    for clave in (
        "tipo_pagina",
        "especialidad",
        "sedes",
        "headings_path",
        "h1",
        "nombre_medico",
        "tags",
        "texto",
    ):
        assert clave in pl
    assert pl.get("nombre_medico") == "Juan Perez"
    assert "Pediatria" in (pl.get("especialidad") or [])

    puntos_vec, _ = cliente.scroll(
        collection_name=cfg.qdrant_collection,
        limit=32,
        with_vectors=True,
    )
    for p in puntos_vec:
        raw = p.vector
        if isinstance(raw, dict):
            raw = next(iter(raw.values()))
        arr = np.asarray(raw, dtype=np.float64)
        assert abs(float(np.linalg.norm(arr)) - 1.0) < 1e-5

    s2 = idx.ejecutar_indexacion(
        raiz,
        cfg,
        md_dir,
        "**/*.md",
        purgar=False,
        limite_archivos=None,
        tam_lote_embed=8,
        tam_lote_retrieve=32,
    )
    assert s2.chunks_upsert == 0
    assert s2.chunks_omitidos_sin_cambio == s2.chunks_totales


def test_sentence_retrocompatible_misma_idempotencia(
    corpus_tres_tipos: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_embeddings(monkeypatch, 8)
    monkeypatch.setenv("CHUNK_STRATEGY", "sentence")
    obtener_configuracion.cache_clear()
    cfg = obtener_configuracion()

    raiz = corpus_tres_tipos
    md_dir = raiz / "data" / "corp" / "md"

    s1 = idx.ejecutar_indexacion(
        raiz,
        cfg,
        md_dir,
        "**/*.md",
        purgar=False,
        limite_archivos=None,
        tam_lote_embed=8,
        tam_lote_retrieve=32,
    )
    assert s1.chunks_totales >= 1
    assert s1.chunks_upsert >= 1

    s2 = idx.ejecutar_indexacion(
        raiz,
        cfg,
        md_dir,
        "**/*.md",
        purgar=False,
        limite_archivos=None,
        tam_lote_embed=8,
        tam_lote_retrieve=32,
    )
    assert s2.chunks_upsert == 0


def test_metadata_documental_educacion_inferencia_pediatria() -> None:
    from scripts.indexar_corpus_qdrant import _metadata_documental

    fm: dict = {}
    cuerpo = "# Intro\n\nContenido."
    tipo, _, _, espec, _, _ = _metadata_documental(
        fm,
        cuerpo,
        "educacion-lactancia.md",
        "Taller de lactancia en pediatria",
        "educacion",
    )
    assert tipo == "educacion"
    assert "Pediatria" in espec


def test_asegurar_coleccion_dispara_indices_sin_excepcion_memoria(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("QDRANT_URL", ":memory:")
    monkeypatch.setenv("EMBEDDING_DIMS", "8")
    monkeypatch.setenv("QDRANT_COLLECTION", "col_payload_idx")
    reiniciar_cliente_qdrant()
    obtener_configuracion.cache_clear()
    cfg = obtener_configuracion()
    from src.rag.runtime.qdrant_store import (
        asegurar_coleccion,
        distancia_desde_settings,
    )

    cliente = obtener_qdrant_client(cfg)
    asegurar_coleccion(
        cliente,
        "col_payload_idx",
        8,
        distancia_desde_settings(cfg.qdrant_distance),
        configuracion=cfg,
    )
