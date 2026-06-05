"""Pruebas del dashboard operativo staff."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from src.persistencia.repositorios.alertas_triage import RepositorioAlertasTriage
from src.persistencia.repositorios.recordatorios_enviados import RepositorioRecordatoriosEnviados
from tests.api.test_staff_seguimiento import (
    _crear_alerta_pendiente,
    _crear_caso_y_vinculo,
)


@pytest.mark.asyncio
async def test_dashboard_staff_resumen_conteos(
    app_api,
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    tipo_procedimiento_ok: str,
    medico_activo_catalogo: dict[str, str | None],
) -> None:
    caso_id = await _crear_caso_y_vinculo(
        app_api,
        cliente_api,
        cabecera_staff,
        tipo_procedimiento_ok,
        medico_activo_catalogo,
    )
    await _crear_alerta_pendiente(app_api, caso_id)

    factory = app_api.state.session_factory
    async with factory() as sesion:
        repo = RepositorioAlertasTriage(sesion)
        await repo.crear(
            caso_id=caso_id,
            severidad="seguimiento",
            resumen="Seguimiento demo",
        )
        await repo.crear(
            caso_id=caso_id,
            severidad="info",
            resumen="Info demo",
        )
        fila_rev = await repo.crear(
            caso_id=caso_id,
            severidad="urgente",
            resumen="Ya revisada",
        )
        fila_rev.revisado = True
        fila_rev.revisado_at = datetime.now(UTC)
        await sesion.commit()

    resp = await cliente_api.get(
        "/api/staff/dashboard/resumen",
        headers=cabecera_staff,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["alertas"]["pendientes"]["urgente"] >= 1
    assert data["alertas"]["pendientes"]["seguimiento"] >= 1
    assert data["alertas"]["pendientes"]["info"] >= 1
    assert data["alertas"]["pendientes"]["total"] >= 3
    assert data["casos"]["activos"] >= 1
    assert data["casos"]["con_telegram_vinculado"] >= 1
    assert len(data["serie_alertas_7d"]) == 7
    assert len(data["alertas_recientes"]) >= 1
    assert "generado_en" in data


@pytest.mark.asyncio
async def test_dashboard_staff_recordatorios_vencidos(
    app_api,
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    tipo_procedimiento_ok: str,
    medico_activo_catalogo: dict[str, str | None],
) -> None:
    from src.persistencia.repositorios.plantillas_recordatorio import (
        RepositorioPlantillasRecordatorio,
    )

    caso_id = await _crear_caso_y_vinculo(
        app_api,
        cliente_api,
        cabecera_staff,
        tipo_procedimiento_ok,
        medico_activo_catalogo,
        chat_id=88099,
    )

    factory = app_api.state.session_factory
    async with factory() as sesion:
        repo_plant = RepositorioPlantillasRecordatorio(sesion)
        plantillas = await repo_plant.listar_por_tipo(uuid.UUID(tipo_procedimiento_ok))
        if not plantillas:
            plantillas = [
                await repo_plant.crear(
                    tipo_procedimiento_id=uuid.UUID(tipo_procedimiento_ok),
                    tipo="medicacion",
                    offset_horas_desde_cirugia=24,
                    texto_plantilla="Recordatorio demo",
                )
            ]
        plantilla_id = plantillas[0].id

        repo_rec = RepositorioRecordatoriosEnviados(sesion)
        await repo_rec.crear(
            caso_id=caso_id,
            plantilla_id=plantilla_id,
            programado_at=datetime.now(UTC) - timedelta(hours=2),
            estado="pendiente",
        )
        await sesion.commit()

    resp = await cliente_api.get(
        "/api/staff/dashboard/resumen",
        headers=cabecera_staff,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["recordatorios"]["pendientes_vencidos"] >= 1


@pytest.mark.asyncio
async def test_dashboard_staff_sin_auth_401(cliente_api: AsyncClient) -> None:
    resp = await cliente_api.get("/api/staff/dashboard/resumen")
    assert resp.status_code == 401
