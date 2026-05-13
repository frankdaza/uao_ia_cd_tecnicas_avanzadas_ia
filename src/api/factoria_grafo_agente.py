"""Construccion del grafo LangGraph del agente para el lifespan de FastAPI."""

from __future__ import annotations

import logging
from pathlib import Path

from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph

from src.agentes.herramientas.faq_tool import crear_faq_tool
from src.agentes.herramientas.rag_tool import crear_rag_tool
from src.agentes.llm_deterministico_modulo2 import (
    CompositorDeterministicoModulo2E2e,
    RouterDeterministicoModulo2E2e,
)
from src.agentes.meta_prompt import ArchivoMetaPromptAusenteError, cargar_meta_prompt_config
from src.agentes.router import crear_grafo_agente
from src.api.configuracion import Configuracion

logger = logging.getLogger(__name__)


def _resolver_ruta_meta_prompt(cfg: Configuracion) -> Path:
    raw = Path(cfg.router_meta_prompt_path)
    if raw.is_absolute():
        return raw
    raiz = Path(__file__).resolve().parents[2]
    return (raiz / raw).resolve()


def construir_grafo_agente_produccion(cfg: Configuracion) -> CompiledStateGraph:
    """
    Compila el grafo del agente con modelos OpenAI y tools por defecto (FAQ + RAG Qdrant).

    Raises
    ------
    ValueError
        Si falta ``OPENAI_API_KEY`` o la configuracion del router no es valida.
    ArchivoMetaPromptAusenteError
        Si no existe el JSON del meta-prompt.
    """
    if not (cfg.openai_api_key and str(cfg.openai_api_key).strip()):
        msg = "Falta OPENAI_API_KEY para inicializar el agente conversacional."
        raise ValueError(msg)
    ruta_meta = _resolver_ruta_meta_prompt(cfg)
    meta = cargar_meta_prompt_config(ruta_meta)
    modelo_router = cfg.router_llm_model.strip()
    modelo_compositor = (cfg.compositor_llm_model or cfg.router_llm_model).strip()
    llm_router = ChatOpenAI(
        model=modelo_router,
        api_key=cfg.openai_api_key,
        temperature=0.0,
    )
    llm_compositor = ChatOpenAI(
        model=modelo_compositor,
        api_key=cfg.openai_api_key,
        temperature=0.2,
    )
    grafo = crear_grafo_agente(
        llm_router=llm_router,
        llm_compositor=llm_compositor,
        meta_prompt=meta,
        etiqueta_modelo_compositor=modelo_compositor,
    )
    logger.info("Grafo del agente compilado (router=%s, compositor=%s).", modelo_router, modelo_compositor)
    return grafo


def construir_grafo_agente_mock_llm(cfg: Configuracion) -> CompiledStateGraph:
    """
    Grafo del agente sin OpenAI: router y compositor deterministicos.

    Requiere meta-prompt JSON valido (misma ruta que produccion). Las tools reales
    (FAQ JSON + RAG Qdrant) se ejecutan normalmente salvo error de dependencias.
    """
    ruta_meta = _resolver_ruta_meta_prompt(cfg)
    meta = cargar_meta_prompt_config(ruta_meta)
    herramientas = [crear_faq_tool(configuracion=cfg), crear_rag_tool(configuracion=cfg)]
    grafo = crear_grafo_agente(
        llm_router=RouterDeterministicoModulo2E2e(),
        llm_compositor=CompositorDeterministicoModulo2E2e(),
        meta_prompt=meta,
        herramientas=herramientas,
        etiqueta_modelo_compositor="mock_llm",
    )
    logger.info("Grafo del agente compilado en modo MOCK_LLM (sin OpenAI).")
    return grafo


def construir_grafo_agente_produccion_o_none(cfg: Configuracion) -> CompiledStateGraph | None:
    """Igual que :func:`construir_grafo_agente_produccion` pero retorna ``None`` ante fallo de arranque."""
    if cfg.mock_llm:
        try:
            return construir_grafo_agente_mock_llm(cfg)
        except (ValueError, ArchivoMetaPromptAusenteError) as exc:
            logger.error("No se pudo compilar el grafo del agente (MOCK_LLM): %s", exc)
            return None
        except Exception as exc:  # noqa: BLE001
            logger.exception("Fallo inesperado al compilar el grafo del agente (MOCK_LLM): %s", exc)
            return None
    try:
        return construir_grafo_agente_produccion(cfg)
    except (ValueError, ArchivoMetaPromptAusenteError) as exc:
        logger.error("No se pudo compilar el grafo del agente: %s", exc)
        return None
    except Exception as exc:  # noqa: BLE001 — arranque tolerante a Qdrant u otros fallos
        logger.exception("Fallo inesperado al compilar el grafo del agente: %s", exc)
        return None


__all__ = [
    "construir_grafo_agente_mock_llm",
    "construir_grafo_agente_produccion",
    "construir_grafo_agente_produccion_o_none",
]
