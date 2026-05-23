"""Tool ``obtener_contexto_caso``."""

from __future__ import annotations

from langchain_core.tools import tool

from src.agentes.contexto import (
    obtener_session_factory_runtime,
    obtener_session_id_runtime,
)
from src.agentes.tools.esquemas import SalidaContextoCaso
from src.agentes.tools.resolver_caso import resolver_caso_activo_por_session


@tool("obtener_contexto_caso")
async def obtener_contexto_caso() -> SalidaContextoCaso:
    """
    Lee metadatos del caso postoperatorio vinculado al chat de Telegram actual.

    Usar al inicio de la conversacion o cuando falte contexto del paciente.
    """
    factory = obtener_session_factory_runtime()
    session_id = obtener_session_id_runtime()
    async with factory() as sesion:
        ctx = await resolver_caso_activo_por_session(sesion, session_id)
        if ctx is None:
            return SalidaContextoCaso(vinculado=False)
        return SalidaContextoCaso(
            vinculado=True,
            paciente_nombre=ctx.paciente_nombre,
            nombre_procedimiento=ctx.nombre_procedimiento,
            fecha_cirugia=ctx.fecha_cirugia.isoformat(),
            notas_especificas=ctx.notas_especificas,
            caso_id=str(ctx.caso_id),
            tipo_procedimiento_id=str(ctx.tipo_procedimiento_id),
        )
