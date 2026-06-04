"""Pruebas de configuracion admin del job de recordatorios."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

import uuid
from datetime import UTC, datetime

from src.configuracion import obtener_configuracion
from src.integracion.recordatorios.programacion import calcular_programado_at_por_intervalo
from src.persistencia.repositorios.recordatorios_enviados import (
    RepositorioRecordatoriosEnviados,
)
from tests.api.conftest import (
    EMAIL_ADMIN_DEMO,
    PASSWORD_STAFF_ADMIN_TEST,
)
from tests.api.test_staff_casos import _cuerpo_caso


def _en_utc(valor: datetime) -> datetime:
    if valor.tzinfo is None:
        return valor.replace(tzinfo=UTC)
    return valor.astimezone(UTC)


@pytest.fixture
async def token_staff_admin(
    cliente_api: AsyncClient,
    usuarios_staff_sembrados: None,  # noqa: ARG001
) -> str:
    resp = await cliente_api.post(
        "/api/auth/staff/login",
        json={"email": EMAIL_ADMIN_DEMO, "password": PASSWORD_STAFF_ADMIN_TEST},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def cabecera_staff_admin(token_staff_admin: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_staff_admin}"}


@pytest.mark.asyncio
async def test_get_recordatorios_job_admin_jwt(
    cliente_api: AsyncClient,
    cabecera_staff_admin: dict[str, str],
) -> None:
    resp = await cliente_api.get(
        "/api/admin/recordatorios-job",
        headers=cabecera_staff_admin,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "habilitado" in data
    assert data["habilitado"] is False
    assert data["interval_seg"] == 60


@pytest.mark.asyncio
async def test_patch_recordatorios_job_admin_jwt(
    cliente_api: AsyncClient,
    cabecera_staff_admin: dict[str, str],
    app_api,
) -> None:
    resp = await cliente_api.patch(
        "/api/admin/recordatorios-job",
        headers=cabecera_staff_admin,
        json={"habilitado": True, "interval_seg": 120},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["habilitado"] is True
    assert data["interval_seg"] == 120
    assert data["updated_at"] is not None

    snapshot = await app_api.state.recordatorios_job.leer()
    assert snapshot.habilitado is True
    assert snapshot.interval_seg == 120


@pytest.mark.asyncio
async def test_get_recordatorios_job_staff_no_admin_403(
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
) -> None:
    resp = await cliente_api.get(
        "/api/admin/recordatorios-job",
        headers=cabecera_staff,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_recordatorios_job_admin_api_key(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    resp = await cliente_api.get(
        "/api/admin/recordatorios-job",
        headers=cabecera_admin,
    )
    assert resp.status_code == 200, resp.text


@pytest.mark.asyncio
async def test_patch_recordatorios_job_vacio_422(
    cliente_api: AsyncClient,
    cabecera_staff_admin: dict[str, str],
) -> None:
    resp = await cliente_api.patch(
        "/api/admin/recordatorios-job",
        headers=cabecera_staff_admin,
        json={},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_patch_interval_reprograma_pendientes(
    cliente_api: AsyncClient,
    cabecera_staff_admin: dict[str, str],
    cabecera_staff: dict[str, str],
    app_api,
    tipo_procedimiento_ok: str,
    medico_activo_catalogo: dict[str, str | None],
) -> None:
    med = medico_activo_catalogo
    crear = await cliente_api.post(
        "/api/staff/casos",
        headers=cabecera_staff,
        json=_cuerpo_caso(
            tipo_id=tipo_procedimiento_ok,
            doc_id="CC-REC-REPROG",
            cirujano_id=med["codigo_registro"],
            cirujano_nombre=med["nombre_completo"],
        ),
    )
    assert crear.status_code == 201
    caso_uuid = uuid.UUID(crear.json()["id"])

    resp = await cliente_api.patch(
        "/api/admin/recordatorios-job",
        headers=cabecera_staff_admin,
        json={"interval_seg": 30},
    )
    assert resp.status_code == 200
    assert resp.json()["interval_seg"] == 30
    ancla = datetime.now(UTC)

    factory = app_api.state.session_factory
    async with factory() as sesion:
        repo_rec = RepositorioRecordatoriosEnviados(sesion)
        todos_caso = sorted(
            [r for r in await repo_rec.listar_pendientes_sin_enviar() if r.caso_id == caso_uuid],
            key=lambda r: r.programado_at,
        )
        assert len(todos_caso) == 3
        for indice, fila in enumerate(todos_caso):
            esperado = calcular_programado_at_por_intervalo(ancla, indice, 30)
            delta = abs((_en_utc(fila.programado_at) - esperado).total_seconds())
            assert delta < 15


@pytest.mark.asyncio
async def test_obtener_o_crear_respeta_env_inicial(
    monkeypatch: pytest.MonkeyPatch,
    app_api,
) -> None:
    """La fila singleton se crea con valores de entorno en el primer arranque."""
    monkeypatch.setenv("RECORDATORIOS_JOB_HABILITADO", "true")
    monkeypatch.setenv("RECORDATORIOS_JOB_INTERVAL_SEG", "90")
    obtener_configuracion.cache_clear()

    from src.api.main import crear_app

    app = crear_app(url_bd="sqlite+aiosqlite:///:memory:")
    async with app.router.lifespan_context(app):
        snapshot = await app.state.recordatorios_job.leer()
        assert snapshot.habilitado is True
        assert snapshot.interval_seg == 90
