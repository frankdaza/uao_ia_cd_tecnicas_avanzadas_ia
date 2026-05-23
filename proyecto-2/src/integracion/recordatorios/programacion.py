"""Calculo de fechas y render de plantillas de recordatorio (UC-MVP-04)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta


def calcular_programado_at(
    fecha_cirugia: date,
    offset_horas_desde_cirugia: int,
) -> datetime:
    """
    ``programado_at`` = medianoche UTC de ``fecha_cirugia`` + offset en horas.

    La fecha de cirugia es un ``date`` sin zona; se ancla a UTC para comparar
    con ``datetime.now(UTC)`` en el job y en tests.
    """
    inicio_dia = datetime(
        fecha_cirugia.year,
        fecha_cirugia.month,
        fecha_cirugia.day,
        tzinfo=UTC,
    )
    return inicio_dia + timedelta(hours=offset_horas_desde_cirugia)


def renderizar_texto_plantilla(
    texto_plantilla: str,
    *,
    nombre_paciente: str,
    tipo_procedimiento: str,
    texto_cuidado: str,
) -> str:
    """Sustituye placeholders documentados en UC-MVP-04."""
    return texto_plantilla.format(
        nombre_paciente=nombre_paciente,
        tipo_procedimiento=tipo_procedimiento,
        texto_cuidado=texto_cuidado,
    )
