"""Calculo de fechas y render de plantillas de recordatorio (UC-MVP-04)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo


def calcular_programado_at(
    fecha_cirugia: date,
    offset_horas_desde_cirugia: int,
    *,
    zona: ZoneInfo,
) -> datetime:
    """
    ``programado_at`` = medianoche en ``zona`` del dia de cirugia + offset en horas.

    Se persiste en UTC (timestamptz) para comparar con ``datetime.now(UTC)`` en el job.
    """
    inicio_dia = datetime(
        fecha_cirugia.year,
        fecha_cirugia.month,
        fecha_cirugia.day,
        tzinfo=zona,
    )
    return (inicio_dia + timedelta(hours=offset_horas_desde_cirugia)).astimezone(UTC)


def calcular_programado_at_por_intervalo(
    ancla_utc: datetime,
    indice_orden: int,
    interval_seg: int,
) -> datetime:
    """
    ``programado_at`` para la plantilla en posición ``indice_orden`` (0-based).

    Espaciado: ``ancla + interval_seg * (indice_orden + 1)`` segundos (panel admin).
    """
    return ancla_utc + timedelta(seconds=interval_seg * (indice_orden + 1))


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
