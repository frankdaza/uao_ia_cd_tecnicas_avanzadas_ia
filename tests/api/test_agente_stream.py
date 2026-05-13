"""Tests del endpoint SSE POST /api/agente/stream."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool

from src.api.dependencias import obtener_sesion_db, obtener_usuario_actual
from src.api.esquemas import EventoFinal, EventoHerramienta, EventoPensamiento, EventoToken
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
        "crear_memoria_usuario",
        lambda *_a, **_k: mem,
    )

    app = crear_app()
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
