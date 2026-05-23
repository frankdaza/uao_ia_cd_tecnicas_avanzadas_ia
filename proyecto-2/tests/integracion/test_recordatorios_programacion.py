"""Pruebas unitarias de programacion de recordatorios (UC-MVP-04)."""

from __future__ import annotations

from datetime import UTC, date, datetime

from src.integracion.recordatorios.programacion import (
    calcular_programado_at,
    renderizar_texto_plantilla,
)


def test_calcular_programado_at_offset_24h() -> None:
    programado = calcular_programado_at(date(2026, 5, 10), 24)
    assert programado == datetime(2026, 5, 11, 0, 0, tzinfo=UTC)


def test_calcular_programado_at_offset_cero() -> None:
    programado = calcular_programado_at(date(2026, 1, 1), 0)
    assert programado == datetime(2026, 1, 1, 0, 0, tzinfo=UTC)


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
