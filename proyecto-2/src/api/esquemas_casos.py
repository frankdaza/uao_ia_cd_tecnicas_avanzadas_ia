"""Esquemas Pydantic de casos postoperatorio y emparejamiento (UC-MVP-02)."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CrearCasoCuerpo(BaseModel):
    """Alta de caso quirurgico por el asistente."""

    paciente_doc_id: str = Field(..., min_length=1, max_length=128)
    paciente_nombre: str = Field(..., min_length=1, max_length=512)
    tipo_procedimiento_id: uuid.UUID
    cirujano_id: str = Field(..., min_length=1, max_length=128)
    cirujano_nombre: str = Field(..., min_length=1, max_length=512)
    fecha_cirugia: date
    notas_especificas: str | None = Field(default=None, max_length=8000)

    @field_validator(
        "paciente_doc_id",
        "paciente_nombre",
        "cirujano_id",
        "cirujano_nombre",
    )
    @classmethod
    def validar_texto_no_vacio(cls, valor: str) -> str:
        v = valor.strip()
        if not v:
            raise ValueError("El campo no puede estar vacio.")
        return v


class CasoVista(BaseModel):
    """Vista de caso para panel staff."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    paciente_doc_id: str
    paciente_nombre: str
    tipo_procedimiento_id: uuid.UUID
    cirujano_id: str
    cirujano_nombre: str
    fecha_cirugia: date
    notas_especificas: str | None
    estado: str
    created_at: datetime
    vinculado_telegram: bool = False
    codigo_emparejamiento_activo: str | None = None


class ListadoCasosRespuesta(BaseModel):
    """Listado paginado de casos."""

    model_config = ConfigDict(frozen=True)

    items: list[CasoVista]
    limit: int
    offset: int


class CodigoEmparejamientoRespuesta(BaseModel):
    """Codigo generado para el paciente."""

    caso_id: uuid.UUID
    codigo: str
    expira_at: datetime


class DesvincularTelegramRespuesta(BaseModel):
    """Resultado de desvincular el dispositivo Telegram de un caso (solo admin)."""

    caso: CasoVista
    notificado_telegram: bool


class EmparejarTelegramCuerpo(BaseModel):
    """Cuerpo del endpoint interno de emparejamiento."""

    codigo: str = Field(..., min_length=1, max_length=32)
    telegram_chat_id: int = Field(..., gt=0)


class EmparejarTelegramRespuesta(BaseModel):
    """Resultado exitoso de emparejamiento."""

    caso_id: uuid.UUID
    vinculado_at: datetime
    mensaje_confirmacion: str


class ErrorEmparejamientoRespuesta(BaseModel):
    """Error estructurado para la capa Telegram."""

    error: str
    mensaje_telegram: str


class TipoProcedimientoOpcion(BaseModel):
    """Opcion minima para select de alta de caso (panel staff)."""

    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    codigo: str
    nombre: str


class ListadoTiposProcedimientoOpcionRespuesta(BaseModel):
    """Tipos de procedimiento filtrados por indexacion (UC-MVP-02)."""

    model_config = ConfigDict(frozen=True)

    items: list[TipoProcedimientoOpcion]


class MedicoOpcion(BaseModel):
    """Opcion minima de medico/cirujano para select de alta de caso (panel staff)."""

    model_config = ConfigDict(frozen=True)

    codigo_registro: str
    nombre_completo: str
    especialidad: str | None


class ListadoMedicosOpcionRespuesta(BaseModel):
    """Medicos activos del catalogo para alta de caso (TASK-138)."""

    model_config = ConfigDict(frozen=True)

    items: list[MedicoOpcion]
