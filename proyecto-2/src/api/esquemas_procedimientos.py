"""Esquemas Pydantic del catalogo de procedimientos (UC-MVP-01)."""

from __future__ import annotations

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

_CODIGO_ASCII = re.compile(r"^[A-Za-z0-9_-]+$")


class MetadataProcedimientoCuerpo(BaseModel):
    """Metadatos enviados en el campo form ``metadata`` (JSON)."""

    codigo: str = Field(..., min_length=1, max_length=64)
    nombre: str = Field(..., min_length=1, max_length=512)

    @field_validator("codigo")
    @classmethod
    def validar_codigo_ascii(cls, valor: str) -> str:
        v = valor.strip()
        if not v or not _CODIGO_ASCII.fullmatch(v):
            raise ValueError(
                "codigo debe ser ASCII alfanumerico (guion y guion bajo permitidos)."
            )
        return v

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, valor: str) -> str:
        v = valor.strip()
        if not v:
            raise ValueError("nombre no puede estar vacio.")
        return v


class MetadataProcedimientoParche(BaseModel):
    """Campos opcionales en PATCH (JSON parcial)."""

    codigo: str | None = Field(default=None, max_length=64)
    nombre: str | None = Field(default=None, max_length=512)

    @field_validator("codigo")
    @classmethod
    def validar_codigo_opcional(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        v = valor.strip()
        if not v or not _CODIGO_ASCII.fullmatch(v):
            raise ValueError(
                "codigo debe ser ASCII alfanumerico (guion y guion bajo permitidos)."
            )
        return v

    @field_validator("nombre")
    @classmethod
    def validar_nombre_opcional(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        v = valor.strip()
        if not v:
            raise ValueError("nombre no puede estar vacio.")
        return v


class ProcedimientoVista(BaseModel):
    """Vista publica de un tipo de procedimiento (sin rutas absolutas ni hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    codigo: str
    nombre: str
    formato_protocolo: str
    indexacion_estado: str
    qdrant_collection_version: int | None = None
    created_at: datetime


class ListadoProcedimientosRespuesta(BaseModel):
    """Listado paginado."""

    model_config = ConfigDict(frozen=True)

    items: list[ProcedimientoVista]
    limit: int
    offset: int
