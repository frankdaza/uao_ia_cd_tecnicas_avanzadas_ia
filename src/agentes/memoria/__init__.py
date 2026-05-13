"""Memoria conversacional persistente (LangChain + PostgreSQL)."""

from src.agentes.memoria.historial import (
    MemoriaConexionError,
    MemoriaUsuario,
    borrar_ultimo_turno_en_pool,
    consultar_max_created_at_chat_pool,
    inicializar_esquema_memoria_chat,
    normalizar_session_id_postgres_langchain,
)

__all__ = [
    "MemoriaUsuario",
    "MemoriaConexionError",
    "borrar_ultimo_turno_en_pool",
    "consultar_max_created_at_chat_pool",
    "inicializar_esquema_memoria_chat",
    "normalizar_session_id_postgres_langchain",
]
