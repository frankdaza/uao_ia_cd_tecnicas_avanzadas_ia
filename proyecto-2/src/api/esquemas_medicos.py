"""Esquemas Pydantic del catalogo de medicos (admin)."""

from __future__ import annotations

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

_CODIGO_REGISTRO_ASCII = re.compile(r"^[A-Za-z0-9._-]+$")


class MedicoCuerpo(BaseModel):
    """Cuerpo JSON para crear un medico."""

    codigo_registro: str = Field(..., min_length=1, max_length=64)
    nombre_completo: str = Field(..., min_length=1, max_length=512)
    especialidad: str | None = Field(default=None, max_length=256)

    @field_validator("codigo_registro")
    @classmethod
    def validar_codigo_registro(cls, valor: str) -> str:
        v = valor.strip()
        if not v or not _CODIGO_REGISTRO_ASCII.fullmatch(v):
            raise ValueError(
                "codigo_registro debe ser ASCII alfanumerico "
                "(punto, guion y guion bajo permitidos)."
            )
        return v

    @field_validator("nombre_completo")
    @classmethod
    def validar_nombre(cls, valor: str) -> str:
        v = valor.strip()
        if not v:
            raise ValueError("nombre_completo no puede estar vacio.")
        return v

    @field_validator("especialidad")
    @classmethod
    def validar_especialidad(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        v = valor.strip()
        return v or None


class MedicoParche(BaseModel):
    """Campos opcionales en PATCH."""

    codigo_registro: str | None = Field(default=None, max_length=64)
    nombre_completo: str | None = Field(default=None, max_length=512)
    especialidad: str | None = Field(default=None, max_length=256)
    activo: bool | None = None

    @field_validator("codigo_registro")
    @classmethod
    def validar_codigo_opcional(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        v = valor.strip()
        if not v or not _CODIGO_REGISTRO_ASCII.fullmatch(v):
            raise ValueError(
                "codigo_registro debe ser ASCII alfanumerico "
                "(punto, guion y guion bajo permitidos)."
            )
        return v

    @field_validator("nombre_completo")
    @classmethod
    def validar_nombre_opcional(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        v = valor.strip()
        if not v:
            raise ValueError("nombre_completo no puede estar vacio.")
        return v

    @field_validator("especialidad")
    @classmethod
    def validar_especialidad_opcional(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        v = valor.strip()
        return v or None


class MedicoVista(BaseModel):
    """Vista publica de un medico del catalogo."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    codigo_registro: str
    nombre_completo: str
    especialidad: str | None
    activo: bool
    created_at: datetime
    updated_at: datetime


class ListadoMedicosRespuesta(BaseModel):
    """Listado paginado con total."""

    model_config = ConfigDict(frozen=True)

    items: list[MedicoVista]
    total: int
