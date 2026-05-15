"""Fabrica de embeddings LlamaIndex segun configuracion (OpenAI o HuggingFace)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from src.api.configuracion import Configuracion, obtener_configuracion

if TYPE_CHECKING:
    from llama_index.core.base.embeddings.base import BaseEmbedding

logger = logging.getLogger(__name__)

_log_config_embeddings_emitido = False


def obtener_embeddings(
    configuracion: Configuracion | None = None,
) -> BaseEmbedding:
    """
    Retorna embeddings listos para LlamaIndex segun ``embedding_provider``.

    No realiza llamadas HTTP: el fallo por credenciales invalidas ocurre al
    invocar ``get_text_embedding`` / ``aget_text_embedding``.
    """
    global _log_config_embeddings_emitido
    cfg = configuracion or obtener_configuracion()

    if not _log_config_embeddings_emitido:
        logger.info(
            "Embeddings: proveedor=%s modelo=%s dims=%s",
            cfg.embedding_provider,
            cfg.embedding_model,
            cfg.embedding_dims,
        )
        _log_config_embeddings_emitido = True

    if cfg.embedding_provider == "openai":
        from llama_index.embeddings.openai import OpenAIEmbedding

        kwargs_openai: dict[str, Any] = {
            "model": cfg.embedding_model,
            "api_key": cfg.openai_api_key,
        }
        # La API de OpenAI solo acepta ``dimensions`` en modelos text-embedding-3*.
        if str(cfg.embedding_model).startswith("text-embedding-3"):
            kwargs_openai["dimensions"] = cfg.embedding_dims

        return OpenAIEmbedding(**kwargs_openai)

    if cfg.embedding_provider == "huggingface":
        # Import diferido: evita cargar torch/sentence-transformers si solo se usa OpenAI.
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding

        return HuggingFaceEmbedding(model_name=cfg.embedding_model)

    raise ValueError(
        f"Proveedor de embeddings no soportado: {cfg.embedding_provider!r}"
    )
