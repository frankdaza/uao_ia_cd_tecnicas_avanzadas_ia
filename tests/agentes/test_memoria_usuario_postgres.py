"""
Integracion: ``MemoriaUsuario`` con PostgreSQL real.

Activa con ``EJECUTAR_INTEGRACION_POSTGRES=1`` y la misma URL que
``tests/persistencia/test_migracion_usuarios_postgres.py`` (variable
``INTEGRATION_POSTGRES_ASYNC_URL`` opcional).

Ejemplo::

    EJECUTAR_INTEGRACION_POSTGRES=1 \\
    INTEGRATION_POSTGRES_ASYNC_URL='postgresql+asyncpg://postgres:postgres@127.0.0.1:15432/app' \\
    uv run pytest tests/agentes/test_memoria_usuario_postgres.py -m integration_postgres
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime, timedelta

import psycopg
import pytest
from langchain_core.messages import HumanMessage, message_to_dict
from sqlalchemy.engine.url import make_url

from src.agentes.memoria.historial import (
    MemoriaUsuario,
    crear_memoria_usuario,
    inicializar_esquema_memoria_chat,
)
from src.api.configuracion import obtener_configuracion
from src.persistencia.repositorios.sesiones import sesion_id_memoria_langchain


@pytest.mark.integration_postgres
def test_memoria_usuario_persiste_y_ventana_dias() -> None:
    if os.environ.get("EJECUTAR_INTEGRACION_POSTGRES", "").strip() != "1":
        pytest.skip(
            "Define EJECUTAR_INTEGRACION_POSTGRES=1 y Postgres accesible "
            "(ver tests/persistencia/test_migracion_usuarios_postgres.py)."
        )

    obtener_configuracion.cache_clear()

    url_async = os.environ.get("INTEGRATION_POSTGRES_ASYNC_URL", "").strip()
    if not url_async:
        url_async = obtener_configuracion().url_base_datos_async()
    if not url_async.startswith("postgresql+asyncpg://"):
        pytest.skip("Se esperaba URL async de PostgreSQL para esta prueba.")

    sync_url = (
        make_url(url_async)
        .set(drivername="postgresql+psycopg")
        .render_as_string(hide_password=False)
    )

    uid = uuid.uuid4()
    sid = sesion_id_memoria_langchain(uid)

    try:
        conn = psycopg.connect(sync_url)
    except psycopg.OperationalError as exc:
        pytest.skip(f"Postgres no alcanzable: {exc}")

    try:
        inicializar_esquema_memoria_chat(sync_url)
        inicializar_esquema_memoria_chat(sync_url)

        mem = MemoriaUsuario(
            sid,
            conn,
            dias_max_defecto=365,
            turnos_max_defecto=50,
        )

        pasado = datetime.now(tz=UTC) - timedelta(days=40)
        payload = json.dumps(message_to_dict(HumanMessage(content="mensaje-antiguo")))
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO chat_history (session_id, message, created_at) "
                "VALUES (%s::uuid, %s::jsonb, %s)",
                (str(uid), payload, pasado),
            )
        conn.commit()

        mem.agregar_humano("mensaje-reciente")
        mem.agregar_ai("respuesta-reciente")

        ventana = mem.cargar_ventana(dias_max=10, turnos_max=20)
        textos = [m.content for m in ventana]
        assert "mensaje-antiguo" not in textos
        assert "mensaje-reciente" in textos
        assert "respuesta-reciente" in textos

        ventana_turnos = mem.cargar_ventana(dias_max=365, turnos_max=1)
        assert sum(1 for m in ventana_turnos if isinstance(m, HumanMessage)) == 1
        assert ventana_turnos[-1].content == "respuesta-reciente"

    finally:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM chat_history WHERE session_id = %s::uuid", (str(uid),))
            conn.commit()
        finally:
            conn.close()


@pytest.mark.integration_postgres
def test_memoria_usuario_crear_desde_conninfo_cierra() -> None:
    if os.environ.get("EJECUTAR_INTEGRACION_POSTGRES", "").strip() != "1":
        pytest.skip("Define EJECUTAR_INTEGRACION_POSTGRES=1.")

    obtener_configuracion.cache_clear()
    url_async = os.environ.get("INTEGRATION_POSTGRES_ASYNC_URL", "").strip()
    if not url_async:
        url_async = obtener_configuracion().url_base_datos_async()
    if not url_async.startswith("postgresql+asyncpg://"):
        pytest.skip("Se esperaba URL async de PostgreSQL para esta prueba.")

    sync_url = (
        make_url(url_async)
        .set(drivername="postgresql+psycopg")
        .render_as_string(hide_password=False)
    )

    uid = uuid.uuid4()
    sid = sesion_id_memoria_langchain(uid)

    try:
        inicializar_esquema_memoria_chat(sync_url)
    except psycopg.OperationalError as exc:
        pytest.skip(f"Postgres no alcanzable: {exc}")

    try:
        with crear_memoria_usuario(sid, sync_url) as mem:
            mem.agregar_humano("hola")
            mem.agregar_ai("hola-usuario")
            assert len(mem.cargar_ventana(dias_max=1, turnos_max=5)) >= 2
    except psycopg.OperationalError as exc:
        pytest.skip(f"Postgres no alcanzable: {exc}")

    conn = psycopg.connect(sync_url)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chat_history WHERE session_id = %s::uuid", (str(uid),))
        conn.commit()
    finally:
        conn.close()
