"""Pruebas API staff seguimiento: alertas y conversacion (UC-MVP-05 / TASK-108)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from langchain_core.messages import AIMessage, HumanMessage

from src.agentes.agente_taam import construir_agente_taam
from src.persistencia.repositorios.alertas_triage import RepositorioAlertasTriage
from src.persistencia.repositorios.tipos_procedimiento import RepositorioTiposProcedimiento
from src.persistencia.repositorios.vinculos_telegram import RepositorioVinculosTelegram
from tests.api.conftest import PDF_FIXTURE_MINIMO
from tests.api.test_staff_casos import _cuerpo_caso


@pytest.fixture
async def tipo_procedimiento_ok(
    app_api,
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> str:
    crear = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files={
            "metadata": (
                None,
                json.dumps(
                    {
                        "codigo": f"seg-{uuid.uuid4().hex[:6]}",
                        "nombre": "Procedimiento Seguimiento",
                    }
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


async def _crear_caso_y_vinculo(
    app_api,
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    tipo_procedimiento_ok: str,
    medico_activo_catalogo: dict[str, str | None],
    *,
    chat_id: int = 88001,
) -> uuid.UUID:
    med = medico_activo_catalogo
    resp = await cliente_api.post(
        "/api/staff/casos",
        headers=cabecera_staff,
        json=_cuerpo_caso(
            tipo_id=tipo_procedimiento_ok,
            doc_id="CC-SEGUIMIENTO",
            cirujano_id=med["codigo_registro"],
            cirujano_nombre=med["nombre_completo"],
        ),
    )
    assert resp.status_code == 201
    caso_id = uuid.UUID(resp.json()["id"])

    factory = app_api.state.session_factory
    async with factory() as sesion:
        repo = RepositorioVinculosTelegram(sesion)
        await repo.crear(
            caso_id=caso_id,
            telegram_chat_id=chat_id,
            vinculado_at=datetime.now(UTC),
        )
        await sesion.commit()
    return caso_id


async def _sembrar_hilo_conversacion(app_api, chat_id: int) -> None:
    checkpointer = app_api.state.checkpointer
    agente = construir_agente_taam(checkpointer)
    session_id = f"telegram:{chat_id}"
    await agente.aupdate_state(
        {"configurable": {"thread_id": session_id}},
        {
            "messages": [
                HumanMessage(content="Me duele la herida"),
                AIMessage(content="Registre su sintoma; si hay fiebre acuda a urgencias."),
            ]
        },
    )


async def _crear_alerta_pendiente(app_api, caso_id: uuid.UUID) -> uuid.UUID:
    factory = app_api.state.session_factory
    async with factory() as sesion:
        repo = RepositorioAlertasTriage(sesion)
        fila = await repo.crear(
            caso_id=caso_id,
            severidad="urgente",
            resumen="Dolor intenso reportado",
            mensaje_paciente_ref="ref-demo",
        )
        await sesion.commit()
        return fila.id


@pytest.mark.asyncio
async def test_listar_alertas_no_revisadas(
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
    alerta_id = await _crear_alerta_pendiente(app_api, caso_id)

    resp = await cliente_api.get(
        "/api/staff/alertas",
        headers=cabecera_staff,
        params={"revisado": "false"},
    )
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert len(cuerpo["items"]) >= 1
    primera = cuerpo["items"][0]
    assert primera["id"] == str(alerta_id)
    assert primera["severidad"] == "urgente"
    assert primera["revisado"] is False
    assert primera["paciente_doc_id"].endswith("IENTO") or "*" in primera["paciente_doc_id"]


@pytest.mark.asyncio
async def test_patch_marcar_revisado_idempotente(
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
        chat_id=88002,
    )
    alerta_id = await _crear_alerta_pendiente(app_api, caso_id)

    patch1 = await cliente_api.patch(
        f"/api/staff/alertas/{alerta_id}",
        headers=cabecera_staff,
        json={"revisado": True},
    )
    assert patch1.status_code == 200
    c1 = patch1.json()
    assert c1["revisado"] is True
    assert c1["revisado_at"] is not None
    assert c1["revisado_staff_id"] is not None
    staff_id_primero = c1["revisado_staff_id"]
    revisado_at_primero = c1["revisado_at"]

    lista = await cliente_api.get(
        "/api/staff/alertas",
        headers=cabecera_staff,
        params={"revisado": "false", "caso_id": str(caso_id)},
    )
    ids_pendientes = {item["id"] for item in lista.json()["items"]}
    assert str(alerta_id) not in ids_pendientes

    patch2 = await cliente_api.patch(
        f"/api/staff/alertas/{alerta_id}",
        headers=cabecera_staff,
        json={"revisado": True},
    )
    assert patch2.status_code == 200
    c2 = patch2.json()
    assert c2["revisado_staff_id"] == staff_id_primero
    assert c2["revisado_at"] == revisado_at_primero


@pytest.mark.asyncio
async def test_conversacion_caso_con_hilo(
    app_api,
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    tipo_procedimiento_ok: str,
    medico_activo_catalogo: dict[str, str | None],
) -> None:
    chat_id = 88003
    caso_id = await _crear_caso_y_vinculo(
        app_api,
        cliente_api,
        cabecera_staff,
        tipo_procedimiento_ok,
        medico_activo_catalogo,
        chat_id=chat_id,
    )
    await _sembrar_hilo_conversacion(app_api, chat_id)

    resp = await cliente_api.get(
        f"/api/staff/casos/{caso_id}/conversacion",
        headers=cabecera_staff,
    )
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["caso_id"] == str(caso_id)
    assert len(cuerpo["mensajes"]) == 2
    assert cuerpo["mensajes"][0]["rol"] == "human"
    assert "herida" in cuerpo["mensajes"][0]["contenido"]
    assert cuerpo["mensajes"][1]["rol"] == "assistant"
    assert cuerpo["telegram_chat_id_enmascarado"] is not None


@pytest.mark.asyncio
async def test_conversacion_sin_vinculo_404(
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    tipo_procedimiento_ok: str,
    medico_activo_catalogo: dict[str, str | None],
) -> None:
    med = medico_activo_catalogo
    crear = await cliente_api.post(
        "/api/staff/casos",
        headers=cabecera_staff,
        json=_cuerpo_caso(
            tipo_id=tipo_procedimiento_ok,
            doc_id="CC-SIN-TG",
            cirujano_id=med["codigo_registro"],
            cirujano_nombre=med["nombre_completo"],
        ),
    )
    assert crear.status_code == 201
    caso_id = crear.json()["id"]

    resp = await cliente_api.get(
        f"/api/staff/casos/{caso_id}/conversacion",
        headers=cabecera_staff,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_resumen_caso(
    app_api,
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    tipo_procedimiento_ok: str,
    medico_activo_catalogo: dict[str, str | None],
) -> None:
    chat_id = 88004
    caso_id = await _crear_caso_y_vinculo(
        app_api,
        cliente_api,
        cabecera_staff,
        tipo_procedimiento_ok,
        medico_activo_catalogo,
        chat_id=chat_id,
    )
    await _sembrar_hilo_conversacion(app_api, chat_id)
    await _crear_alerta_pendiente(app_api, caso_id)

    resp = await cliente_api.get(
        f"/api/staff/casos/{caso_id}/resumen",
        headers=cabecera_staff,
    )
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["vinculado_telegram"] is True
    assert cuerpo["conteo_mensajes"] == 2
    assert cuerpo["ultima_severidad"] == "urgente"
    assert cuerpo["proximo_recordatorio_at"] is not None


@pytest.mark.asyncio
async def test_reanudar_hitl_sin_pendiente(
    app_api,
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    tipo_procedimiento_ok: str,
    medico_activo_catalogo: dict[str, str | None],
) -> None:
    chat_id = 88005
    caso_id = await _crear_caso_y_vinculo(
        app_api,
        cliente_api,
        cabecera_staff,
        tipo_procedimiento_ok,
        medico_activo_catalogo,
        chat_id=chat_id,
    )

    resp = await cliente_api.post(
        f"/api/staff/casos/{caso_id}/reanudar-hitl",
        headers=cabecera_staff,
        json={"decision": "approve"},
    )
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["reanudado"] is False
    assert cuerpo["session_id"] == f"telegram:{chat_id}"


@pytest.mark.asyncio
async def test_openapi_tag_staff_seguimiento(cliente_api: AsyncClient) -> None:
    resp = await cliente_api.get("/openapi.json")
    assert resp.status_code == 200
    rutas = resp.json()["paths"]
    assert "/api/staff/alertas" in rutas
    get_alertas = rutas["/api/staff/alertas"]["get"]
    assert "staff-seguimiento" in get_alertas.get("tags", [])
