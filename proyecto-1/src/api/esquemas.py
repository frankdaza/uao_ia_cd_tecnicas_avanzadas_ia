"""Modelos Pydantic v2 para requests y responses del API Q&A."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


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


class MetadataTurnoHistorial(BaseModel):
    """
    Metadatos de un turno del agente M2 expuestos en el historial (TASK-94).

    Paridad con eventos SSE: herramienta efectiva, trazas resumidas del router y fuentes RAG.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    motor: str = Field(default="agente", description="Motor conversacional (producto: agente).")
    herramienta_efectiva: str | None = Field(
        default=None,
        description="Nombre de tool ejecutada tras el router (p. ej. faq_estructurada, rag_denso).",
    )
    pensamientos: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Trazas serializables (tipo, herramienta, razon_breve, ...).",
    )
    fuentes: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Chunks RAG devueltos por la tool densa (mismo shape que evento fuentes SSE).",
    )
    recortado: bool | None = Field(
        default=None,
        description="True si se aplico truncado por tamano al persistir.",
    )


class MensajeHistorialItem(BaseModel):
    """Un mensaje del historial persistido (LangChain) listo para el frontend."""

    model_config = ConfigDict(frozen=True)

    rol: RolMensajeHistorial
    contenido: str
    creado_en: datetime | None = Field(
        default=None,
        description="Marca de tiempo si esta disponible en el modelo de persistencia.",
    )
    metadata_turno: MetadataTurnoHistorial | None = Field(
        default=None,
        description="Solo mensajes ai: metadatos del turno (tool, pensamientos, fuentes Qdrant).",
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
                        {
                            "rol": "ai",
                            "contenido": "Hola, ¿en qué puedo ayudarte?",
                            "creado_en": None,
                            "metadata_turno": None,
                        },
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
    mensaje: str = (
        "Sesion cerrada en el cliente; la cookie de sesion se elimino si existia."
    )


class RespuestaBorradoUltimoTurno(BaseModel):
    """Resultado de eliminar el ultimo turno persistido (0 a 2 filas en ``chat_history``)."""

    model_config = ConfigDict(frozen=True)

    ok: bool = True
    filas_borradas: int = Field(ge=0, le=2)


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
    pregunta: str = Field(
        ..., min_length=1, description="Texto de la consulta del usuario."
    )
    primer_turno: bool = Field(
        default=False,
        description="True si el cliente considera este el primer turno (saludo institucional).",
    )


# ---------------------------------------------------------------------------
# Response bodies (salud)
# ---------------------------------------------------------------------------


class RespuestaSalud(BaseModel):
    """Estado de salud del servidor."""

    model_config = ConfigDict(frozen=True)

    estado: str = "ok"
    version: str = "1.0.0"
    agente_mock_llm: bool | None = Field(
        default=None,
        description="True si el agente se compilo con MOCK_LLM (sin OpenAI en router/compositor).",
    )


# ---------------------------------------------------------------------------
# Eventos SSE (Modulo 2 — agente)
# ---------------------------------------------------------------------------


class EventoPensamiento(BaseModel):
    """Transparencia del router: herramienta candidata y razon breve."""

    model_config = ConfigDict(frozen=True)

    tipo: Literal["pensamiento"] = "pensamiento"
    herramienta_candidata: str = Field(
        ..., description="Nombre de la tool elegida o considerada."
    )
    razon: str = Field(
        default="", description="Justificacion corta y segura para el cliente."
    )
    argumentos_resumidos: dict[str, Any] | None = Field(
        default=None,
        description="Argumentos del tool-call del router (p. ej. consulta truncada), sin secretos.",
    )


class EventoHerramienta(BaseModel):
    """Ejecucion de una tool con latencia observada."""

    model_config = ConfigDict(frozen=True)

    tipo: Literal["herramienta"] = "herramienta"
    nombre: str = Field(
        ..., description="Nombre estable de la tool (contrato LangChain)."
    )
    latencia_ms: int = Field(
        ..., ge=0, description="Tiempo aproximado de ejecucion en milisegundos."
    )
    faq_match_encontrado: bool | None = Field(
        default=None,
        description="Solo FAQ: True si el JSON devolvio match por umbral.",
    )
    faq_umbral_match: float | None = Field(
        default=None,
        description="Solo FAQ: umbral FAQ_UMBRAL_MATCH efectivo al ejecutar la tool.",
    )
    faq_consulta_ejecutada: str | None = Field(
        default=None,
        description="Solo FAQ: cadena usada para el match (truncada en servidor).",
    )
    resultado_listado: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Solo ``listar_estructurado``: resumen JSON seguro (conteo, muestra_truncada, "
            "primeros items) para la UI sin repetir todo el payload."
        ),
    )


class EventoToken(BaseModel):
    """Delta de texto emitido durante el streaming del compositor."""

    model_config = ConfigDict(frozen=True)

    tipo: Literal["token"] = "token"
    motor: str = Field(
        default="agente", description="Motor logico del token (producto M2: agente)."
    )
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
    codigo: str = Field(
        default="error", description="Codigo estable para manejo en cliente."
    )
    mensaje: str
    motor: str = Field(default="agente")
