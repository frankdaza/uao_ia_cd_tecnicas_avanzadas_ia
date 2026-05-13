"""Tests del endpoint SSE POST /api/agente/stream."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool

from src.api.dependencias import obtener_sesion_db, obtener_usuario_actual
from src.agentes.memoria.historial import MemoriaConexionError
from src.api.esquemas import (
    EventoError,
    EventoFinal,
    EventoHerramienta,
    EventoPensamiento,
    EventoToken,
)
from src.api.main import crear_app
from src.api.routers import agente as agente_mod
from src.agentes.router import crear_grafo_agente
from src.persistencia.modelos import Usuario
from src.persistencia.repositorios.sesiones import sesion_id_memoria_langchain
from tests.agentes.test_router_grafo import (
    _ListaRouterFalso,
    _MemoriaFalsa,
    _meta_prompt_minimo,
    _tool_faq_falsa,
    _tool_rag_falsa,
)


@pytest.fixture
def herramientas_kv() -> tuple[StructuredTool, StructuredTool]:
    return (_tool_faq_falsa(), _tool_rag_falsa())


def _parsear_eventos_sse(cuerpo: bytes) -> list[tuple[str, dict[str, Any]]]:
    salida: list[tuple[str, dict[str, Any]]] = []
    buffer = cuerpo.decode("utf-8", errors="replace")
    evento_actual: str | None = None
    for linea in buffer.splitlines():
        if linea.startswith("event:"):
            evento_actual = linea.split(":", 1)[1].strip()
        elif linea.startswith("data:") and evento_actual:
            raw = linea[5:].strip()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            salida.append((evento_actual, payload))
            evento_actual = None
    return salida


@pytest.mark.asyncio
async def test_agente_stream_emite_eventos_parseables(
    herramientas_kv: tuple[StructuredTool, StructuredTool],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /api/agente/stream emite JSON validado por los modelos Pydantic de eventos."""
    faq_t, rag_t = herramientas_kv
    uid = uuid.UUID("00000000-0000-4000-8000-00000000c0de")
    usuario = MagicMock(spec=Usuario)
    usuario.id = uid
    usuario.nombre = "Tester"
    usuario.documento_identidad = "123"

    async def override_sesion() -> AsyncIterator[AsyncMock]:
        yield AsyncMock()

    async def override_usuario() -> Usuario:
        return usuario  # type: ignore[return-value]

    router_llm = _ListaRouterFalso(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "rag_denso",
                        "args": {"consulta": "politica"},
                        "id": "c1",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    )
    compositor = FakeListChatModel(responses=["Texto final del agente para SSE."])
    grafo = crear_grafo_agente(
        llm_router=router_llm,
        llm_compositor=compositor,
        meta_prompt=_meta_prompt_minimo(),
        herramientas=[faq_t, rag_t],
    )

    mem = _MemoriaFalsa()
    mem.cerrar = lambda: None  # type: ignore[method-assign]

    monkeypatch.setattr(
        agente_mod,
        "MemoriaUsuario",
        lambda *args, **kwargs: mem,
    )

    app = crear_app()
    pool = MagicMock()
    ctx = MagicMock()
    ctx.__enter__.return_value = MagicMock()
    ctx.__exit__.return_value = None
    pool.connection.return_value = ctx
    app.state.psycopg_pool = pool
    app.dependency_overrides[obtener_sesion_db] = override_sesion
    app.dependency_overrides[obtener_usuario_actual] = override_usuario
    app.state.grafo_agente = grafo

    session_id = sesion_id_memoria_langchain(uid)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async with client.stream(
            "POST",
            "/api/agente/stream",
            headers={"X-Session-Id": session_id},
            json={
                "session_id": session_id,
                "pregunta": "Consulta de prueba",
                "primer_turno": False,
            },
        ) as response:
            assert response.status_code == 200
            cuerpo = await response.aread()

    eventos = _parsear_eventos_sse(cuerpo)
    tipos = [e for e, _ in eventos]
    assert "pensamiento" in tipos
    assert "herramienta" in tipos
    assert "token" in tipos
    assert "fuentes" in tipos
    assert "final" in tipos

    for nombre, payload in eventos:
        if nombre == "pensamiento":
            EventoPensamiento.model_validate(payload)
        elif nombre == "herramienta":
            EventoHerramienta.model_validate(payload)
        elif nombre == "token":
            EventoToken.model_validate(payload)
        elif nombre == "final":
            EventoFinal.model_validate(payload)


@pytest.mark.asyncio
async def test_agente_stream_401_sin_credencial(fastapi_app_sesion_mock: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app_sesion_mock),
        base_url="http://test",
    ) as client:
        resp = await client.post(
            "/api/agente/stream",
            json={
                "session_id": "user:00000000-0000-4000-8000-00000000ab01",
                "pregunta": "Hola",
                "primer_turno": True,
            },
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_agente_stream_403_session_id_no_alineado(
    fastapi_app_sesion_mock: FastAPI,
    herramientas_kv: tuple[StructuredTool, StructuredTool],
) -> None:
    uid_a = uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    uid_b = uuid.UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
    usuario = MagicMock(spec=Usuario)
    usuario.id = uid_a
    usuario.nombre = "A"
    usuario.documento_identidad = "1"

    async def _usuario_fijo() -> Usuario:
        return usuario  # type: ignore[return-value]

    faq_t, rag_t = herramientas_kv
    grafo = crear_grafo_agente(
        llm_router=_ListaRouterFalso([AIMessage(content="ok")]),
        llm_compositor=FakeListChatModel(responses=["x"]),
        meta_prompt=_meta_prompt_minimo(),
        herramientas=[faq_t, rag_t],
    )
    fastapi_app_sesion_mock.state.grafo_agente = grafo
    fastapi_app_sesion_mock.dependency_overrides[obtener_usuario_actual] = _usuario_fijo
    try:
        sid_a = sesion_id_memoria_langchain(uid_a)
        sid_b = sesion_id_memoria_langchain(uid_b)
        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app_sesion_mock),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/api/agente/stream",
                headers={"X-Session-Id": sid_a},
                json={
                    "session_id": sid_b,
                    "pregunta": "Hola",
                    "primer_turno": False,
                },
            )
    finally:
        del fastapi_app_sesion_mock.dependency_overrides[obtener_usuario_actual]

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_agente_stream_503_sin_grafo(fastapi_app_sesion_mock: FastAPI) -> None:
    uid = uuid.UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
    usuario = MagicMock(spec=Usuario)
    usuario.id = uid
    usuario.nombre = "C"
    usuario.documento_identidad = "3"

    async def _usuario_fijo() -> Usuario:
        return usuario  # type: ignore[return-value]

    fastapi_app_sesion_mock.state.grafo_agente = None
    fastapi_app_sesion_mock.dependency_overrides[obtener_usuario_actual] = _usuario_fijo
    try:
        sid = sesion_id_memoria_langchain(uid)
        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app_sesion_mock),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/api/agente/stream",
                headers={"X-Session-Id": sid},
                json={
                    "session_id": sid,
                    "pregunta": "Hola",
                    "primer_turno": True,
                },
            )
    finally:
        del fastapi_app_sesion_mock.dependency_overrides[obtener_usuario_actual]
        fastapi_app_sesion_mock.state.grafo_agente = None

    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_agente_stream_emite_evento_error_memoria_postgres(
    herramientas_kv: tuple[StructuredTool, StructuredTool],
    monkeypatch: pytest.MonkeyPatch,
    fastapi_app_sesion_mock: FastAPI,
) -> None:
    class _MemoriaQueFalla:
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise MemoriaConexionError("postgres no disponible en prueba")

    monkeypatch.setattr(agente_mod, "MemoriaUsuario", _MemoriaQueFalla)

    faq_t, rag_t = herramientas_kv
    uid = uuid.UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
    usuario = MagicMock(spec=Usuario)
    usuario.id = uid
    usuario.nombre = "D"
    usuario.documento_identidad = "4"

    async def _usuario_fijo() -> Usuario:
        return usuario  # type: ignore[return-value]

    router_llm = _ListaRouterFalso(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "rag_denso",
                        "args": {"consulta": "x"},
                        "id": "c1",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    )
    compositor = FakeListChatModel(responses=["Texto final."])
    grafo = crear_grafo_agente(
        llm_router=router_llm,
        llm_compositor=compositor,
        meta_prompt=_meta_prompt_minimo(),
        herramientas=[faq_t, rag_t],
    )
    fastapi_app_sesion_mock.state.grafo_agente = grafo
    fastapi_app_sesion_mock.dependency_overrides[obtener_usuario_actual] = _usuario_fijo
    sid = sesion_id_memoria_langchain(uid)
    try:
        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app_sesion_mock),
            base_url="http://test",
        ) as client:
            async with client.stream(
                "POST",
                "/api/agente/stream",
                headers={"X-Session-Id": sid},
                json={
                    "session_id": sid,
                    "pregunta": "Pregunta",
                    "primer_turno": False,
                },
            ) as response:
                assert response.status_code == 200
                cuerpo = await response.aread()
    finally:
        del fastapi_app_sesion_mock.dependency_overrides[obtener_usuario_actual]

    eventos = _parsear_eventos_sse(cuerpo)
    errores = [(e, p) for e, p in eventos if e == "error"]
    assert len(errores) == 1
    EventoError.model_validate(errores[0][1])
    assert errores[0][1]["codigo"] == "memoria_postgres"
    nombres = [e for e, _ in eventos]
    assert "final" not in nombres
