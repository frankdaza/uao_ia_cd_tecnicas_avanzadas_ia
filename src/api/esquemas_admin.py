"""Esquemas Pydantic del panel administrativo M2 (API ``/api/admin``)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EstadoConfigAdminM2Respuesta(BaseModel):
    """Estado fusionado expuesto al panel (valores efectivos que usa el agente)."""

    model_config = ConfigDict(frozen=True)

    version: int = Field(ge=0, description="Version optimista para PATCH (0 si no hay fila).")
    updated_at: datetime | None = Field(
        default=None,
        description="Ultima actualizacion de overrides en base de datos, si existe fila.",
    )
    modelo_llm_router: str
    modelo_llm_compositor: str
    temperatura_router: float
    temperatura_compositor: float
    top_p_router: float | None = Field(
        default=None,
        description="Si es null, el cliente OpenAI usa su valor por defecto del modelo.",
    )
    top_p_compositor: float | None = None
    model_kwargs_router: dict[str, Any] = Field(default_factory=dict)
    model_kwargs_compositor: dict[str, Any] = Field(default_factory=dict)
    meta_prompt: dict[str, Any]
    prompt_institucional: str
    rag_top_k: int = Field(ge=1, le=50, description="Top-k efectivo del recuperador denso (Qdrant).")
    rag_score_minimo: float = Field(
        ge=0.0,
        le=1.0,
        description="Umbral minimo de similitud para conservar fragmentos RAG.",
    )
    historial_turnos_max: int = Field(
        ge=1,
        le=200,
        description=(
            "Tope de turnos (mensajes humano como ancla) cargados para router y compositor; "
            "columna admin o HISTORIAL_TURNOS_MAX en .env."
        ),
    )
    nota_precedencia: str = Field(
        default=(
            "Valores mostrados son los efectivos al atender peticiones: overrides en "
            "PostgreSQL (tabla config_admin_m2) sustituyen al archivo config/router_meta_prompt.json, "
            "a su vez sobre valores por defecto de variables de entorno y constantes de codigo "
            "(temperaturas 0.0 router / 0.2 compositor cuando no hay override en base de datos; "
            "RAG_TOP_K y RAG_SCORE_MINIMO cuando las columnas rag_* estan en NULL)."
        ),
        description="Texto fijo de documentacion para operadores humanos.",
    )


class ParcheConfigAdminM2Cuerpo(BaseModel):
    """Cuerpo PATCH: solo se actualizan campos presentes (no null en JSON)."""

    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=0)
    modelo_llm_router: str | None = None
    modelo_llm_compositor: str | None = None
    temperatura_router: float | None = Field(default=None, ge=0.0, le=2.0)
    temperatura_compositor: float | None = Field(default=None, ge=0.0, le=2.0)
    top_p_router: float | None = Field(default=None, ge=0.0, le=1.0)
    top_p_compositor: float | None = Field(default=None, ge=0.0, le=1.0)
    model_kwargs_router: dict[str, Any] | None = None
    model_kwargs_compositor: dict[str, Any] | None = None
    meta_prompt: dict[str, Any] | None = None
    prompt_institucional: str | None = None
    rag_top_k: int | None = Field(default=None, ge=1, le=50)
    rag_score_minimo: float | None = Field(default=None, ge=0.0, le=1.0)
    historial_turnos_max: int | None = Field(default=None, ge=1, le=200)

    @field_validator("modelo_llm_router", "modelo_llm_compositor")
    @classmethod
    def validar_modelo_no_vacio_si_presente(cls, v: str | None) -> str | None:
        """Si el campo viene en el JSON, no se acepta cadena vacía (solo omitir o texto no vacío)."""
        if v is None:
            return None
        s = v.strip()
        if not s:
            msg = "Los identificadores de modelo no pueden ser cadenas vacias."
            raise ValueError(msg)
        return s


class UsuarioAdminVista(BaseModel):
    """Usuario listado en panel admin (PII minimizada)."""

    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    nombre: str
    documento_identidad_enmascarado: str
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None


class ListadoUsuariosAdminRespuesta(BaseModel):
    """Paginacion por offset/limit acotada."""

    model_config = ConfigDict(frozen=True)

    items: list[UsuarioAdminVista]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=200)
    offset: int = Field(ge=0)


class MetricasAdminResumen(BaseModel):
    """Agregados ligeros para dashboard (consultas acotadas a conteos)."""

    model_config = ConfigDict(frozen=True)

    usuarios_total: int = Field(ge=0)
    usuarios_activos_ultimos_7_dias: int = Field(ge=0)
    sesiones_estimadas: int = Field(
        default=0,
        description="Reservado: hoy no hay tabla de sesiones OLTP; se devuelve 0 documentado.",
    )


__all__ = [
    "EstadoConfigAdminM2Respuesta",
    "ListadoUsuariosAdminRespuesta",
    "MetricasAdminResumen",
    "ParcheConfigAdminM2Cuerpo",
    "UsuarioAdminVista",
]
