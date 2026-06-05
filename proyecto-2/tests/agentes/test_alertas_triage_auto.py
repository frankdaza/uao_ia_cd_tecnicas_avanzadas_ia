"""Pruebas de persistencia automatica de alertas de triage."""

from __future__ import annotations

import pytest
from langchain_core.messages import ToolMessage
from sqlalchemy import select

from src.api.servicios.alertas_triage_auto import (
    asegurar_alerta_desde_turno,
    escalar_creo_alerta_en_turno,
    resolver_severidad_turno,
)
from src.persistencia.modelos import AlertaTriage


def test_resolver_severidad_turno_heuristica_sangrado() -> None:
    severidad, rationale = resolver_severidad_turno({}, "Tengo mucho sangrado en la herida")
    assert severidad == "urgente"
    assert rationale


def test_escalar_creo_alerta_en_turno_true() -> None:
    estado = {
        "messages": [
            ToolMessage(
                content='{"alerta_id": "abc-123", "mensaje": "ok"}',
                name="escalar_a_equipo",
                tool_call_id="1",
            ),
        ]
    }
    assert escalar_creo_alerta_en_turno(estado) is True


@pytest.mark.asyncio
async def test_asegurar_alerta_desde_turno_crea_urgente(
    factory_sqlite,
    caso_vinculado_telegram_123,
) -> None:
    estado = {
        "messages": [
            ToolMessage(
                content='{"severidad": "urgente", "rationale": "Sangrado detectado."}',
                name="clasificar_triage",
                tool_call_id="1",
            ),
        ]
    }
    mensaje = "Tengo mucho sangrado, creo que se me abrio la herida"
    alerta_id = await asegurar_alerta_desde_turno(
        session_factory=factory_sqlite,
        session_id="telegram:123",
        mensaje_paciente=mensaje,
        estado=estado,
    )
    assert alerta_id is not None
    async with factory_sqlite() as sesion:
        res = await sesion.execute(select(AlertaTriage))
        filas = list(res.scalars().all())
    assert len(filas) == 1
    assert filas[0].severidad == "urgente"
    assert filas[0].mensaje_paciente_ref == mensaje
    assert filas[0].tool_trace_json == {
        "origen": "auto_triage",
        "session_id": "telegram:123",
    }


@pytest.mark.asyncio
async def test_asegurar_alerta_no_duplica_si_escalar_ya_corrio(
    factory_sqlite,
    caso_vinculado_telegram_123,
) -> None:
    estado = {
        "messages": [
            ToolMessage(
                content='{"severidad": "urgente", "rationale": "Alarma"}',
                name="clasificar_triage",
                tool_call_id="1",
            ),
            ToolMessage(
                content='{"alerta_id": "existente", "mensaje": "Alerta registrada"}',
                name="escalar_a_equipo",
                tool_call_id="2",
            ),
        ]
    }
    alerta_id = await asegurar_alerta_desde_turno(
        session_factory=factory_sqlite,
        session_id="telegram:123",
        mensaje_paciente="Tengo sangrado abundante",
        estado=estado,
    )
    assert alerta_id is None
    async with factory_sqlite() as sesion:
        res = await sesion.execute(select(AlertaTriage))
        assert len(list(res.scalars().all())) == 0


@pytest.mark.asyncio
async def test_asegurar_alerta_no_crea_con_hitl_pendiente(
    factory_sqlite,
    caso_vinculado_telegram_123,
) -> None:
    from src.agentes.estado_hitl import AgenteHitlEstado, registrar_agente_hitl_runtime

    registrar_agente_hitl_runtime(AgenteHitlEstado(habilitado=True))

    estado = {
        "__interrupt__": [{"value": "pendiente"}],
        "messages": [
            ToolMessage(
                content='{"severidad": "urgente", "rationale": "Alarma"}',
                name="clasificar_triage",
                tool_call_id="1",
            ),
        ],
    }
    alerta_id = await asegurar_alerta_desde_turno(
        session_factory=factory_sqlite,
        session_id="telegram:123",
        mensaje_paciente="Tengo sangrado abundante",
        estado=estado,
    )
    assert alerta_id is None
    async with factory_sqlite() as sesion:
        res = await sesion.execute(select(AlertaTriage))
        assert len(list(res.scalars().all())) == 0

    registrar_agente_hitl_runtime(None)
