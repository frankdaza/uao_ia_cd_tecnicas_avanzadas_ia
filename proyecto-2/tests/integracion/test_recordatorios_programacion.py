"""Pruebas unitarias de programacion de recordatorios (UC-MVP-04)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from src.integracion.recordatorios.programacion import (
    calcular_programado_at,
    calcular_programado_at_por_intervalo,
    renderizar_texto_plantilla,
)

ZONA_BOGOTA = ZoneInfo("America/Bogota")


def test_calcular_programado_at_offset_24h() -> None:
    programado = calcular_programado_at(date(2026, 5, 10), 24, zona=ZONA_BOGOTA)
    # 11/05 00:00 Bogota (UTC-5) = 11/05 05:00 UTC
    assert programado == datetime(2026, 5, 11, 5, 0, tzinfo=UTC)


def test_calcular_programado_at_offset_cero() -> None:
    programado = calcular_programado_at(date(2026, 1, 1), 0, zona=ZONA_BOGOTA)
    # 01/01 00:00 Bogota = 01/01 05:00 UTC
    assert programado == datetime(2026, 1, 1, 5, 0, tzinfo=UTC)


def test_calcular_programado_at_por_intervalo() -> None:
    ancla = datetime(2026, 6, 4, 12, 0, 0, tzinfo=UTC)
    assert calcular_programado_at_por_intervalo(ancla, 0, 10) == datetime(
        2026, 6, 4, 12, 0, 10, tzinfo=UTC
    )
    assert calcular_programado_at_por_intervalo(ancla, 2, 10) == datetime(
        2026, 6, 4, 12, 0, 30, tzinfo=UTC
    )


def test_renderizar_texto_plantilla_placeholders() -> None:
    texto = renderizar_texto_plantilla(
        "Hola {nombre_paciente}, {tipo_procedimiento}: {texto_cuidado}",
        nombre_paciente="Ana",
        tipo_procedimiento="Colecistectomia",
        texto_cuidado="Tomar analgesicos.",
    )
    assert "Ana" in texto
    assert "Colecistectomia" in texto
    assert "Tomar analgesicos." in texto
