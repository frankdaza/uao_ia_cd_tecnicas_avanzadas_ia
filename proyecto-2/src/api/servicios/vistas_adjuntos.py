"""Mapeo de adjuntos ORM a vistas API staff."""

from __future__ import annotations

import uuid
from collections import defaultdict

from src.api.esquemas_seguimiento import AdjuntoMensajeVista
from src.persistencia.modelos import AdjuntoMensaje


def adjunto_a_vista(adjunto: AdjuntoMensaje) -> AdjuntoMensajeVista:
    return AdjuntoMensajeVista(
        id=adjunto.id,
        tipo=adjunto.tipo,  # type: ignore[arg-type]
        mime_type=adjunto.mime_type,
        caption=adjunto.caption,
        url=f"/api/staff/adjuntos/{adjunto.id}",
    )


def agrupar_adjuntos_por_indice(
    adjuntos: list[AdjuntoMensaje],
) -> dict[int, list[AdjuntoMensajeVista]]:
    agrupado: dict[int, list[AdjuntoMensajeVista]] = defaultdict(list)
    for adj in adjuntos:
        agrupado[adj.indice_hilo].append(adjunto_a_vista(adj))
    return dict(agrupado)


def adjuntos_por_alerta(
    filas: list[tuple[uuid.UUID, AdjuntoMensaje]],
) -> dict[uuid.UUID, list[AdjuntoMensajeVista]]:
    agrupado: dict[uuid.UUID, list[AdjuntoMensajeVista]] = defaultdict(list)
    for alerta_id, adj in filas:
        agrupado[alerta_id].append(adjunto_a_vista(adj))
    return dict(agrupado)
