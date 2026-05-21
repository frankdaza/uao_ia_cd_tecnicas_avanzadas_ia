"""Esquemas Pydantic de entrada y salida de tools."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SeveridadTriage = Literal["info", "seguimiento", "urgente"]


class EntradaConsultarProtocoloRag(BaseModel):
    consulta: str = Field(..., description="Pregunta del paciente sobre cuidados o protocolo.")


class EntradaFaqPostoperatorio(BaseModel):
    consulta: str = Field(
        ...,
        description="Texto de la pregunta o palabras clave para buscar en FAQs.",
    )


class EntradaClasificarTriage(BaseModel):
    sintomas_descritos: str = Field(
        ...,
        description="Descripcion de sintomas o motivo de consulta del paciente.",
    )
    mensaje_paciente: str | None = Field(
        default=None,
        description="Ultimo mensaje literal del paciente (opcional).",
    )


class SalidaClasificarTriage(BaseModel):
    severidad: SeveridadTriage
    rationale: str = Field(..., description="Justificacion breve de la clasificacion.")


class EntradaEscalarEquipo(BaseModel):
    severidad: SeveridadTriage = Field(
        ...,
        description="Severidad de triage; use urgente para red flags.",
    )
    resumen: str = Field(..., max_length=1024, description="Resumen para el equipo clinico.")
    mensaje_paciente_ref: str | None = Field(
        default=None,
        description="Fragmento del mensaje del paciente que motivo la alerta.",
    )


class SalidaEscalarEquipo(BaseModel):
    alerta_id: str
    mensaje: str


class SalidaContextoCaso(BaseModel):
    vinculado: bool
    paciente_nombre: str | None = None
    nombre_procedimiento: str | None = None
    fecha_cirugia: str | None = None
    notas_especificas: str | None = None
    caso_id: str | None = None
    tipo_procedimiento_id: str | None = None
