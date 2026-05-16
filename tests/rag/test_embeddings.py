"""Pruebas de la fabrica de embeddings."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.api.configuracion import obtener_configuracion
from src.rag.runtime.embeddings import obtener_embeddings
from src.rag.runtime.qdrant_store import reiniciar_cliente_qdrant


@pytest.fixture(autouse=True)
def limpiar_config(monkeypatch: pytest.MonkeyPatch) -> None:
    reiniciar_cliente_qdrant()
    obtener_configuracion.cache_clear()
    yield
    reiniciar_cliente_qdrant()
    obtener_configuracion.cache_clear()


def test_obtener_embeddings_openai_pasa_modelo_y_dims(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-3-small")
    monkeypatch.setenv("EMBEDDING_DIMS", "1536")
    obtener_configuracion.cache_clear()
    with patch("llama_index.embeddings.openai.OpenAIEmbedding") as mock_cls:
        mock_cls.return_value = MagicMock()
        obtener_embeddings()
        mock_cls.assert_called_once()
        kwargs = mock_cls.call_args.kwargs
        assert kwargs["model"] == "text-embedding-3-small"
        assert kwargs["dimensions"] == 1536


def test_obtener_embeddings_openai_sin_dimensions_para_ada(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    monkeypatch.setenv("EMBEDDING_DIMS", "1536")
    obtener_configuracion.cache_clear()
    with patch("llama_index.embeddings.openai.OpenAIEmbedding") as mock_cls:
        mock_cls.return_value = MagicMock()
        obtener_embeddings()
        kwargs = mock_cls.call_args.kwargs
        assert kwargs["model"] == "text-embedding-ada-002"
        assert "dimensions" not in kwargs


def test_obtener_embeddings_huggingface_lazy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EMBEDDING_PROVIDER", "huggingface")
    monkeypatch.setenv("EMBEDDING_MODEL", "BAAI/bge-small-en")
    obtener_configuracion.cache_clear()
    with patch("llama_index.embeddings.huggingface.HuggingFaceEmbedding") as mock_cls:
        mock_cls.return_value = MagicMock()
        obtener_embeddings()
        mock_cls.assert_called_once_with(model_name="BAAI/bge-small-en")


def test_openai_embedding_falla_al_embed_no_en_instanciacion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-3-small")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-clave-falsa-prueba")
    obtener_configuracion.cache_clear()
    from llama_index.embeddings.openai import OpenAIEmbedding

    emb = obtener_embeddings()
    assert isinstance(emb, OpenAIEmbedding)
    with patch(
        "llama_index.embeddings.openai.base.get_embedding",
        side_effect=RuntimeError("fallo_en_embed"),
    ):
        with pytest.raises(RuntimeError, match="fallo_en_embed"):
            emb.get_text_embedding("hola")
