"""Lectura del historial conversacional desde el checkpointer LangGraph."""

from __future__ import annotations

import uuid

from langgraph.checkpoint.base import BaseCheckpointSaver
from sqlalchemy.ext.asyncio import AsyncSession

from src.agentes.agente_taam import construir_agente_taam
from src.api.esquemas_seguimiento import AdjuntoMensajeVista, MensajeConversacionVista
from src.api.servicios.vistas_adjuntos import agrupar_adjuntos_por_indice
from src.persistencia.repositorios.adjuntos_mensaje import RepositorioAdjuntosMensaje


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


def _extraer_adjuntos_kwargs(msg: object) -> list[AdjuntoMensajeVista]:
    kwargs = getattr(msg, "additional_kwargs", None)
    if not isinstance(kwargs, dict):
        return []
    raw = kwargs.get("adjuntos")
    if not isinstance(raw, list):
        return []
    vistas: list[AdjuntoMensajeVista] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        aid = item.get("id")
        tipo = item.get("tipo")
        if not isinstance(aid, str) or tipo not in ("imagen", "video", "audio", "multimedia"):
            continue
        try:
            uid = uuid.UUID(aid)
        except ValueError:
            continue
        tipo_vista = "imagen" if tipo == "multimedia" else tipo
        vistas.append(
            AdjuntoMensajeVista(
                id=uid,
                tipo=tipo_vista,  # type: ignore[arg-type]
                mime_type="application/octet-stream",
                caption=None,
                url=f"/api/staff/adjuntos/{uid}",
            )
        )
    return vistas


async def listar_mensajes_hilo(
    checkpointer: BaseCheckpointSaver,
    session_id: str,
    *,
    caso_id: uuid.UUID | None = None,
    sesion_db: AsyncSession | None = None,
) -> list[MensajeConversacionVista]:
    """
    Mensajes human/assistant del estado del grafo para ``thread_id`` = ``session_id``.

    No incluye mensajes ``tool`` ni otros roles internos.
    """
    agente = construir_agente_taam(checkpointer)
    snap = await agente.aget_state({"configurable": {"thread_id": session_id}})
    if snap is None or not snap.values:
        return []

    adjuntos_por_indice: dict[int, list[AdjuntoMensajeVista]] = {}
    if caso_id is not None and sesion_db is not None:
        repo = RepositorioAdjuntosMensaje(sesion_db)
        filas = await repo.listar_por_caso(caso_id)
        adjuntos_por_indice = agrupar_adjuntos_por_indice(filas)

    vistas: list[MensajeConversacionVista] = []
    for msg in snap.values.get("messages", []):
        rol = _normalizar_rol(msg)
        if rol is None:
            continue
        texto = _extraer_texto_mensaje(msg)
        indice = len(vistas)
        adjuntos = adjuntos_por_indice.get(indice, [])
        if rol == "human" and not adjuntos:
            adjuntos = _extraer_adjuntos_kwargs(msg)
        if not texto and not adjuntos:
            continue
        vistas.append(
            MensajeConversacionVista(
                rol=rol,  # type: ignore[arg-type]
                contenido=texto,
                indice=indice,
                adjuntos=adjuntos,
            )
        )
    return vistas


def contar_mensajes_hilo(mensajes: list[MensajeConversacionVista]) -> int:
    return len(mensajes)
