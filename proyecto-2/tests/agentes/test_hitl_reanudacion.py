"""Pruebas de reanudacion HITL antes de turnos nuevos (tool_call huérfano)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command

from src.agentes.servicio import invocar_agente, reanudar_hitl_si_pendiente


@pytest.mark.asyncio
async def test_reanudar_hitl_si_pendiente_no_op_sin_next() -> None:
    agente = AsyncMock()
    snap = MagicMock()
    snap.next = ()
    agente.aget_state = AsyncMock(return_value=snap)

    resultado = await reanudar_hitl_si_pendiente(
        agente,
        session_id="telegram:1",
        contexto={"session_id": "telegram:1"},
    )

    assert resultado is None
    agente.ainvoke.assert_not_called()


@pytest.mark.asyncio
async def test_reanudar_hitl_si_pendiente_envia_command() -> None:
    agente = AsyncMock()
    snap = MagicMock()
    snap.next = ("model",)
    agente.aget_state = AsyncMock(return_value=snap)
    agente.ainvoke = AsyncMock(return_value={"messages": []})

    await reanudar_hitl_si_pendiente(
        agente,
        session_id="telegram:1",
        contexto={"session_id": "telegram:1"},
        decision="reject",
    )

    agente.ainvoke.assert_awaited_once()
    entrada = agente.ainvoke.await_args.args[0]
    assert isinstance(entrada, Command)
    assert entrada.resume == {"decisions": [{"type": "reject"}]}


@pytest.mark.asyncio
async def test_invocar_agente_reanuda_antes_de_human_message() -> None:
    from src.agentes.estado_hitl import AgenteHitlEstado, registrar_agente_hitl_runtime

    registrar_agente_hitl_runtime(AgenteHitlEstado(habilitado=True))

    invocaciones: list[object] = []

    class AgenteMock:
        async def aget_state(self, _config: dict) -> MagicMock:
            snap = MagicMock()
            snap.next = ("model",) if not invocaciones else ()
            return snap

        async def ainvoke(self, entrada: object, **kwargs: object) -> dict:
            invocaciones.append(entrada)
            if isinstance(entrada, Command):
                return {"messages": []}
            return {"messages": [AIMessage(content="Respuesta tras reanudar.")]}

    factory = MagicMock()
    sesion = AsyncMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=sesion)
    factory.return_value.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("src.agentes.servicio.construir_agente_taam", return_value=AgenteMock()),
        patch(
            "src.agentes.servicio._construir_contexto_invoke",
            new_callable=AsyncMock,
            return_value={"session_id": "telegram:99"},
        ),
        patch("src.agentes.servicio.establecer_contexto_runtime"),
        patch("src.agentes.servicio.limpiar_contexto_runtime"),
    ):
        estado = await invocar_agente(
            session_factory=factory,
            checkpointer=MagicMock(),
            session_id="telegram:99",
            mensaje="¿Cuales son mis medicamentos?",
        )

    assert len(invocaciones) == 2
    assert isinstance(invocaciones[0], Command)
    assert "messages" in invocaciones[1]
    assert isinstance(invocaciones[1]["messages"][0], HumanMessage)
    assert estado["messages"][0].content == "Respuesta tras reanudar."
    registrar_agente_hitl_runtime(None)
