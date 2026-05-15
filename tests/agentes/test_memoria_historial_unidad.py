"""Pruebas unitarias de memoria conversacional (sin PostgreSQL)."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import psycopg
import pytest
from langchain_core.messages import AIMessage, HumanMessage

from src.agentes.memoria.historial import (
    MemoriaConexionError,
    aplicar_tope_turnos_ultimos,
    conectar_memoria_sync,
    normalizar_session_id_postgres_langchain,
)
from src.persistencia.repositorios.sesiones import sesion_id_memoria_langchain


def test_normalizar_session_id_acepta_user_prefijo() -> None:
    uid = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
    canon = sesion_id_memoria_langchain(uid)
    assert normalizar_session_id_postgres_langchain(canon) == str(uid)


def test_normalizar_session_id_acepta_uuid_plano() -> None:
    uid = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
    assert normalizar_session_id_postgres_langchain(str(uid)) == str(uid)


def test_normalizar_session_id_rechaza_basura() -> None:
    with pytest.raises(ValueError, match="session_id"):
        normalizar_session_id_postgres_langchain("no-es-uuid")


def test_aplicar_tope_turnos_ultimos() -> None:
    mensajes = [
        HumanMessage(content="h1"),
        AIMessage(content="a1"),
        HumanMessage(content="h2"),
        AIMessage(content="a2"),
        HumanMessage(content="h3"),
        AIMessage(content="a3"),
    ]
    recortado = aplicar_tope_turnos_ultimos(mensajes, turnos_max=2)
    assert [m.content for m in recortado] == ["h2", "a2", "h3", "a3"]


def test_conectar_memoria_sync_operational_error_en_espanol() -> None:
    with patch("src.agentes.memoria.historial.psycopg.connect") as mock_c:
        mock_c.side_effect = psycopg.OperationalError("simulado")
        with pytest.raises(MemoriaConexionError, match="No se pudo conectar"):
            conectar_memoria_sync("postgresql://usuario:clave@127.0.0.1:5432/app")
