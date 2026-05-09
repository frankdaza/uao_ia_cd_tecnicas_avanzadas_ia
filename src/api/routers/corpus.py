"""Endpoints del corpus: GET /api/modelos, POST /api/recargar-corpus, GET /api/prompt-defecto."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.dependencias import obtener_pipeline
from src.api.esquemas import RespuestaModelos, RespuestaPromptDefecto, RespuestaRecarga
from src.qa.cliente_ollama import MODELOS_OLLAMA_SOPORTADOS
from src.qa.cliente_openai import MODELOS_OPENAI_SOPORTADOS
from src.qa.pipeline import PipelineQa
from src.qa.prompt import PROMPT_SISTEMA_DEFECTO

router = APIRouter(tags=["corpus"])


@router.get("/modelos", response_model=RespuestaModelos)
async def listar_modelos(
    pipeline: PipelineQa = Depends(obtener_pipeline),
) -> RespuestaModelos:
    """Lista los modelos disponibles por motor y el estado de la clave OpenAI."""
    openai_disponible = (
        pipeline.cliente_openai is not None
        and pipeline.cliente_openai.configuracion.tiene_api_key()
    )
    return RespuestaModelos(
        modelos_ollama=list(MODELOS_OLLAMA_SOPORTADOS),
        modelos_openai=list(MODELOS_OPENAI_SOPORTADOS),
        openai_disponible=openai_disponible,
    )


@router.post("/recargar-corpus", response_model=RespuestaRecarga)
async def recargar_corpus(
    pipeline: PipelineQa = Depends(obtener_pipeline),
) -> RespuestaRecarga:
    """Recarga el índice BM25 desde el directorio de Markdown."""
    pipeline.recuperador.recargar()
    return RespuestaRecarga(
        mensaje="Listo: índice BM25 recargado desde el directorio de Markdown."
    )


@router.get("/prompt-defecto", response_model=RespuestaPromptDefecto)
async def obtener_prompt_defecto() -> RespuestaPromptDefecto:
    """Retorna el prompt de sistema predeterminado."""
    return RespuestaPromptDefecto(prompt_sistema=PROMPT_SISTEMA_DEFECTO)
