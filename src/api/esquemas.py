"""Modelos Pydantic v2 para requests y responses del API Q&A."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.qa.cliente_openai import MODELO_OPENAI_GPT_4O_MINI, MODELOS_OPENAI_SOPORTADOS


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class PeticionQa(BaseModel):
    """Parámetros de una consulta Q&A (sincrónica o en streaming) vía OpenAI."""

    model_config = ConfigDict(frozen=True)

    pregunta: str = Field(..., min_length=1, description="Texto de la pregunta del usuario.")
    prompt_sistema: str | None = Field(
        default=None,
        description="Prompt de sistema personalizado; si es None se usa el predeterminado.",
    )
    modelo_openai: str = Field(
        default=MODELO_OPENAI_GPT_4O_MINI,
        description=f"Modelo OpenAI. Opciones: {list(MODELOS_OPENAI_SOPORTADOS)}",
    )
    max_tokens_openai: int | None = Field(
        default=None,
        ge=1,
        description="Límite de tokens en la respuesta OpenAI; None = sin límite.",
    )
    temperatura: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Temperatura de muestreo (0 = más determinista, valores altos = más variación).",
    )
    top_p: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling: masa de probabilidad acumulada considerada por token.",
    )


# ---------------------------------------------------------------------------
# Response bodies
# ---------------------------------------------------------------------------


class FuenteRespuesta(BaseModel):
    """Metadatos de un documento recuperado por BM25."""

    model_config = ConfigDict(frozen=True)

    archivo: str
    titulo: str
    source_url: str
    score: float


class MetadatosMotor(BaseModel):
    """Metadatos de trazabilidad de un motor LLM."""

    model_config = ConfigDict(frozen=True)

    modelo: str
    latencia_ms: int


class RespuestaQa(BaseModel):
    """Resultado de una consulta Q&A sincrónica."""

    model_config = ConfigDict(frozen=True)

    texto_ollama: str | None = None
    texto_openai: str | None = None
    fuentes: list[FuenteRespuesta] = Field(default_factory=list)
    metadatos_ollama: MetadatosMotor | None = None
    metadatos_openai: MetadatosMotor | None = None


class RespuestaModelos(BaseModel):
    """Lista de modelos disponibles por motor."""

    model_config = ConfigDict(frozen=True)

    modelos_ollama: list[str]
    modelos_openai: list[str]
    openai_disponible: bool


class RespuestaSalud(BaseModel):
    """Estado de salud del servidor."""

    model_config = ConfigDict(frozen=True)

    estado: str = "ok"
    version: str = "1.0.0"


class RespuestaRecarga(BaseModel):
    """Resultado de recargar el índice BM25."""

    model_config = ConfigDict(frozen=True)

    mensaje: str


class RespuestaPromptDefecto(BaseModel):
    """Prompt de sistema predeterminado."""

    model_config = ConfigDict(frozen=True)

    prompt_sistema: str


# ---------------------------------------------------------------------------
# Eventos SSE
# ---------------------------------------------------------------------------


class EventoToken(BaseModel):
    """Token parcial emitido durante el streaming."""

    tipo: Literal["token"] = "token"
    motor: str
    texto: str


class EventoFuentes(BaseModel):
    """Fuentes BM25 emitidas tras completar una respuesta."""

    tipo: Literal["fuentes"] = "fuentes"
    fuentes: list[FuenteRespuesta]


class EventoFinal(BaseModel):
    """Metadatos finales de la respuesta completa."""

    tipo: Literal["final"] = "final"
    motor: str
    texto: str
    latencia_ms: int
    modelo: str


class EventoError(BaseModel):
    """Error ocurrido durante el streaming."""

    tipo: Literal["error"] = "error"
    motor: str
    mensaje: str
