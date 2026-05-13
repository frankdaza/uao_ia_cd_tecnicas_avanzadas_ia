"""Modelos Pydantic v2 para requests y responses del API Q&A."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from src.qa.cliente_openai import MODELO_OPENAI_GPT_4O_MINI, MODELOS_OPENAI_SOPORTADOS


# ---------------------------------------------------------------------------
# Modulo 2: sesion de usuario e historial conversacional
# ---------------------------------------------------------------------------


class PeticionInicioSesion(BaseModel):
    """Credenciales ligeras para identificar al visitante (sin JWT)."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "examples": [
                {"documento_identidad": "1234567890", "nombre": "María Pérez"},
            ]
        },
    )

    documento_identidad: str = Field(..., min_length=1, max_length=128)
    nombre: str = Field(..., min_length=1, max_length=512)


class RespuestaInicioSesion(BaseModel):
    """Resultado de iniciar sesion: ids canonicos y bandera de usuario previo."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "examples": [
                {
                    "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
                    "session_id": "user:550e8400-e29b-41d4-a716-446655440000",
                    "nombre": "María Pérez",
                    "ya_existia": False,
                    "ultimo_mensaje_at": None,
                },
            ]
        },
    )

    usuario_id: uuid.UUID
    session_id: str
    nombre: str
    ya_existia: bool
    ultimo_mensaje_at: datetime | None = None


RolMensajeHistorial = Literal["human", "ai", "system", "tool"]


class MensajeHistorialItem(BaseModel):
    """Un mensaje del historial persistido (LangChain) listo para el frontend."""

    model_config = ConfigDict(frozen=True)

    rol: RolMensajeHistorial
    contenido: str
    creado_en: datetime | None = Field(
        default=None,
        description="Marca de tiempo si esta disponible en el modelo de persistencia.",
    )


class RespuestaHistorialSesion(BaseModel):
    """Lista ordenada de mensajes (cronologico ascendente)."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "examples": [
                {
                    "mensajes": [
                        {"rol": "human", "contenido": "Hola", "creado_en": None},
                        {"rol": "ai", "contenido": "Hola, ¿en qué puedo ayudarte?", "creado_en": None},
                    ],
                },
            ]
        },
    )

    mensajes: list[MensajeHistorialItem] = Field(default_factory=list)


class RespuestaCierreSesion(BaseModel):
    """Confirmacion de cierre (operacion idempotente en el servidor)."""

    model_config = ConfigDict(frozen=True)

    ok: bool = True
    mensaje: str = "Sesion cerrada en el cliente; la cookie de sesion se elimino si existia."


class PeticionAgente(BaseModel):
    """Cuerpo de una consulta al agente conversacional con streaming SSE."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "examples": [
                {
                    "session_id": "user:550e8400-e29b-41d4-a716-446655440000",
                    "pregunta": "Cual es el telefono de la linea PBX?",
                    "primer_turno": False,
                },
            ]
        },
    )

    session_id: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Identificador canonico de sesion (alineado con POST /api/sesiones).",
    )
    pregunta: str = Field(..., min_length=1, description="Texto de la consulta del usuario.")
    primer_turno: bool = Field(
        default=False,
        description="True si el cliente considera este el primer turno (saludo institucional).",
    )


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
    """Metadatos de documento (historico BM25 / referencias de texto)."""

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
    agente_mock_llm: bool | None = Field(
        default=None,
        description="True si el agente se compilo con MOCK_LLM (sin OpenAI en router/compositor).",
    )


class RespuestaRecarga(BaseModel):
    """Mensaje informativo sobre reindexacion o estado del corpus (sin BM25 en runtime)."""

    model_config = ConfigDict(frozen=True)

    mensaje: str


class RespuestaPromptDefecto(BaseModel):
    """Prompt de sistema predeterminado."""

    model_config = ConfigDict(frozen=True)

    prompt_sistema: str


# ---------------------------------------------------------------------------
# Eventos SSE (Modulo 2 — agente)
# ---------------------------------------------------------------------------


class EventoPensamiento(BaseModel):
    """Transparencia del router: herramienta candidata y razon breve."""

    model_config = ConfigDict(frozen=True)

    tipo: Literal["pensamiento"] = "pensamiento"
    herramienta_candidata: str = Field(..., description="Nombre de la tool elegida o considerada.")
    razon: str = Field(default="", description="Justificacion corta y segura para el cliente.")


class EventoHerramienta(BaseModel):
    """Ejecucion de una tool con latencia observada."""

    model_config = ConfigDict(frozen=True)

    tipo: Literal["herramienta"] = "herramienta"
    nombre: str = Field(..., description="Nombre estable de la tool (contrato LangChain).")
    latencia_ms: int = Field(..., ge=0, description="Tiempo aproximado de ejecucion en milisegundos.")


class EventoToken(BaseModel):
    """Delta de texto emitido durante el streaming del compositor."""

    model_config = ConfigDict(frozen=True)

    tipo: Literal["token"] = "token"
    motor: str = Field(default="agente", description="Motor logico del token (producto M2: agente).")
    texto: str


class EventoFuentes(BaseModel):
    """Fragmentos recuperados desde Qdrant (RAG denso), serializables como dict."""

    model_config = ConfigDict(frozen=True)

    tipo: Literal["fuentes"] = "fuentes"
    chunks: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Metadatos y texto de chunks vectoriales (p. ej. score, id, payload).",
    )


class EventoFinal(BaseModel):
    """Cierre del turno con texto acumulado y metricas opcionales."""

    model_config = ConfigDict(frozen=True)

    tipo: Literal["final"] = "final"
    motor: str = Field(default="agente")
    texto: str
    latencia_ms: int = Field(..., ge=0)
    modelo: str
    metricas: dict[str, Any] | None = Field(
        default=None,
        description="Metricas agregadas opcionales (p. ej. nodos ejecutados).",
    )


class EventoError(BaseModel):
    """Error seguro durante el streaming (sin traceback)."""

    model_config = ConfigDict(frozen=True)

    tipo: Literal["error"] = "error"
    codigo: str = Field(default="error", description="Codigo estable para manejo en cliente.")
    mensaje: str
    motor: str = Field(default="agente")
