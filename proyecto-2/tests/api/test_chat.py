"""Pruebas de ``POST /chat`` (TASK-104)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from langchain_core.messages import AIMessage

from src.agentes.servicio import extraer_fuentes_respuesta, extraer_severidad_triage
from src.persistencia.repositorios.casos_postoperatorio import RepositorioCasosPostoperatorio
from src.persistencia.repositorios.tipos_procedimiento import RepositorioTiposProcedimiento
from src.persistencia.repositorios.vinculos_telegram import RepositorioVinculosTelegram


async def _sembrar_vinculo_telegram_123(app_api) -> None:
    from datetime import date

    factory = app_api.state.session_factory
    async with factory() as sesion:
        repo_t = RepositorioTiposProcedimiento(sesion)
        tipo = await repo_t.crear(codigo="chat-demo", nombre="Procedimiento chat")
        repo_c = RepositorioCasosPostoperatorio(sesion)
        caso = await repo_c.crear(
            paciente_doc_id="CC-CHAT-1",
            paciente_nombre="Paciente Chat",
            tipo_procedimiento_id=tipo.id,
            cirujano_id="DOC-CHAT",
            cirujano_nombre="Dr. Chat",
            fecha_cirugia=date(2026, 5, 1),
        )
        repo_v = RepositorioVinculosTelegram(sesion)
        await repo_v.crear(
            caso_id=caso.id,
            telegram_chat_id=123,
            vinculado_at=datetime.now(UTC),
        )
        await sesion.commit()


@pytest.mark.asyncio
async def test_chat_200_respuesta_mock(
    cliente_api: AsyncClient,
    app_api,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _sembrar_vinculo_telegram_123(app_api)

    async def _invocar_mock(**_kwargs):
        return {
            "messages": [
                AIMessage(content="Puede caminar con moderacion segun su protocolo."),
            ]
        }

    monkeypatch.setattr(
        "src.api.servicios.chat.invocar_agente",
        _invocar_mock,
    )

    resp = await cliente_api.post(
        "/chat",
        json={
            "session_id": "telegram:123",
            "mensaje": "¿Cuando puedo caminar?",
            "metadata": {"canal": "telegram", "update_id": 99},
        },
    )
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["respuesta"].strip()
    assert cuerpo["requiere_revision_humana"] is False
    assert cuerpo["error"] is None


@pytest.mark.asyncio
async def test_chat_403_sin_vinculo(cliente_api: AsyncClient) -> None:
    resp = await cliente_api.post(
        "/chat",
        json={
            "session_id": "telegram:999",
            "mensaje": "Hola",
        },
    )
    assert resp.status_code == 403
    detalle = resp.json()["detail"]
    assert "vinculada" in detalle.lower() or "vincul" in detalle.lower()
    assert "codigo" in detalle.lower() or "emparejamiento" in detalle.lower()


@pytest.mark.asyncio
async def test_chat_503_timeout(
    cliente_api: AsyncClient,
    app_api,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _sembrar_vinculo_telegram_123(app_api)

    async def _invocar_lento(**_kwargs):
        await asyncio.sleep(2.0)
        return {"messages": [AIMessage(content="tarde")]}

    async def _wait_for_corto(coro, timeout):
        del timeout
        return await asyncio.wait_for(coro, timeout=0.05)

    monkeypatch.setattr(
        "src.api.servicios.chat.invocar_agente",
        _invocar_lento,
    )
    monkeypatch.setattr(
        "src.api.servicios.chat.asyncio.wait_for",
        _wait_for_corto,
    )

    resp = await cliente_api.post(
        "/chat",
        json={
            "session_id": "telegram:123",
            "mensaje": "Consulta lenta",
        },
    )
    assert resp.status_code == 503
    detalle = resp.json()["detail"]
    assert "tiempo" in detalle.lower() or "respondio" in detalle.lower()
    assert "sk-" not in detalle
    assert "OPENAI" not in detalle.upper()


@pytest.mark.asyncio
async def test_openapi_documenta_chat(cliente_api: AsyncClient) -> None:
    resp = await cliente_api.get("/openapi.json")
    assert resp.status_code == 200
    esquema = resp.json()
    assert "ChatPeticion" in esquema["components"]["schemas"]
    assert "ChatRespuesta" in esquema["components"]["schemas"]
    rutas = esquema["paths"]
    assert "/chat" in rutas
    assert "post" in rutas["/chat"]
    tags = rutas["/chat"]["post"].get("tags", [])
    assert "chat" in tags


def test_extraer_severidad_y_fuentes_desde_estado() -> None:
    from langchain_core.messages import ToolMessage

    estado = {
        "messages": [
            ToolMessage(
                content='{"severidad": "urgente", "rationale": "Alarma"}',
                name="clasificar_triage",
                tool_call_id="1",
            ),
            ToolMessage(
                content="[1] Evitar esfuerzo intenso.\n\n[2] Control de herida diario.",
                name="consultar_protocolo_rag",
                tool_call_id="2",
            ),
        ]
    }
    assert extraer_severidad_triage(estado) == "urgente"
    fuentes = extraer_fuentes_respuesta(estado)
    assert len(fuentes) == 2
    assert fuentes[0]["titulo"] == "Protocolo [1]"
