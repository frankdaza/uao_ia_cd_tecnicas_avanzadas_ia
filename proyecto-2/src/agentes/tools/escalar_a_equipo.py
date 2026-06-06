"""Tool ``escalar_a_equipo`` — persiste ``alertas_triage``."""

from __future__ import annotations

import logging

from langchain_core.tools import tool

from src.agentes.contexto import (
    obtener_session_factory_runtime,
    obtener_session_id_runtime,
)
from src.agentes.tools.esquemas import EntradaEscalarEquipo, SalidaEscalarEquipo
from src.agentes.tools.resolver_caso import resolver_caso_activo_por_session
from src.agentes.contexto import obtener_adjuntos_turno_runtime
from src.api.servicios.vincular_adjuntos_alerta import (
    enriquecer_resumen_con_adjuntos,
    vincular_adjuntos_turno_a_alerta,
)
from src.persistencia.repositorios.alertas_triage import RepositorioAlertasTriage

logger = logging.getLogger(__name__)

_MENSAJE_SIN_CASO = "No hay caso vinculado; no se pudo crear la alerta."
_MENSAJE_ERROR = "No se pudo registrar la alerta; el equipo revisara manualmente."


@tool("escalar_a_equipo", args_schema=EntradaEscalarEquipo)
async def escalar_a_equipo(
    severidad: str,
    resumen: str,
    mensaje_paciente_ref: str | None = None,
) -> SalidaEscalarEquipo:
    """
    Crea una alerta de triage para revision del personal clinico (UC-MVP-05).

    Esta accion esta sujeta a Human-in-the-loop antes de ejecutarse en produccion.
    """
    factory = obtener_session_factory_runtime()
    session_id = obtener_session_id_runtime()

    async with factory() as sesion:
        ctx = await resolver_caso_activo_por_session(sesion, session_id)
        if ctx is None:
            return SalidaEscalarEquipo(alerta_id="", mensaje=_MENSAJE_SIN_CASO)

        try:
            repo = RepositorioAlertasTriage(sesion)
            hay_adjuntos = bool(obtener_adjuntos_turno_runtime())
            resumen_final = enriquecer_resumen_con_adjuntos(resumen, hay_adjuntos)[:1024]
            fila = await repo.crear(
                caso_id=ctx.caso_id,
                severidad=severidad,
                resumen=resumen_final,
                mensaje_paciente_ref=mensaje_paciente_ref,
                tool_trace_json={
                    "session_id": session_id,
                    "tool": "escalar_a_equipo",
                },
            )
            await vincular_adjuntos_turno_a_alerta(sesion, fila.id)
            await sesion.commit()
            return SalidaEscalarEquipo(
                alerta_id=str(fila.id),
                mensaje="Alerta registrada para revision del equipo clinico.",
            )
        except Exception:
            logger.exception("Fallo escalar_a_equipo")
            await sesion.rollback()
            return SalidaEscalarEquipo(alerta_id="", mensaje=_MENSAJE_ERROR)
