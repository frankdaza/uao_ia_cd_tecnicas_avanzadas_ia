"""Endpoints del corpus: GET /api/modelos, POST /api/recargar-corpus, GET /api/prompt-defecto."""

from __future__ import annotations

from fastapi import APIRouter

from src.api.configuracion import obtener_configuracion
from src.api.esquemas import RespuestaModelos, RespuestaPromptDefecto, RespuestaRecarga
from src.qa.cliente_ollama import MODELOS_OLLAMA_SOPORTADOS
from src.qa.cliente_openai import MODELOS_OPENAI_SOPORTADOS
from src.qa.prompt import PROMPT_SISTEMA_DEFECTO

router = APIRouter(tags=["corpus"])


@router.get("/modelos", response_model=RespuestaModelos)
async def listar_modelos() -> RespuestaModelos:
    """Lista los modelos disponibles por motor y el estado de la clave OpenAI."""
    cfg = obtener_configuracion()
    clave = cfg.openai_api_key
    openai_disponible = bool(clave and str(clave).strip())
    return RespuestaModelos(
        modelos_ollama=list(MODELOS_OLLAMA_SOPORTADOS),
        modelos_openai=list(MODELOS_OPENAI_SOPORTADOS),
        openai_disponible=openai_disponible,
    )


@router.post("/recargar-corpus", response_model=RespuestaRecarga)
async def recargar_corpus() -> RespuestaRecarga:
    """
    Indice en caliente: el producto M2 usa Qdrant; no hay recarga BM25 en runtime.

    Para reindexar vectores ejecute ``uv run python scripts/indexar_corpus_qdrant.py``.
    """
    return RespuestaRecarga(
        mensaje=(
            "El indice BM25 en memoria fue retirado del servidor. "
            "Para actualizar el corpus vectorial use el script de ingesta a Qdrant."
        )
    )


@router.get("/prompt-defecto", response_model=RespuestaPromptDefecto)
async def obtener_prompt_defecto() -> RespuestaPromptDefecto:
    """Retorna el prompt de sistema predeterminado."""
    return RespuestaPromptDefecto(prompt_sistema=PROMPT_SISTEMA_DEFECTO)
