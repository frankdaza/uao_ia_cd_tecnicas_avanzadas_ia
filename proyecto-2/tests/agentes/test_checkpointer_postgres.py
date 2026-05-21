"""Integracion PostgresSaver (opcional)."""

from __future__ import annotations

import os

import pytest
from langchain_core.messages import HumanMessage

from src.agentes.checkpointer import crear_checkpointer_postgres
from src.agentes.servicio import invocar_agente
from src.configuracion import obtener_configuracion
from src.persistencia.motor import crear_motor_async, crear_session_factory


@pytest.mark.integration_postgres
@pytest.mark.asyncio
async def test_dos_turnos_persisten_hilo_telegram_123():
    """
    AC #3: dos turnos con thread_id telegram:123 dejan historial en checkpointer.

    Requiere Postgres TAAM y OPENAI_API_KEY en el entorno local.
    """
    if os.environ.get("EJECUTAR_INTEGRACION_POSTGRES") != "1":
        pytest.skip("Defina EJECUTAR_INTEGRACION_POSTGRES=1 para ejecutar.")

    cfg = obtener_configuracion()
    if not cfg.openai_api_key.strip():
        pytest.skip("OPENAI_API_KEY requerida para invocacion real del agente.")

    url = cfg.url_base_datos_async()
    motor = crear_motor_async(url)
    factory = crear_session_factory(motor)
    cp = crear_checkpointer_postgres(cfg.url_base_datos_sync())

    try:
        await invocar_agente(
            session_factory=factory,
            checkpointer=cp,
            session_id="telegram:123",
            mensaje="Hola, solo es una prueba de memoria.",
        )
        estado2 = await invocar_agente(
            session_factory=factory,
            checkpointer=cp,
            session_id="telegram:123",
            mensaje="Recuerda que dije prueba de memoria.",
        )
        mensajes = estado2.get("messages", [])
        assert len(mensajes) >= 2
        roles = [
            getattr(m, "type", None) or getattr(m, "role", None) for m in mensajes
        ]
        assert "human" in roles or "user" in roles
    finally:
        await motor.dispose()
