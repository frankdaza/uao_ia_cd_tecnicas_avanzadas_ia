"""Lectura del historial conversacional desde el checkpointer LangGraph."""

from __future__ import annotations

from langgraph.checkpoint.base import BaseCheckpointSaver

from src.agentes.agente_taam import construir_agente_taam
from src.api.esquemas_seguimiento import MensajeConversacionVista


def _normalizar_rol(msg: object) -> str | None:
    tipo = getattr(msg, "type", None) or getattr(msg, "role", None)
    if tipo in ("human", "user"):
        return "human"
    if tipo in ("ai", "assistant"):
        return "assistant"
    return None


def _extraer_texto_mensaje(msg: object) -> str:
    contenido = getattr(msg, "content", "")
    if isinstance(contenido, str):
        return contenido.strip()
    if isinstance(contenido, list):
        partes: list[str] = []
        for bloque in contenido:
            if isinstance(bloque, dict) and bloque.get("type") == "text":
                texto = bloque.get("text", "")
                if isinstance(texto, str) and texto.strip():
                    partes.append(texto.strip())
        return " ".join(partes).strip()
    return ""


async def listar_mensajes_hilo(
    checkpointer: BaseCheckpointSaver,
    session_id: str,
) -> list[MensajeConversacionVista]:
    """
    Mensajes human/assistant del estado del grafo para ``thread_id`` = ``session_id``.

    No incluye mensajes ``tool`` ni otros roles internos.
    """
    agente = construir_agente_taam(checkpointer)
    snap = await agente.aget_state({"configurable": {"thread_id": session_id}})
    if snap is None or not snap.values:
        return []

    vistas: list[MensajeConversacionVista] = []
    for msg in snap.values.get("messages", []):
        rol = _normalizar_rol(msg)
        if rol is None:
            continue
        texto = _extraer_texto_mensaje(msg)
        if not texto:
            continue
        vistas.append(
            MensajeConversacionVista(
                rol=rol,  # type: ignore[arg-type]
                contenido=texto,
                indice=len(vistas),
            )
        )
    return vistas


def contar_mensajes_hilo(mensajes: list[MensajeConversacionVista]) -> int:
    return len(mensajes)
