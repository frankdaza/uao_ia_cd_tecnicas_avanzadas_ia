"""Pruebas del script de ingesta Markdown -> Qdrant (idempotencia y purga)."""

from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from qdrant_client.models import PointStruct

from scripts import indexar_corpus_qdrant as idx
from src.api.configuracion import obtener_configuracion
from src.rag.runtime.qdrant_store import obtener_qdrant_client, reiniciar_cliente_qdrant


@pytest.fixture
def proyecto_minimo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Arbol temporal con pyproject.toml y un Markdown valido."""
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'test'\nversion = '0'\n", encoding="utf-8"
    )
    md = tmp_path / "data" / "markdown" / "testcorp"
    md.mkdir(parents=True)
    cuerpo_largo = "Oracion de prueba. " * 80
    (md / "uno.md").write_text(
        "---\n"
        "titulo: Doc uno\n"
        "source_url: https://ejemplo.org/uno\n"
        "seccion: pruebas\n"
        "---\n\n"
        "# Titulo\n\n" + cuerpo_largo,
        encoding="utf-8",
    )
    (md / "mal_yaml.md").write_text(
        "---\n[ no es mapping\n---\n\ncuerpo\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("QDRANT_URL", ":memory:")
    monkeypatch.setenv("EMBEDDING_DIMS", "8")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-prueba-local")
    monkeypatch.setenv("QDRANT_COLLECTION", "coleccion_idx_test")
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


def test_segunda_corrida_sin_upsert_por_idempotencia(
    proyecto_minimo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_embeddings(monkeypatch, 8)
    raiz = proyecto_minimo
    cfg = obtener_configuracion()
    md_dir = raiz / "data" / "markdown" / "testcorp"

    s1 = idx.ejecutar_indexacion(
        raiz,
        cfg,
        md_dir,
        "**/*.md",
        purgar=False,
        limite_archivos=None,
        tam_lote_embed=16,
        tam_lote_retrieve=64,
    )
    assert s1.chunks_totales >= 1
    assert s1.chunks_upsert >= 1
    assert s1.chunks_omitidos_sin_cambio == 0

    s2 = idx.ejecutar_indexacion(
        raiz,
        cfg,
        md_dir,
        "**/*.md",
        purgar=False,
        limite_archivos=None,
        tam_lote_embed=16,
        tam_lote_retrieve=64,
    )
    assert s2.chunks_upsert == 0
    assert s2.chunks_omitidos_sin_cambio == s2.chunks_totales


def test_archivo_yaml_invalido_se_omite_con_advertencia(
    proyecto_minimo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_embeddings(monkeypatch, 8)
    raiz = proyecto_minimo
    cfg = obtener_configuracion()
    md_dir = raiz / "data" / "markdown" / "testcorp"

    s = idx.ejecutar_indexacion(
        raiz,
        cfg,
        md_dir,
        "**/*.md",
        purgar=False,
        limite_archivos=None,
        tam_lote_embed=8,
        tam_lote_retrieve=32,
    )
    assert s.archivos_omitidos_aviso >= 1
    assert any("mal_yaml" in a for a in s.advertencias)


def test_purgar_elimina_punto_huerfano_mismo_prefijo(
    proyecto_minimo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_embeddings(monkeypatch, 8)
    raiz = proyecto_minimo
    cfg = obtener_configuracion()
    md_dir = raiz / "data" / "markdown" / "testcorp"

    idx.ejecutar_indexacion(
        raiz,
        cfg,
        md_dir,
        "uno.md",
        purgar=False,
        limite_archivos=None,
        tam_lote_embed=8,
        tam_lote_retrieve=32,
    )

    cliente = obtener_qdrant_client(cfg)
    prefijo = md_dir.resolve().relative_to(raiz).as_posix()
    huerfano_id = str(uuid.uuid4())
    cliente.upsert(
        collection_name=cfg.qdrant_collection,
        points=[
            PointStruct(
                id=huerfano_id,
                vector=[0.01] * cfg.embedding_dims,
                payload={
                    "archivo": f"{prefijo}/viejo.md",
                    "titulo": "",
                    "source_url": "",
                    "seccion": "",
                    "chunk_index": 0,
                    "content_hash": "aa",
                    "id_chunk": "bb",
                    "texto": "huerfano",
                },
            )
        ],
    )

    s = idx.ejecutar_indexacion(
        raiz,
        cfg,
        md_dir,
        "uno.md",
        purgar=True,
        limite_archivos=None,
        tam_lote_embed=8,
        tam_lote_retrieve=32,
    )
    assert s.puntos_purgados >= 1
    r = cliente.retrieve(collection_name=cfg.qdrant_collection, ids=[huerfano_id])
    assert len(r) == 0


def test_purgar_se_ignora_con_limit(
    proyecto_minimo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_embeddings(monkeypatch, 8)
    raiz = proyecto_minimo
    cfg = obtener_configuracion()
    md_dir = raiz / "data" / "markdown" / "testcorp"

    s = idx.ejecutar_indexacion(
        raiz,
        cfg,
        md_dir,
        "**/*.md",
        purgar=True,
        limite_archivos=1,
        tam_lote_embed=8,
        tam_lote_retrieve=32,
    )
    assert s.puntos_purgados == 0
    assert any("purgar" in m.lower() for m in s.advertencias)


def test_no_importa_recuperador_bm25() -> None:
    import scripts.indexar_corpus_qdrant as mod

    fuente = Path(mod.__file__).read_text(encoding="utf-8")
    assert "recuperador" not in fuente.lower()
