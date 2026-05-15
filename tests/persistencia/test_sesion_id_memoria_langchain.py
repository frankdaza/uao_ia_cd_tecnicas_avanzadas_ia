"""Pruebas del helper de session_id para memoria LangChain."""

from __future__ import annotations

import uuid

from src.persistencia.repositorios.sesiones import sesion_id_memoria_langchain


def test_sesion_id_memoria_langchain_formato_estable() -> None:
    uid = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
    assert sesion_id_memoria_langchain(uid) == "user:550e8400-e29b-41d4-a716-446655440000"
