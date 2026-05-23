"""Reintentos con backoff en ingesta Qdrant (embed y upsert)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from unittest.mock import MagicMock

from scripts import indexar_corpus_qdrant as idx
from src.api.configuracion import obtener_configuracion
from src.rag.runtime import qdrant_store as qs
from src.rag.runtime.qdrant_store import reiniciar_cliente_qdrant


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
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("QDRANT_URL", ":memory:")
    monkeypatch.setenv("EMBEDDING_DIMS", "8")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-prueba-local")
    monkeypatch.setenv("QDRANT_COLLECTION", "coleccion_retry_test")
    reiniciar_cliente_qdrant()
    obtener_configuracion.cache_clear()
    return tmp_path


def _mock_embeddings_estable(monkeypatch: pytest.MonkeyPatch, dims: int) -> MagicMock:
    mock = MagicMock()

    def batch(texts: list[str]) -> list[list[float]]:
        return [[0.02 * (k + 1) / max(len(t), 1) for k in range(dims)] for t in texts]

    mock.get_text_embedding_batch.side_effect = batch
    monkeypatch.setattr(idx, "obtener_embeddings", lambda _cfg=None: mock)
    return mock


class ClienteUpsertFallaDosVeces:
    """Delega en un cliente real salvo ``upsert`` (fallos transitorios simulados)."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.upsert_calls = 0

    def upsert(self, *args: Any, **kwargs: Any) -> Any:
        self.upsert_calls += 1
        if self.upsert_calls <= 2:
            raise ConnectionError("red transitoria simulada")
        return self._inner.upsert(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class ClienteUpsertSiempre401:
    """Simula respuesta HTTP 401 en upsert (no reintentar)."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.upsert_calls = 0

    def upsert(self, *args: Any, **kwargs: Any) -> Any:
        self.upsert_calls += 1
        exc = Exception("no autorizado simulado")
        exc.status_code = 401
        raise exc

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


def test_main_upsert_se_reintenta_y_completa(
    proyecto_minimo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_embeddings_estable(monkeypatch, 8)
    estado: dict[str, ClienteUpsertFallaDosVeces] = {}

    def fabricar_cliente(_cfg: Any = None) -> ClienteUpsertFallaDosVeces:
        inner = qs.obtener_qdrant_client(_cfg)
        wrap = ClienteUpsertFallaDosVeces(inner)
        estado["cliente"] = wrap
        return wrap

    monkeypatch.setattr(idx, "obtener_qdrant_client", fabricar_cliente)

    md_dir = proyecto_minimo / "data" / "markdown" / "testcorp"
    codigo = idx.main(
        [
            "--markdown-dir",
            str(md_dir.relative_to(proyecto_minimo)),
            "--reintentos",
            "5",
            "--backoff-max",
            "1",
        ]
    )
    assert codigo == 0
    assert estado["cliente"].upsert_calls == 3


def test_main_upsert_401_aborta_sin_reintentar(
    proyecto_minimo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_embeddings_estable(monkeypatch, 8)
    estado: dict[str, ClienteUpsertSiempre401] = {}

    def fabricar_cliente(_cfg: Any = None) -> ClienteUpsertSiempre401:
        inner = qs.obtener_qdrant_client(_cfg)
        wrap = ClienteUpsertSiempre401(inner)
        estado["cliente"] = wrap
        return wrap

    monkeypatch.setattr(idx, "obtener_qdrant_client", fabricar_cliente)

    md_dir = proyecto_minimo / "data" / "markdown" / "testcorp"
    codigo = idx.main(
        [
            "--markdown-dir",
            str(md_dir.relative_to(proyecto_minimo)),
            "--reintentos",
            "5",
            "--backoff-max",
            "1",
        ]
    )
    assert codigo == 1
    assert estado["cliente"].upsert_calls == 1


def test_embed_se_reintenta(
    proyecto_minimo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = MagicMock()
    dims = 8
    llamadas = {"n": 0}

    def batch(texts: list[str]) -> list[list[float]]:
        llamadas["n"] += 1
        if llamadas["n"] < 3:
            raise TimeoutError("timeout simulado")
        return [[0.02 * (k + 1) / max(len(t), 1) for k in range(dims)] for t in texts]

    mock.get_text_embedding_batch.side_effect = batch
    monkeypatch.setattr(idx, "obtener_embeddings", lambda _cfg=None: mock)

    raiz = proyecto_minimo
    cfg = obtener_configuracion()
    md_dir = raiz / "data" / "markdown" / "testcorp"

    stats = idx.ejecutar_indexacion(
        raiz,
        cfg,
        md_dir,
        "**/*.md",
        purgar=False,
        limite_archivos=None,
        tam_lote_embed=16,
        tam_lote_retrieve=64,
        reintentos=5,
        backoff_max_seg=1.0,
    )
    assert stats.chunks_upsert >= 1
    assert llamadas["n"] == 3
