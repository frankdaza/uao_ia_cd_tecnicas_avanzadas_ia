"""Pruebas de casos postoperatorio y emparejamiento Telegram (UC-MVP-02)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from src.persistencia.repositorios.tipos_procedimiento import RepositorioTiposProcedimiento
from src.persistencia.repositorios.vinculos_telegram import RepositorioVinculosTelegram
from tests.api.conftest import PDF_FIXTURE_MINIMO


def _cuerpo_caso(*, tipo_id: str, doc_id: str = "CC-9001") -> dict:
    return {
        "paciente_doc_id": doc_id,
        "paciente_nombre": "Paciente Demo A",
        "tipo_procedimiento_id": tipo_id,
        "cirujano_id": "MED-10",
        "cirujano_nombre": "Dr. Cirujano Demo",
        "fecha_cirugia": "2026-05-15",
        "notas_especificas": "Sin alergias conocidas",
    }


@pytest.fixture
async def tipo_procedimiento_ok(
    app_api,
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> str:
    """Procedimiento con ``indexacion_estado=ok`` en la misma BD del cliente."""
    crear = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files={
            "metadata": (
                None,
                json.dumps(
                    {"codigo": f"ok-{uuid.uuid4().hex[:6]}", "nombre": "Procedimiento OK"}
                ),
                "application/json",
            ),
            "archivo": ("protocolo.pdf", PDF_FIXTURE_MINIMO, "application/pdf"),
        },
    )
    assert crear.status_code == 201
    tipo_id = uuid.UUID(crear.json()["id"])

    factory = app_api.state.session_factory
    async with factory() as sesion:
        repo = RepositorioTiposProcedimiento(sesion)
        fila = await repo.obtener_por_id(tipo_id)
        assert fila is not None
        await repo.actualizar(fila, indexacion_estado="ok")
        await sesion.commit()

    return str(tipo_id)


@pytest.mark.asyncio
async def test_crear_caso_201(
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    tipo_procedimiento_ok: str,
) -> None:
    resp = await cliente_api.post(
        "/api/staff/casos",
        headers=cabecera_staff,
        json=_cuerpo_caso(tipo_id=tipo_procedimiento_ok),
    )
    assert resp.status_code == 201
    cuerpo = resp.json()
    assert cuerpo["estado"] == "activo"
    assert cuerpo["paciente_doc_id"] == "CC-9001"
    assert cuerpo["vinculado_telegram"] is False
    assert cuerpo["codigo_emparejamiento_activo"] is None


@pytest.mark.asyncio
async def test_crear_caso_procedimiento_no_indexado_422(
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    cabecera_admin: dict[str, str],
) -> None:
    crear = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files={
            "metadata": (
                None,
                json.dumps({"codigo": "pendiente-1", "nombre": "Pendiente"}),
                "application/json",
            ),
            "archivo": ("protocolo.pdf", PDF_FIXTURE_MINIMO, "application/pdf"),
        },
    )
    tipo_id = crear.json()["id"]
    resp = await cliente_api.post(
        "/api/staff/casos",
        headers=cabecera_staff,
        json=_cuerpo_caso(tipo_id=tipo_id),
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"] == "procedimiento_no_indexado"


@pytest.mark.asyncio
async def test_listar_casos_con_vinculo(
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    cabecera_telegram: dict[str, str],
    tipo_procedimiento_ok: str,
) -> None:
    crear = await cliente_api.post(
        "/api/staff/casos",
        headers=cabecera_staff,
        json=_cuerpo_caso(tipo_id=tipo_procedimiento_ok),
    )
    caso_id = crear.json()["id"]
    gen = await cliente_api.post(
        f"/api/staff/casos/{caso_id}/codigo-emparejamiento",
        headers=cabecera_staff,
    )
    codigo = gen.json()["codigo"]
    await cliente_api.post(
        "/api/telegram/emparejar",
        headers=cabecera_telegram,
        json={"codigo": codigo, "telegram_chat_id": 555001},
    )

    lista = await cliente_api.get(
        "/api/staff/casos",
        headers=cabecera_staff,
        params={"estado": "activo", "limit": 10, "offset": 0},
    )
    assert lista.status_code == 200
    items = lista.json()["items"]
    caso = next(i for i in items if i["id"] == caso_id)
    assert caso["vinculado_telegram"] is True


@pytest.mark.asyncio
async def test_flujo_codigo_y_emparejar(
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    cabecera_telegram: dict[str, str],
    tipo_procedimiento_ok: str,
) -> None:
    crear = await cliente_api.post(
        "/api/staff/casos",
        headers=cabecera_staff,
        json=_cuerpo_caso(tipo_id=tipo_procedimiento_ok),
    )
    caso_id = crear.json()["id"]

    codigo_resp = await cliente_api.post(
        f"/api/staff/casos/{caso_id}/codigo-emparejamiento",
        headers=cabecera_staff,
    )
    assert codigo_resp.status_code == 200
    codigo_data = codigo_resp.json()
    assert 6 <= len(codigo_data["codigo"]) <= 8
    expira = datetime.fromisoformat(codigo_data["expira_at"].replace("Z", "+00:00"))
    assert expira > datetime.now(UTC)

    emparejar = await cliente_api.post(
        "/api/telegram/emparejar",
        headers=cabecera_telegram,
        json={"codigo": codigo_data["codigo"], "telegram_chat_id": 555002},
    )
    assert emparejar.status_code == 200
    emp = emparejar.json()
    assert emp["caso_id"] == caso_id
    assert "mensaje_confirmacion" in emp


@pytest.mark.asyncio
async def test_emparejar_chat_duplicado_409(
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    cabecera_telegram: dict[str, str],
    tipo_procedimiento_ok: str,
) -> None:
    async def _caso_con_codigo(doc_id: str) -> str:
        crear = await cliente_api.post(
            "/api/staff/casos",
            headers=cabecera_staff,
            json=_cuerpo_caso(tipo_id=tipo_procedimiento_ok, doc_id=doc_id),
        )
        cid = crear.json()["id"]
        gen = await cliente_api.post(
            f"/api/staff/casos/{cid}/codigo-emparejamiento",
            headers=cabecera_staff,
        )
        return gen.json()["codigo"]

    codigo1 = await _caso_con_codigo("CC-A")
    codigo2 = await _caso_con_codigo("CC-B")

    ok = await cliente_api.post(
        "/api/telegram/emparejar",
        headers=cabecera_telegram,
        json={"codigo": codigo1, "telegram_chat_id": 777001},
    )
    assert ok.status_code == 200

    dup = await cliente_api.post(
        "/api/telegram/emparejar",
        headers=cabecera_telegram,
        json={"codigo": codigo2, "telegram_chat_id": 777001},
    )
    assert dup.status_code == 409
    assert dup.json()["error"] == "chat_ya_vinculado"


@pytest.mark.asyncio
async def test_codigo_expirado_400(
    app_api,
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    cabecera_telegram: dict[str, str],
    tipo_procedimiento_ok: str,
) -> None:
    crear = await cliente_api.post(
        "/api/staff/casos",
        headers=cabecera_staff,
        json=_cuerpo_caso(tipo_id=tipo_procedimiento_ok),
    )
    caso_id = crear.json()["id"]
    gen = await cliente_api.post(
        f"/api/staff/casos/{caso_id}/codigo-emparejamiento",
        headers=cabecera_staff,
    )
    codigo = gen.json()["codigo"]

    factory = app_api.state.session_factory
    async with factory() as sesion:
        repo = RepositorioVinculosTelegram(sesion)
        pendiente = await repo.obtener_pendiente_por_codigo(codigo)
        assert pendiente is not None
        await repo.actualizar(
            pendiente,
            codigo_expira_at=datetime.now(UTC) - timedelta(hours=1),
        )
        await sesion.commit()

    resp = await cliente_api.post(
        "/api/telegram/emparejar",
        headers=cabecera_telegram,
        json={"codigo": codigo, "telegram_chat_id": 888001},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "codigo_expirado"
    assert "mensaje_telegram" in resp.json()
