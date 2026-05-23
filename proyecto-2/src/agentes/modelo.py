"""Fabrica del modelo de chat del agente TAAM."""

from __future__ import annotations

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from src.configuracion import Configuracion, obtener_configuracion


def crear_modelo_agente(cfg: Configuracion | None = None) -> BaseChatModel:
    """Inicializa el LLM via ``init_chat_model`` (rubrica M3)."""
    conf = cfg or obtener_configuracion()
    kwargs: dict[str, object] = {}
    if conf.openai_api_key.strip():
        kwargs["api_key"] = conf.openai_api_key
    return init_chat_model(conf.agente_modelo, temperature=0.2, **kwargs)
